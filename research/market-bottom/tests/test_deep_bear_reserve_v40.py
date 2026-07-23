from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from backtest import Config, indicators, run
from deep_bear_reserve_v40 import (
    ReservePolicy,
    add_reserve_features,
    reserve_cap_for_row,
    run_reserve,
)
from test_backtest import synthetic_prices


def test_disabled_policy_reproduces_baseline_trades() -> None:
    cfg = Config(symbol="TEST")
    x = indicators(synthetic_prices(), cfg)
    baseline, baseline_catalog = run(x, cfg)
    challenger, challenger_catalog = run_reserve(
        x, cfg, ReservePolicy(enabled=False, name="BASELINE")
    )
    columns = [
        "episode",
        "signal_index",
        "execution_index",
        "execution_price",
        "tranche",
        "cumulative",
    ]
    pd.testing.assert_frame_equal(
        baseline[columns].reset_index(drop=True),
        challenger[columns].reset_index(drop=True),
    )
    pd.testing.assert_frame_equal(baseline_catalog, challenger_catalog)


def test_reserve_signals_execute_only_at_next_open() -> None:
    cfg = Config(symbol="TEST", transaction_cost_bps=2, slippage_bps=3)
    x = indicators(synthetic_prices(), cfg)
    trades, _ = run_reserve(x, cfg, ReservePolicy())
    for _, trade in trades.iterrows():
        assert int(trade.execution_index) == int(trade.signal_index) + 1
        expected = x.iloc[int(trade.execution_index)].Open * 1.0005
        assert abs(float(trade.execution_price) - expected) < 1e-9


def test_reserve_cap_never_exceeds_configured_limits() -> None:
    cfg = Config(symbol="TEST", max_deploy=0.50)
    policy = ReservePolicy(
        reserve_cap=0.10,
        deep_cap=0.20,
        maturity_cap=0.20,
        combined_cap=0.30,
    )
    x = add_reserve_features(indicators(synthetic_prices(), cfg), cfg, policy)
    for _, row in x.iloc[200:].iterrows():
        cap, _ = reserve_cap_for_row(row, cfg, policy)
        assert 0 <= cap <= cfg.max_deploy


def test_future_mutation_does_not_change_past_reserve_features() -> None:
    cfg = Config(symbol="TEST")
    policy = ReservePolicy()
    prices = synthetic_prices()
    first = add_reserve_features(indicators(prices, cfg), cfg, policy)
    mutated = prices.copy()
    cut = 600
    mutated.loc[cut:, ["Open", "High", "Low", "Close"]] *= 1.5
    second = add_reserve_features(indicators(mutated, cfg), cfg, policy)
    columns = [
        "reserve_structural_votes",
        "reserve_falling_knife_votes",
        "reserve_maturity_votes",
        "reserve_deep_zone",
        "reserve_maturity",
    ]
    pd.testing.assert_frame_equal(
        first.loc[: cut - 1, columns],
        second.loc[: cut - 1, columns],
    )
