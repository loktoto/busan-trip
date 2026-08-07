#!/usr/bin/env python3
"""Compare the baseline market-bottom engine with recovery overlay v1.1.

This is a research regression harness, not a promotion claim.  It uses the same
completed-close indicators and next-open execution assumptions as backtest.py.
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


def _safe(value: Any) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if np.isfinite(x) else None


def _summary_delta(new: dict[str, Any], old: dict[str, Any], key: str) -> float | None:
    a, b = _safe(new.get(key)), _safe(old.get(key))
    return None if a is None or b is None else a - b


def _symbol_report(csv_path: Path, config_path: Path, symbol: str) -> dict[str, Any]:
    cfg = load_config(config_path, symbol)
    prices = load_prices(csv_path)
    x = indicators(prices, cfg)

    baseline_trades, baseline_catalog = run(x, cfg)
    _, baseline_episodes, baseline_summary = evaluate(
        x,
        baseline_trades,
        baseline_catalog,
        cfg,
    )

    v11_trades, v11_catalog = run_v11(x, cfg)
    _, v11_episodes, v11_summary = evaluate(
        x,
        v11_trades,
        v11_catalog,
        cfg,
    )

    recovery = pd.DataFrame()
    if not v11_trades.empty and "recovery_probe_transition" in v11_trades:
        recovery = v11_trades.loc[
            v11_trades.recovery_probe_transition.fillna(False)
        ].copy()

    invariant_failures: list[str] = []
    if not v11_trades.empty:
        if (v11_trades.tranche > cfg.max_tranche + 1e-12).any():
            invariant_failures.append("TRANCHE_CAP")
        if (v11_trades.cumulative > cfg.max_deploy + 1e-12).any():
            invariant_failures.append("DEPLOYMENT_CAP")
        if (v11_trades.tranche < cfg.min_tranche - 1e-12).any():
            invariant_failures.append("MINIMUM_TRANCHE")
        for _, group in v11_trades.groupby("episode"):
            if not group.cumulative.is_monotonic_increasing:
                invariant_failures.append("NON_MONOTONIC_CUMULATIVE")
                break
    if not recovery.empty:
        if (recovery.groupby("episode").size() > 1).any():
            invariant_failures.append("MULTIPLE_RECOVERY_PROBES_PER_EPISODE")
        if recovery.long_bear.any():
            invariant_failures.append("RECOVERY_IN_LONG_BEAR")
        if (recovery.cycle_dd > -cfg.start_dd + 1e-12).any():
            invariant_failures.append("RECOVERY_OUTSIDE_START_DRAWDOWN")

    complete_baseline = baseline_episodes.loc[baseline_episodes.complete]
    complete_v11 = v11_episodes.loc[v11_episodes.complete]

    report = {
        "symbol": symbol,
        "history_start": prices.iloc[0].Date.date().isoformat(),
        "history_end": prices.iloc[-1].Date.date().isoformat(),
        "bar_count": int(len(prices)),
        "baseline": baseline_summary,
        "v11": v11_summary,
        "delta": {
            key: _summary_delta(v11_summary, baseline_summary, key)
            for key in (
                "trade_count",
                "missed_rate_complete",
                "mean_deployment_complete",
                "mean_weighted_distance_complete",
                "mean_worst_additional_downside_complete",
                "any_within_3_rate_complete",
                "any_within_5_rate_complete",
                "any_within_8_rate_complete",
            )
        },
        "recovery_probe_trade_count": int(len(recovery)),
        "recovery_probe_episode_count": (
            int(recovery.episode.nunique()) if not recovery.empty else 0
        ),
        "recovery_probe_mean_cycle_dd": (
            _safe(recovery.cycle_dd.mean()) if not recovery.empty else None
        ),
        "recovery_probe_mean_bounce": (
            _safe(recovery.recovery_bounce.mean()) if not recovery.empty else None
        ),
        "complete_episode_count_baseline": int(len(complete_baseline)),
        "complete_episode_count_v11": int(len(complete_v11)),
        "invariant_failures": invariant_failures,
    }
    return report


def _promotion_diagnostics(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    for symbol, r in results.items():
        failures.extend(f"{symbol}:{x}" for x in r["invariant_failures"])
        d = r["delta"]
        missed = d.get("missed_rate_complete")
        downside = d.get("mean_worst_additional_downside_complete")
        deployment = d.get("mean_deployment_complete")
        distance = d.get("mean_weighted_distance_complete")
        if missed is not None and missed > 0.02:
            warnings.append(f"{symbol}:MISSED_RATE_WORSE_BY_{missed:.4f}")
        if downside is not None and downside < -0.02:
            warnings.append(f"{symbol}:ADDITIONAL_DOWNSIDE_WORSE_BY_{downside:.4f}")
        if deployment is not None and deployment > 0.08:
            warnings.append(f"{symbol}:MEAN_DEPLOYMENT_HIGHER_BY_{deployment:.4f}")
        if distance is not None and distance > 0.03:
            warnings.append(f"{symbol}:WEIGHTED_DISTANCE_WORSE_BY_{distance:.4f}")

    return {
        "classification": "RESEARCH REGRESSION — NOT PROMOTED",
        "hard_invariant_pass": not failures,
        "hard_failures": failures,
        "performance_warnings": warnings,
        "promotion_status": "BLOCKED_PENDING_REVIEW",
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Market-bottom recovery overlay v1.1 validation",
        "",
        f"- Classification: **{payload['governance']['classification']}**",
        f"- Hard invariant pass: **{payload['governance']['hard_invariant_pass']}**",
        f"- Promotion status: **{payload['governance']['promotion_status']}**",
        "",
        "| Symbol | Baseline trades | v1.1 trades | Recovery probes | Missed Δ | Weighted distance Δ | Worst downside Δ | Deployment Δ |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for symbol in PRIMARY:
        r = payload["symbols"][symbol]
        d = r["delta"]
        fmt = lambda v: "n/a" if v is None else f"{v:.4f}"
        lines.append(
            f"| {symbol} | {r['baseline']['trade_count']} | {r['v11']['trade_count']} | "
            f"{r['recovery_probe_trade_count']} | {fmt(d['missed_rate_complete'])} | "
            f"{fmt(d['mean_weighted_distance_complete'])} | "
            f"{fmt(d['mean_worst_additional_downside_complete'])} | "
            f"{fmt(d['mean_deployment_complete'])} |"
        )
    lines.extend(["", "## Performance warnings"])
    warnings = payload["governance"]["performance_warnings"]
    lines.extend(f"- `{x}`" for x in warnings) if warnings else lines.append("- None")
    lines.extend(["", "## Hard failures"])
    failures = payload["governance"]["hard_failures"]
    lines.extend(f"- `{x}`" for x in failures) if failures else lines.append("- None")
    lines.extend(
        [
            "",
            "> This validation does not prove an optimal bottom or authorise an order.",
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
        default=Path("runtime/market-bottom/recovery-v11-validation.json"),
    )
    ap.add_argument(
        "--out-md",
        type=Path,
        default=Path("runtime/market-bottom/recovery-v11-validation.md"),
    )
    args = ap.parse_args()

    symbols = {
        symbol: _symbol_report(args.data_dir / f"{symbol}.csv", args.config, symbol)
        for symbol in PRIMARY
    }
    payload = {
        "schema_version": "1.0",
        "engine_version": "1.1",
        "symbols": symbols,
        "governance": _promotion_diagnostics(symbols),
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    args.out_md.write_text(_markdown(payload))
    print(json.dumps(payload, indent=2, default=str))

    if not payload["governance"]["hard_invariant_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
