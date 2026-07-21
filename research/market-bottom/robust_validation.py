#!/usr/bin/env python3
"""Regime-aware, one-standard-error walk-forward validation.

This is the preferred optimiser. It preserves an outer purged test fold, records
all candidate-by-fold results, and selects the simplest candidate whose training
utility is within one standard error of the apparent winner.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from backtest import Config, load_config, load_features, load_prices
from data_audit import assert_price_continuity
from selection import (
    assert_monotonic_deployment,
    robust_episode_stats,
    select_one_standard_error,
)
from validation import episode_bootstrap, parameter_grid, score_period, selection_instability


def robust_walk_forward(
    prices: pd.DataFrame,
    features: pd.DataFrame | None,
    base: Config,
    candidates: list[Config],
    train_days: int,
    test_days: int,
    purge_days: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    fold_rows: list[dict] = []
    candidate_rows: list[dict] = []
    episode_rows: list[pd.DataFrame] = []
    fold = 0
    train_start = 0

    for cfg in candidates:
        assert_monotonic_deployment(cfg)

    while True:
        train_end = train_start + train_days
        test_start = train_end + purge_days
        test_end = test_start + test_days
        if test_end > len(prices):
            break
        fold += 1
        stats_rows = []
        train_episodes: dict[int, pd.DataFrame] = {}
        for i, cfg in enumerate(candidates):
            _, ep = score_period(prices, features, cfg, train_start, train_end)
            stats = robust_episode_stats(ep)
            stats_rows.append({"candidate_index": i, **stats})
            train_episodes[i] = ep
            candidate_rows.append(
                {
                    "fold": fold,
                    "sample": "TRAIN",
                    "candidate_index": i,
                    **stats,
                    "config": json.dumps(asdict(cfg), sort_keys=True),
                }
            )

        stats_df = pd.DataFrame(stats_rows)
        try:
            selected_i, decision = select_one_standard_error(stats_df, candidates, base)
        except ValueError:
            fold_rows.append(
                {
                    "fold": fold,
                    "status": "SKIPPED_NO_COMPLETE_TRAIN_EPISODE",
                    "train_start": prices.iloc[train_start].Date.date(),
                    "train_end": prices.iloc[train_end - 1].Date.date(),
                    "test_start": prices.iloc[test_start].Date.date(),
                    "test_end": prices.iloc[test_end - 1].Date.date(),
                }
            )
            train_start += test_days
            continue

        cfg = candidates[selected_i]
        _, test_ep = score_period(prices, features, cfg, test_start, test_end)
        test_stats = robust_episode_stats(test_ep)
        candidate_rows.append(
            {
                "fold": fold,
                "sample": "TEST_SELECTED",
                "candidate_index": selected_i,
                **test_stats,
                "config": json.dumps(asdict(cfg), sort_keys=True),
            }
        )
        fold_rows.append(
            {
                "fold": fold,
                "status": "OK" if np.isfinite(test_stats["robust_mean"]) else "NO_COMPLETE_TEST_EPISODE",
                "train_start": prices.iloc[train_start].Date.date(),
                "train_end": prices.iloc[train_end - 1].Date.date(),
                "test_start": prices.iloc[test_start].Date.date(),
                "test_end": prices.iloc[test_end - 1].Date.date(),
                "candidate_index": selected_i,
                "train_utility": float(stats_df.loc[stats_df.candidate_index == selected_i, "robust_mean"].iloc[0]),
                "test_utility": test_stats["robust_mean"] if np.isfinite(test_stats["robust_mean"]) else np.nan,
                "test_worst_regime": test_stats.get("worst_regime", np.nan),
                "one_se_threshold": decision["one_se_threshold"],
                "one_se_eligible_count": decision["eligible_count"],
                "apparent_best_candidate": decision["best_candidate_index"],
                "selected_complexity": json.dumps(decision["selected_complexity"]),
                "config": json.dumps(asdict(cfg), sort_keys=True),
            }
        )
        if not test_ep.empty:
            e = test_ep.copy()
            e["fold"] = fold
            e["candidate_index"] = selected_i
            episode_rows.append(e)
        train_start += test_days

    return (
        pd.DataFrame(fold_rows),
        pd.DataFrame(candidate_rows),
        pd.concat(episode_rows, ignore_index=True) if episode_rows else pd.DataFrame(),
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, required=True)
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--grid", type=Path, required=True)
    ap.add_argument("--features-csv", type=Path)
    ap.add_argument("--train-days", type=int, default=1008)
    ap.add_argument("--test-days", type=int, default=252)
    ap.add_argument("--purge-days", type=int, default=84)
    ap.add_argument("--max-unexplained-jump", type=float, default=0.45)
    ap.add_argument("--out", type=Path, default=Path("robust-validation-output"))
    a = ap.parse_args()

    prices = load_prices(a.csv)
    assert_price_continuity(prices, a.max_unexplained_jump)
    features = load_features(a.features_csv)
    base = load_config(a.config, a.symbol)
    grid = json.loads(a.grid.read_text())
    candidates = parameter_grid(base, grid)

    folds, matrix, episodes = robust_walk_forward(
        prices, features, base, candidates, a.train_days, a.test_days, a.purge_days
    )
    result = {
        "classification": "PURGED WALK-FORWARD — ONE-SE SELECTION — NOT GUARANTEED",
        "symbol": a.symbol,
        "candidate_count": len(candidates),
        "fold_count": int(len(folds)),
        "purge_days": a.purge_days,
        "selection_rule": "simplest candidate within one standard error of best regime-robust training utility",
        "bootstrap": episode_bootstrap(episodes),
        "selection_instability": selection_instability(folds),
        "median_test_utility": float(folds.test_utility.dropna().median()) if "test_utility" in folds else np.nan,
        "worst_test_utility": float(folds.test_utility.dropna().min()) if "test_utility" in folds and folds.test_utility.notna().any() else np.nan,
    }
    out = a.out / a.symbol
    out.mkdir(parents=True, exist_ok=True)
    folds.to_csv(out / "robust_walk_forward_folds.csv", index=False)
    matrix.to_csv(out / "candidate_fold_matrix.csv", index=False)
    episodes.to_csv(out / "robust_walk_forward_episodes.csv", index=False)
    (out / "robust_validation_summary.json").write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
