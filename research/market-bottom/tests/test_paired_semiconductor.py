from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import paired_semiconductor as paired
from backtest import Config


def histories(n: int = 320) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.bdate_range("2020-01-02", periods=n)
    base = 100 * np.exp(np.cumsum(np.full(n, 0.0002)))

    def frame(close: np.ndarray) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "Date": dates,
                "Open": close * 0.999,
                "High": close * 1.01,
                "Low": close * 0.99,
                "Close": close,
                "Volume": np.full(n, 1_000_000.0),
            }
        )

    return frame(base), frame(base * 1.03)


def pair_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": pd.bdate_range("2024-01-02", periods=4),
            "exhaustion": [True, True, False, False],
            "confirmation": [True, True, False, False],
            "newlow20": [True, True, True, False],
            "exhaustion_score": [2, 2, 1, 0],
            "confirmation_score": [3, 3, 2, 0],
            "cycle_dd": [-0.20, -0.20, -0.20, -0.05],
            "smh_exhaustion_recent": [False, True, True, False],
            "smh_confirmation_recent": [False, True, True, False],
            "pair_veto": [False, True, False, False],
            "pair_status": ["DIVERGES", "VETO", "CONFIRMS", "NEUTRAL"],
        }
    )


def test_alignment_uses_only_same_completed_dates():
    soxx, smh = histories()
    smh = smh.drop(index=[4, 9]).reset_index(drop=True)
    a, b = paired.align_histories(soxx, smh)
    assert len(a) == len(b) == 318
    assert a["Date"].equals(b["Date"])
    assert pd.Timestamp("2020-01-08") not in set(a["Date"])


def test_confirmation_veto_preserves_exhaustion_probe():
    x = paired.apply_variant(
        pair_frame(), Config(symbol="SOXX"), "SMH_CONFIRMATION_VETO"
    )
    assert bool(x.loc[1, "exhaustion"])
    assert not bool(x.loc[1, "confirmation"])


def test_confirmation_gate_preserves_exhaustion_but_requires_smh_for_state4():
    x = paired.apply_variant(
        pair_frame(), Config(symbol="SOXX"), "SMH_CONFIRMATION_GATE"
    )
    assert bool(x.loc[0, "exhaustion"])
    assert not bool(x.loc[0, "confirmation"])
    assert bool(x.loc[1, "exhaustion"])
    assert not bool(x.loc[1, "confirmation"])  # pair veto has priority


def test_veto_only_removes_larger_state_transitions():
    x = paired.apply_variant(pair_frame(), Config(symbol="SOXX"), "SMH_VETO_ONLY")
    assert bool(x.loc[0, "exhaustion"])
    assert not bool(x.loc[1, "exhaustion"])
    assert not bool(x.loc[1, "confirmation"])


def test_hard_confirmation_requires_smh_but_creates_no_new_state():
    x = paired.apply_variant(pair_frame(), Config(symbol="SOXX"), "SMH_HARD_CONFIRM")
    assert not bool(x.loc[0, "exhaustion"])
    assert not bool(x.loc[0, "confirmation"])
    assert not bool(x.loc[1, "exhaustion"])  # pair veto has priority
    assert not bool(x.loc[2, "confirmation"])  # SOXX itself was not confirmed


def test_soft_confirmation_needs_soxx_setup_and_respects_veto():
    x = paired.apply_variant(pair_frame(), Config(symbol="SOXX"), "SMH_SOFT_CONFIRM")
    assert not bool(x.loc[1, "exhaustion"])
    assert bool(x.loc[2, "exhaustion"])
    assert bool(x.loc[2, "confirmation"])
    assert not bool(x.loc[3, "confirmation"])  # no SOXX drawdown/setup


def test_run_variant_rejects_reference_symbol_trade(monkeypatch):
    x = pair_frame()
    x["episode"] = 1

    def fake_run(_x, _cfg):
        trades = pd.DataFrame(
            {
                "symbol": ["SMH"],
                "episode": [1],
                "signal_index": [0],
                "execution_index": [1],
            }
        )
        catalog = pd.DataFrame(
            {
                "episode": [1],
                "start_index": [0],
                "end_index": [3],
                "complete": [True],
            }
        )
        return trades, catalog

    monkeypatch.setattr(paired, "run", fake_run)
    with pytest.raises(AssertionError, match="non-SOXX trade"):
        paired.run_variant(x, Config(symbol="SOXX"), "SOXX_ONLY")


def test_promotion_gate_never_promotes_from_single_comparison():
    table = pd.DataFrame(
        [
            {
                "variant": "SOXX_ONLY",
                "missed_rate_complete": 0.20,
                "any_within_8_rate_complete": 0.60,
                "mean_weighted_distance_complete": 0.08,
                "mean_worst_additional_downside_complete": -0.10,
            },
            {
                "variant": "SMH_VETO_ONLY",
                "missed_rate_complete": 0.10,
                "any_within_8_rate_complete": 0.70,
                "mean_weighted_distance_complete": 0.06,
                "mean_worst_additional_downside_complete": -0.09,
            },
        ]
    )
    decision = paired.promotion_decision(table)
    assert decision["eligible_variants"] == ["SMH_VETO_ONLY"]
    assert decision["promote"] is False
