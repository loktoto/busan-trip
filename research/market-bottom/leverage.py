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
    transaction_cost_bps_each_side: float = 2.0
    slippage_bps_each_side: float = 4.0
    require_breadth_when_available: bool = True

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
    x["leverage_entry_signal"] = (
        transition
        & (x.Close > x.sma20)
        & (x.sma10_slope > 0)
        & (x.atrp < x.atrp.shift(5))
        & breadth_ok.fillna(False)
        & ~x.credit_veto
    )

    trades: list[dict] = []
    position: dict | None = None
    one_way = leverage_cfg.one_way_cost_bps / 10_000
    for i in range(200, len(x) - 1):
        r, nxt = x.iloc[i], x.iloc[i + 1]
        if position is None:
            if not bool(r.leverage_entry_signal):
                continue
            entry_px = float(nxt.lev_Open) * (1 + one_way)
            position = {
                "signal_index": i,
                "entry_index": i + 1,
                "signal_date": r.Date.date(),
                "entry_date": nxt.Date.date(),
                "entry_price": entry_px,
                "entry_underlying": float(r.Close),
                "underlying_stop": float(r.underlying_stop),
                "entry_atrp": float(r.atrp),
                "breadth_available": bool(breadth_available),
            }
            continue

        held = i - int(position["entry_index"]) + 1
        lev_return_close = float(r.lev_Close) / float(position["entry_price"]) - 1
        stop_fail = float(r.Close) < float(position["underlying_stop"])
        vol_exit = (
            float(r.atrp) >= float(position["entry_atrp"]) * leverage_cfg.vol_exit_multiple
            and float(r.atrp) > float(x.iloc[i - 5].atrp)
        )
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

        exit_px = float(nxt.lev_Open) * (1 - one_way)
        window = x.iloc[int(position["entry_index"]) : i + 2]
        path = window.lev_Close / float(position["entry_price"]) - 1
        trades.append(
            {
                **position,
                "exit_signal_date": r.Date.date(),
                "exit_date": nxt.Date.date(),
                "exit_price": exit_px,
                "holding_days": held,
                "exit_reasons": "|".join(reasons),
                "return_after_costs": exit_px / float(position["entry_price"]) - 1,
                "max_adverse_excursion": float(path.min()),
                "max_favourable_excursion": float(path.max()),
                "one_way_cost_bps": leverage_cfg.one_way_cost_bps,
            }
        )
        position = None

    t = pd.DataFrame(trades)
    summary = {
        "classification": "TACTICAL ACTUAL-PRODUCT RESEARCH — NOT A LONG-TERM HOLD",
        "trade_count": int(len(t)),
        "breadth_available": bool(breadth_available),
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
