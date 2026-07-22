#!/usr/bin/env python3
"""Validate regime-aware QQQ and SOXX late-stage candidates."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest import evaluate, indicators, load_config, load_prices, run
from late_stage_v14 import (
    REGIME_PARAMS,
    REGIME_SPECS,
    RegimeParams,
    regime_spec_dict,
    run_regime_late_stage,
)
from validate_late_stage_v13 import (
    _episode_entry_metrics,
    _gate,
    _ibkr_boundary_check,
    _paired_bootstrap,
    _utility,
)

PRIMARY = ("QQQ", "SOXX")


def _invariants(trades: pd.DataFrame, spec, params: RegimeParams, cfg) -> list[str]:
    failures: list[str] = []
    if trades.empty:
        return failures
    if (trades.groupby("episode").size() > 1).any():
        failures.append("MULTIPLE_TRADES_PER_EPISODE")
    if (trades.execution_index != trades.signal_index + 1).any():
        failures.append("NOT_NEXT_OPEN_EXECUTION")
    if trades.symbol.ne(spec.symbol).any():
        failures.append("WRONG_SYMBOL")
    if (trades.tranche > cfg.max_tranche + 1e-12).any():
        failures.append("TRANCHE_CAP")
    if (trades.tranche < cfg.min_tranche - 1e-12).any():
        failures.append("MINIMUM_TRANCHE")
    if not np.allclose(trades.tranche.to_numpy(float), spec.tranche):
        failures.append("UNDECLARED_TRANCHE")
    if (trades.cumulative > cfg.max_deploy + 1e-12).any():
        failures.append("DEPLOYMENT_CAP")
    invalid_regime = ~(
        trades.ordinary_correction_regime.astype(bool)
        | trades.mature_bear_regime.astype(bool)
    )
    if invalid_regime.any():
        failures.append("ENTRY_WITHOUT_REGIME_GATE")
    if (
        trades.long_bear.astype(bool)
        & ~trades.mature_bear_regime.astype(bool)
    ).any():
        failures.append("LONG_BEAR_WITHOUT_MATURITY")
    mature = trades.loc[trades.mature_bear_regime.astype(bool)]
    if not mature.empty:
        if (mature.underwater < params.min_underwater_days).any():
            failures.append("MATURE_BEAR_TOO_EARLY")
        if (mature.regime_washout_count < params.min_prior_washouts).any():
            failures.append("MATURE_BEAR_INSUFFICIENT_WASHOUTS")
        if (mature.cycle_dd > -params.deep_bear_drawdown + 1e-12).any():
            failures.append("MATURE_BEAR_NOT_DEEP_ENOUGH")
        if (~mature.regime_sma200_flattening.astype(bool)).any():
            failures.append("MATURE_BEAR_NOT_FLATTENING")
    return failures


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# QQQ / SOXX regime-aware late-stage validation v1.4",
        "",
        f"- Classification: **{payload['classification']}**",
        f"- IBKR boundary check: **{payload['ibkr_boundary']['all_pass']}**",
        f"- Overall promotion: **{payload['overall_promotion']}**",
        "",
    ]
    for symbol in PRIMARY:
        s = payload["assets"][symbol]
        b = s["baseline_recent"]
        lines.extend(
            [
                f"## {symbol}",
                "",
                f"Baseline recent distance **{b['mean_entry_distance']:.4f}**, "
                f"downside **{b['mean_additional_downside']:.4f}**, "
                f"missed **{b['missed_rate_complete']:.4f}**.",
                "",
                "| Candidate | Recent missed | Entry distance | Additional downside | 63d return | Paired n | P(distance improves) | P(downside non-worse) | Promote |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---|",
            ]
        )
        fmt = lambda v: "n/a" if v is None else f"{float(v):.4f}"
        for c in s["candidates"]:
            r, boot = c["recent"], c["paired_bootstrap_recent"]
            lines.append(
                f"| {c['name']} | {fmt(r['missed_rate_complete'])} | "
                f"{fmt(r['mean_entry_distance'])} | {fmt(r['mean_additional_downside'])} | "
                f"{fmt(r['mean_forward_63d'])} | {boot['paired_episode_count']} | "
                f"{fmt(boot['probability_distance_improves'])} | "
                f"{fmt(boot['probability_downside_nonworse'])} | {c['gate']['promote']} |"
            )
        lines.extend(
            [
                "",
                f"Selected diagnostic: **{s['selected_diagnostic']}**",
                f"Selected promoted: **{s['selected_promoted'] or 'NONE'}**",
            ]
        )
        for c in s["candidates"]:
            if c["gate"]["failures"]:
                lines.append(
                    f"- `{c['name']}` blocked by: "
                    + ", ".join(c["gate"]["failures"])
                )
        lines.append("")
    lines.append("> Regime filtering is retained only when it passes the same asset-level promotion gate.")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--ibkr-audit", type=Path, required=True)
    ap.add_argument("--recent-start", type=pd.Timestamp, default=pd.Timestamp("2021-07-26"))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    prices = {symbol: load_prices(args.data_dir / f"{symbol}.csv") for symbol in PRIMARY}
    ibkr_boundary = _ibkr_boundary_check(args.ibkr_audit, prices)
    assets: dict[str, Any] = {}
    hard_failures: list[str] = []
    any_promoted = False

    for symbol in PRIMARY:
        cfg = load_config(args.config, symbol)
        x = indicators(prices[symbol], cfg)
        baseline_trades, baseline_catalog = run(x, cfg)
        _, baseline_episodes, _ = evaluate(x, baseline_trades, baseline_catalog, cfg)
        baseline_full_detail, baseline_full = _episode_entry_metrics(
            x, baseline_trades, baseline_episodes, None
        )
        baseline_recent_detail, baseline_recent = _episode_entry_metrics(
            x, baseline_trades, baseline_episodes, args.recent_start
        )
        params = REGIME_PARAMS[symbol]
        candidates: list[dict[str, Any]] = []

        for i, spec in enumerate(REGIME_SPECS[symbol]):
            trades, catalog = run_regime_late_stage(x, cfg, spec, params)
            _, episodes, _ = evaluate(x, trades, catalog, cfg)
            full_detail, full = _episode_entry_metrics(x, trades, episodes, None)
            recent_detail, recent = _episode_entry_metrics(
                x, trades, episodes, args.recent_start
            )
            bootstrap = _paired_bootstrap(
                baseline_recent_detail,
                recent_detail,
                seed=1400 + i + (0 if symbol == "QQQ" else 100),
            )
            invariants = _invariants(trades, spec, params, cfg)
            hard_failures.extend(f"{spec.name}:{failure}" for failure in invariants)
            gate = _gate(symbol, baseline_recent, recent, full, bootstrap, invariants)
            candidate = {
                "name": spec.name,
                "spec": regime_spec_dict(spec, params),
                "trade_count": int(len(trades)),
                "full": full,
                "recent": recent,
                "paired_bootstrap_recent": bootstrap,
                "gate": gate,
                "diagnostic_utility": _utility(recent),
            }
            candidates.append(candidate)
            out = args.out / symbol / spec.name
            out.mkdir(parents=True, exist_ok=True)
            trades.to_csv(out / "trades.csv", index=False)
            full_detail.to_csv(out / "episodes-full.csv", index=False)
            recent_detail.to_csv(out / "episodes-recent.csv", index=False)

        selected_diagnostic = max(candidates, key=lambda c: c["diagnostic_utility"])["name"]
        promoted = [c for c in candidates if c["gate"]["promote"]]
        selected_promoted = (
            max(promoted, key=lambda c: c["diagnostic_utility"])["name"] if promoted else None
        )
        any_promoted = any_promoted or bool(selected_promoted)
        assets[symbol] = {
            "history_start": prices[symbol].iloc[0].Date.date().isoformat(),
            "history_end": prices[symbol].iloc[-1].Date.date().isoformat(),
            "bar_count": int(len(prices[symbol])),
            "baseline_full": baseline_full,
            "baseline_recent": baseline_recent,
            "selected_diagnostic": selected_diagnostic,
            "selected_promoted": selected_promoted,
            "candidates": candidates,
        }

    payload = {
        "schema_version": "1.0",
        "engine_version": "1.4-research",
        "classification": "REGIME-AWARE CAUSAL RESEARCH — NOT AUTOMATICALLY PROMOTED",
        "recent_start": args.recent_start.date().isoformat(),
        "ibkr_boundary": ibkr_boundary,
        "assets": assets,
        "hard_invariant_pass": not hard_failures,
        "hard_failures": hard_failures,
        "overall_promotion": (
            "ASSET_SPECIFIC_CANDIDATE_AVAILABLE" if any_promoted else "BLOCKED_NO_CANDIDATE_PASSED"
        ),
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    (args.out / "summary.md").write_text(_markdown(payload))
    print(json.dumps(payload, indent=2, default=str))
    if hard_failures or not ibkr_boundary["all_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
