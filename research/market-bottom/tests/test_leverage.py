from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

import leverage
from backtest import Config
from leverage import LeverageConfig, tactical_backtest


def histories(n: int = 300) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.bdate_range("2020-01-01", periods=n)
    close = np.full(n, 100.0)
    underlying = pd.DataFrame(
        {
            "Date": dates,
            "Open": close,
            "High": close + 1,
            "Low": close - 1,
            "Close": close,
            "Volume": np.full(n, 1_000_000.0),
        }
    )
    lev_close = np.linspace(50, 80, n)
    leveraged = pd.DataFrame(
        {
            "Date": dates,
            "Open": lev_close,
            "High": lev_close + 1,
            "Low": lev_close - 1,
            "Close": lev_close,
            "Volume": np.full(n, 500_000.0),
        }
    )
    return underlying, leveraged


def fake_indicators(df, cfg, features=None):
    x = df.copy().reset_index(drop=True)
    n = len(x)
    x["confirmation"] = False
    x.loc[205, "confirmation"] = True
    x["sma20"] = 99.0
    x["sma10"] = 99.0
    x["sma10_slope"] = 0.01
    x["atrp"] = np.linspace(0.03, 0.01, n)
    x["credit_veto"] = False
    # Force a recovery-structure exit at close 210, executed next open.
    x.loc[210, "sma10"] = 101.0
    x.loc[210, "sma10_slope"] = -0.01
    return x


def test_signals_use_underlying_and_execution_uses_actual_product(monkeypatch):
    underlying, leveraged = histories()
    monkeypatch.setattr(leverage, "indicators", fake_indicators)
    cfg = LeverageConfig(
        max_holding_days=42,
        target_return=10.0,
        transaction_cost_bps_each_side=2,
        slippage_bps_each_side=3,
    )
    trades, summary = tactical_backtest(
        underlying, leveraged, Config(symbol="TEST"), cfg
    )
    assert summary["trade_count"] == 1
    t = trades.iloc[0]
    expected_entry = leveraged.iloc[206].Open * 1.0005
    expected_exit = leveraged.iloc[211].Open * 0.9995
    assert abs(t.entry_price - expected_entry) < 1e-10
    assert abs(t.exit_price - expected_exit) < 1e-10
    assert t.exit_reasons == "RECOVERY_STRUCTURE_BREAK"
    assert t.return_after_costs == expected_exit / expected_entry - 1
