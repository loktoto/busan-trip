#!/usr/bin/env python3
"""Tactical leveraged-ETF backtest using the unleveraged underlying for signals.

Examples: SPY->SSO, QQQ->QLD, SMH/SOXX->USD. The leveraged product's
actual adjusted prices determine P&L; returns are never approximated by simply
multiplying the underlying return.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from backtest import Config, indicators, load_config, load_features, load_prices
from data_audit import assert_price_continuity


@dataclass(frozen=True)
class LeverageConfig:
    max_holding_days: int = 42
    target_return: float = 0.20
    vol_exit_multiple: float = 1.25
    stop_lookback: int = 20
    recent_stress_lookback: int = 42
    transaction_cost_bps_each_side: float = 2.0
    slippage_bps_each_side: float = 4.0
    require_breadth_when_available: bool = True
    require_realized_vol_decline: bool = True

    @property
    def one_way_cost_bps(self) -> float:
        return self.transaction_cost_bps_each_side + self.slippage_bps_each_side


def align_histories(underlying: pd.DataFrame, leveraged: pd.DataFrame) -> pd.DataFrame:
    u = underlying.copy()
    l = leveraged.copy().rename(
        columns={c: f"lev_{c}" for c in ["Open", "High", "Low", "Close", "Volume"]}
    )
    x = u.merge(l, on="Date", how="inner").sort_values("Date").reset_index(drop=True)
    if len(x) < 260:
        raise ValueError("Aligned underlying/leveraged history requires at least 260 rows")
    return x


def _benchmark_path(
    x: pd.DataFrame,
    entry_index: int,
    exit_index: int,
    raw_entry_price: float,
    raw_exit_price: float,
    end_of_data_close: bool = False,
) -> dict:
    if end_of_data_close:
        underlying_marks = pd.concat(
            [
                x.loc[entry_index:exit_index, "Open"],
                pd.Series([float(x.loc[exit_index, "Close"])]),
            ],
            ignore_index=True,
        )
    else:
        underlying_marks = x.loc[entry_index:exit_index, "Open"].reset_index(drop=True)
    underlying_marks = underlying_marks.astype(float)
    underlying_return = float(underlying_marks.iloc[-1] / underlying_marks.iloc[0] - 1)
    daily = underlying_marks.pct_change().dropna().to_numpy(float)
    reset_factors = np.maximum(1.0 + 2.0 * daily, 1e-9)
    theoretical_daily_reset = float(np.prod(reset_factors) - 1.0)
    linear_two_x = float(2.0 * underlying_return)
    actual_gross = float(raw_exit_price / raw_entry_price - 1.0)
    return {
        "underlying_return": underlying_return,
        "linear_two_x_return": linear_two_x,
        "theoretical_daily_reset_two_x_return": theoretical_daily_reset,
        "actual_product_gross_return": actual_gross,
        "tracking_gap_vs_daily_reset": actual_gross - theoretical_daily_reset,
        "path_dependency_gap_vs_linear_two_x": theoretical_daily_reset - linear_two_x,
    }


def tactical_backtest(
    underlying: pd.DataFrame,
    leveraged: pd.DataFrame,
    bottom_cfg: Config,
    leverage_cfg: LeverageConfig,
    features: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, dict]:
    aligned = align_histories(underlying, leveraged)
    base_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
    x = indicators(aligned[base_cols], bottom_cfg, features)
    for c in ["lev_Open", "lev_High", "lev_Low", "lev_Close", "lev_Volume"]:
        x[c] = aligned[c].to_numpy()

    x["underlying_stop"] = x.Low.shift(1).rolling(leverage_cfg.stop_lookback).min()
    transition = x.confirmation & ~x.confirmation.shift(1, fill_value=False)
    breadth_available = "breadth_score_z" in x and x.breadth_score_z.notna().any()
    breadth_ok = pd.Series(True, index=x.index)
    if breadth_available and leverage_cfg.require_breadth_when_available:
        breadth_ok = x.breadth_score_z > x.breadth_score_z.shift(5)

    stress_now = (
        (x.cycle_dd <= -bottom_cfg.watch_dd)
        | x.exhaustion.fillna(False)
        | x.crash.fillna(False)
    )
    x["recent_bottom_stress"] = (
        stress_now.astype(int)
        .rolling(leverage_cfg.recent_stress_lookback, min_periods=1)
        .max()
        .astype(bool)
    )
    rv_declining = x.rv20 < x.rv20.shift(5)
    if not leverage_cfg.require_realized_vol_decline:
        rv_declining = pd.Series(True, index=x.index)
    x["leverage_entry_signal"] = (
        transition
        & x.recent_bottom_stress
        & (x.Close > x.sma20)
        & (x.sma10_slope > 0)
        & (x.atrp < x.atrp.shift(5))
        & rv_declining.fillna(False)
        & breadth_ok.fillna(False)
        & ~x.credit_veto
    )

    trades: list[dict] = []
    position: dict | None = None
    one_way = leverage_cfg.one_way_cost_bps / 10_000

    def close_position(
        pos: dict,
        exit_signal_index: int,
        exit_index: int,
        raw_exit_px: float,
        reasons: list[str],
        end_of_data_close: bool = False,
    ) -> dict:
        exit_px = raw_exit_px * (1 - one_way)
        window = x.iloc[int(pos["entry_index"]) : exit_index + 1]
        adverse = float((window.lev_Low / float(pos["entry_price"]) - 1).min())
        favourable = float((window.lev_High / float(pos["entry_price"]) - 1).max())
        benchmark = _benchmark_path(
            x,
            int(pos["entry_index"]),
            exit_index,
            float(pos["raw_entry_price"]),
            raw_exit_px,
            end_of_data_close=end_of_data_close,
        )
        return {
            **pos,
            "exit_signal_date": x.iloc[exit_signal_index].Date.date(),
            "exit_date": x.iloc[exit_index].Date.date(),
            "raw_exit_price": raw_exit_px,
            "exit_price": exit_px,
            "holding_days": exit_index - int(pos["entry_index"]),
            "exit_reasons": "|".join(reasons),
            "return_after_costs": exit_px / float(pos["entry_price"]) - 1,
            "max_adverse_excursion": adverse,
            "max_favourable_excursion": favourable,
            "one_way_cost_bps": leverage_cfg.one_way_cost_bps,
            **benchmark,
        }

    for i in range(200, len(x) - 1):
        r, nxt = x.iloc[i], x.iloc[i + 1]
        if position is None:
            if not bool(r.leverage_entry_signal):
                continue
            raw_entry_px = float(nxt.lev_Open)
            entry_px = raw_entry_px * (1 + one_way)
            position = {
                "signal_index": i,
                "entry_index": i + 1,
                "signal_date": r.Date.date(),
                "entry_date": nxt.Date.date(),
                "raw_entry_price": raw_entry_px,
                "entry_price": entry_px,
                "entry_underlying_signal_close": float(r.Close),
                "entry_underlying_open": float(nxt.Open),
                "underlying_stop": float(r.underlying_stop),
                "entry_atrp": float(r.atrp),
                "entry_rv20": float(r.rv20),
                "breadth_available": bool(breadth_available),
            }
            continue

        held = i - int(position["entry_index"]) + 1
        lev_return_close = float(r.lev_Close) / float(position["entry_price"]) - 1
        stop_fail = float(r.Close) < float(position["underlying_stop"])
        atr_exit = (
            float(r.atrp) >= float(position["entry_atrp"]) * leverage_cfg.vol_exit_multiple
            and float(r.atrp) > float(x.iloc[i - 5].atrp)
        )
        rv_exit = (
            float(r.rv20) >= float(position["entry_rv20"]) * leverage_cfg.vol_exit_multiple
            and float(r.rv20) > float(x.iloc[i - 5].rv20)
        )
        vol_exit = atr_exit or rv_exit
        structure_break = bool((r.Close < r.sma10) and (r.sma10_slope < 0))
        target_hit = lev_return_close >= leverage_cfg.target_return
        time_stop = held >= leverage_cfg.max_holding_days
        credit_exit = bool(r.credit_veto)
        reasons = [
            name
            for name, active in {
                "UNDERLYING_STOP_FAIL": stop_fail,
                "VOLATILITY_REACCELERATION": vol_exit,
                "RECOVERY_STRUCTURE_BREAK": structure_break,
                "TARGET_REACHED": target_hit,
                "TIME_STOP": time_stop,
                "CREDIT_VETO": credit_exit,
            }.items()
            if active
        ]
        if not reasons:
            continue

        trades.append(
            close_position(
                position,
                exit_signal_index=i,
                exit_index=i + 1,
                raw_exit_px=float(nxt.lev_Open),
                reasons=reasons,
            )
        )
        position = None

    # Do not silently drop an open losing or winning trade at the dataset boundary.
    # It is marked and liquidated at the final available close for audit purposes.
    if position is not None:
        last = len(x) - 1
        trades.append(
            close_position(
                position,
                exit_signal_index=last,
                exit_index=last,
                raw_exit_px=float(x.iloc[last].lev_Close),
                reasons=["END_OF_DATA"],
                end_of_data_close=True,
            )
        )

    t = pd.DataFrame(trades)
    summary = {
        "classification": "TACTICAL ACTUAL-PRODUCT RESEARCH — NOT A LONG-TERM HOLD",
        "trade_count": int(len(t)),
        "breadth_available": bool(breadth_available),
        "entry_requires_recent_bottom_stress": True,
        "entry_requires_falling_realized_volatility": leverage_cfg.require_realized_vol_decline,
        "leverage_config": asdict(leverage_cfg),
    }
    if not t.empty:
        summary.update(
            {
                "win_rate": float((t.return_after_costs > 0).mean()),
                "mean_return": float(t.return_after_costs.mean()),
                "median_return": float(t.return_after_costs.median()),
                "worst_return": float(t.return_after_costs.min()),
                "mean_holding_days": float(t.holding_days.mean()),
                "mean_max_adverse_excursion": float(t.max_adverse_excursion.mean()),
                "worst_max_adverse_excursion": float(t.max_adverse_excursion.min()),
                "mean_tracking_gap_vs_daily_reset": float(t.tracking_gap_vs_daily_reset.mean()),
                "mean_path_dependency_gap_vs_linear_two_x": float(
                    t.path_dependency_gap_vs_linear_two_x.mean()
                ),
                "end_of_data_exit_count": int(t.exit_reasons.str.contains("END_OF_DATA").sum()),
                "exit_reason_counts": t.exit_reasons.str.get_dummies(sep="|").sum().astype(int).to_dict(),
            }
        )
    return t, summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--underlying-csv", type=Path, required=True)
    ap.add_argument("--leveraged-csv", type=Path, required=True)
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--leveraged-symbol", required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--features-csv", type=Path)
    ap.add_argument("--max-holding-days", type=int, default=42)
    ap.add_argument("--target-return", type=float, default=0.20)
    ap.add_argument("--out", type=Path, default=Path("leverage-output"))
    a = ap.parse_args()

    underlying = load_prices(a.underlying_csv)
    leveraged = load_prices(a.leveraged_csv)
    assert_price_continuity(underlying)
    assert_price_continuity(leveraged)
    bottom_cfg = load_config(a.config, a.symbol)
    leverage_cfg = LeverageConfig(
        max_holding_days=a.max_holding_days,
        target_return=a.target_return,
    )
    trades, summary = tactical_backtest(
        underlying,
        leveraged,
        bottom_cfg,
        leverage_cfg,
        load_features(a.features_csv),
    )
    summary.update({"underlying": a.symbol, "leveraged_product": a.leveraged_symbol})
    out = a.out / f"{a.symbol}-{a.leveraged_symbol}"
    out.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out / "tactical_leverage_trades.csv", index=False)
    (out / "tactical_leverage_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
