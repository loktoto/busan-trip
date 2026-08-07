from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from backtest import Config, episode_ids, evaluate, indicators, load_config, run


def synthetic_prices(n: int = 900) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    r = rng.normal(0.0003, 0.012, n)
    r[300:325] -= 0.012
    r[580:720] -= 0.0025
    close = 100 * np.exp(np.cumsum(r))
    open_ = close * (1 + rng.normal(0, 0.002, n))
    high = np.maximum(open_, close) * (1 + rng.uniform(0.001, 0.012, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0.001, 0.012, n))
    volume = rng.lognormal(16, 0.35, n)
    return pd.DataFrame(
        {
            "Date": pd.bdate_range("2010-01-01", periods=n),
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        }
    )


def test_next_open_and_causal_costs():
    cfg = Config(symbol="TEST", transaction_cost_bps=2, slippage_bps=3)
    x = indicators(synthetic_prices(), cfg)
    trades, catalog = run(x, cfg)
    assert len(catalog) >= 1
    if not trades.empty:
        t = trades.iloc[0]
        expected = x.iloc[int(t.execution_index)].Open * 1.0005
        assert abs(t.execution_price - expected) < 1e-9
        assert int(t.execution_index) == int(t.signal_index) + 1


def test_missed_episodes_are_not_dropped():
    cfg = Config(symbol="TEST", start_dd=0.90, max_dd=0.99, watch_dd=0.05)
    x = indicators(synthetic_prices(), cfg)
    trades, catalog = run(x, cfg)
    _, ep, summary = evaluate(x, trades, catalog, cfg)
    assert len(ep) == len(catalog)
    assert summary["episode_count_all"] == len(catalog)
    assert ep.missed.any()


def test_episode_ids_recover_only_after_near_full_recovery():
    cfg = Config(symbol="TEST", watch_dd=0.05, recovery_dd=0.002)
    x = indicators(synthetic_prices(), cfg)
    ids = episode_ids(x, cfg)
    assert ids.min() == 0
    assert ids.max() >= 1


def test_no_tranche_exceeds_limits():
    cfg = Config(symbol="TEST", max_tranche=0.05, max_deploy=0.30)
    x = indicators(synthetic_prices(), cfg)
    trades, _ = run(x, cfg)
    if not trades.empty:
        assert (trades.tranche <= 0.05 + 1e-12).all()
        assert (trades.cumulative <= 0.30 + 1e-12).all()


def test_optional_features_do_not_create_missing_values_as_zero():
    cfg = Config(symbol="TEST")
    prices = synthetic_prices()
    features = pd.DataFrame({"Date": prices.Date, "hy_oas": np.nan})
    x = indicators(prices, cfg, features)
    assert x.hy_oas.isna().all()
    assert not x.credit_veto.any()


def test_symbol_config_inherits_default(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"default": {"transaction_cost_bps": 7.0, "cooldown": 12}, "SPY": {"cooldown": 9}}))
    cfg = load_config(path, "SPY")
    assert cfg.transaction_cost_bps == 7.0
    assert cfg.cooldown == 9
