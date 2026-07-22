#!/usr/bin/env python3
"""Validate asset-specific late-stage bottom candidates for QQQ and SOXX.

The validator compares each declared candidate with the existing staged baseline
on full audited public adjusted history and on the exact recent five-year window
independently checked against IBKR.  It does not optimise a continuous parameter
grid.  Promotion requires absolute safety, relative improvement and paired
bootstrap evidence; otherwise the candidate remains diagnostic only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest import evaluate, indicators, load_config, load_prices, run
from late_stage_v13 import SPECS, LateStageSpec, run_late_stage, spec_dict

PRIMARY = ("QQQ", "SOXX")
FORWARD_HORIZONS = (21, 63, 126)
BOOTSTRAP_SAMPLES = 5000


def _finite(value: Any) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if np.isfinite(x) else None


def _complete(episodes: pd.DataFrame, start: pd.Timestamp | None) -> pd.DataFrame:
    if episodes.empty:
        return episodes.copy()
    e = episodes.loc[episodes.complete].copy()
    e["start_ts"] = pd.to_datetime(e.start_date)
    if start is not None:
        e = e.loc[e.start_ts >= start]
    return e


def _episode_entry_metrics(
    x: pd.DataFrame,
    trades: pd.DataFrame,
    episodes: pd.DataFrame,
    start: pd.Timestamp | None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    e = _complete(episodes, start)
    rows: list[dict[str, Any]] = []
    for _, episode in e.iterrows():
        eid = int(episode.episode)
        g = (
            trades.loc[trades.episode == eid].sort_values("execution_index")
            if not trades.empty
            else pd.DataFrame()
        )
        eval_end = int(episode.evaluation_end_index)
        trough_window = x.iloc[int(episode.start_index) : eval_end + 1]
        trough_i = int(trough_window.Close.idxmin())
        trough = float(x.loc[trough_i, "Close"])
        row: dict[str, Any] = {
            "episode": eid,
            "start_date": str(episode.start_date),
            "trough_date": str(x.loc[trough_i, "Date"].date()),
            "max_drawdown": float(episode.max_drawdown),
            "missed": bool(g.empty),
            "entry_distance": np.nan,
            "additional_downside": np.nan,
            "signed_sessions_from_trough": np.nan,
            "absolute_sessions_from_trough": np.nan,
            "false_start_10pct": False,
        }
        for h in FORWARD_HORIZONS:
            row[f"forward_{h}d"] = np.nan
        if not g.empty:
            first = g.iloc[0]
            exec_i = int(first.execution_index)
            entry = float(first.execution_price)
            post = x.iloc[exec_i : eval_end + 1]
            signed = exec_i - trough_i
            row.update(
                {
                    "execution_date": str(first.execution_date),
                    "entry_distance": entry / trough - 1.0,
                    "additional_downside": float(post.Close.min() / entry - 1.0),
                    "signed_sessions_from_trough": int(signed),
                    "absolute_sessions_from_trough": abs(int(signed)),
                    "false_start_10pct": bool(float(post.Close.min() / entry - 1.0) <= -0.10),
                }
            )
            for h in FORWARD_HORIZONS:
                if exec_i + h < len(x):
                    row[f"forward_{h}d"] = float(x.iloc[exec_i + h].Close / entry - 1.0)
        rows.append(row)

    detail = pd.DataFrame(rows)
    traded = detail.loc[~detail.missed] if not detail.empty else detail
    summary: dict[str, Any] = {
        "episode_count_complete": int(len(detail)),
        "traded_episode_count": int(len(traded)),
        "missed_rate_complete": _finite(detail.missed.mean()) if len(detail) else None,
        "mean_entry_distance": _finite(traded.entry_distance.mean()) if len(traded) else None,
        "median_entry_distance": _finite(traded.entry_distance.median()) if len(traded) else None,
        "mean_additional_downside": _finite(traded.additional_downside.mean()) if len(traded) else None,
        "mean_signed_sessions_from_trough": (
            _finite(traded.signed_sessions_from_trough.mean()) if len(traded) else None
        ),
        "mean_absolute_sessions_from_trough": (
            _finite(traded.absolute_sessions_from_trough.mean()) if len(traded) else None
        ),
        "late_after_trough_rate": (
            _finite((traded.signed_sessions_from_trough > 0).mean()) if len(traded) else None
        ),
        "false_start_10pct_rate": (
            _finite(traded.false_start_10pct.mean()) if len(traded) else None
        ),
    }
    for h in FORWARD_HORIZONS:
        summary[f"mean_forward_{h}d"] = (
            _finite(traded[f"forward_{h}d"].dropna().mean()) if len(traded) else None
        )
    return detail, summary


def _paired_bootstrap(
    baseline: pd.DataFrame,
    challenger: pd.DataFrame,
    seed: int,
) -> dict[str, Any]:
    b = baseline.loc[~baseline.missed, ["episode", "entry_distance", "additional_downside"]]
    c = challenger.loc[~challenger.missed, ["episode", "entry_distance", "additional_downside"]]
    z = b.merge(c, on="episode", suffixes=("_base", "_new")).dropna()
    if len(z) < 3:
        return {
            "paired_episode_count": int(len(z)),
            "probability_distance_improves": None,
            "probability_downside_nonworse": None,
            "mean_distance_delta": None,
            "mean_downside_delta": None,
        }

    distance_delta = (z.entry_distance_new - z.entry_distance_base).to_numpy(float)
    downside_delta = (z.additional_downside_new - z.additional_downside_base).to_numpy(float)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(z), size=(BOOTSTRAP_SAMPLES, len(z)))
    boot_distance = distance_delta[indices].mean(axis=1)
    boot_downside = downside_delta[indices].mean(axis=1)
    return {
        "paired_episode_count": int(len(z)),
        "mean_distance_delta": float(distance_delta.mean()),
        "mean_downside_delta": float(downside_delta.mean()),
        "probability_distance_improves": float((boot_distance < 0).mean()),
        "probability_downside_nonworse": float((boot_downside >= 0).mean()),
        "distance_delta_ci_95": [
            float(np.quantile(boot_distance, 0.025)),
            float(np.quantile(boot_distance, 0.975)),
        ],
        "downside_delta_ci_95": [
            float(np.quantile(boot_downside, 0.025)),
            float(np.quantile(boot_downside, 0.975)),
        ],
    }


def _invariants(trades: pd.DataFrame, spec: LateStageSpec, cfg) -> list[str]:
    failures: list[str] = []
    if trades.empty:
        return failures
    if trades.symbol.ne(spec.symbol).any():
        failures.append("WRONG_SYMBOL")
    if (trades.groupby("episode").size() > 1).any():
        failures.append("MULTIPLE_TRADES_PER_EPISODE")
    if (trades.execution_index != trades.signal_index + 1).any():
        failures.append("NOT_NEXT_OPEN_EXECUTION")
    if trades.long_bear.any():
        failures.append("ENTRY_IN_LONG_BEAR")
    if (trades.tranche > cfg.max_tranche + 1e-12).any():
        failures.append("TRANCHE_CAP")
    if (trades.tranche < cfg.min_tranche - 1e-12).any():
        failures.append("MINIMUM_TRANCHE")
    if not np.allclose(trades.tranche.to_numpy(float), spec.tranche):
        failures.append("UNDECLARED_TRANCHE")
    if (trades.cumulative > cfg.max_deploy + 1e-12).any():
        failures.append("DEPLOYMENT_CAP")
    return failures


def _gate(
    symbol: str,
    baseline_recent: dict[str, Any],
    candidate_recent: dict[str, Any],
    candidate_full: dict[str, Any],
    bootstrap: dict[str, Any],
    invariant_failures: list[str],
) -> dict[str, Any]:
    failures: list[str] = list(invariant_failures)
    warnings: list[str] = []

    def need(condition: bool, reason: str) -> None:
        if not condition:
            failures.append(reason)

    episodes = candidate_recent.get("episode_count_complete") or 0
    missed = candidate_recent.get("missed_rate_complete")
    base_distance = baseline_recent.get("mean_entry_distance")
    new_distance = candidate_recent.get("mean_entry_distance")
    base_false = baseline_recent.get("false_start_10pct_rate")
    new_false = candidate_recent.get("false_start_10pct_rate")
    new_downside = candidate_recent.get("mean_additional_downside")
    forward63 = candidate_recent.get("mean_forward_63d")
    full_missed = candidate_full.get("missed_rate_complete")
    full_forward63 = candidate_full.get("mean_forward_63d")
    p_distance = bootstrap.get("probability_distance_improves")
    p_downside = bootstrap.get("probability_downside_nonworse")

    need(episodes >= 5, "INSUFFICIENT_RECENT_EPISODES")
    need(missed is not None and missed <= 0.34, "RECENT_MISSED_RATE_TOO_HIGH")
    need(base_distance is not None and new_distance is not None, "MISSING_DISTANCE_METRIC")
    if base_distance is not None and new_distance is not None:
        required = min(base_distance * 0.75, base_distance - 0.02)
        need(new_distance <= required, "BOTTOM_PROXIMITY_NOT_IMPROVED_ENOUGH")
    absolute_distance_cap = 0.10 if symbol == "QQQ" else 0.15
    need(new_distance is not None and new_distance <= absolute_distance_cap, "ABSOLUTE_DISTANCE_TOO_HIGH")
    if base_false is not None and new_false is not None:
        need(new_false <= base_false + 0.05, "FALSE_START_RATE_WORSE")
    downside_floor = -0.08 if symbol == "QQQ" else -0.12
    need(new_downside is not None and new_downside >= downside_floor, "ADDITIONAL_DOWNSIDE_TOO_LARGE")
    need(forward63 is not None and forward63 > 0, "RECENT_63D_FORWARD_NOT_POSITIVE")
    need(full_missed is not None and full_missed <= 0.50, "FULL_HISTORY_MISSED_RATE_TOO_HIGH")
    need(full_forward63 is not None and full_forward63 > 0, "FULL_HISTORY_63D_FORWARD_NOT_POSITIVE")
    need(p_distance is not None and p_distance >= 0.70, "PAIRED_DISTANCE_EVIDENCE_WEAK")
    need(p_downside is not None and p_downside >= 0.60, "PAIRED_DOWNSIDE_EVIDENCE_WEAK")

    if candidate_recent.get("late_after_trough_rate") is not None:
        late_rate = float(candidate_recent["late_after_trough_rate"])
        if late_rate > 0.80:
            warnings.append("MOST_ENTRIES_AFTER_TROUGH")
    return {
        "promote": not failures,
        "failures": failures,
        "warnings": warnings,
    }


def _utility(summary: dict[str, Any]) -> float:
    missed = float(summary.get("missed_rate_complete") or 1.0)
    distance = float(summary.get("mean_entry_distance") or 0.50)
    downside = float(summary.get("mean_additional_downside") or -0.50)
    forward63 = float(summary.get("mean_forward_63d") or -0.50)
    false_start = float(summary.get("false_start_10pct_rate") or 0.0)
    return float(-distance + 0.50 * downside + 0.25 * forward63 - 0.50 * missed - 0.20 * false_start)


def _ibkr_boundary_check(audit_path: Path, prices: dict[str, pd.DataFrame]) -> dict[str, Any]:
    audit = json.loads(audit_path.read_text())
    checks: dict[str, Any] = {}
    all_pass = True
    for symbol in PRIMARY:
        expected = audit["assets"][symbol]["latest_completed_rth_bar"]
        p = prices[symbol].iloc[-1]
        date_match = p.Date.date().isoformat() == expected["Date"]
        close_gap_bps = abs(float(p.Close) / float(expected["Close"]) - 1.0) * 10_000
        passed = bool(date_match and close_gap_bps <= 20.0)
        checks[symbol] = {
            "expected_date": expected["Date"],
            "public_date": p.Date.date().isoformat(),
            "ibkr_close": float(expected["Close"]),
            "public_close": float(p.Close),
            "close_gap_bps": float(close_gap_bps),
            "pass": passed,
        }
        all_pass = all_pass and passed
    return {
        "classification": audit.get("classification"),
        "window": audit.get("window"),
        "all_pass": all_pass,
        "checks": checks,
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# QQQ / SOXX late-stage bottom validation v1.3",
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
                f"Baseline recent mean entry distance: **{b['mean_entry_distance']:.4f}**; "
                f"additional downside: **{b['mean_additional_downside']:.4f}**; "
                f"missed rate: **{b['missed_rate_complete']:.4f}**.",
                "",
                "| Candidate | Recent missed | Entry distance | Additional downside | False-start >10% | 63d return | P(distance improves) | P(downside non-worse) | Promote |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---|",
            ]
        )
        for candidate in s["candidates"]:
            r = candidate["recent"]
            boot = candidate["paired_bootstrap_recent"]
            fmt = lambda v: "n/a" if v is None else f"{float(v):.4f}"
            lines.append(
                f"| {candidate['name']} | {fmt(r['missed_rate_complete'])} | "
                f"{fmt(r['mean_entry_distance'])} | {fmt(r['mean_additional_downside'])} | "
                f"{fmt(r['false_start_10pct_rate'])} | {fmt(r['mean_forward_63d'])} | "
                f"{fmt(boot['probability_distance_improves'])} | "
                f"{fmt(boot['probability_downside_nonworse'])} | "
                f"{candidate['gate']['promote']} |"
            )
        lines.extend(
            [
                "",
                f"Selected diagnostic candidate: **{s['selected_diagnostic']}**",
                f"Selected promoted candidate: **{s['selected_promoted'] or 'NONE'}**",
                "",
            ]
        )
        for candidate in s["candidates"]:
            if candidate["gate"]["failures"]:
                lines.append(
                    f"- `{candidate['name']}` blocked by: "
                    + ", ".join(candidate["gate"]["failures"])
                )
    lines.extend(
        [
            "",
            "> A diagnostic winner is not a production signal unless every promotion gate passes.",
        ]
    )
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
    any_promoted = False
    hard_failures: list[str] = []

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

        candidates: list[dict[str, Any]] = []
        for i, spec in enumerate(SPECS[symbol]):
            trades, catalog = run_late_stage(x, cfg, spec)
            _, episodes, _ = evaluate(x, trades, catalog, cfg)
            full_detail, full = _episode_entry_metrics(x, trades, episodes, None)
            recent_detail, recent = _episode_entry_metrics(
                x, trades, episodes, args.recent_start
            )
            bootstrap = _paired_bootstrap(
                baseline_recent_detail,
                recent_detail,
                seed=1300 + i + (0 if symbol == "QQQ" else 100),
            )
            invariants = _invariants(trades, spec, cfg)
            hard_failures.extend(f"{spec.name}:{failure}" for failure in invariants)
            gate = _gate(symbol, baseline_recent, recent, full, bootstrap, invariants)
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

            candidate_dir = args.out / symbol / spec.name
            candidate_dir.mkdir(parents=True, exist_ok=True)
            trades.to_csv(candidate_dir / "trades.csv", index=False)
            full_detail.to_csv(candidate_dir / "episodes-full.csv", index=False)
            recent_detail.to_csv(candidate_dir / "episodes-recent.csv", index=False)

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
        "engine_version": "1.3-research",
        "classification": "CAUSAL ASSET-SPECIFIC RESEARCH — NOT AUTOMATICALLY PROMOTED",
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
