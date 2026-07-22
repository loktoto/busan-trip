from __future__ import annotations

import numpy as np
import pandas as pd

from backtest import Config
from recovery_v12 import add_catchup_features, run_v12


def _feature_frame(symbol: str = "SPY", n: int = 210) -> pd.DataFrame:
    cfg = Config(symbol=symbol)
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    close = np.full(n, 100.0)
    cycle_dd = np.zeros(n)
    # Enter the 5% SPY watch zone, remain inside for one close, then rebound above it.
    close[200] = 94.0
    close[201] = 94.2
    close[202:] = 95.8
    cycle_dd[200] = -0.060
    cycle_dd[201] = -0.058
    cycle_dd[202:] = -0.042

    frame = pd.DataFrame(
        {
            "Date": dates,
            "Open": close,
            "High": close + 0.8,
            "Low": close - 0.8,
            "Close": close,
            "Volume": 1_000_000.0,
            "cycle_high": 100.0,
            "cycle_dd": cycle_dd,
            "dd_52w": cycle_dd,
            "r1": 0.0,
            "r5": 0.0,
            "rv20": 0.20,
            "atr14": 2.0,
            "atrp": 0.02,
            "sma10": 95.0,
            "sma10_slope": 0.01,
            "newlow10": False,
            "newlow20": False,
            "crash": False,
            "exhaustion": False,
            "confirmation": False,
            "close_loc": 0.80,
            "vol_ratio": 1.00,
            "underwater": 0,
            "long_bear": False,
            "credit_veto": False,
        }
    )
    frame.loc[200, ["r1", "r5", "newlow20", "close_loc"]] = [-0.06, -0.06, True, 0.20]
    frame.loc[201, ["r1", "r5", "close_loc"]] = [0.002, -0.04, 0.55]
    frame.loc[202:, ["r1", "r5", "close_loc"]] = [0.017, 0.03, 0.85]
    frame.loc[:199, "underwater"] = 0
    frame.loc[200:, "underwater"] = np.arange(1, n - 199)
    return frame


def test_catchup_can_trigger_after_prior_breach_above_watch_threshold() -> None:
    cfg = Config(symbol="SPY")
    y = add_catchup_features(_feature_frame(), cfg)
    assert bool(y.loc[202, "catchup_recent_breach"])
    assert y.loc[202, "cycle_dd"] > -cfg.watch_dd
    assert bool(y.loc[202, "catchup_probe"])


def test_catchup_requires_prior_breach() -> None:
    cfg = Config(symbol="SPY")
    x = _feature_frame()
    x.loc[200:201, "cycle_dd"] = -0.04
    x.loc[200:201, "Close"] = 96.0
    y = add_catchup_features(x, cfg)
    assert not bool(y.loc[202, "catchup_recent_breach"])
    assert not bool(y.loc[202, "catchup_probe"])


def test_catchup_rejects_excessive_rebound_or_veto() -> None:
    cfg = Config(symbol="SPY")
    x = _feature_frame()
    x.loc[202:, "Close"] = 99.0
    x.loc[202:, "cycle_dd"] = -0.01
    y = add_catchup_features(x, cfg)
    assert not bool(y.loc[202, "catchup_probe"])

    x = _feature_frame()
    x.loc[202, "credit_veto"] = True
    y = add_catchup_features(x, cfg)
    assert not bool(y.loc[202, "catchup_probe"])

    x = _feature_frame()
    x.loc[202, "long_bear"] = True
    y = add_catchup_features(x, cfg)
    assert not bool(y.loc[202, "catchup_probe"])


def test_run_v12_emits_only_one_bounded_catchup_per_episode() -> None:
    cfg = Config(symbol="SPY")
    trades, _ = run_v12(_feature_frame(), cfg)
    catchups = trades.loc[trades.catchup_probe_transition.fillna(False)]
    assert len(catchups) == 1
    assert catchups.iloc[0].reason == "POST_THRESHOLD_CATCHUP"
    assert abs(float(catchups.iloc[0].tranche) - 0.02) < 1e-12
    assert float(catchups.iloc[0].cumulative) <= cfg.max_deploy
    assert float(catchups.iloc[0].tranche) <= cfg.max_tranche
