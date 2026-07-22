from __future__ import annotations

import numpy as np
import pandas as pd

from backtest import Config
from orthogonal_indicators_v16 import SPECS, add_orthogonal_features, run_orthogonal_candidate


def _asset_frame(n: int = 240) -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    close = np.full(n, 100.0)
    close[205] = 90.0
    close[206:212] = [90.5, 91.0, 92.0, 93.0, 94.0, 95.0]
    close[212:] = 96.0
    frame = pd.DataFrame(
        {
            "Date": dates,
            "Open": close,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": 1_000_000.0,
            "cycle_high": 100.0,
            "cycle_dd": close / 100.0 - 1.0,
            "dd_52w": close / 100.0 - 1.0,
            "r1": 0.0,
            "r3": 0.0,
            "r5": 0.0,
            "r10": 0.0,
            "r20": 0.0,
            "r63": 0.0,
            "r126": 0.0,
            "rv20": 0.25,
            "atr14": 2.0,
            "atrp": 0.02,
            "sma10": 96.0,
            "sma20": 97.0,
            "sma50": 98.0,
            "sma100": 99.0,
            "sma200": 100.0,
            "sma200_slope": 0.0,
            "sma10_slope": -0.01,
            "prior_low10": 90.0,
            "prior_low20": 90.0,
            "newlow10": False,
            "newlow20": False,
            "vol_ratio": 1.0,
            "close_loc": 0.7,
            "down_volume_ratio": 0.0,
            "sell_pressure": 0.0,
            "r5z": 0.0,
            "underwater": 0,
            "long_bear": False,
            "exhaustion_score": 0,
            "breadth_divergence": False,
            "vrp_divergence": False,
            "exhaustion": False,
            "confirmation_score": 0,
            "confirmation": False,
            "crash": False,
            "credit_veto": False,
        }
    )
    frame.loc[205:, "underwater"] = np.arange(1, n - 204)
    frame.loc[205, ["newlow10", "newlow20"]] = [True, True]
    frame.loc[211, ["r5", "rv20", "sma10", "sma10_slope", "confirmation_score", "confirmation"]] = [
        0.04,
        0.22,
        93.0,
        0.01,
        4,
        True,
    ]
    return frame


def _series(dates: pd.Series, values: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({"Date": dates, "Close": values})


def _proxies(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    n = len(frame)
    dates = frame.Date
    asset = frame.Close.to_numpy(float)
    # Equal-weight proxy accelerates faster than the cap-weight asset into signal day.
    breadth_ratio = np.linspace(0.95, 1.05, n)
    qqqe = asset * breadth_ratio
    # Credit risk appetite improves.
    ief = np.full(n, 100.0)
    hyg = 80.0 * np.linspace(0.95, 1.05, n)
    # Tech volatility falls faster than broad volatility.
    vix = np.linspace(25.0, 20.0, n)
    vxn = np.linspace(35.0, 22.0, n)
    return {
        "QQQE": _series(dates, qqqe),
        "HYG": _series(dates, hyg),
        "IEF": _series(dates, ief),
        "VXN": _series(dates, vxn),
        "VIX": _series(dates, vix),
        "SPY": _series(dates, asset * 0.8),
    }


def test_orthogonal_features_detect_independent_support() -> None:
    frame = _asset_frame()
    cfg = Config(symbol="QQQ", watch_dd=0.07, start_dd=0.07)
    y = add_orthogonal_features(frame, "QQQ", _proxies(frame), cfg)
    assert bool(y.loc[211, "breadth_support"])
    assert bool(y.loc[211, "credit_support"])
    assert bool(y.loc[211, "vol_support"])
    assert int(y.loc[211, "orthogonal_support_votes"]) >= 3


def test_orthogonal_candidate_executes_next_open_once() -> None:
    frame = _asset_frame()
    cfg = Config(symbol="QQQ", watch_dd=0.07, start_dd=0.07)
    trades, _, _ = run_orthogonal_candidate(
        frame,
        cfg,
        SPECS["QQQ"][3],
        _proxies(frame),
    )
    assert len(trades) == 1
    trade = trades.iloc[0]
    assert int(trade.execution_index) == int(trade.signal_index) + 1
    assert float(trade.tranche) == 0.04
    assert int(trade.support_votes) >= 3


def test_future_proxy_changes_do_not_change_prior_signal() -> None:
    frame = _asset_frame()
    cfg = Config(symbol="QQQ", watch_dd=0.07, start_dd=0.07)
    proxies = _proxies(frame)
    a = add_orthogonal_features(frame, "QQQ", proxies, cfg)
    changed = {k: v.copy() for k, v in proxies.items()}
    for key in changed:
        changed[key].loc[changed[key].index > 211, "Close"] *= 10
    b = add_orthogonal_features(frame, "QQQ", changed, cfg)
    pd.testing.assert_series_equal(
        a.loc[:211, "orthogonal_support_votes"],
        b.loc[:211, "orthogonal_support_votes"],
    )
