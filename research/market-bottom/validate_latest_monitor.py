#!/usr/bin/env python3
"""Backtest the latest production-intended market-bottom monitor.

Compares the audited baseline engine with recovery overlay v1.1 for SPY, QQQ
and SOXX. The report is deliberately bottom-quality focused rather than a CAGR
optimization:

- missed drawdown episodes;
- capital-weighted distance from the subsequent episode trough;
- additional downside after entry;
- deployment;
- 5/20/63-session forward returns of recovery-probe trades;
- full-history, since-2010 and since-2020 slices;
- drawdown-depth buckets.

Signals use completed close t and execute at next open t+1 plus configured
costs. Future prices are used only for evaluation. This script does not promote
parameters or create orders.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest import evaluate, indicators, load_config, load_prices, run
from recovery_v11 import run_v11

PRIMARY = ("SPY", "QQQ", "SOXX")
SLICES: dict[str, str | None] = {
    "FULL_HISTORY": None,
    "SINCE_2010": "2010-01-01",
    "SINCE_2020": "2020-01-01",
}
FORWARD_HORIZONS = (5, 20, 63)


def _safe(value: Any) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if np.isfinite(x) else None


def _mean(series: pd.Series) -> float | None:
    return _safe(series.dropna().mean()) if len(series.dropna()) else None


def _median(series: pd.Series) -> float | None:
    return _safe(series.dropna().median()) if len(series.dropna()) else None


def _episode_summary(episodes: pd.DataFrame) -> dict[str, Any]:
    if episodes.empty:
        return {
            "episode_count_all": 0,
            "episode_count_complete": 0,
            "missed_rate_complete": None,
            "mean_deployment_complete": None,
            "mean_weighted_distance_complete": None,
            "mean_worst_additional_downside_complete": None,
            "any_within_5_rate_complete": None,
            "any_within_8_rate_complete": None,
        }
    complete = episodes.loc[episodes.complete.astype(bool)].copy()
    return {
        "episode_count_all": int(len(episodes)),
        "episode_count_complete": int(len(complete)),
        "missed_rate_complete": _mean(complete.missed.astype(float)),
        "mean_deployment_complete": _mean(complete.total_deployment),
        "mean_weighted_distance_complete": _mean(complete.weighted_distance),
        "mean_worst_additional_downside_complete": _mean(
            complete.worst_additional_downside
        ),
        "any_within_5_rate_complete": _mean(complete.any_within_5.astype(float)),
        "any_within_8_rate_complete": _mean(complete.any_within_8.astype(float)),
    }


def _filter_episodes(episodes: pd.DataFrame, cutoff: str | None) -> pd.DataFrame:
    if cutoff is None or episodes.empty:
        return episodes.copy()
    dates = pd.to_datetime(episodes.start_date, errors="coerce")
    return episodes.loc[dates >= pd.Timestamp(cutoff)].copy()


def _delta(new: dict[str, Any], old: dict[str, Any]) -> dict[str, float | None]:
    keys = (
        "episode_count_complete",
        "missed_rate_complete",
        "mean_deployment_complete",
        "mean_weighted_distance_complete",
        "mean_worst_additional_downside_complete",
        "any_within_5_rate_complete",
        "any_within_8_rate_complete",
    )
    out: dict[str, float | None] = {}
    for key in keys:
        a, b = _safe(new.get(key)), _safe(old.get(key))
        out[key] = None if a is None or b is None else a - b
    return out


def _slice_reports(
    baseline_episodes: pd.DataFrame,
    v11_episodes: pd.DataFrame,
) -> dict[str, Any]:
    reports: dict[str, Any] = {}
    for name, cutoff in SLICES.items():
        base = _episode_summary(_filter_episodes(baseline_episodes, cutoff))
        v11 = _episode_summary(_filter_episodes(v11_episodes, cutoff))
        reports[name] = {"baseline": base, "v11": v11, "delta": _delta(v11, base)}
    return reports


def _depth_buckets(episodes: pd.DataFrame) -> dict[str, Any]:
    if episodes.empty:
        return {}
    y = episodes.copy()
    y["depth"] = y.max_drawdown.abs()
    specs = {
        "LT_15_PERCENT": (0.0, 0.15),
        "15_TO_25_PERCENT": (0.15, 0.25),
        "GE_25_PERCENT": (0.25, float("inf")),
    }
    out: dict[str, Any] = {}
    for name, (lo, hi) in specs.items():
        subset = y.loc[(y.depth >= lo) & (y.depth < hi)]
        out[name] = _episode_summary(subset)
    return out


def _recovery_trade_metrics(
    x: pd.DataFrame,
    trades: pd.DataFrame,
    episodes: pd.DataFrame,
) -> dict[str, Any]:
    if trades.empty or "recovery_probe_transition" not in trades:
        return {"trade_count": 0, "episode_count": 0, "rows": []}
    recovery = trades.loc[trades.recovery_probe_transition.fillna(False)].copy()
    if recovery.empty:
        return {"trade_count": 0, "episode_count": 0, "rows": []}

    ep_lookup = episodes.set_index("episode") if not episodes.empty else pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for _, trade in recovery.iterrows():
        i = int(trade.execution_index)
        eid = int(trade.episode)
        row: dict[str, Any] = {
            "episode": eid,
            "signal_date": str(trade.signal_date),
            "execution_date": str(trade.execution_date),
            "execution_price": float(trade.execution_price),
            "tranche": float(trade.tranche),
            "signal_cycle_drawdown": float(trade.cycle_dd),
            "recovery_bounce": float(trade.recovery_bounce),
        }
        if not ep_lookup.empty and eid in ep_lookup.index:
            ep = ep_lookup.loc[eid]
            trough = float(ep.evaluation_trough)
            eval_end = int(ep.evaluation_end_index)
            row["distance_to_episode_trough"] = float(trade.execution_price / trough - 1)
            row["additional_downside_to_episode_trough"] = float(
                trough / trade.execution_price - 1
            )
            post = x.iloc[i : eval_end + 1]
            row["max_adverse_to_evaluation_end"] = float(
                post.Close.min() / trade.execution_price - 1
            )
        else:
            row["distance_to_episode_trough"] = None
            row["additional_downside_to_episode_trough"] = None
            row["max_adverse_to_evaluation_end"] = None

        for horizon in FORWARD_HORIZONS:
            j = i + horizon
            row[f"return_{horizon}d"] = (
                float(x.iloc[j].Close / trade.execution_price - 1)
                if j < len(x)
                else None
            )
        rows.append(row)

    frame = pd.DataFrame(rows)
    summary: dict[str, Any] = {
        "trade_count": int(len(frame)),
        "episode_count": int(frame.episode.nunique()),
        "mean_signal_cycle_drawdown": _mean(frame.signal_cycle_drawdown),
        "mean_recovery_bounce": _mean(frame.recovery_bounce),
        "mean_distance_to_episode_trough": _mean(frame.distance_to_episode_trough),
        "median_distance_to_episode_trough": _median(frame.distance_to_episode_trough),
        "within_5_percent_of_trough_rate": _mean(
            (frame.distance_to_episode_trough <= 0.05).astype(float)
        ),
        "within_8_percent_of_trough_rate": _mean(
            (frame.distance_to_episode_trough <= 0.08).astype(float)
        ),
        "mean_max_adverse_to_evaluation_end": _mean(
            frame.max_adverse_to_evaluation_end
        ),
        "rows": rows,
    }
    for horizon in FORWARD_HORIZONS:
        col = frame[f"return_{horizon}d"]
        summary[f"mean_return_{horizon}d"] = _mean(col)
        summary[f"median_return_{horizon}d"] = _median(col)
        valid = col.dropna()
        summary[f"positive_rate_{horizon}d"] = (
            _mean((valid > 0).astype(float)) if len(valid) else None
        )
    return summary


def _invariant_failures(trades: pd.DataFrame, cfg: Any) -> list[str]:
    failures: list[str] = []
    if trades.empty:
        return failures
    if (trades.tranche > cfg.max_tranche + 1e-12).any():
        failures.append("TRANCHE_CAP")
    if (trades.cumulative > cfg.max_deploy + 1e-12).any():
        failures.append("DEPLOYMENT_CAP")
    if (trades.tranche < cfg.min_tranche - 1e-12).any():
        failures.append("MINIMUM_TRANCHE")
    for _, group in trades.groupby("episode"):
        if not group.cumulative.is_monotonic_increasing:
            failures.append("NON_MONOTONIC_CUMULATIVE")
            break
    if "recovery_probe_transition" in trades:
        probes = trades.loc[trades.recovery_probe_transition.fillna(False)]
        if not probes.empty:
            if (probes.groupby("episode").size() > 1).any():
                failures.append("MULTIPLE_RECOVERY_PROBES_PER_EPISODE")
            if probes.long_bear.any():
                failures.append("RECOVERY_IN_LONG_BEAR")
            if (probes.cycle_dd > -cfg.start_dd + 1e-12).any():
                failures.append("RECOVERY_OUTSIDE_START_DRAWDOWN")
    return failures


def _assessment(report: dict[str, Any]) -> dict[str, Any]:
    failures = report["invariant_failures"]
    probes = report["recovery_probes"]
    full = report["slices"]["FULL_HISTORY"]["delta"]
    modern = report["slices"]["SINCE_2020"]["delta"]
    reasons: list[str] = []

    if failures:
        return {
            "status": "DOES_NOT_MAKE_SENSE_HARD_FAILURE",
            "reasons": failures,
        }
    if probes["trade_count"] < 5:
        reasons.append("FEWER_THAN_5_RECOVERY_PROBES")

    for label, delta in (("FULL", full), ("SINCE_2020", modern)):
        dist = delta.get("mean_weighted_distance_complete")
        downside = delta.get("mean_worst_additional_downside_complete")
        missed = delta.get("missed_rate_complete")
        if dist is not None and dist > 0.01:
            reasons.append(f"{label}_WEIGHTED_DISTANCE_WORSE_GT_1PP")
        if downside is not None and downside < -0.015:
            reasons.append(f"{label}_ADDITIONAL_DOWNSIDE_WORSE_GT_1_5PP")
        if missed is not None and missed > 0.02:
            reasons.append(f"{label}_MISSED_RATE_WORSE_GT_2PP")

    mean_63 = probes.get("mean_return_63d")
    if mean_63 is not None and mean_63 < 0:
        reasons.append("RECOVERY_PROBE_MEAN_63D_RETURN_NEGATIVE")

    material = [r for r in reasons if not r.startswith("FEWER_THAN_5")]
    if material:
        status = "DOES_NOT_MAKE_SENSE_AS_CURRENTLY_SPECIFIED"
    elif reasons:
        status = "UNDERPOWERED_NOT_PROMOTED"
    else:
        status = "SMALL_OVERLAY_MAKES_SENSE_NOT_PROMOTED"
    return {"status": status, "reasons": reasons}


def _symbol_report(csv_path: Path, config_path: Path, symbol: str) -> dict[str, Any]:
    cfg = load_config(config_path, symbol)
    prices = load_prices(csv_path)
    x = indicators(prices, cfg)

    baseline_trades, baseline_catalog = run(x, cfg)
    _, baseline_episodes, baseline_summary = evaluate(
        x, baseline_trades, baseline_catalog, cfg
    )

    v11_trades, v11_catalog = run_v11(x, cfg)
    _, v11_episodes, v11_summary = evaluate(x, v11_trades, v11_catalog, cfg)

    report: dict[str, Any] = {
        "symbol": symbol,
        "history_start": prices.iloc[0].Date.date().isoformat(),
        "history_end": prices.iloc[-1].Date.date().isoformat(),
        "bar_count": int(len(prices)),
        "baseline_full_summary": baseline_summary,
        "v11_full_summary": v11_summary,
        "slices": _slice_reports(baseline_episodes, v11_episodes),
        "baseline_depth_buckets": _depth_buckets(baseline_episodes),
        "v11_depth_buckets": _depth_buckets(v11_episodes),
        "recovery_probes": _recovery_trade_metrics(x, v11_trades, v11_episodes),
        "invariant_failures": _invariant_failures(v11_trades, cfg),
        "implementation_audit": {
            "left_side_probe_supported": True,
            "confirmation_add_supported": True,
            "recovery_probe_supported": True,
            "recovery_probe_requires_cycle_drawdown_at_or_below_start_threshold": True,
            "true_catch_up_after_rebound_above_start_threshold_supported": False,
            "one_recovery_probe_max_per_episode": True,
        },
    }
    report["assessment"] = _assessment(report)
    return report


def _overall(symbols: dict[str, dict[str, Any]]) -> dict[str, Any]:
    statuses = {symbol: report["assessment"]["status"] for symbol, report in symbols.items()}
    if any(status.startswith("DOES_NOT") for status in statuses.values()):
        status = "LATEST_MONITOR_DOES_NOT_YET_MAKE_SENSE_FOR_PRODUCTION"
    elif any(status.startswith("UNDERPOWERED") for status in statuses.values()):
        status = "MIXED_OR_UNDERPOWERED_NOT_PROMOTED"
    else:
        status = "SMALL_RECOVERY_OVERLAY_IS_REASONABLE_NOT_PROMOTED"
    return {
        "status": status,
        "symbol_statuses": statuses,
        "critical_implementation_finding": (
            "v1.1 does not implement a true V-shaped catch-up after price rebounds "
            "above the asset start-drawdown threshold; it only permits a recovery "
            "probe while drawdown remains at or below that threshold."
        ),
        "promotion_status": "BLOCKED_PENDING_CAUSAL_OUT_OF_SAMPLE_VALIDATION",
    }


def _fmt(value: Any) -> str:
    x = _safe(value)
    return "n/a" if x is None else f"{x:.4f}"


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Latest market-bottom monitor backtest",
        "",
        f"- Overall assessment: **{payload['overall']['status']}**",
        f"- Promotion: **{payload['overall']['promotion_status']}**",
        "- Execution: completed close t -> next open t+1 plus configured costs",
        "- Objective: bottom proximity, missed episodes and adverse excursion; not CAGR optimisation",
        "",
        "## Baseline versus recovery v1.1",
        "",
        "| Symbol | Slice | Episodes | Recovery probes | Missed Δ | Distance Δ | Downside Δ | Deployment Δ | Assessment |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for symbol in PRIMARY:
        report = payload["symbols"][symbol]
        for slice_name in SLICES:
            item = report["slices"][slice_name]
            d = item["delta"]
            lines.append(
                f"| {symbol} | {slice_name} | {item['v11']['episode_count_complete']} | "
                f"{report['recovery_probes']['trade_count']} | "
                f"{_fmt(d['missed_rate_complete'])} | "
                f"{_fmt(d['mean_weighted_distance_complete'])} | "
                f"{_fmt(d['mean_worst_additional_downside_complete'])} | "
                f"{_fmt(d['mean_deployment_complete'])} | "
                f"{report['assessment']['status']} |"
            )

    lines.extend(["", "## Recovery-probe forward outcomes", ""])
    lines.append(
        "| Symbol | Trades | Mean DD at signal | Mean distance to trough | Mean max adverse | 5d mean | 20d mean | 63d mean |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for symbol in PRIMARY:
        p = payload["symbols"][symbol]["recovery_probes"]
        lines.append(
            f"| {symbol} | {p['trade_count']} | {_fmt(p.get('mean_signal_cycle_drawdown'))} | "
            f"{_fmt(p.get('mean_distance_to_episode_trough'))} | "
            f"{_fmt(p.get('mean_max_adverse_to_evaluation_end'))} | "
            f"{_fmt(p.get('mean_return_5d'))} | {_fmt(p.get('mean_return_20d'))} | "
            f"{_fmt(p.get('mean_return_63d'))} |"
        )

    lines.extend(
        [
            "",
            "## Critical implementation finding",
            "",
            payload["overall"]["critical_implementation_finding"],
            "",
            "This means v1.1 can test one small rebound probe inside the existing bottom zone, but it does not fully solve the practical complaint that both a deeper fall and a rebound can result in WAIT.",
            "",
            "> Research diagnostic only. No parameter is promoted and no order is created.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--data-dir",
        type=Path,
        default=Path("runtime/market-bottom/data"),
    )
    ap.add_argument(
        "--config",
        type=Path,
        default=Path("research/market-bottom/config.example.json"),
    )
    ap.add_argument(
        "--out-json",
        type=Path,
        default=Path("runtime/market-bottom/latest-monitor-backtest.json"),
    )
    ap.add_argument(
        "--out-md",
        type=Path,
        default=Path("runtime/market-bottom/latest-monitor-backtest.md"),
    )
    args = ap.parse_args()

    symbols = {
        symbol: _symbol_report(args.data_dir / f"{symbol}.csv", args.config, symbol)
        for symbol in PRIMARY
    }
    payload = {
        "schema_version": "1.0",
        "engine_under_test": "market-bottom recovery v1.1",
        "data_classification": "PUBLIC_ADJUSTED_REPRODUCIBILITY_DIAGNOSTIC_NOT_IBKR_HOLDOUT",
        "symbols": symbols,
        "overall": _overall(symbols),
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    args.out_md.write_text(_markdown(payload))
    print(json.dumps(payload["overall"], indent=2))

    if any(report["invariant_failures"] for report in symbols.values()):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
