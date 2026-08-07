#!/usr/bin/env python3
"""Price-only local-bottom ensemble for bounded ordinary-ETF probes.

This module evaluates a narrower, more defensible question than "is this the
final cycle low?": after a material drawdown, does completed-bar evidence place
the next-open entry sufficiently close to a local 63-session trough?

The six indicator families are deliberately interpretable:

1. momentum washout and reversal;
2. intraday price reversal;
3. realised-volatility maturity;
4. selling-pressure maturity;
5. retest/higher-low structure;
6. short-trend reclaim.

Signals are transition-only, separated by the existing cooldown/price-spacing
controls.  A structural-bear flag is reported but never relabelled as cycle-bottom
confirmation.  No signal in this module authorises leverage or an order.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest import (
    Config,
    episode_catalog,
    episode_ids,
    indicators,
    load_config,
    load_prices,
    run,
)

LOCAL_HORIZON = 63
LONG_HORIZON = 252


def _rsi(close: pd.Series, days: int = 14) -> pd.Series:
    change = close.diff()
    gain = change.clip(lower=0).ewm(
        alpha=1 / days, adjust=False, min_periods=days
    ).mean()
    loss = (-change.clip(upper=0)).ewm(
        alpha=1 / days, adjust=False, min_periods=days
    ).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(100)


def _age_since(flag: pd.Series) -> pd.Series:
    last: int | None = None
    out: list[float] = []
    for i, value in enumerate(flag.fillna(False).astype(bool)):
        if value:
            last = i
        out.append(np.nan if last is None else i - last)
    return pd.Series(out, index=flag.index, dtype=float)


def add_local_bottom_features(frame: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    x = frame.copy()
    x["rsi14"] = _rsi(x.Close, 14)
    std20 = x.Close.rolling(20).std(ddof=0)
    x["bb_z20"] = (x.Close - x.sma20) / std20.replace(0, np.nan)

    washout = (
        (x.rsi14 <= 30)
        | (x.r5z <= -1.5)
        | (x.bb_z20 <= -2.0)
    )
    x["local_washout_age"] = _age_since(washout)
    washout_recent = x.local_washout_age.between(1, 10)
    x["local_momentum_reversal"] = (
        washout_recent
        & (x.rsi14 > x.rsi14.shift(3))
        & (x.r1 > 0)
    ).fillna(False)

    x["local_price_reversal"] = (
        (x.r1 > 0)
        & (x.close_loc >= 0.60)
        & ((x.Close > x.Open) | (x.Close > x.High.shift(1)))
    ).fillna(False)

    x["local_vol_maturity"] = (
        (x.rv20 < x.rv20.shift(1).rolling(5).max())
        & (x.atrp <= x.atrp.shift(5) * 1.05)
    ).fillna(False)

    sell_now = x.sell_pressure.rolling(3).mean()
    sell_prior = x.sell_pressure.shift(3).rolling(10).mean()
    x["local_selling_maturity"] = (
        (sell_now < sell_prior)
        & (x.vol_ratio < x.vol_ratio.shift(1).rolling(10).max())
    ).fillna(False)

    low_age = _age_since(x.newlow20)
    rolling_low20 = x.Low.rolling(20).min()
    atr_from_low = (x.Close - rolling_low20) / x.atr14.replace(0, np.nan)
    low5 = x.Low.rolling(5).min()
    prior_low5 = x.Low.shift(5).rolling(5).min()
    x["local_retest"] = (
        low_age.between(2, 20)
        & (atr_from_low <= 3.0)
        & (low5 >= prior_low5)
    ).fillna(False)
    x["local_sessions_since_low"] = low_age
    x["local_atr_from_low"] = atr_from_low

    x["local_trend_reclaim"] = (
        (x.Close > x.sma10)
        & (x.sma10_slope > 0)
        & (x.r5 > 0)
    ).fillna(False)

    families = [
        "local_momentum_reversal",
        "local_price_reversal",
        "local_vol_maturity",
        "local_selling_maturity",
        "local_retest",
        "local_trend_reclaim",
    ]
    x["local_bottom_score"] = x[families].sum(axis=1).astype(int)
    x["local_structural_bear"] = (
        (x.Close < x.sma200)
        & (x.sma200_slope < 0)
        & (x.sma50 < x.sma200)
    ).fillna(False)
    return x


def run_score_signals(
    x: pd.DataFrame, cfg: Config, threshold: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if threshold not in range(2, 7):
        raise ValueError("threshold must be between 2 and 6")
    y = add_local_bottom_features(x, cfg)
    y["episode"] = episode_ids(y, cfg)
    catalog = episode_catalog(y, cfg)
    rows: list[dict[str, Any]] = []
    last_i: dict[int, int] = {}
    last_px: dict[int, float] = {}
    was_active: dict[int, bool] = {}

    for i in range(200, len(y) - 1):
        row = y.iloc[i]
        eid = int(row.episode)
        setup = (
            eid > 0
            and float(row.cycle_dd) <= -cfg.start_dd
            and int(row.local_bottom_score) >= threshold
            and not bool(row.credit_veto)
        )
        transition = setup and not was_active.get(eid, False)
        was_active[eid] = setup
        if not transition:
            continue

        cooldown_ok = eid not in last_i or i - last_i[eid] >= cfg.cooldown
        spacing_ok = (
            eid not in last_px
            or float(row.Close) <= last_px[eid] * (1 - cfg.spacing)
        )
        # A new completed 20-day low re-arms the local-bottom search even when
        # the previous transition occurred recently.
        if not (cooldown_ok or spacing_ok or bool(row.newlow20)):
            continue

        nxt = y.iloc[i + 1]
        raw_px = float(nxt.Open)
        execution_price = raw_px * (1 + cfg.all_in_cost_bps / 10_000)
        last_i[eid] = i + 1
        last_px[eid] = execution_price
        rows.append(
            {
                "symbol": cfg.symbol,
                "episode": eid,
                "threshold": threshold,
                "signal_index": i,
                "execution_index": i + 1,
                "signal_date": row.Date.date(),
                "execution_date": nxt.Date.date(),
                "execution_price": execution_price,
                "cycle_dd": float(row.cycle_dd),
                "score": int(row.local_bottom_score),
                "momentum_reversal": bool(row.local_momentum_reversal),
                "price_reversal": bool(row.local_price_reversal),
                "vol_maturity": bool(row.local_vol_maturity),
                "selling_maturity": bool(row.local_selling_maturity),
                "retest": bool(row.local_retest),
                "trend_reclaim": bool(row.local_trend_reclaim),
                "structural_bear": bool(row.local_structural_bear),
                "classification": (
                    "LOCAL_BOTTOM_ONLY_STRUCTURAL_BEAR"
                    if bool(row.local_structural_bear)
                    else "LOCAL_BOTTOM_CANDIDATE"
                ),
            }
        )
    return pd.DataFrame(rows), catalog


def baseline_signals(
    x: pd.DataFrame, cfg: Config
) -> tuple[pd.DataFrame, pd.DataFrame]:
    trades, catalog = run(x, cfg)
    if trades.empty:
        return trades, catalog
    out = trades[
        [
            "symbol",
            "episode",
            "signal_index",
            "execution_index",
            "signal_date",
            "execution_date",
            "execution_price",
            "cycle_dd",
        ]
    ].copy()
    out["threshold"] = 0
    out["score"] = np.nan
    out["structural_bear"] = trades.long_bear.astype(bool)
    out["classification"] = "BASELINE_STAGED_EVENT"
    return out, catalog


def evaluate_signals(
    x: pd.DataFrame, signals: pd.DataFrame, catalog: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    detailed: list[dict[str, Any]] = []
    for _, signal in signals.iterrows():
        row = signal.to_dict()
        i = int(signal.execution_index)
        for horizon in (LOCAL_HORIZON, LONG_HORIZON):
            forward = x.iloc[i : min(i + horizon, len(x) - 1) + 1]
            trough_rel = int(forward.Close.to_numpy().argmin())
            trough = float(forward.iloc[trough_rel].Close)
            distance = float(signal.execution_price / trough - 1)
            row[f"distance_{horizon}"] = distance
            row[f"days_to_trough_{horizon}"] = trough_rel
            row[f"within_5_{horizon}"] = distance <= 0.05
            row[f"within_8_{horizon}"] = distance <= 0.08
            row[f"false_start_10_{horizon}"] = distance > 0.10
        detailed.append(row)
    detail = pd.DataFrame(detailed)

    episodes: list[dict[str, Any]] = []
    for _, episode in catalog.iterrows():
        if not bool(episode.complete):
            continue
        eid = int(episode.episode)
        group = (
            detail.loc[detail.episode == eid].sort_values("execution_index")
            if not detail.empty
            else pd.DataFrame()
        )
        record = episode.to_dict()
        record["signal_count"] = int(len(group))
        record["missed"] = bool(group.empty)
        for horizon in (LOCAL_HORIZON, LONG_HORIZON):
            record[f"any_within_5_{horizon}"] = bool(
                not group.empty and group[f"within_5_{horizon}"].any()
            )
            record[f"any_within_8_{horizon}"] = bool(
                not group.empty and group[f"within_8_{horizon}"].any()
            )
            record[f"first_distance_{horizon}"] = (
                np.nan if group.empty else float(group.iloc[0][f"distance_{horizon}"])
            )
            record[f"best_distance_{horizon}"] = (
                np.nan if group.empty else float(group[f"distance_{horizon}"].min())
            )
            record[f"false_start_rate_{horizon}"] = (
                np.nan
                if group.empty
                else float(group[f"false_start_10_{horizon}"].mean())
            )
        episodes.append(record)
    ep = pd.DataFrame(episodes)
    summary = summarize_episodes(ep, detail)
    return detail, ep, summary


def summarize_episodes(ep: pd.DataFrame, detail: pd.DataFrame) -> dict:
    if ep.empty:
        return {"episodes": 0}
    return {
        "episodes": int(len(ep)),
        "signals": int(len(detail)),
        "signals_per_episode": float(len(detail) / len(ep)),
        "missed_rate": float(ep.missed.mean()),
        "episode_hit_5_63": float(ep.any_within_5_63.mean()),
        "episode_hit_8_63": float(ep.any_within_8_63.mean()),
        "mean_first_distance_63": float(ep.first_distance_63.dropna().mean())
        if ep.first_distance_63.notna().any()
        else np.nan,
        "mean_best_distance_63": float(ep.best_distance_63.dropna().mean())
        if ep.best_distance_63.notna().any()
        else np.nan,
        "signal_precision_8_63": float(detail.within_8_63.mean())
        if len(detail)
        else np.nan,
        "signal_false_start_10_63": float(detail.false_start_10_63.mean())
        if len(detail)
        else np.nan,
        "episode_hit_8_252": float(ep.any_within_8_252.mean()),
        "mean_first_distance_252": float(ep.first_distance_252.dropna().mean())
        if ep.first_distance_252.notna().any()
        else np.nan,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, required=True)
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--threshold", type=int, default=4)
    ap.add_argument("--out", type=Path, default=Path("local-bottom-v41-output"))
    args = ap.parse_args()

    cfg = load_config(args.config, args.symbol)
    x = indicators(load_prices(args.csv), cfg)
    signals, catalog = run_score_signals(x, cfg, args.threshold)
    detail, episodes, summary = evaluate_signals(x, signals, catalog)
    summary.update(
        {
            "symbol": args.symbol,
            "threshold": args.threshold,
            "config": asdict(cfg),
            "classification": (
                "PRICE-ONLY LOCAL-BOTTOM RESEARCH — NO CYCLE-BOTTOM, "
                "LEVERAGE OR ORDER AUTHORITY"
            ),
        }
    )
    out = args.out / args.symbol / f"score-{args.threshold}"
    out.mkdir(parents=True, exist_ok=True)
    detail.to_csv(out / "signal_metrics.csv", index=False)
    episodes.to_csv(out / "episode_metrics.csv", index=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
