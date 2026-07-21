#!/usr/bin/env python3
"""Robust model-selection helpers for bottom-zone research.

The module deliberately favours a simpler, lower-capital candidate when its
estimated utility is statistically indistinguishable from the apparent winner.
"""
from __future__ import annotations

from dataclasses import asdict
from math import sqrt

import numpy as np
import pandas as pd

from backtest import Config, target_deployment


def episode_scores(ep: pd.DataFrame) -> np.ndarray:
    """Return one utility contribution per complete drawdown episode."""
    if ep.empty or "complete" not in ep:
        return np.array([], dtype=float)
    e = ep.loc[ep.complete].copy()
    if e.empty:
        return np.array([], dtype=float)
    any8 = e.any_within_8.astype(float)
    capital8 = e.capital_within_8.fillna(0.0).clip(lower=0.0, upper=1.0)
    missed = e.missed.astype(float)
    # Downside is negative; retaining the sign penalises more adverse outcomes.
    downside = e.worst_additional_downside.fillna(-0.25).clip(lower=-0.75, upper=0.0)
    weighted = e.weighted_distance.fillna(0.30).clip(lower=0.0, upper=0.50)
    return (2.0 * any8 + 1.5 * capital8 - 2.0 * missed + downside - weighted).to_numpy(float)


def mean_standard_error(values: np.ndarray) -> tuple[float, float, int]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    n = int(values.size)
    if n == 0:
        return float("-inf"), float("inf"), 0
    mean = float(values.mean())
    se = float(values.std(ddof=1) / sqrt(n)) if n > 1 else float("inf")
    return mean, se, n


def regime_labels(ep: pd.DataFrame) -> pd.Series:
    """Evaluation-only episode taxonomy; never used as a live signal.

    The taxonomy is intentionally coarse. It helps reject candidates whose
    aggregate score is dominated by only one market regime.
    """
    duration = (ep.end_index - ep.start_index + 1).astype(float)
    max_dd = ep.max_drawdown.astype(float)
    label = pd.Series("ORDINARY_CORRECTION", index=ep.index, dtype="object")
    label.loc[(duration <= 42) & (max_dd <= -0.12)] = "FAST_CRASH"
    label.loc[(duration >= 126) | (max_dd <= -0.30)] = "LONG_BEAR"
    return label


def robust_episode_stats(ep: pd.DataFrame, regime_penalty: float = 0.25) -> dict:
    """Mean/SE plus a penalty for regime concentration."""
    scores = episode_scores(ep)
    mean, se, n = mean_standard_error(scores)
    if n == 0:
        return {"mean": mean, "se": se, "n": 0, "robust_mean": mean, "worst_regime": np.nan}

    e = ep.loc[ep.complete].copy()
    e["episode_score"] = scores
    e["regime"] = regime_labels(e)
    regime_means = e.groupby("regime").episode_score.mean()
    worst = float(regime_means.min())
    dispersion = float(regime_means.std(ddof=0)) if len(regime_means) > 1 else 0.0
    robust = float(mean - regime_penalty * dispersion)
    return {
        "mean": mean,
        "se": se,
        "n": n,
        "robust_mean": robust,
        "worst_regime": worst,
        "regime_dispersion": dispersion,
        "regime_count": int(len(regime_means)),
    }


def config_complexity(base: Config, cfg: Config) -> tuple:
    """Lexicographic simplicity/risk score used inside the one-SE set."""
    b, c = asdict(base), asdict(cfg)
    ignored = {"symbol"}
    changed = sum(not np.isclose(float(c[k]), float(b[k])) for k in c if k not in ignored)
    # Prefer fewer changed knobs, lower capital commitment, smaller single trades,
    # and wider spacing. These are governance preferences, not return forecasts.
    return (
        int(changed),
        float(cfg.max_deploy),
        float(cfg.max_tranche),
        float(cfg.micro_probe),
        -float(cfg.spacing),
        -int(cfg.cooldown),
    )


def select_one_standard_error(
    candidate_stats: pd.DataFrame,
    candidates: list[Config],
    base: Config,
) -> tuple[int, dict]:
    """Choose the simplest candidate within one SE of the best robust mean."""
    valid = candidate_stats.loc[
        np.isfinite(candidate_stats.robust_mean) & np.isfinite(candidate_stats.se)
    ].copy()
    if valid.empty:
        raise ValueError("No candidate has finite episode statistics")
    best_row = valid.sort_values("robust_mean", ascending=False).iloc[0]
    threshold = float(best_row.robust_mean - best_row.se)
    eligible = valid.loc[valid.robust_mean >= threshold].copy()
    selected_i = min(
        eligible.candidate_index.astype(int),
        key=lambda i: config_complexity(base, candidates[i]),
    )
    return selected_i, {
        "best_candidate_index": int(best_row.candidate_index),
        "best_robust_mean": float(best_row.robust_mean),
        "best_standard_error": float(best_row.se),
        "one_se_threshold": threshold,
        "eligible_count": int(len(eligible)),
        "selected_candidate_index": int(selected_i),
        "selected_complexity": config_complexity(base, candidates[selected_i]),
    }


def assert_monotonic_deployment(cfg: Config, points: int = 1001) -> None:
    """Fail if deeper drawdowns ever reduce the causal base deployment target."""
    depths = np.linspace(0.0, cfg.max_dd, points)
    targets = np.array([target_deployment(-float(d), cfg) for d in depths])
    if np.any(np.diff(targets) < -1e-12):
        raise ValueError("Deployment curve is not monotonic in drawdown depth")
    if targets.min() < -1e-12 or targets.max() > cfg.max_deploy + 1e-12:
        raise ValueError("Deployment curve breaches configured capital bounds")


def feature_promotion_decision(
    baseline: pd.Series,
    challenger: pd.Series,
    min_median_gain: float = 0.02,
    max_worst_fold_damage: float = 0.10,
    min_nonnegative_fraction: float = 0.60,
) -> dict:
    """Governance gate for adding a new feature family.

    A feature is not retained merely because average utility rises. It must also
    avoid a material deterioration in the worst fold and improve a majority of
    comparable folds.
    """
    z = pd.concat([baseline.rename("base"), challenger.rename("new")], axis=1).dropna()
    if z.empty:
        return {"promote": False, "reason": "NO_COMPARABLE_FOLDS", "folds": 0}
    delta = z.new - z.base
    median_gain = float(delta.median())
    worst_damage = float(delta.min())
    nonnegative = float((delta >= 0).mean())
    promote = (
        median_gain >= min_median_gain
        and worst_damage >= -max_worst_fold_damage
        and nonnegative >= min_nonnegative_fraction
    )
    return {
        "promote": bool(promote),
        "folds": int(len(delta)),
        "median_gain": median_gain,
        "worst_fold_delta": worst_damage,
        "nonnegative_fraction": nonnegative,
        "thresholds": {
            "min_median_gain": min_median_gain,
            "max_worst_fold_damage": max_worst_fold_damage,
            "min_nonnegative_fraction": min_nonnegative_fraction,
        },
    }
