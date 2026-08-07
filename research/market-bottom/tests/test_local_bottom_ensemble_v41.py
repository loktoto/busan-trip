from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import pytest

from backtest import Config, indicators
from local_bottom_ensemble_v41 import (
    add_local_bottom_features,
    run_score_signals,
)
from test_backtest import synthetic_prices


def test_local_bottom_features_are_causal() -> None:
    cfg = Config(symbol="TEST")
    prices = synthetic_prices()
    first = add_local_bottom_features(indicators(prices, cfg), cfg)
    mutated = prices.copy()
    cut = 600
    mutated.loc[cut:, ["Open", "High", "Low", "Close"]] *= 1.4
    second = add_local_bottom_features(indicators(mutated, cfg), cfg)
    columns = [
        "rsi14",
        "bb_z20",
        "local_bottom_score",
        "local_structural_bear",
    ]
    pd.testing.assert_frame_equal(
        first.loc[: cut - 1, columns],
        second.loc[: cut - 1, columns],
    )


def test_score_signals_use_next_open_and_never_claim_cycle_bottom() -> None:
    cfg = Config(symbol="TEST")
    x = indicators(synthetic_prices(), cfg)
    signals, _ = run_score_signals(x, cfg, threshold=3)
    for _, signal in signals.iterrows():
        assert int(signal.execution_index) == int(signal.signal_index) + 1
        assert "CYCLE_BOTTOM" not in str(signal.classification)


def test_score_threshold_is_bounded() -> None:
    cfg = Config(symbol="TEST")
    x = indicators(synthetic_prices(), cfg)
    with pytest.raises(ValueError):
        run_score_signals(x, cfg, threshold=1)
    with pytest.raises(ValueError):
        run_score_signals(x, cfg, threshold=7)
