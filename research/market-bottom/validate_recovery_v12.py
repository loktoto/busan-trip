#!/usr/bin/env python3
"""Validate the latest conservative monitor against dual-path recovery candidates.

Variants
--------
BASELINE
    Current audited conservative engine.
V1_1_INSIDE_ZONE
    Adds one recovery probe, but only while price remains inside the watch zone.
V1_2_POST_THRESHOLD
    Adds one bounded catch-up after a prior completed close entered the watch zone
    and a later completed close rebounded above it.

The script evaluates full audited public adjusted history and the exact recent
five-year boundary independently checked through IBKR.  Raw IBKR licensed bars
are not committed to the public repository.  All signals are close-t and all
entries are next-open t+1 plus configured costs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from backtest import Config, evaluate, indicators, load_config, load_prices, run
from recovery_v11 import run_v11
from recovery_v12 import (
    CATCHUP_MAX_ATR_ABOVE_THRESHOLD,
    CATCHUP_MAX_RECOVERED_DD,
    CATCHUP_SIZE,
    CATCHUP_WINDOW,
    add_catchup_features,
    run_v12,
)

PRIMARY = ("SPY", "QQQ", "SOXX")
VARIANTS: dict[str, Callable] = {
    "BASELINE": run,
    "V1_1_INSIDE_ZONE": run_v11,
    "V1_2_POST_THRESHOLD": run_v12,
}
FORWARD_HORIZONS = (21, 63, 126)


def _finite(value: Any) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if np.isfinite(x) else None


def _mean(values: list[float]) -> float | None:
    clean = [float(x) for x in values if np.isfinite(x)]
    return float(np.mean(clean)) if clean else None


def _rate(values: list[bool]) -> float | None:
    return float(np.mean(values)) if values else None


def _complete_subset(episodes: pd.DataFrame, start: pd.Timestamp | None) -> pd.DataFrame:
    if episodes.empty:
        return episodes.copy()
    e = episodes.loc[episodes.complete].copy()
    e["start_ts"] = pd.to_datetime(e.start_date)
    if start is not None:
        e = e.loc[e.start_ts >= start]
    return e


def _episode_summary(episodes: pd.DataFrame, start: pd.Timestamp | None) -> dict[str, Any]:
    e = _complete_subset(episodes, start)
    traded = e.loc[~e.missed] if not e.empty else e
    out: dict[str, Any] = {
        "episode_count_complete": int(len(e)),
        "missed_rate_complete": _finite(e.missed.mean()) if len(e) else None,
        "mean_deployment_complete": _finite(e.total_deployment.mean()) if len(e) else None,
        "mean_weighted_distance_complete": (
            _finite(e.weighted_distance.dropna().mean()) if len(e) else None
        ),
        "mean_worst_additional_downside_complete": (
            _finite(e.worst_additional_downside.dropna().mean()) if len(e) else None
        ),
    }
    for p in (3, 5, 8):
        out[f"any_within_{p}_rate_complete"] = (
            _finite(e[f"any_within_{p}"].mean()) if len(e) else None
        )
        out[f"weighted_within_{p}_rate_traded_complete"] = (
            _finite(traded[f"weighted_within_{p}"].mean()) if len(traded) else None
        )
        out[f"mean_capital_within_{p}_complete"] = (
            _finite(e[f"capital_within_{p}"].mean()) if len(e) else None
        )
    return out


def _path_metrics(
    x: pd.DataFrame,
    trades: pd.DataFrame,
    episodes: pd.DataFrame,
    start: pd.Timestamp | None,
) -> dict[str, Any]:
    e = _complete_subset(episodes, start)
    first_distances: list[float] = []
    signed_days: list[int] = []
    absolute_days: list[int] = []
    late: list[bool] = []
    false_start_10: list[bool] = []
    forward: dict[int, list[float]] = {h: [] for h in FORWARD_HORIZONS}

    for _, episode in e.iterrows():
        eid = int(episode.episode)
        g = (
            trades.loc[trades.episode == eid].sort_values("execution_index")
            if not trades.empty
            else pd.DataFrame()
        )
        if g.empty:
            continue
        first = g.iloc[0]
        exec_i = int(first.execution_index)
        eval_end = int(episode.evaluation_end_index)
        trough_window = x.iloc[int(episode.start_index) : eval_end + 1]
        trough_i = int(trough_window.Close.idxmin())
        trough = float(x.loc[trough_i, "Close"])
        entry = float(first.execution_price)
        lag = exec_i - trough_i
        post = x.iloc[exec_i : eval_end + 1]

        first_distances.append(entry / trough - 1.0)
        signed_days.append(lag)
        absolute_days.append(abs(lag))
        late.append(lag > 0)
        false_start_10.append(float(post.Close.min() / entry - 1.0) <= -0.10)
        for h in FORWARD_HORIZONS:
            if exec_i + h < len(x):
                forward[h].append(float(x.iloc[exec_i + h].Close / entry - 1.0))

    return {
        "traded_complete_episode_count": int(len(first_distances)),
        "mean_first_entry_distance": _mean(first_distances),
        "mean_signed_sessions_from_trough": _mean([float(v) for v in signed_days]),
        "mean_absolute_sessions_from_trough": _mean([float(v) for v in absolute_days]),
        "late_after_trough_rate": _rate(late),
        "false_start_10pct_rate": _rate(false_start_10),
        **{f"mean_first_entry_forward_{h}d": _mean(forward[h]) for h in FORWARD_HORIZONS},
    }


def _catchup_metrics(
    x: pd.DataFrame,
    trades: pd.DataFrame,
    episodes: pd.DataFrame,
    start: pd.Timestamp | None,
) -> dict[str, Any]:
    if trades.empty or "catchup_probe_transition" not in trades:
        return {"trade_count": 0, "episode_count": 0}
    catchups = trades.loc[trades.catchup_probe_transition.fillna(False)].copy()
    e = _complete_subset(episodes, start)
    valid_eids = set(e.episode.astype(int))
    catchups = catchups.loc[catchups.episode.astype(int).isin(valid_eids)]
    if catchups.empty:
        return {"trade_count": 0, "episode_count": 0}

    by_episode = e.set_index(e.episode.astype(int))
    distances: list[float] = []
    adverse: list[float] = []
    forward: dict[int, list[float]] = {h: [] for h in FORWARD_HORIZONS}
    for _, trade in catchups.iterrows():
        episode = by_episode.loc[int(trade.episode)]
        exec_i = int(trade.execution_index)
        eval_end = int(episode.evaluation_end_index)
        window = x.iloc[int(episode.start_index) : eval_end + 1]
        trough = float(window.Close.min())
        entry = float(trade.execution_price)
        post = x.iloc[exec_i : eval_end + 1]
        distances.append(entry / trough - 1.0)
        adverse.append(float(post.Close.min() / entry - 1.0))
        for h in FORWARD_HORIZONS:
            if exec_i + h < len(x):
                forward[h].append(float(x.iloc[exec_i + h].Close / entry - 1.0))
    return {
        "trade_count": int(len(catchups)),
        "episode_count": int(catchups.episode.nunique()),
        "mean_distance_to_episode_trough": _mean(distances),
        "mean_additional_downside": _mean(adverse),
        "mean_signal_cycle_dd": _finite(catchups.cycle_dd.mean()),
        "mean_tranche": _finite(catchups.tranche.mean()),
        **{f"mean_forward_{h}d": _mean(forward[h]) for h in FORWARD_HORIZONS},
    }


def _missed_first_signal_stress(
    x: pd.DataFrame,
    baseline_trades: pd.DataFrame,
    baseline_episodes: pd.DataFrame,
    cfg: Config,
    start: pd.Timestamp | None,
) -> dict[str, Any]:
    """Ask whether v1.2 offers a causal second chance after a missed first alert.

    This is not a portfolio simulation.  It deliberately removes the first
    baseline entry as an operational stress and measures whether a later bounded
    post-threshold catch-up signal appears in that same episode.
    """
    y = add_catchup_features(x, cfg)
    e = _complete_subset(baseline_episodes, start)
    opportunities = 0
    recovered = 0
    distances: list[float] = []
    adverse: list[float] = []
    lags: list[int] = []

    for _, episode in e.iterrows():
        eid = int(episode.episode)
        g = baseline_trades.loc[baseline_trades.episode == eid].sort_values("signal_index")
        if g.empty:
            continue
        first = g.iloc[0]
        opportunities += 1
        start_i = int(first.signal_index) + 1
        end_i = min(int(episode.evaluation_end_index), len(y) - 2)
        candidates = y.loc[start_i:end_i]
        candidates = candidates.loc[candidates.catchup_probe.fillna(False)]
        if candidates.empty:
            continue
        signal_i = int(candidates.index[0])
        exec_i = signal_i + 1
        entry = float(y.iloc[exec_i].Open) * (1 + cfg.all_in_cost_bps / 10_000)
        window = y.iloc[int(episode.start_index) : int(episode.evaluation_end_index) + 1]
        trough_i = int(window.Close.idxmin())
        trough = float(y.loc[trough_i, "Close"])
        post = y.iloc[exec_i : int(episode.evaluation_end_index) + 1]
        recovered += 1
        distances.append(entry / trough - 1.0)
        adverse.append(float(post.Close.min() / entry - 1.0))
        lags.append(exec_i - int(first.execution_index))

    return {
        "missed_first_alert_opportunities": int(opportunities),
        "episodes_with_catchup_second_chance": int(recovered),
        "second_chance_rate": (float(recovered / opportunities) if opportunities else None),
        "mean_sessions_after_missed_entry": _mean([float(v) for v in lags]),
        "mean_catchup_distance_to_trough": _mean(distances),
        "mean_catchup_additional_downside": _mean(adverse),
    }


def _invariants(
    x: pd.DataFrame,
    trades: pd.DataFrame,
    cfg: Config,
) -> list[str]:
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

    if "catchup_probe_transition" not in trades:
        return failures
    c = trades.loc[trades.catchup_probe_transition.fillna(False)]
    if c.empty:
        return failures
    if (c.groupby("episode").size() > 1).any():
        failures.append("MULTIPLE_CATCHUPS_PER_EPISODE")
    if c.long_bear.any():
        failures.append("CATCHUP_IN_LONG_BEAR")
    if (c.cycle_dd <= -cfg.watch_dd + 1e-12).any():
        failures.append("CATCHUP_NOT_ABOVE_WATCH_THRESHOLD")
    if (c.tranche > CATCHUP_SIZE[cfg.symbol] + 1e-12).any():
        failures.append("CATCHUP_SIZE_CAP")
    if (c.catchup_sessions_since_breach > CATCHUP_WINDOW[cfg.symbol]).any():
        failures.append("STALE_CATCHUP_BREACH")
    if (c.catchup_recovered_dd > CATCHUP_MAX_RECOVERED_DD[cfg.symbol] + 1e-12).any():
        failures.append("CATCHUP_DRAWDOWN_BAND")
    if (c.catchup_atr_above_threshold > CATCHUP_MAX_ATR_ABOVE_THRESHOLD + 1e-12).any():
        failures.append("CATCHUP_ATR_BAND")
    for _, trade in c.iterrows():
        signal_i = int(trade.signal_index)
        prior = x.iloc[max(0, signal_i - CATCHUP_WINDOW[cfg.symbol]) : signal_i]
        if not (prior.cycle_dd <= -cfg.watch_dd).any():
            failures.append("NO_PRIOR_CAUSAL_BREACH")
            break
    return failures


def _ibkr_audit(
    audit_path: Path,
    public_prices: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    audit = json.loads(audit_path.read_text())
    checks: dict[str, Any] = {}
    all_pass = True
    for symbol in PRIMARY:
        expected = audit["assets"][symbol]["latest_completed_rth_bar"]
        p = public_prices[symbol].iloc[-1]
        date_match = p.Date.date().isoformat() == expected["Date"]
        close_gap = abs(float(p.Close) / float(expected["Close"]) - 1.0)
        pass_symbol = date_match and close_gap <= 0.002
        all_pass = all_pass and pass_symbol
        checks[symbol] = {
            "date_match": date_match,
            "public_latest_date": p.Date.date().isoformat(),
            "ibkr_latest_date": expected["Date"],
            "public_latest_close": float(p.Close),
            "ibkr_latest_close": float(expected["Close"]),
            "absolute_close_gap_fraction": close_gap,
            "pass_20bps": pass_symbol,
        }
    return {
        "classification": audit["classification"],
        "window": audit["window"],
        "raw_ibkr_bars_committed": audit["governance"]["raw_ibkr_bars_committed"],
        "checks": checks,
        "all_latest_bar_checks_pass": all_pass,
    }


def _delta(new: dict[str, Any], old: dict[str, Any], key: str) -> float | None:
    a, b = _finite(new.get(key)), _finite(old.get(key))
    return None if a is None or b is None else a - b


def _candidate_gate(symbols: dict[str, Any]) -> dict[str, Any]:
    hard_failures: list[str] = []
    utility_failures: list[str] = []
    positive_findings: list[str] = []
    for symbol, report in symbols.items():
        hard_failures.extend(f"{symbol}:{x}" for x in report["invariant_failures"])
        for sample in ("full_history", "ibkr_recent_window"):
            base = report["variants"]["BASELINE"][sample]
            v12 = report["variants"]["V1_2_POST_THRESHOLD"][sample]
            missed_delta = _delta(v12["episode"], base["episode"], "missed_rate_complete")
            distance_delta = _delta(
                v12["episode"], base["episode"], "mean_weighted_distance_complete"
            )
            downside_delta = _delta(
                v12["episode"], base["episode"], "mean_worst_additional_downside_complete"
            )
            false_delta = _delta(v12["path"], base["path"], "false_start_10pct_rate")
            if missed_delta is not None and missed_delta > 0.001:
                utility_failures.append(f"{symbol}:{sample}:MISSED_RATE_WORSE_{missed_delta:.4f}")
            if distance_delta is not None and distance_delta > 0.015:
                utility_failures.append(f"{symbol}:{sample}:DISTANCE_WORSE_{distance_delta:.4f}")
            if downside_delta is not None and downside_delta < -0.020:
                utility_failures.append(f"{symbol}:{sample}:DOWNSIDE_WORSE_{downside_delta:.4f}")
            if false_delta is not None and false_delta > 0.05:
                utility_failures.append(f"{symbol}:{sample}:FALSE_START_WORSE_{false_delta:.4f}")
            if missed_delta is not None and missed_delta < -0.001:
                positive_findings.append(f"{symbol}:{sample}:MISSED_RATE_IMPROVED_{missed_delta:.4f}")

        stress = report["missed_first_alert_stress"]["ibkr_recent_window"]
        rate = _finite(stress.get("second_chance_rate"))
        if rate is not None and rate > 0:
            positive_findings.append(f"{symbol}:MISSED_ALERT_SECOND_CHANCE_{rate:.4f}")

    empirical_pass = not hard_failures and not utility_failures
    return {
        "classification": "PUBLIC REPRODUCIBILITY + DERIVED IBKR AUDIT — NOT FORMAL OOS PROMOTION",
        "hard_invariant_pass": not hard_failures,
        "candidate_utility_gate_pass": empirical_pass,
        "hard_failures": hard_failures,
        "utility_failures": utility_failures,
        "positive_findings": positive_findings,
        "promotion_status": (
            "BLOCKED_PENDING_CAUSAL_OOS_AND_ACTUAL_MONITOR_LEDGER"
            if empirical_pass
            else "REJECT_OR_REVISE_V1_2"
        ),
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Latest bottom monitor — dual-path v1.2 backtest",
        "",
        f"- Classification: **{payload['governance']['classification']}**",
        f"- Utility gate: **{payload['governance']['candidate_utility_gate_pass']}**",
        f"- Promotion: **{payload['governance']['promotion_status']}**",
        f"- IBKR latest-bar audit: **{payload['ibkr_audit']['all_latest_bar_checks_pass']}**",
        "",
        "## Recent five-year comparison",
        "",
        "| Symbol | Variant | Complete episodes | Missed | Weighted distance | Worst extra downside | First-entry distance | False-start >10% | Catch-ups |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for symbol in PRIMARY:
        report = payload["symbols"][symbol]
        for variant in VARIANTS:
            r = report["variants"][variant]["ibkr_recent_window"]
            e, p, c = r["episode"], r["path"], r["catchup"]
            fmt = lambda v: "n/a" if v is None else f"{v:.4f}"
            lines.append(
                f"| {symbol} | {variant} | {e['episode_count_complete']} | "
                f"{fmt(e['missed_rate_complete'])} | "
                f"{fmt(e['mean_weighted_distance_complete'])} | "
                f"{fmt(e['mean_worst_additional_downside_complete'])} | "
                f"{fmt(p['mean_first_entry_distance'])} | "
                f"{fmt(p['false_start_10pct_rate'])} | {c.get('trade_count', 0)} |"
            )
    lines.extend(["", "## Missed-first-alert resilience", ""])
    lines.append("| Symbol | Opportunities | Second chances | Rate | Catch-up distance | Catch-up downside |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for symbol in PRIMARY:
        s = payload["symbols"][symbol]["missed_first_alert_stress"]["ibkr_recent_window"]
        fmt = lambda v: "n/a" if v is None else f"{v:.4f}"
        lines.append(
            f"| {symbol} | {s['missed_first_alert_opportunities']} | "
            f"{s['episodes_with_catchup_second_chance']} | {fmt(s['second_chance_rate'])} | "
            f"{fmt(s['mean_catchup_distance_to_trough'])} | "
            f"{fmt(s['mean_catchup_additional_downside'])} |"
        )
    lines.extend(["", "## Governance findings"])
    for key in ("positive_findings", "utility_failures", "hard_failures"):
        lines.append(f"### {key.replace('_', ' ').title()}")
        values = payload["governance"][key]
        lines.extend(f"- `{v}`" for v in values) if values else lines.append("- None")
    lines.extend(
        [
            "",
            "> Raw IBKR history is not redistributed in this public repository. The IBKR connector independently validates the recent window, latest completed RTH bars and split handling; reproducible numerical tests use audited public adjusted histories.",
            "",
            "> This research result does not create or transmit an order.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=Path("config.example.json"))
    ap.add_argument(
        "--ibkr-audit",
        type=Path,
        default=Path("ibkr-five-year-audit-2026-07-22.json"),
    )
    ap.add_argument("--recent-start", default="2021-07-26")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    recent_start = pd.Timestamp(args.recent_start)
    public_prices: dict[str, pd.DataFrame] = {}
    symbols: dict[str, Any] = {}

    for symbol in PRIMARY:
        prices = load_prices(args.data_dir / f"{symbol}.csv")
        public_prices[symbol] = prices
        cfg = load_config(args.config, symbol)
        x = indicators(prices, cfg)
        variants: dict[str, Any] = {}
        baseline_trades = pd.DataFrame()
        baseline_episodes = pd.DataFrame()
        invariant_failures: list[str] = []

        for name, runner in VARIANTS.items():
            trades, catalog = runner(x, cfg)
            _, episodes, _ = evaluate(x, trades, catalog, cfg)
            if name == "BASELINE":
                baseline_trades, baseline_episodes = trades, episodes
            if name == "V1_2_POST_THRESHOLD":
                invariant_failures.extend(_invariants(x, trades, cfg))
            variants[name] = {
                "trade_count_all": int(len(trades)),
                "full_history": {
                    "episode": _episode_summary(episodes, None),
                    "path": _path_metrics(x, trades, episodes, None),
                    "catchup": _catchup_metrics(x, trades, episodes, None),
                },
                "ibkr_recent_window": {
                    "episode": _episode_summary(episodes, recent_start),
                    "path": _path_metrics(x, trades, episodes, recent_start),
                    "catchup": _catchup_metrics(x, trades, episodes, recent_start),
                },
            }

        stress = {
            "full_history": _missed_first_signal_stress(
                x, baseline_trades, baseline_episodes, cfg, None
            ),
            "ibkr_recent_window": _missed_first_signal_stress(
                x, baseline_trades, baseline_episodes, cfg, recent_start
            ),
        }
        symbols[symbol] = {
            "history_start": prices.iloc[0].Date.date().isoformat(),
            "history_end": prices.iloc[-1].Date.date().isoformat(),
            "bar_count": int(len(prices)),
            "variants": variants,
            "missed_first_alert_stress": stress,
            "invariant_failures": sorted(set(invariant_failures)),
        }

    payload = {
        "schema_version": "1.0",
        "engine_candidate": "dual-path-v1.2",
        "signal_time": "completed close t",
        "execution_time": "next open t+1 plus configured costs",
        "recent_window_start": args.recent_start,
        "ibkr_audit": _ibkr_audit(args.ibkr_audit, public_prices),
        "symbols": symbols,
    }
    payload["governance"] = _candidate_gate(symbols)

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "result.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    (args.out / "report.md").write_text(_markdown(payload))
    print(json.dumps(payload, indent=2, default=str))

    if not payload["governance"]["hard_invariant_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
