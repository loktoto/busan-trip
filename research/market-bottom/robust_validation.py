#!/usr/bin/env python3
"""Regime-aware, one-standard-error walk-forward validation.

The validator separates three questions that must not be conflated:

- modern five-year recent-holdout behaviour;
- dense but label-dependent stability diagnostics;
- long-cycle, non-overlapping partitions suitable for a formal CSCV/PBO attempt.

A candidate's training utility uses forward bottom labels. Therefore the purge
between the training signal window and the test signal window must be at least as
long as the evaluation tail. Otherwise model selection has already observed test-
period prices. This module fails closed when that condition is violated.
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
from selection import assert_monotonic_deployment, robust_episode_stats, select_one_standard_error
from validation import episode_bootstrap, parameter_grid, score_period, selection_instability


PROTOCOLS = {
    # A five-year daily history supports only one clean recent holdout once the
    # 252-session training-label purge and test-label tail are respected.
    "MODERN_5Y_PRIMARY": {
        "train_days": 504,
        "test_days": 126,
        "purge_days": 252,
        "step_days": 126,
        "role": "RECENT_HOLDOUT_ONLY",
        "independent_oos_labels": False,
    },
    # More rolling observations, but adjacent test outcomes share future label
    # periods. Useful for sensitivity checks, not for a formal PBO estimate.
    "MODERN_5Y_DENSE_DIAGNOSTIC": {
        "train_days": 315,
        "test_days": 63,
        "purge_days": 252,
        "step_days": 63,
        "role": "DEPENDENT_STABILITY_DIAGNOSTIC_ONLY",
        "independent_oos_labels": False,
    },
    # Test signal blocks plus their 252-session labels do not overlap. Roughly
    # twenty-plus years of daily data are needed to approach eight partitions.
    "LONG_CYCLE": {
        "train_days": 1008,
        "test_days": 252,
        "purge_days": 252,
        "step_days": 504,
        "role": "LONG_HISTORY_CSCV_CANDIDATE",
        "independent_oos_labels": True,
    },
}


def resolve_protocol(
    name: str,
    train_days: int | None,
    test_days: int | None,
    purge_days: int | None,
    step_days: int | None,
) -> dict:
    if name not in PROTOCOLS:
        raise ValueError(f"Unknown protocol {name!r}; choose from {sorted(PROTOCOLS)}")
    out = dict(PROTOCOLS[name])
    for key, value in {
        "train_days": train_days,
        "test_days": test_days,
        "purge_days": purge_days,
        "step_days": step_days,
    }.items():
        if value is not None:
            out[key] = int(value)
    if min(out[k] for k in ("train_days", "test_days", "purge_days", "step_days")) <= 0:
        raise ValueError("Validation windows must be positive")
    return out


def expected_fold_count(
    n_rows: int,
    train_days: int,
    test_days: int,
    purge_days: int,
    step_days: int,
    evaluation_tail_days: int = 252,
) -> int:
    available = n_rows - (train_days + purge_days + test_days + evaluation_tail_days)
    return 0 if available < 0 else 1 + available // step_days


def _date_at(prices: pd.DataFrame, index: int) -> str:
    index = min(max(index, 0), len(prices) - 1)
    return str(prices.iloc[index].Date.date())


def robust_walk_forward(
    prices: pd.DataFrame,
    features: pd.DataFrame | None,
    base: Config,
    candidates: list[Config],
    train_days: int,
    test_days: int,
    purge_days: int,
    step_days: int | None = None,
    independent_oos_labels: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    step_days = test_days if step_days is None else step_days
    tail = base.episode_eval_max_days
    if purge_days < tail:
        raise ValueError(
            f"purge_days={purge_days} is shorter than the {tail}-session forward label tail; "
            "training labels would overlap the test period"
        )
    if independent_oos_labels and step_days < test_days + tail:
        raise ValueError(
            "Independent OOS label partitions require step_days >= test_days + evaluation tail"
        )
    predicted_folds = expected_fold_count(
        len(prices), train_days, test_days, purge_days, step_days, tail
    )
    if predicted_folds <= 0:
        need = train_days + purge_days + test_days + tail
        raise ValueError(
            f"Validation protocol requires at least {need} rows including a {tail}-row "
            f"forward label tail, but received {len(prices)}"
        )

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
        label_end = test_end + tail
        if label_end > len(prices):
            break
        fold += 1
        metadata = {
            "train_start": _date_at(prices, train_start),
            "train_end": _date_at(prices, train_end - 1),
            "test_start": _date_at(prices, test_start),
            "test_end": _date_at(prices, test_end - 1),
            "label_end": _date_at(prices, label_end - 1),
            "independent_oos_labels": bool(independent_oos_labels),
        }
        stats_rows = []
        for i, cfg in enumerate(candidates):
            _, ep = score_period(prices, features, cfg, train_start, train_end)
            stats = robust_episode_stats(ep)
            stats_rows.append({"candidate_index": i, **stats})
            candidate_rows.append(
                {
                    "fold": fold,
                    "sample": "TRAIN",
                    "candidate_index": i,
                    **metadata,
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
                    "status": "SKIPPED_NO_EVALUABLE_TRAIN_EPISODE",
                    **metadata,
                }
            )
            train_start += step_days
            continue

        test_stats_by_i: dict[int, dict] = {}
        selected_ep = pd.DataFrame()
        for i, cfg_i in enumerate(candidates):
            _, test_ep_i = score_period(prices, features, cfg_i, test_start, test_end)
            test_stats_i = robust_episode_stats(test_ep_i)
            test_stats_by_i[i] = test_stats_i
            candidate_rows.append(
                {
                    "fold": fold,
                    "sample": "TEST_ALL",
                    "candidate_index": i,
                    **metadata,
                    **test_stats_i,
                    "config": json.dumps(asdict(cfg_i), sort_keys=True),
                }
            )
            if i == selected_i:
                selected_ep = test_ep_i

        cfg = candidates[selected_i]
        test_stats = test_stats_by_i[selected_i]
        candidate_rows.append(
            {
                "fold": fold,
                "sample": "TEST_SELECTED",
                "candidate_index": selected_i,
                **metadata,
                **test_stats,
                "config": json.dumps(asdict(cfg), sort_keys=True),
            }
        )
        fold_rows.append(
            {
                "fold": fold,
                "status": "OK" if np.isfinite(test_stats["robust_mean"]) else "NO_EVALUABLE_TEST_EPISODE",
                **metadata,
                "candidate_index": selected_i,
                "train_utility": float(
                    stats_df.loc[stats_df["candidate_index"] == selected_i, "robust_mean"].iloc[0]
                ),
                "test_utility": test_stats["robust_mean"]
                if np.isfinite(test_stats["robust_mean"])
                else np.nan,
                "test_worst_regime": test_stats.get("worst_regime", np.nan),
                "one_se_threshold": decision["one_se_threshold"],
                "one_se_eligible_count": decision["eligible_count"],
                "apparent_best_candidate": decision["best_candidate_index"],
                "selected_complexity": json.dumps(decision["selected_complexity"]),
                "config": json.dumps(asdict(cfg), sort_keys=True),
            }
        )
        if not selected_ep.empty:
            e = selected_ep.copy()
            e["fold"] = fold
            e["candidate_index"] = selected_i
            episode_rows.append(e)
        train_start += step_days

    if fold == 0:
        raise RuntimeError("No fully labelled validation folds were generated")

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
    ap.add_argument("--protocol", choices=sorted(PROTOCOLS), default="MODERN_5Y_PRIMARY")
    ap.add_argument("--train-days", type=int)
    ap.add_argument("--test-days", type=int)
    ap.add_argument("--purge-days", type=int)
    ap.add_argument("--step-days", type=int)
    ap.add_argument("--max-unexplained-jump", type=float, default=0.45)
    ap.add_argument("--out", type=Path, default=Path("robust-validation-output"))
    a = ap.parse_args()

    protocol = resolve_protocol(a.protocol, a.train_days, a.test_days, a.purge_days, a.step_days)
    prices = load_prices(a.csv)
    assert_price_continuity(prices, a.max_unexplained_jump)
    features = load_features(a.features_csv)
    base = load_config(a.config, a.symbol)
    candidates = parameter_grid(base, json.loads(a.grid.read_text()))

    folds, matrix, episodes = robust_walk_forward(
        prices,
        features,
        base,
        candidates,
        protocol["train_days"],
        protocol["test_days"],
        protocol["purge_days"],
        protocol["step_days"],
        protocol["independent_oos_labels"],
    )
    result = {
        "classification": "PURGED WALK-FORWARD — ONE-SE SELECTION — NOT GUARANTEED",
        "symbol": a.symbol,
        "protocol": a.protocol,
        "protocol_role": protocol["role"],
        "candidate_count": len(candidates),
        "fold_count": int(len(folds)),
        "expected_fold_count": expected_fold_count(
            len(prices),
            protocol["train_days"],
            protocol["test_days"],
            protocol["purge_days"],
            protocol["step_days"],
            base.episode_eval_max_days,
        ),
        "windows": {k: protocol[k] for k in ("train_days", "test_days", "purge_days", "step_days")},
        "evaluation_tail_days": base.episode_eval_max_days,
        "training_label_overlap_with_test": False,
        "independent_oos_labels": protocol["independent_oos_labels"],
        "formal_cscv_eligible_by_design": protocol["independent_oos_labels"],
        "unlabelled_live_tail": True,
        "selection_rule": "simplest candidate within one standard error of best regime-robust training utility",
        "bootstrap": episode_bootstrap(episodes),
        "selection_instability": selection_instability(folds),
        "median_test_utility": float(folds["test_utility"].dropna().median())
        if "test_utility" in folds
        else np.nan,
        "worst_test_utility": float(folds["test_utility"].dropna().min())
        if "test_utility" in folds and folds["test_utility"].notna().any()
        else np.nan,
    }
    out = a.out / a.symbol / a.protocol
    out.mkdir(parents=True, exist_ok=True)
    folds.to_csv(out / "robust_walk_forward_folds.csv", index=False)
    matrix.to_csv(out / "candidate_fold_matrix.csv", index=False)
    episodes.to_csv(out / "robust_walk_forward_episodes.csv", index=False)
    (out / "robust_validation_summary.json").write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
