from __future__ import annotations

import numpy as np
import pandas as pd

from bottom_taxonomy_v15 import classify_bottom_taxonomy


def _frame(n: int = 20, with_features: bool = False) -> pd.DataFrame:
    close = np.linspace(90.0, 100.0, n)
    frame = pd.DataFrame(
        {
            "Close": close,
            "High": close + 1.0,
            "Low": close - 1.0,
            "sma10": close - 1.0,
            "sma10_slope": 0.01,
            "r5": 0.03,
            "rv20": np.linspace(0.30, 0.20, n),
            "confirmation_score": 4,
            "newlow20": False,
        }
    )
    if with_features:
        frame["breadth_score_z"] = np.linspace(-2.0, 0.0, n)
        frame["downside_vrp_z"] = np.linspace(2.0, 0.0, n)
        frame["hy_oas_z"] = np.linspace(2.0, 0.0, n)
    return frame


def _asset() -> dict:
    return {
        "candidate_tranche": 0.0,
        "cumulative_model_deployment": 0.05,
        "state": 5,
        "credit_veto": False,
    }


def test_taxonomy_separates_local_recovery_from_cycle_bottom() -> None:
    result = classify_bottom_taxonomy("QQQ", _frame(), _asset())
    assert result["local_swing_status"] == "LOCAL_SWING_RECOVERY"
    assert result["cycle_bottom_status"] == "CYCLE_BOTTOM_UNCONFIRMED_MISSING_EVIDENCE"
    assert result["trade_authority"] == "NONE"
    assert result["leverage_authority"] == "NONE_FROM_TAXONOMY"


def test_independent_features_remain_research_only_without_promotion() -> None:
    result = classify_bottom_taxonomy(
        "SOXX",
        _frame(with_features=True),
        _asset(),
        feature_provenance_verified=True,
    )
    assert result["independent_evidence"]["supportive_count"] == 3
    assert result["cycle_bottom_status"] == "CYCLE_BOTTOM_RESEARCH_CONFIRMATION_ONLY"
    assert "QQQ_SOXX_CYCLE_BOTTOM_RULE_NOT_PROMOTED" in result["evidence_gaps"]


def test_taxonomy_does_not_mutate_trading_fields() -> None:
    asset = _asset()
    before = asset.copy()
    classify_bottom_taxonomy("SPY", _frame(), asset)
    assert asset == before
