from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from backtest import Config
from data_audit import assert_price_continuity, audit_price_continuity
from selection import (
    assert_monotonic_deployment,
    feature_promotion_decision,
    select_one_standard_error,
)


def prices(n: int = 300) -> pd.DataFrame:
    close = np.linspace(100, 130, n)
    return pd.DataFrame(
        {
            "Date": pd.bdate_range("2020-01-01", periods=n),
            "Open": close,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": np.full(n, 1_000_000.0),
        }
    )


def test_monotonic_deployment_curve():
    assert_monotonic_deployment(Config(symbol="TEST"))


def test_one_se_prefers_simpler_lower_risk_candidate():
    base = Config(symbol="TEST")
    complex_cfg = replace(base, power=2.2, max_deploy=0.75, max_tranche=0.12)
    stats = pd.DataFrame(
        [
            {"candidate_index": 0, "robust_mean": 1.00, "se": 0.08},
            {"candidate_index": 1, "robust_mean": 1.04, "se": 0.08},
        ]
    )
    selected, decision = select_one_standard_error(stats, [base, complex_cfg], base)
    assert decision["eligible_count"] == 2
    assert selected == 0


def test_feature_promotion_requires_broad_fold_improvement():
    base = pd.Series([1.0, 1.0, 1.0, 1.0])
    noisy = pd.Series([1.5, 1.5, 0.6, 0.6])
    stable = pd.Series([1.05, 1.04, 1.03, 1.02])
    assert not feature_promotion_decision(base, noisy)["promote"]
    assert feature_promotion_decision(base, stable)["promote"]


def test_corporate_action_audit_catches_unadjusted_split():
    x = prices()
    x.loc[150:, ["Open", "High", "Low", "Close"]] /= 3.0
    issues, summary = audit_price_continuity(x)
    assert summary["split_like_count"] >= 1
    with pytest.raises(ValueError):
        assert_price_continuity(x)


def test_clean_adjusted_history_passes_audit():
    x = prices()
    issues, summary = audit_price_continuity(x)
    assert issues.empty
    assert summary["clean"]
    assert_price_continuity(x)
