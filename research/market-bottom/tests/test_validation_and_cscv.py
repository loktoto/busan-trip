from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from backtest import Config
from cscv import build_utility_matrix, cscv_pbo
from robust_validation import expected_fold_count, robust_walk_forward
from validation import subset_with_warmup_and_tail


def synthetic_market(n: int = 1400) -> pd.DataFrame:
    rng = np.random.default_rng(17)
    r = rng.normal(0.00035, 0.006, n)
    for start, stop, shock in [
        (100, 128, -0.012),
        (300, 345, -0.009),
        (520, 548, -0.015),
        (760, 815, -0.008),
        (1020, 1058, -0.012),
    ]:
        r[start:stop] += shock
    for start, stop, rebound in [
        (128, 190, 0.009),
        (345, 435, 0.006),
        (548, 630, 0.010),
        (815, 955, 0.005),
        (1058, 1170, 0.007),
    ]:
        r[start:stop] += rebound
    close = 100 * np.exp(np.cumsum(r))
    open_ = close * (1 + rng.normal(0, 0.0015, n))
    high = np.maximum(open_, close) * (1 + rng.uniform(0.001, 0.008, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0.001, 0.008, n))
    volume = rng.lognormal(15.0, 0.3, n)
    return pd.DataFrame(
        {
            "Date": pd.bdate_range("2010-01-04", periods=n),
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        }
    )


def test_path_dependent_context_is_not_truncated():
    prices = synthetic_market()
    sub, offset, signal_end = subset_with_warmup_and_tail(prices, 700, 800, evaluation_tail=252)
    assert sub.iloc[0].Date == prices.iloc[0].Date
    assert offset == 700
    assert signal_end == 800
    assert sub.iloc[-1].Date == prices.iloc[1051].Date


def test_expected_folds_reserve_purge_and_forward_label_tail():
    assert expected_fold_count(1258, 504, 126, 252, 126, 252) == 1
    assert expected_fold_count(1258, 315, 63, 252, 63, 252) == 6
    assert expected_fold_count(900, 504, 126, 252, 126, 252) == 0


def test_robust_walk_forward_persists_all_oos_candidates():
    prices = synthetic_market()
    base = Config(symbol="TEST", watch_dd=0.05, start_dd=0.05)
    candidates = [
        base,
        replace(base, power=1.4),
        replace(base, max_deploy=0.45, max_tranche=0.06),
    ]
    folds, matrix, _ = robust_walk_forward(
        prices,
        None,
        base,
        candidates,
        train_days=315,
        test_days=63,
        purge_days=252,
        step_days=63,
        independent_oos_labels=False,
    )
    assert not folds.empty
    test_all = matrix.loc[matrix["sample"].eq("TEST_ALL")]
    assert not test_all.empty
    counts = test_all.groupby("fold")["candidate_index"].nunique()
    assert (counts == len(candidates)).all()
    assert not test_all["independent_oos_labels"].any()


def test_robust_walk_forward_rejects_training_label_leakage():
    prices = synthetic_market()
    base = Config(symbol="TEST")
    with pytest.raises(ValueError, match="training labels would overlap"):
        robust_walk_forward(
            prices,
            None,
            base,
            [base, replace(base, power=1.4)],
            train_days=504,
            test_days=126,
            purge_days=84,
            step_days=126,
        )


def test_independent_labels_require_sufficient_step():
    prices = synthetic_market(1800)
    base = Config(symbol="TEST")
    with pytest.raises(ValueError, match="step_days"):
        robust_walk_forward(
            prices,
            None,
            base,
            [base, replace(base, power=1.4)],
            train_days=504,
            test_days=126,
            purge_days=252,
            step_days=126,
            independent_oos_labels=True,
        )


def candidate_rows(folds: int = 8, independent: bool = True) -> pd.DataFrame:
    rows = []
    origin = pd.Timestamp("2000-01-03")
    spacing = 504 if independent else 63
    for fold in range(1, folds + 1):
        test_start = origin + pd.offsets.BDay((fold - 1) * spacing)
        label_end = test_start + pd.offsets.BDay(503)
        values = {
            0: 1.0 if fold <= folds // 2 else -0.6,
            1: 0.35,
            2: 0.20 + 0.10 * np.sin(fold),
            3: 0.05,
        }
        for candidate, value in values.items():
            rows.append(
                {
                    "fold": fold,
                    "sample": "TEST_ALL",
                    "candidate_index": candidate,
                    "robust_mean": value,
                    "test_start": str(test_start.date()),
                    "label_end": str(label_end.date()),
                    "independent_oos_labels": independent,
                }
            )
    return pd.DataFrame(rows)


def test_cscv_requires_enough_independent_partitions():
    matrix, _ = build_utility_matrix(candidate_rows(6, independent=True))
    detail, summary = cscv_pbo(matrix, min_partitions=8)
    assert detail.empty
    assert summary["classification"].startswith("CSCV/PBO UNDERPOWERED")
    assert np.isnan(summary["pbo"])


def test_cscv_blocks_dependent_label_windows():
    matrix, audit = build_utility_matrix(candidate_rows(8, independent=False))
    detail, summary = cscv_pbo(matrix, min_partitions=8)
    assert detail.empty
    assert summary["classification"].startswith("CSCV/PBO BLOCKED")
    assert audit["label_independence"]["verified_non_overlapping"] is False


def test_cscv_produces_bounded_pbo_and_all_half_splits():
    matrix, audit = build_utility_matrix(candidate_rows(8, independent=True))
    detail, summary = cscv_pbo(matrix, min_partitions=8)
    assert audit["candidate_failure_penalties"] == 0
    assert audit["label_independence"]["verified_non_overlapping"] is True
    assert len(detail) == 70  # C(8, 4)
    assert 0.0 <= summary["pbo"] <= 1.0
    assert detail["oos_rank_fraction"].between(0, 1).all()


def test_candidate_specific_nonfinite_result_is_penalised_not_dropped():
    raw = candidate_rows(8, independent=True)
    raw.loc[(raw["fold"] == 3) & (raw["candidate_index"] == 2), "robust_mean"] = -np.inf
    matrix, audit = build_utility_matrix(raw, floor_margin=0.5)
    assert matrix.shape == (8, 4)
    assert np.isfinite(matrix.to_numpy()).all()
    assert audit["candidate_failure_penalties"] == 1
