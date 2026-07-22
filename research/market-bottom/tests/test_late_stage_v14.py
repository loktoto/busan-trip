from __future__ import annotations

import numpy as np
import pandas as pd

from backtest import Config
from late_stage_v14 import REGIME_PARAMS, REGIME_SPECS, add_regime_features, run_regime_late_stage


def _bear_frame(n: int = 230) -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    close = np.full(n, 100.0)
    close[180] = 84.0
    close[205] = 80.0
    close[206:211] = [80.5, 81.0, 81.5, 81.8, 82.0]
    close[211:] = 83.0
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
            "atrp": 0.024,
            "sma10": 83.0,
            "sma20": 86.0,
            "sma50": 90.0,
            "sma200": 100.0,
            "sma200_slope": -0.05,
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
    for i in (180, 205):
        frame.loc[i, ["newlow10", "newlow20", "exhaustion", "exhaustion_score"]] = [
            True,
            True,
            True,
            3,
        ]
    frame.loc[180:, "underwater"] = np.arange(1, n - 179)
    frame.loc[210, ["r1", "r5", "r10", "rv20", "sma10", "sma20", "sma10_slope"]] = [
        0.01,
        0.03,
        0.02,
        0.20,
        81.5,
        85.0,
        0.01,
    ]
    frame.loc[210, ["close_loc", "vol_ratio", "confirmation", "confirmation_score"]] = [
        0.80,
        1.00,
        True,
        4,
    ]
    frame.loc[190, "sma200_slope"] = -0.06
    frame.loc[210, "sma200_slope"] = -0.02
    frame.loc[210, "long_bear"] = True
    return frame


def test_early_falling_200dma_rebound_is_blocked() -> None:
    spec = REGIME_SPECS["QQQ"][0]
    x = _bear_frame()
    x.loc[210, "underwater"] = 59
    y = add_regime_features(x, spec, REGIME_PARAMS["QQQ"])
    assert bool(y.loc[210, "late_stage_signal"])
    assert not bool(y.loc[210, "mature_bear_regime"])
    assert not bool(y.loc[210, "regime_late_stage_signal"])


def test_mature_bear_can_pass_after_multiple_washouts_and_flattening() -> None:
    spec = REGIME_SPECS["QQQ"][0]
    x = _bear_frame()
    x.loc[210, "underwater"] = 80
    y = add_regime_features(x, spec, REGIME_PARAMS["QQQ"])
    assert y.loc[210, "regime_washout_count"] >= 2
    assert bool(y.loc[210, "mature_bear_regime"])
    assert bool(y.loc[210, "regime_late_stage_signal"])

    cfg = Config(symbol="QQQ", watch_dd=0.07, start_dd=0.07)
    trades, _ = run_regime_late_stage(x, cfg, spec, REGIME_PARAMS["QQQ"])
    assert len(trades) == 1
    assert bool(trades.iloc[0].mature_bear_regime)
    assert int(trades.iloc[0].execution_index) == int(trades.iloc[0].signal_index) + 1
