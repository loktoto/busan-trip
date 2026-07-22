#!/usr/bin/env python3
"""Validate OFR/volatility/funding stress-normalisation candidates v1.7."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest import evaluate, indicators, load_config, load_prices, run
from stress_normalization_v17 import SPECS, StressSpec, run_stress_candidate, spec_dict
from validate_late_stage_v13 import _episode_entry_metrics, _paired_bootstrap, _utility

PRIMARY = ("SPY", "QQQ", "SOXX")


FAMILY_KEYS = {
    "FSI": {"FSI_TOTAL", "FSI_CREDIT", "FSI_FUNDING", "FSI_VOL", "FSI_US"},
    "VOL": {"VIX", "VIX3M", "VIX9D", "VVIX", "VXN", "MOVE"},
    "FUNDING": {
        "SOFR", "SOFR_1P", "SOFR_99P", "BGCR", "DVP_RATE", "DVP_VOLUME", "FAILS_TOTAL", "FAILS_CORP"
    },
}
FAMILY_KEYS["COMPOSITE"] = set().union(*FAMILY_KEYS.values())

LAGS = {
    "FSI_TOTAL": 2,
    "FSI_CREDIT": 2,
    "FSI_FUNDING": 2,
    "FSI_VOL": 2,
    "FSI_US": 2,
    "VIX": 0,
    "VIX3M": 0,
    "VIX9D": 0,
    "VVIX": 0,
    "VXN": 0,
    "MOVE": 0,
    "SOFR": 1,
    "SOFR_1P": 1,
    "SOFR_99P": 1,
    "BGCR": 1,
    "DVP_RATE": 1,
    "DVP_VOLUME": 1,
    "FAILS_TOTAL": 2,
    "FAILS_CORP": 2,
}


def _series(path: Path, column: str | None = None) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "Date" not in frame:
        raise ValueError(f"{path} missing Date")
    if column is None:
        column = "Value" if "Value" in frame else "Close"
    if column not in frame:
        raise ValueError(f"{path} missing {column}")
    out = frame[["Date", column]].rename(columns={column: "Value"})
    out["Date"] = pd.to_datetime(out.Date, utc=False).dt.tz_localize(None)
    out["Value"] = pd.to_numeric(out.Value, errors="coerce")
    return out.dropna().sort_values("Date").drop_duplicates("Date", keep="last")


def _load_external(ofr_dir: Path, series_dir: Path) -> dict[str, pd.DataFrame]:
    fsi = pd.read_csv(ofr_dir / "FSI.csv")
    fsi["Date"] = pd.to_datetime(fsi.Date, utc=False).dt.tz_localize(None)
    external = {
        "FSI_TOTAL": fsi[["Date", "OFR FSI"]].rename(columns={"OFR FSI": "Value"}),
        "FSI_CREDIT": fsi[["Date", "Credit"]].rename(columns={"Credit": "Value"}),
        "FSI_FUNDING": fsi[["Date", "Funding"]].rename(columns={"Funding": "Value"}),
        "FSI_VOL": fsi[["Date", "Volatility"]].rename(columns={"Volatility": "Value"}),
        "FSI_US": fsi[["Date", "United States"]].rename(columns={"United States": "Value"}),
        "VIX": _series(series_dir / "VIX.csv"),
        "VIX3M": _series(series_dir / "VIX3M.csv"),
        "VIX9D": _series(series_dir / "VIX9D.csv"),
        "VVIX": _series(series_dir / "VVIX.csv"),
        "VXN": _series(series_dir / "VXN.csv"),
        "MOVE": _series(series_dir / "MOVE.csv"),
        "SOFR": _series(ofr_dir / "SOFR.csv"),
        "SOFR_1P": _series(ofr_dir / "SOFR_1P.csv"),
        "SOFR_99P": _series(ofr_dir / "SOFR_99P.csv"),
        "BGCR": _series(ofr_dir / "BGCR.csv"),
        "DVP_RATE": _series(ofr_dir / "DVP_RATE.csv"),
        "DVP_VOLUME": _series(ofr_dir / "DVP_VOLUME.csv"),
        "FAILS_TOTAL": _series(ofr_dir / "FAILS_TOTAL.csv"),
        "FAILS_CORP": _series(ofr_dir / "FAILS_CORP.csv"),
    }
    return external


def _common_start(prices: pd.DataFrame, external: dict[str, pd.DataFrame], family: str) -> pd.Timestamp:
    starts = [pd.Timestamp(prices.Date.min())]
    starts.extend(pd.Timestamp(external[key].Date.min()) for key in FAMILY_KEYS[family])
    return max(starts)


def _invariants(trades: pd.DataFrame, spec: StressSpec, cfg) -> list[str]:
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
    if (trades.stress_rv_ratio > spec.max_rv_ratio + 1e-12).any():
        failures.append("RV_NOT_CONTRACTING")
    if (trades.sessions_since_breach > spec.max_sessions_after_breach + 1e-12).any():
        failures.append("STALE_BREACH")
    for _, trade in trades.iterrows():
        if spec.family == "FSI" and not bool(trade.fsi_normalizing):
            failures.append("FSI_SIGNAL_WITHOUT_FSI_NORMALIZATION")
        if spec.family == "VOL" and not bool(trade.vol_normalizing):
            failures.append("VOL_SIGNAL_WITHOUT_VOL_NORMALIZATION")
        if spec.family == "FUNDING" and not bool(trade.funding_normalizing):
            failures.append("FUNDING_SIGNAL_WITHOUT_FUNDING_NORMALIZATION")
        if spec.family == "COMPOSITE" and int(trade.stress_family_votes) < 2:
            failures.append("COMPOSITE_WITH_FEWER_THAN_TWO_FAMILIES")
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
        need(new_downside >= base_downside - 0.03, "ADDITIONAL_DOWNSIDE_TOO_MUCH_WORSE")
    need(forward63 is not None and forward63 > 0, "RECENT_63D_FORWARD_NOT_POSITIVE")
    need(full_forward63 is not None and full_forward63 > 0, "FULL_HISTORY_63D_FORWARD_NOT_POSITIVE")
    need(full_missed is not None and full_missed <= 0.55, "FULL_HISTORY_MISSED_RATE_TOO_HIGH")
    need(p_distance is not None and p_distance >= 0.65, "PAIRED_DISTANCE_EVIDENCE_WEAK")
    need(p_downside is not None and p_downside >= 0.55, "PAIRED_DOWNSIDE_EVIDENCE_WEAK")
    return {
        "research_retain": not failures,
        "production_promote": False,
        "production_block_reason": "CURRENT_REVISED_OR_PRELIMINARY_HISTORY_NOT_IMMUTABLE_PIT_VINTAGE",
        "failures": sorted(set(failures)),
    }


def _ibkr_boundary(audit_path: Path, prices: dict[str, pd.DataFrame]) -> dict[str, Any]:
    audit = json.loads(audit_path.read_text())
    checks = {}
    all_pass = True
    for symbol in PRIMARY:
        expected = audit["assets"][symbol]["latest_completed_rth_bar"]
        row = prices[symbol].iloc[-1]
        gap = abs(float(row.Close) / float(expected["Close"]) - 1) * 10_000
        passed = row.Date.date().isoformat() == expected["Date"] and gap <= 20
        checks[symbol] = {"date": row.Date.date().isoformat(), "close_gap_bps": gap, "pass": passed}
        all_pass = all_pass and passed
    return {"all_pass": all_pass, "checks": checks, "window": audit.get("window")}


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Stress peak-normalisation research v1.7",
        "",
        f"- IBKR boundary check: **{payload['ibkr_boundary']['all_pass']}**",
        "- Production promotion: **BLOCKED — revised/preliminary histories are not immutable point-in-time vintages**",
        f"- Research family retained: **{payload['research_family_retained']}**",
        "",
    ]
    fmt = lambda v: "n/a" if v is None else f"{float(v):.4f}"
    for symbol in PRIMARY:
        lines.extend([f"## {symbol}", ""])
        lines.append("| Candidate | Common start | Recent missed | Entry distance | Additional downside | 63d return | P(distance improves) | P(downside non-worse) | Retain |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|---|")
        for c in payload["assets"][symbol]["candidates"]:
            r, b = c["recent"], c["paired_bootstrap_recent"]
            lines.append(
                f"| {c['name']} | {c['common_start']} | {fmt(r['missed_rate_complete'])} | "
                f"{fmt(r['mean_entry_distance'])} | {fmt(r['mean_additional_downside'])} | "
                f"{fmt(r['mean_forward_63d'])} | {fmt(b['probability_distance_improves'])} | "
                f"{fmt(b['probability_downside_nonworse'])} | {c['gate']['research_retain']} |"
            )
        a = payload["assets"][symbol]
        lines.extend(["", f"Diagnostic winner: **{a['selected_diagnostic']}**", f"Retained family: **{a['selected_research'] or 'NONE'}**", ""])
        for c in a["candidates"]:
            if c["gate"]["failures"]:
                lines.append(f"- `{c['name']}` blocked by: " + ", ".join(c["gate"]["failures"]))
        lines.append("")
    lines.extend([
        "## Explicitly blocked indicators",
        "",
        "- Cboe COR1M/COR3M and DSPX/VIXEQ historical data: not used without an authorised historical dataset; Cboe DataShop access is treated as licensed.",
        "- Earnings-revision breadth: not used without a historical point-in-time consensus database.",
        "",
        "> A retained family still requires immutable vintage reconstruction and identical-fold validation before it can affect a live tranche.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--ofr-dir", type=Path, required=True)
    ap.add_argument("--series-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--ibkr-audit", type=Path, required=True)
    ap.add_argument("--recent-start", type=pd.Timestamp, default=pd.Timestamp("2021-07-26"))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    prices = {symbol: load_prices(args.data_dir / f"{symbol}.csv") for symbol in PRIMARY}
    external = _load_external(args.ofr_dir, args.series_dir)
    boundary = _ibkr_boundary(args.ibkr_audit, prices)
    assets = {}
    hard_failures: list[str] = []
    retained_any = False

    for symbol in PRIMARY:
        cfg = load_config(args.config, symbol)
        candidates = []
        for i, spec in enumerate(SPECS[symbol]):
            start = _common_start(prices[symbol], external, spec.family)
            sample = prices[symbol].loc[prices[symbol].Date >= start].reset_index(drop=True)
            x = indicators(sample, cfg)
            base_trades, base_catalog = run(x, cfg)
            _, base_episodes, _ = evaluate(x, base_trades, base_catalog, cfg)
            base_full_detail, base_full = _episode_entry_metrics(x, base_trades, base_episodes, None)
            base_recent_detail, base_recent = _episode_entry_metrics(x, base_trades, base_episodes, args.recent_start)

            required_external = {key: external[key] for key in FAMILY_KEYS[spec.family]}
            required_lags = {key: LAGS[key] for key in FAMILY_KEYS[spec.family]}
            trades, catalog, _ = run_stress_candidate(x, cfg, spec, required_external, required_lags)
            _, episodes, _ = evaluate(x, trades, catalog, cfg)
            full_detail, full = _episode_entry_metrics(x, trades, episodes, None)
            recent_detail, recent = _episode_entry_metrics(x, trades, episodes, args.recent_start)
            bootstrap = _paired_bootstrap(base_recent_detail, recent_detail, seed=1700 + PRIMARY.index(symbol) * 100 + i)
            invariants = _invariants(trades, spec, cfg)
            hard_failures.extend(f"{spec.name}:{f}" for f in invariants)
            gate = _gate(symbol, base_recent, recent, full, bootstrap, invariants)
            candidate = {
                "name": spec.name,
                "spec": spec_dict(spec),
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
            out = args.out / symbol / spec.name
            out.mkdir(parents=True, exist_ok=True)
            trades.to_csv(out / "trades.csv", index=False)
            full_detail.to_csv(out / "episodes-full.csv", index=False)
            recent_detail.to_csv(out / "episodes-recent.csv", index=False)

        diagnostic = max(candidates, key=lambda c: c["diagnostic_utility"])["name"]
        retained = [c for c in candidates if c["gate"]["research_retain"]]
        selected = max(retained, key=lambda c: c["diagnostic_utility"])["name"] if retained else None
        retained_any = retained_any or bool(selected)
        assets[symbol] = {"selected_diagnostic": diagnostic, "selected_research": selected, "candidates": candidates}

    payload = {
        "schema_version": "1.0",
        "engine_version": "1.7-research",
        "classification": "OFFICIAL/PUBLIC STRESS NORMALIZATION RESEARCH — NOT IMMUTABLE PIT VINTAGES",
        "recent_start": args.recent_start.date().isoformat(),
        "ibkr_boundary": boundary,
        "availability_lags_business_days": LAGS,
        "assets": assets,
        "hard_invariant_pass": not hard_failures,
        "hard_failures": hard_failures,
        "research_family_retained": retained_any,
        "production_promotion": False,
        "blocked_features": {
            "COR1M_COR3M_DSPX_VIXEQ": "HISTORICAL_DATA_REQUIRES_AUTHORISED_LICENSED_SOURCE",
            "EARNINGS_REVISION_BREADTH": "POINT_IN_TIME_CONSENSUS_DATABASE_UNAVAILABLE",
        },
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    (args.out / "summary.md").write_text(_markdown(payload))
    print(json.dumps(payload, indent=2, default=str))
    if hard_failures or not boundary["all_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
