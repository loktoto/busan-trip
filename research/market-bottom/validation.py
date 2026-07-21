#!/usr/bin/env python3
"""Walk-forward validation, feature ablation and episode bootstrap.

The primary score measures bottom proximity, missed episodes, adverse excursion and
capital deployed near the later trough. It deliberately does not optimise CAGR.

Signals are restricted to the requested train/test interval. Evaluation is allowed
to use a forward tail because bottom proximity is a forward-labelled outcome. No
trades generated inside that tail are retained. The full price path before each
interval is preserved because unresolved cycle highs and underwater duration are
path-dependent state variables that cannot be reconstructed from a short warm-up.
"""
from __future__ import annotations

import argparse
import itertools
import json
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd

from backtest import Config, evaluate, indicators, load_config, load_features, load_prices, run


def utility(ep: pd.DataFrame) -> float:
    if ep.empty or "complete" not in ep.columns:
        return float("-inf")
    e = ep.loc[ep.complete].copy()
    if e.empty:
        return float("-inf")
    any8 = e.any_within_8.mean()
    miss = e.missed.mean()
    capital8 = e.capital_within_8.mean()
    adverse = -e.worst_additional_downside.fillna(-0.25).mean()
    weighted = e.weighted_distance.fillna(0.30).clip(upper=0.50).mean()
    return float(2.0 * any8 + 1.5 * capital8 - 2.0 * miss - adverse - weighted)


def parameter_grid(base: Config, grid: dict) -> list[Config]:
    keys = list(grid)
    return [replace(base, **dict(zip(keys, values))) for values in itertools.product(*(grid[k] for k in keys))]


def subset_with_warmup_and_tail(
    df: pd.DataFrame,
    start: int,
    end: int,
    warmup: int = 260,
    evaluation_tail: int = 252,
) -> tuple[pd.DataFrame, int, int]:
    """Return full causal history, a signal interval and an evaluation-only tail.

    `warmup` remains in the signature for backward compatibility but is not used
    to truncate history. `offset` is the first permitted signal row and
    `signal_end` is the exclusive last permitted signal row. Future rows are
    present only so the evaluator can measure later troughs/recovery.
    """
    del warmup
    if not (0 <= start < end <= len(df)):
        raise ValueError("Require 0 <= start < end <= len(df)")
    left = 0
    right = min(len(df), end + evaluation_tail)
    return df.iloc[left:right].reset_index(drop=True), start, end


def score_period(
    prices: pd.DataFrame,
    features: pd.DataFrame | None,
    cfg: Config,
    start: int,
    end: int,
) -> tuple[float, pd.DataFrame]:
    sub, offset, signal_end = subset_with_warmup_and_tail(
        prices,
        start,
        end,
        evaluation_tail=cfg.episode_eval_max_days,
    )
    sub_features = None
    if features is not None:
        d0, d1 = sub.Date.min(), sub.Date.max()
        sub_features = features.loc[(features.Date >= d0) & (features.Date <= d1)].copy()
    x = indicators(sub, cfg, sub_features)
    trades, catalog = run(x, cfg)

    # Each episode is assigned to exactly one signal partition by its start date.
    # This avoids double-counting an episode across adjacent test partitions.
    catalog = catalog.loc[
        (catalog.start_index >= offset) & (catalog.start_index < signal_end)
    ].copy()
    allowed = set(catalog.episode)
    if not trades.empty:
        trades = trades.loc[
            trades.episode.isin(allowed)
            & (trades.signal_index >= offset)
            & (trades.signal_index < signal_end)
        ].copy()

    # A still-unrecovered episode is nevertheless evaluable once the full fixed
    # 252-session horizon is observed. Near-dataset-end episodes without the full
    # horizon remain incomplete and are excluded rather than filled with hindsight.
    if not catalog.empty:
        fixed_horizon_observed = (
            catalog.start_index.astype(int) + cfg.episode_eval_max_days <= len(x) - 1
        )
        catalog.loc[fixed_horizon_observed, "complete"] = True

    _, ep, _ = evaluate(x, trades, catalog, cfg)
    return utility(ep), ep


def walk_forward(
    prices: pd.DataFrame,
    features: pd.DataFrame | None,
    candidates: list[Config],
    train_days: int,
    test_days: int,
    purge_days: int,
    step_days: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, episodes = [], []
    fold = 0
    train_start = 0
    step_days = test_days if step_days is None else step_days
    while True:
        train_end = train_start + train_days
        test_start = train_end + purge_days
        test_end = test_start + test_days
        if test_end > len(prices):
            break
        fold += 1
        train_scores = []
        for i, cfg in enumerate(candidates):
            score, _ = score_period(prices, features, cfg, train_start, train_end)
            if np.isfinite(score):
                train_scores.append((score, i))
        if not train_scores:
            rows.append(
                {
                    "fold": fold,
                    "train_start": prices.iloc[train_start].Date.date(),
                    "train_end": prices.iloc[train_end - 1].Date.date(),
                    "test_start": prices.iloc[test_start].Date.date(),
                    "test_end": prices.iloc[test_end - 1].Date.date(),
                    "candidate_index": np.nan,
                    "train_utility": np.nan,
                    "test_utility": np.nan,
                    "config": None,
                    "status": "SKIPPED_NO_EVALUABLE_TRAIN_EPISODE",
                }
            )
            train_start += step_days
            continue
        train_scores.sort(reverse=True)
        best_train, best_i = train_scores[0]
        cfg = candidates[best_i]
        test_score, ep = score_period(prices, features, cfg, test_start, test_end)
        rows.append(
            {
                "fold": fold,
                "train_start": prices.iloc[train_start].Date.date(),
                "train_end": prices.iloc[train_end - 1].Date.date(),
                "test_start": prices.iloc[test_start].Date.date(),
                "test_end": prices.iloc[test_end - 1].Date.date(),
                "candidate_index": best_i,
                "train_utility": best_train,
                "test_utility": test_score if np.isfinite(test_score) else np.nan,
                "config": json.dumps(asdict(cfg), sort_keys=True),
                "status": "OK" if np.isfinite(test_score) else "NO_EVALUABLE_TEST_EPISODE",
            }
        )
        if not ep.empty:
            ep = ep.copy()
            ep["fold"] = fold
            ep["candidate_index"] = best_i
            episodes.append(ep)
        train_start += step_days
    return pd.DataFrame(rows), pd.concat(episodes, ignore_index=True) if episodes else pd.DataFrame()


def episode_bootstrap(ep: pd.DataFrame, samples: int = 2000, seed: int = 7) -> dict:
    if ep.empty or "complete" not in ep.columns:
        return {}
    e = ep.loc[ep.complete].copy()
    if e.empty:
        return {}
    rng = np.random.default_rng(seed)
    metrics = {
        "missed_rate": e.missed.astype(float).to_numpy(),
        "any_within_8_rate": e.any_within_8.astype(float).to_numpy(),
        "capital_within_8": e.capital_within_8.to_numpy(float),
        "weighted_distance": e.weighted_distance.fillna(0.30).to_numpy(float),
        "worst_additional_downside": e.worst_additional_downside.fillna(-0.25).to_numpy(float),
    }
    out = {}
    n = len(e)
    for name, arr in metrics.items():
        draws = np.empty(samples)
        for i in range(samples):
            idx = rng.integers(0, n, size=n)
            draws[i] = arr[idx].mean()
        out[name] = {
            "estimate": float(arr.mean()),
            "ci_2_5": float(np.quantile(draws, 0.025)),
            "ci_97_5": float(np.quantile(draws, 0.975)),
        }
    return out


def selection_instability(folds: pd.DataFrame) -> dict:
    """PBO-inspired diagnostic; not the formal CSCV PBO statistic."""
    if folds.empty:
        return {}
    valid = folds.loc[np.isfinite(folds.train_utility) & np.isfinite(folds.test_utility)].copy()
    if valid.empty:
        return {
            "classification": "PBO-INSPIRED DIAGNOSTIC — NOT FORMAL CSCV PBO",
            "folds": 0,
            "note": "No folds contained evaluable train and test episodes.",
        }
    train = valid.train_utility.to_numpy(float)
    test = valid.test_utility.to_numpy(float)
    corr = float(pd.Series(train).corr(pd.Series(test), method="spearman")) if len(valid) > 1 else np.nan
    return {
        "classification": "PBO-INSPIRED DIAGNOSTIC — NOT FORMAL CSCV PBO",
        "folds": int(len(valid)),
        "negative_oos_fraction": float((test < 0).mean()),
        "median_train_utility": float(np.median(train)),
        "median_test_utility": float(np.median(test)),
        "train_test_spearman": corr,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, required=True)
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--grid", type=Path, required=True)
    ap.add_argument("--features-csv", type=Path)
    ap.add_argument("--train-days", type=int, default=504)
    ap.add_argument("--test-days", type=int, default=126)
    ap.add_argument("--purge-days", type=int, default=84)
    ap.add_argument("--step-days", type=int, default=126)
    ap.add_argument("--out", type=Path, default=Path("validation-output"))
    a = ap.parse_args()

    prices = load_prices(a.csv)
    features = load_features(a.features_csv)
    base = load_config(a.config, a.symbol)
    grid = json.loads(a.grid.read_text())
    candidates = parameter_grid(base, grid)
    folds, episodes = walk_forward(
        prices,
        features,
        candidates,
        a.train_days,
        a.test_days,
        a.purge_days,
        a.step_days,
    )
    result = {
        "symbol": a.symbol,
        "candidate_count": len(candidates),
        "fold_count": len(folds),
        "purge_days": a.purge_days,
        "evaluation_tail_days": base.episode_eval_max_days,
        "path_history": "FULL_AVAILABLE_HISTORY_BEFORE_SIGNAL_WINDOW",
        "bootstrap": episode_bootstrap(episodes),
        "selection_instability": selection_instability(folds),
    }
    out = a.out / a.symbol
    out.mkdir(parents=True, exist_ok=True)
    folds.to_csv(out / "walk_forward_folds.csv", index=False)
    episodes.to_csv(out / "walk_forward_episodes.csv", index=False)
    (out / "validation_summary.json").write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
