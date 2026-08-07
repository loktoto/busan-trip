#!/usr/bin/env python3
"""Validate orthogonal bottom-indicator families on identical episode samples.

Public ETF/index histories are used only to discover promising feature families.
Because they are proxies rather than licensed point-in-time production datasets,
this validator can retain a family for further research but can never promote it
directly into the live trading engine.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest import evaluate, indicators, load_config, load_prices, run
from orthogonal_indicators_v16 import (
    ASSET_PROXY_MAP,
    SPECS,
    OrthogonalSpec,
    run_orthogonal_candidate,
    spec_dict,
)
from validate_late_stage_v13 import _episode_entry_metrics, _paired_bootstrap, _utility

PRIMARY = ("SPY", "QQQ", "SOXX")


def _load_series(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if not {"Date", "Close"}.issubset(df.columns):
        raise ValueError(f"{path} requires Date,Close")
    df["Date"] = pd.to_datetime(df.Date, utc=False).dt.tz_localize(None)
    df["Close"] = pd.to_numeric(df.Close, errors="coerce")
    return df.dropna().sort_values("Date").drop_duplicates("Date", keep="last")


def _required_proxies(symbol: str) -> set[str]:
    mapping = ASSET_PROXY_MAP[symbol]
    names = {mapping["breadth"], "HYG", "IEF", mapping["vol"], mapping["term"]}
    if mapping["benchmark"]:
        names.add(mapping["benchmark"])
    return names


def _common_start(asset: pd.DataFrame, proxies: dict[str, pd.DataFrame], symbol: str) -> pd.Timestamp:
    starts = [pd.Timestamp(asset.Date.min())]
    starts.extend(pd.Timestamp(proxies[name].Date.min()) for name in _required_proxies(symbol))
    return max(starts)


def _invariants(trades: pd.DataFrame, spec: OrthogonalSpec, cfg) -> list[str]:
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
    if not np.allclose(trades.tranche.to_numpy(float), spec.tranche):
        failures.append("UNDECLARED_TRANCHE")
    if (trades.support_votes < spec.min_support_votes).any():
        failures.append("INSUFFICIENT_SUPPORT_VOTES")
    if (trades.orthogonal_rv_ratio > spec.max_rv_ratio + 1e-12).any():
        failures.append("RV_NOT_CONTRACTING")
    if (trades.sessions_since_breach > spec.max_days_after_breach + 1e-12).any():
        failures.append("STALE_PRIOR_BREACH")
    return failures


def _research_gate(
    symbol: str,
    baseline_recent: dict[str, Any],
    candidate_recent: dict[str, Any],
    candidate_full: dict[str, Any],
    bootstrap: dict[str, Any],
    invariant_failures: list[str],
) -> dict[str, Any]:
    failures = list(invariant_failures)

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
    if base_downside is not None and new_downside is not None:
        need(new_downside >= base_downside - 0.03, "ADDITIONAL_DOWNSIDE_TOO_MUCH_WORSE")
    absolute_cap = {"SPY": 0.09, "QQQ": 0.12, "SOXX": 0.18}[symbol]
    need(new_distance is not None and new_distance <= absolute_cap, "ABSOLUTE_DISTANCE_TOO_HIGH")
    need(forward63 is not None and forward63 > 0, "RECENT_63D_FORWARD_NOT_POSITIVE")
    need(full_forward63 is not None and full_forward63 > 0, "FULL_HISTORY_63D_FORWARD_NOT_POSITIVE")
    need(full_missed is not None and full_missed <= 0.55, "FULL_HISTORY_MISSED_RATE_TOO_HIGH")
    need(p_distance is not None and p_distance >= 0.65, "PAIRED_DISTANCE_EVIDENCE_WEAK")
    need(p_downside is not None and p_downside >= 0.55, "PAIRED_DOWNSIDE_EVIDENCE_WEAK")
    return {
        "research_retain": not failures,
        "production_promote": False,
        "production_block_reason": "PUBLIC_PROXY_NOT_POINT_IN_TIME_PRODUCTION_FEATURE",
        "failures": failures,
    }


def _ibkr_boundary_check(audit_path: Path, prices: dict[str, pd.DataFrame]) -> dict[str, Any]:
    audit = json.loads(audit_path.read_text())
    checks: dict[str, Any] = {}
    all_pass = True
    for symbol in PRIMARY:
        expected = audit["assets"][symbol]["latest_completed_rth_bar"]
        public = prices[symbol].iloc[-1]
        date_match = public.Date.date().isoformat() == expected["Date"]
        close_gap_bps = abs(float(public.Close) / float(expected["Close"]) - 1.0) * 10_000
        passed = bool(date_match and close_gap_bps <= 20.0)
        checks[symbol] = {
            "expected_date": expected["Date"],
            "public_date": public.Date.date().isoformat(),
            "ibkr_close": float(expected["Close"]),
            "public_close": float(public.Close),
            "close_gap_bps": float(close_gap_bps),
            "pass": passed,
        }
        all_pass = all_pass and passed
    return {"all_pass": all_pass, "checks": checks, "window": audit.get("window")}


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Orthogonal bottom-indicator research v1.6",
        "",
        f"- Classification: **{payload['classification']}**",
        f"- IBKR boundary check: **{payload['ibkr_boundary']['all_pass']}**",
        f"- Production promotion: **BLOCKED — public proxies are not production PIT features**",
        "",
    ]
    for symbol in PRIMARY:
        asset = payload["assets"][symbol]
        base = asset["baseline_recent"]
        lines.extend(
            [
                f"## {symbol}",
                "",
                f"Common history start: **{asset['common_start']}**. Baseline recent entry distance "
                f"**{base['mean_entry_distance']:.4f}**, downside **{base['mean_additional_downside']:.4f}**.",
                "",
                "| Candidate | Recent missed | Entry distance | Additional downside | 63d return | P(distance improves) | P(downside non-worse) | Research retain |",
                "|---|---:|---:|---:|---:|---:|---:|---|",
            ]
        )
        fmt = lambda v: "n/a" if v is None else f"{float(v):.4f}"
        for c in asset["candidates"]:
            recent = c["recent"]
            boot = c["paired_bootstrap_recent"]
            lines.append(
                f"| {c['name']} | {fmt(recent['missed_rate_complete'])} | "
                f"{fmt(recent['mean_entry_distance'])} | {fmt(recent['mean_additional_downside'])} | "
                f"{fmt(recent['mean_forward_63d'])} | "
                f"{fmt(boot['probability_distance_improves'])} | "
                f"{fmt(boot['probability_downside_nonworse'])} | "
                f"{c['gate']['research_retain']} |"
            )
        lines.extend(
            [
                "",
                f"Diagnostic winner: **{asset['selected_diagnostic']}**",
                f"Retained feature family: **{asset['selected_research'] or 'NONE'}**",
                "",
            ]
        )
        for c in asset["candidates"]:
            if c["gate"]["failures"]:
                lines.append(f"- `{c['name']}` blocked by: " + ", ".join(c["gate"]["failures"]))
        lines.append("")
    lines.append("> A retained proxy family must be rebuilt with immutable point-in-time data and re-run on identical folds before production use.")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--series-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--ibkr-audit", type=Path, required=True)
    ap.add_argument("--recent-start", type=pd.Timestamp, default=pd.Timestamp("2021-07-26"))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    prices = {symbol: load_prices(args.data_dir / f"{symbol}.csv") for symbol in PRIMARY}
    proxy_names = {"RSP", "QQQE", "XSD", "HYG", "IEF", "VIX", "VXN", "VIX3M", "SPY", "QQQ"}
    proxies: dict[str, pd.DataFrame] = {}
    for name in sorted(proxy_names):
        price_path = args.data_dir / f"{name}.csv"
        series_path = args.series_dir / f"{name}.csv"
        proxies[name] = (
            load_prices(price_path)[["Date", "Close"]]
            if price_path.exists()
            else _load_series(series_path)
        )

    ibkr_boundary = _ibkr_boundary_check(args.ibkr_audit, prices)
    assets: dict[str, Any] = {}
    hard_failures: list[str] = []
    retained_any = False

    for symbol in PRIMARY:
        cfg = load_config(args.config, symbol)
        common_start = _common_start(prices[symbol], proxies, symbol)
        sample = prices[symbol].loc[prices[symbol].Date >= common_start].reset_index(drop=True)
        x = indicators(sample, cfg)
        baseline_trades, baseline_catalog = run(x, cfg)
        _, baseline_episodes, _ = evaluate(x, baseline_trades, baseline_catalog, cfg)
        baseline_full_detail, baseline_full = _episode_entry_metrics(x, baseline_trades, baseline_episodes, None)
        baseline_recent_detail, baseline_recent = _episode_entry_metrics(
            x, baseline_trades, baseline_episodes, args.recent_start
        )

        candidates: list[dict[str, Any]] = []
        for i, spec in enumerate(SPECS[symbol]):
            trades, catalog, _ = run_orthogonal_candidate(x, cfg, spec, proxies)
            _, episodes, _ = evaluate(x, trades, catalog, cfg)
            full_detail, full = _episode_entry_metrics(x, trades, episodes, None)
            recent_detail, recent = _episode_entry_metrics(x, trades, episodes, args.recent_start)
            bootstrap = _paired_bootstrap(
                baseline_recent_detail,
                recent_detail,
                seed=1600 + i + PRIMARY.index(symbol) * 100,
            )
            invariants = _invariants(trades, spec, cfg)
            hard_failures.extend(f"{spec.name}:{failure}" for failure in invariants)
            gate = _research_gate(symbol, baseline_recent, recent, full, bootstrap, invariants)
            candidate = {
                "name": spec.name,
                "spec": spec_dict(spec),
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
        retained = [c for c in candidates if c["gate"]["research_retain"]]
        selected_research = (
            max(retained, key=lambda c: c["diagnostic_utility"])["name"] if retained else None
        )
        retained_any = retained_any or bool(selected_research)
        assets[symbol] = {
            "common_start": common_start.date().isoformat(),
            "history_end": sample.iloc[-1].Date.date().isoformat(),
            "bar_count": int(len(sample)),
            "baseline_full": baseline_full,
            "baseline_recent": baseline_recent,
            "selected_diagnostic": selected_diagnostic,
            "selected_research": selected_research,
            "candidates": candidates,
        }

    payload = {
        "schema_version": "1.0",
        "engine_version": "1.6-research",
        "classification": "PUBLIC ORTHOGONAL PROXY ABLATION — NOT PRODUCTION PIT DATA",
        "recent_start": args.recent_start.date().isoformat(),
        "ibkr_boundary": ibkr_boundary,
        "assets": assets,
        "hard_invariant_pass": not hard_failures,
        "hard_failures": hard_failures,
        "research_family_retained": retained_any,
        "production_promotion": False,
        "production_block_reason": "PROXY_FEATURES_REQUIRE_POINT_IN_TIME_REBUILD_AND_IDENTICAL_FOLD_RETEST",
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    (args.out / "summary.md").write_text(_markdown(payload))
    print(json.dumps(payload, indent=2, default=str))
    if hard_failures or not ibkr_boundary["all_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
