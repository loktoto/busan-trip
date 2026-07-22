#!/usr/bin/env python3
"""Validate corrected regime-mature stress-normalisation candidates v1.8."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest import evaluate, indicators, load_config, load_prices, run
from stress_cycle_maturity_v18 import PARAMS, SPECS, MaturityParams, run_mature_stress_candidate, spec_dict
from validate_late_stage_v13 import _episode_entry_metrics, _paired_bootstrap, _utility
from validate_stress_normalization_v17 import FAMILY_KEYS, LAGS, _common_start, _ibkr_boundary, _load_external

PRIMARY = ("SPY", "QQQ", "SOXX")


def _invariants(trades: pd.DataFrame, spec, params: MaturityParams, cfg) -> list[str]:
    failures: list[str] = []
    if trades.empty:
        return failures
    if trades.symbol.ne(spec.symbol).any():
        failures.append("WRONG_SYMBOL")
    if (trades.groupby("episode").size() > 1).any():
        failures.append("MULTIPLE_TRADES_PER_EPISODE")
    if (trades.execution_index != trades.signal_index + 1).any():
        failures.append("NOT_NEXT_OPEN_EXECUTION")
    if (trades.tranche > cfg.max_tranche + 1e-12).any():
        failures.append("TRANCHE_CAP")
    if (trades.tranche < cfg.min_tranche - 1e-12).any():
        failures.append("MINIMUM_TRANCHE")
    if (trades.sessions_since_breach_transition < 1).any():
        failures.append("SAME_DAY_BREACH_CONFIRMATION")
    if (trades.sessions_since_breach_transition > spec.max_sessions_after_breach + 1e-12).any():
        failures.append("STALE_BREACH_TRANSITION")
    if (trades.stress_rv_ratio > spec.max_rv_ratio + 1e-12).any():
        failures.append("RV_NOT_CONTRACTING")
    if (~(trades.ordinary_regime.astype(bool) | trades.mature_bear_regime.astype(bool))).any():
        failures.append("ENTRY_WITHOUT_REGIME_GATE")

    mature = trades.loc[trades.mature_bear_regime.astype(bool)]
    if not mature.empty:
        if (mature.cycle_dd > -params.deep_bear_drawdown + 1e-12).any():
            failures.append("MATURE_BEAR_NOT_DEEP_ENOUGH")
        if (mature.underwater < params.min_underwater_days).any():
            failures.append("MATURE_BEAR_TOO_EARLY")
        if (mature.prior_stress_event_count < params.min_prior_stress_events).any():
            failures.append("MATURE_BEAR_INSUFFICIENT_STRESS_EVENTS")
        if (mature.stress_family_votes < 2).any():
            failures.append("MATURE_BEAR_NOT_INDEPENDENT")
        if (~mature.sma200_flattening.astype(bool)).any():
            failures.append("MATURE_BEAR_200DMA_NOT_FLATTENING")
    return sorted(set(failures))


def _gate(
    symbol: str,
    baseline_recent: dict[str, Any],
    candidate_recent: dict[str, Any],
    candidate_full: dict[str, Any],
    bootstrap: dict[str, Any],
    invariants: list[str],
) -> dict[str, Any]:
    failures = list(invariants)

    def need(condition: bool, reason: str) -> None:
        if not condition:
            failures.append(reason)

    episodes = int(candidate_recent.get("episode_count_complete") or 0)
    missed = candidate_recent.get("missed_rate_complete")
    base_distance = baseline_recent.get("mean_entry_distance")
    new_distance = candidate_recent.get("mean_entry_distance")
    base_downside = baseline_recent.get("mean_additional_downside")
    new_downside = candidate_recent.get("mean_additional_downside")
    forward63 = candidate_recent.get("mean_forward_63d")
    full_forward63 = candidate_full.get("mean_forward_63d")
    full_missed = candidate_full.get("missed_rate_complete")
    p_distance = bootstrap.get("probability_distance_improves")
    p_downside = bootstrap.get("probability_downside_nonworse")

    need(episodes >= 5, "INSUFFICIENT_RECENT_EPISODES")
    need(missed is not None and missed <= 0.50, "RECENT_MISSED_RATE_TOO_HIGH")
    need(base_distance is not None and new_distance is not None, "MISSING_DISTANCE_METRIC")
    if base_distance is not None and new_distance is not None:
        required = min(base_distance * 0.80, base_distance - 0.015)
        need(new_distance <= required, "BOTTOM_PROXIMITY_NOT_IMPROVED_ENOUGH")
    absolute_cap = {"SPY": 0.09, "QQQ": 0.12, "SOXX": 0.18}[symbol]
    need(new_distance is not None and new_distance <= absolute_cap, "ABSOLUTE_DISTANCE_TOO_HIGH")
    if base_downside is not None and new_downside is not None:
        need(new_downside >= base_downside - 0.02, "ADDITIONAL_DOWNSIDE_TOO_MUCH_WORSE")
    need(forward63 is not None and forward63 > 0, "RECENT_63D_FORWARD_NOT_POSITIVE")
    need(full_forward63 is not None and full_forward63 > 0, "FULL_HISTORY_63D_FORWARD_NOT_POSITIVE")
    need(full_missed is not None and full_missed <= 0.55, "FULL_HISTORY_MISSED_RATE_TOO_HIGH")
    need(p_distance is not None and p_distance >= 0.70, "PAIRED_DISTANCE_EVIDENCE_WEAK")
    need(p_downside is not None and p_downside >= 0.60, "PAIRED_DOWNSIDE_EVIDENCE_WEAK")
    return {
        "research_retain": not failures,
        "production_promote": False,
        "production_block_reason": "REVISED_OR_PRELIMINARY_STRESS_HISTORY_NOT_IMMUTABLE_PIT_VINTAGE",
        "failures": sorted(set(failures)),
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Regime-mature stress normalisation v1.8",
        "",
        f"- IBKR boundary check: **{payload['ibkr_boundary']['all_pass']}**",
        f"- Research family retained: **{payload['research_family_retained']}**",
        "- Production promotion: **BLOCKED — source vintages are not immutable point-in-time archives**",
        "- Breach age correction: **measured from threshold transition; same-day confirmation prohibited**",
        "",
    ]
    fmt = lambda value: "n/a" if value is None else f"{float(value):.4f}"
    for symbol in PRIMARY:
        lines.extend([f"## {symbol}", ""])
        lines.append("| Candidate | Common start | Recent missed | Entry distance | Additional downside | 63d return | P(distance improves) | P(downside non-worse) | Retain |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|---|")
        asset = payload["assets"][symbol]
        for candidate in asset["candidates"]:
            recent = candidate["recent"]
            boot = candidate["paired_bootstrap_recent"]
            lines.append(
                f"| {candidate['name']} | {candidate['common_start']} | {fmt(recent['missed_rate_complete'])} | "
                f"{fmt(recent['mean_entry_distance'])} | {fmt(recent['mean_additional_downside'])} | "
                f"{fmt(recent['mean_forward_63d'])} | {fmt(boot['probability_distance_improves'])} | "
                f"{fmt(boot['probability_downside_nonworse'])} | {candidate['gate']['research_retain']} |"
            )
        lines.extend(["", f"Diagnostic winner: **{asset['selected_diagnostic']}**", f"Retained family: **{asset['selected_research'] or 'NONE'}**", ""])
        for candidate in asset["candidates"]:
            if candidate["gate"]["failures"]:
                lines.append(f"- `{candidate['name']}` blocked by: " + ", ".join(candidate["gate"]["failures"]))
        lines.append("")
    lines.extend([
        "## Governance",
        "",
        "- COR1M/COR3M and DSPX/VIXEQ remain blocked without authorised historical data.",
        "- Earnings-revision breadth remains blocked without historical point-in-time consensus data.",
        "- No candidate may affect the production monitor, tranche sizing or leverage.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--ofr-dir", type=Path, required=True)
    parser.add_argument("--series-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--ibkr-audit", type=Path, required=True)
    parser.add_argument("--recent-start", type=pd.Timestamp, default=pd.Timestamp("2021-07-26"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    prices = {symbol: load_prices(args.data_dir / f"{symbol}.csv") for symbol in PRIMARY}
    external = _load_external(args.ofr_dir, args.series_dir)
    boundary = _ibkr_boundary(args.ibkr_audit, prices)
    assets: dict[str, Any] = {}
    hard_failures: list[str] = []
    retained_any = False

    for symbol in PRIMARY:
        cfg = load_config(args.config, symbol)
        params = PARAMS[symbol]
        candidates = []
        for index, spec in enumerate(SPECS[symbol]):
            start = _common_start(prices[symbol], external, spec.family)
            sample = prices[symbol].loc[prices[symbol].Date >= start].reset_index(drop=True)
            x = indicators(sample, cfg)
            base_trades, base_catalog = run(x, cfg)
            _, base_episodes, _ = evaluate(x, base_trades, base_catalog, cfg)
            base_full_detail, base_full = _episode_entry_metrics(x, base_trades, base_episodes, None)
            base_recent_detail, base_recent = _episode_entry_metrics(x, base_trades, base_episodes, args.recent_start)

            required_external = {key: external[key] for key in FAMILY_KEYS[spec.family]}
            required_lags = {key: LAGS[key] for key in FAMILY_KEYS[spec.family]}
            trades, catalog, _ = run_mature_stress_candidate(
                x, cfg, spec, required_external, required_lags, params
            )
            _, episodes, _ = evaluate(x, trades, catalog, cfg)
            full_detail, full = _episode_entry_metrics(x, trades, episodes, None)
            recent_detail, recent = _episode_entry_metrics(x, trades, episodes, args.recent_start)
            bootstrap = _paired_bootstrap(
                base_recent_detail,
                recent_detail,
                seed=1800 + PRIMARY.index(symbol) * 100 + index,
            )
            invariants = _invariants(trades, spec, params, cfg)
            hard_failures.extend(f"{spec.name}:{failure}" for failure in invariants)
            gate = _gate(symbol, base_recent, recent, full, bootstrap, invariants)
            candidate = {
                "name": spec.name,
                "spec": spec_dict(spec, params),
                "common_start": start.date().isoformat(),
                "bar_count": int(len(sample)),
                "trade_count": int(len(trades)),
                "baseline_full": base_full,
                "baseline_recent": base_recent,
                "full": full,
                "recent": recent,
                "paired_bootstrap_recent": bootstrap,
                "gate": gate,
                "diagnostic_utility": _utility(recent),
            }
            candidates.append(candidate)
            output = args.out / symbol / spec.name
            output.mkdir(parents=True, exist_ok=True)
            trades.to_csv(output / "trades.csv", index=False)
            full_detail.to_csv(output / "episodes-full.csv", index=False)
            recent_detail.to_csv(output / "episodes-recent.csv", index=False)

        diagnostic = max(candidates, key=lambda candidate: candidate["diagnostic_utility"])["name"]
        retained = [candidate for candidate in candidates if candidate["gate"]["research_retain"]]
        selected = max(retained, key=lambda candidate: candidate["diagnostic_utility"])["name"] if retained else None
        retained_any = retained_any or bool(selected)
        assets[symbol] = {
            "selected_diagnostic": diagnostic,
            "selected_research": selected,
            "candidates": candidates,
        }

    payload = {
        "schema_version": "1.0",
        "engine_version": "1.8-research",
        "classification": "REGIME-MATURE STRESS NORMALIZATION — CORRECTED BREACH AGE — NOT PIT VINTAGES",
        "recent_start": args.recent_start.date().isoformat(),
        "ibkr_boundary": boundary,
        "availability_lags_business_days": LAGS,
        "maturity_parameters": {symbol: asdict(PARAMS[symbol]) for symbol in PRIMARY},
        "assets": assets,
        "hard_invariant_pass": not hard_failures,
        "hard_failures": hard_failures,
        "research_family_retained": retained_any,
        "production_promotion": False,
        "v17_status": "INVALIDATED_FOR_PROMOTION_BY_BREACH_AGE_ACCOUNTING_DEFECT",
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    (args.out / "summary.md").write_text(_markdown(payload))
    print(json.dumps(payload, indent=2, default=str))
    if hard_failures or not boundary["all_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    from dataclasses import asdict
    main()
