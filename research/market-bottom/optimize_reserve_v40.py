#!/usr/bin/env python3
"""Leakage-aware comparison of a small deep-bear reserve policy set.

Candidate policies are selected only on episodes that began before 2018.  The
2018+ episodes are a chronological holdout.  Results are also reported for the
latest five-year window and for the full completed cycle as descriptive stress
tests.  The full-cycle metric is never used to create historical signals.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd

from backtest import evaluate, indicators, load_config, load_prices
from deep_bear_reserve_v40 import ReservePolicy, run_reserve
from selection import episode_scores, mean_standard_error, robust_episode_stats

SYMBOLS = ("SPY", "QQQ", "SOXX")
TRAIN_CUTOFF = pd.Timestamp("2018-01-01")
MODERN_START = pd.Timestamp("2021-07-26")


def candidate_policies() -> list[ReservePolicy]:
    """Return a deliberately small, auditable candidate family."""
    base = ReservePolicy()
    return [
        replace(
            base,
            name="BASELINE",
            enabled=False,
        ),
        replace(
            base,
            name="R05_CONSERVATIVE",
            reserve_cap=0.05,
            deep_cap=0.20,
            maturity_cap=0.15,
            combined_cap=0.30,
        ),
        replace(base, name="R10_BALANCED"),
        replace(
            base,
            name="R15_BALANCED",
            reserve_cap=0.15,
            deep_cap=0.30,
            maturity_cap=0.25,
            combined_cap=0.40,
        ),
        replace(
            base,
            name="R20_LIGHT",
            reserve_cap=0.20,
            deep_cap=0.35,
            maturity_cap=0.30,
            combined_cap=0.45,
        ),
        replace(
            base,
            name="R10_STRUCTURAL4",
            structural_votes=4,
        ),
        replace(
            base,
            name="R15_STRUCTURAL4",
            structural_votes=4,
            reserve_cap=0.15,
            deep_cap=0.30,
            maturity_cap=0.25,
            combined_cap=0.40,
        ),
        replace(
            base,
            name="R10_MATURITY4",
            maturity_votes=4,
        ),
        replace(
            base,
            name="R10_MATURITY6",
            maturity_votes=6,
        ),
        replace(
            base,
            name="R10_DEEP30",
            deep_fraction=0.30,
        ),
        replace(
            base,
            name="R10_DEEP50",
            deep_fraction=0.50,
        ),
        replace(
            base,
            name="R15_EARLY_RELEASE",
            reserve_cap=0.15,
            deep_fraction=0.30,
            deep_cap=0.30,
            maturity_votes=4,
            maturity_cap=0.25,
            combined_cap=0.40,
        ),
    ]


def _summary(ep: pd.DataFrame) -> dict:
    e = ep.loc[ep.complete].copy()
    stats = robust_episode_stats(e)
    return {
        **stats,
        "episodes": int(len(e)),
        "missed_rate": float(e.missed.mean()) if len(e) else np.nan,
        "mean_deployment": float(e.total_deployment.mean()) if len(e) else np.nan,
        "weighted_distance": float(e.weighted_distance.dropna().mean())
        if e.weighted_distance.notna().any()
        else np.nan,
        "additional_downside": float(e.worst_additional_downside.dropna().mean())
        if e.worst_additional_downside.notna().any()
        else np.nan,
        "any_within_5": float(e.any_within_5.mean()) if len(e) else np.nan,
        "any_within_8": float(e.any_within_8.mean()) if len(e) else np.nan,
        "capital_within_8": float(e.capital_within_8.mean()) if len(e) else np.nan,
    }


def _period(ep: pd.DataFrame, period: str) -> pd.DataFrame:
    starts = pd.to_datetime(ep.start_date)
    if period == "TRAIN_PRE_2018":
        return ep.loc[starts < TRAIN_CUTOFF].copy()
    if period == "HOLDOUT_2018_PLUS":
        return ep.loc[starts >= TRAIN_CUTOFF].copy()
    if period == "MODERN_5Y":
        return ep.loc[starts >= MODERN_START].copy()
    if period == "FULL":
        return ep.copy()
    raise ValueError(period)


def _full_cycle_stress(
    prices: pd.DataFrame, trades: pd.DataFrame, catalog: pd.DataFrame
) -> dict:
    """Descriptive distance to the full recovered-cycle trough."""
    rows = []
    for _, e in catalog.loc[catalog.complete].iterrows():
        g = trades.loc[trades.episode == int(e.episode)]
        if g.empty:
            rows.append(
                {
                    "missed": True,
                    "weighted_distance": np.nan,
                    "additional_downside": np.nan,
                }
            )
            continue
        weights = g.tranche.to_numpy(float)
        prices_paid = g.execution_price.to_numpy(float)
        average = float(np.average(prices_paid, weights=weights))
        trough = float(e.trough)
        adverse = []
        for _, trade in g.iterrows():
            post = prices.iloc[
                int(trade.execution_index) : int(e.end_index) + 1
            ]
            adverse.append(
                float(post.Close.min() / float(trade.execution_price) - 1)
            )
        rows.append(
            {
                "missed": False,
                "weighted_distance": average / trough - 1,
                "additional_downside": min(adverse),
            }
        )
    z = pd.DataFrame(rows)
    return {
        "episodes": int(len(z)),
        "missed_rate": float(z.missed.mean()) if len(z) else np.nan,
        "weighted_distance": float(z.weighted_distance.dropna().mean())
        if z.weighted_distance.notna().any()
        else np.nan,
        "additional_downside": float(z.additional_downside.dropna().mean())
        if z.additional_downside.notna().any()
        else np.nan,
    }


def _policy_complexity(policy: ReservePolicy) -> tuple:
    if not policy.enabled:
        return (0, 0.0, 0.0, 0.0)
    default = ReservePolicy()
    changed = sum(
        getattr(policy, key) != getattr(default, key)
        for key in asdict(default)
        if key not in {"name", "enabled"}
    )
    return (
        1 + changed,
        policy.reserve_cap,
        policy.combined_cap,
        -policy.structural_votes,
    )


def _select_one_se(
    stats: pd.DataFrame, policies: list[ReservePolicy]
) -> dict:
    valid = stats.loc[
        np.isfinite(stats.robust_mean) & np.isfinite(stats.se)
    ].copy()
    if valid.empty:
        return {"selected": None, "reason": "NO_EVALUABLE_TRAIN_EPISODES"}
    best = valid.sort_values("robust_mean", ascending=False).iloc[0]
    threshold = float(best.robust_mean - best.se)
    eligible = valid.loc[valid.robust_mean >= threshold]
    selected_index = min(
        eligible.policy_index.astype(int),
        key=lambda i: _policy_complexity(policies[i]),
    )
    return {
        "selected": policies[selected_index].name,
        "selected_index": int(selected_index),
        "apparent_best": policies[int(best.policy_index)].name,
        "apparent_best_robust_mean": float(best.robust_mean),
        "best_standard_error": float(best.se),
        "one_se_threshold": threshold,
        "eligible_count": int(len(eligible)),
        "selection_sample": "EPISODE_START_BEFORE_2018_ONLY",
    }


def _holdout_gate(
    baseline: pd.DataFrame, challenger: pd.DataFrame
) -> dict:
    b = baseline.loc[baseline.complete].sort_values("episode")
    c = challenger.loc[challenger.complete].sort_values("episode")
    z = b[["episode"]].copy()
    z["base"] = episode_scores(b)
    z = z.merge(
        pd.DataFrame(
            {
                "episode": c.episode.to_numpy(int),
                "new": episode_scores(c),
            }
        ),
        on="episode",
        how="inner",
    )
    if z.empty:
        return {"promote": False, "reason": "NO_COMPARABLE_HOLDOUT_EPISODES"}
    delta = z.new - z.base
    mean, se, n = mean_standard_error(delta.to_numpy(float))
    promote = bool(
        mean > 0
        and mean - se >= -0.02
        and float((delta >= 0).mean()) >= 0.60
        and float(delta.min()) >= -0.25
    )
    return {
        "promote": promote,
        "episodes": n,
        "mean_episode_score_delta": mean,
        "standard_error": se,
        "nonnegative_fraction": float((delta >= 0).mean()),
        "worst_episode_delta": float(delta.min()),
        "thresholds": {
            "mean_delta": "> 0",
            "mean_minus_se": ">= -0.02",
            "nonnegative_fraction": ">= 0.60",
            "worst_episode_delta": ">= -0.25",
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("reserve-v40-optimisation"))
    args = ap.parse_args()

    policies = candidate_policies()
    records: list[dict] = []
    episode_map: dict[tuple[str, str], pd.DataFrame] = {}
    selected: dict[str, dict] = {}
    stress: dict[str, dict] = {}

    for symbol in SYMBOLS:
        cfg = load_config(args.config, symbol)
        prices = load_prices(args.data_dir / f"{symbol}.csv")
        x = indicators(prices, cfg)
        for policy_index, policy in enumerate(policies):
            trades, catalog = run_reserve(x, cfg, policy)
            _, episodes, _ = evaluate(x, trades, catalog, cfg)
            episode_map[(symbol, policy.name)] = episodes
            stress[f"{symbol}:{policy.name}"] = _full_cycle_stress(
                prices, trades, catalog
            )
            for period in (
                "TRAIN_PRE_2018",
                "HOLDOUT_2018_PLUS",
                "MODERN_5Y",
                "FULL",
            ):
                records.append(
                    {
                        "symbol": symbol,
                        "policy": policy.name,
                        "policy_index": policy_index,
                        "period": period,
                        **_summary(_period(episodes, period)),
                    }
                )

    results = pd.DataFrame(records)
    for symbol in SYMBOLS:
        train = results.loc[
            (results.symbol == symbol)
            & (results.period == "TRAIN_PRE_2018")
        ].copy()
        decision = _select_one_se(train, policies)
        if decision.get("selected"):
            holdout_base = _period(
                episode_map[(symbol, "BASELINE")], "HOLDOUT_2018_PLUS"
            )
            holdout_new = _period(
                episode_map[(symbol, decision["selected"])],
                "HOLDOUT_2018_PLUS",
            )
            decision["holdout_gate"] = _holdout_gate(
                holdout_base, holdout_new
            )
        selected[symbol] = decision

    args.out.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.out / "candidate-period-metrics.csv", index=False)
    payload = {
        "schema_version": "4.0",
        "classification": (
            "PURGED CHRONOLOGICAL POLICY COMPARISON — NO ORDER OR LEVERAGE AUTHORITY"
        ),
        "candidate_count": len(policies),
        "policies": [asdict(p) for p in policies],
        "selection": selected,
        "full_cycle_descriptive_stress": stress,
        "controls": {
            "signal_information": "completed close t only",
            "execution": "next open t+1 plus stored costs",
            "selection_sample": "episode start before 2018",
            "holdout_sample": "episode start on/after 2018",
            "modern_sample": "episode start on/after 2021-07-26",
            "full_cycle_role": "descriptive stress only; never signal input",
            "multi_testing_control": "small declared family plus one-standard-error selection",
        },
    }
    (args.out / "optimisation-summary.json").write_text(
        json.dumps(payload, indent=2, default=str)
    )
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
