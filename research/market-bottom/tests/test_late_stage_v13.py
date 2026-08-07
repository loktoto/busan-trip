from __future__ import annotations

import numpy as np
import pandas as pd

from backtest import Config
from late_stage_v13 import SPECS, add_late_stage_features, run_late_stage


def _frame(n: int = 230) -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    close = np.full(n, 100.0)
    close[205] = 90.0
    close[206:211] = [91.0, 92.0, 93.0, 94.0, 95.0]
    close[211:] = 96.0
    low = close - 1.0
    high = close + 1.0
    cycle_dd = close / 100.0 - 1.0
    frame = pd.DataFrame(
        {
            "Date": dates,
            "Open": close,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": 1_000_000.0,
            "cycle_high": 100.0,
            "cycle_dd": cycle_dd,
            "dd_52w": cycle_dd,
            "r1": 0.0,
            "r5": 0.0,
            "r10": 0.0,
            "rv20": 0.22,
            "atr14": 2.0,
            "atrp": 0.02,
            "sma10": 96.0,
            "sma20": 97.0,
            "sma10_slope": -0.01,
            "newlow10": False,
            "newlow20": False,
            "crash": False,
            "exhaustion": False,
            "exhaustion_score": 0,
            "confirmation": False,
            "confirmation_score": 0,
            "close_loc": 0.50,
            "vol_ratio": 1.00,
            "underwater": 0,
            "long_bear": False,
            "credit_veto": False,
        }
    )
    frame.loc[205, ["newlow10", "newlow20", "exhaustion", "exhaustion_score"]] = [
        True,
        True,
        True,
        3,
    ]
    frame.loc[205:, "underwater"] = np.arange(1, n - 204)
    frame.loc[210, ["r1", "r5", "r10", "rv20", "sma10", "sma20", "sma10_slope"]] = [
        0.01,
        0.05,
        0.03,
        0.20,
        94.0,
        96.0,
        0.01,
    ]
    frame.loc[210, ["close_loc", "vol_ratio", "confirmation", "confirmation_score"]] = [
        0.80,
        1.00,
        True,
        4,
    ]
    return frame


def test_late_stage_signal_is_causal_to_completed_close() -> None:
    spec = SPECS["QQQ"][0]
    x = _frame()
    a = add_late_stage_features(x, spec)
    changed = x.copy()
    changed.loc[211:, ["Open", "High", "Low", "Close"]] = 150.0
    b = add_late_stage_features(changed, spec)
    assert bool(a.loc[210, "late_stage_signal"])
    assert bool(b.loc[210, "late_stage_signal"])
    pd.testing.assert_series_equal(
        a.loc[:210, "late_stage_signal"],
        b.loc[:210, "late_stage_signal"],
    )


def test_late_stage_executes_next_open_once_per_episode() -> None:
    cfg = Config(symbol="QQQ", watch_dd=0.07, start_dd=0.07)
    trades, _ = run_late_stage(_frame(), cfg, SPECS["QQQ"][0])
    assert len(trades) == 1
    trade = trades.iloc[0]
    assert int(trade.execution_index) == int(trade.signal_index) + 1
    assert float(trade.tranche) == 0.05
    assert trade.reason == "EXHAUSTION_RECLAIM"


def test_late_stage_rejects_long_bear_and_credit_veto() -> None:
    cfg = Config(symbol="QQQ", watch_dd=0.07, start_dd=0.07)
    x = _frame()
    x.loc[210, "long_bear"] = True
    trades, _ = run_late_stage(x, cfg, SPECS["QQQ"][0])
    assert trades.empty

    x = _frame()
    x.loc[210, "credit_veto"] = True
    trades, _ = run_late_stage(x, cfg, SPECS["QQQ"][0])
    assert trades.empty
