from __future__ import annotations

import numpy as np
import pandas as pd

from backtest import Config
from stress_normalization_v17 import (
    SPECS,
    add_stress_features,
    align_to_strategy_sessions,
    run_stress_candidate,
)


def _asset(n: int = 300) -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    close = np.full(n, 100.0)
    close[250] = 90.0
    close[251:261] = np.linspace(90.5, 96.0, 10)
    close[261:] = 97.0
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
    frame.loc[250:, "underwater"] = np.arange(1, n - 249)
    frame.loc[250, ["newlow10", "newlow20"]] = [True, True]
    frame.loc[260, ["r5", "rv20", "sma10", "sma10_slope", "confirmation_score", "confirmation"]] = [
        0.04,
        0.20,
        94.0,
        0.01,
        4,
        True,
    ]
    return frame


def _series(dates: pd.Series, values: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({"Date": dates, "Value": values})


def _external(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    n = len(frame)
    dates = frame.Date
    # Stress rises sharply then normalises into the signal date.
    peak = np.concatenate([np.linspace(-0.5, 0.0, 240), np.linspace(0.2, 3.0, 11), np.linspace(2.8, 0.0, n - 251)])
    vix = 15.0 + np.maximum(peak, 0) * 8.0
    return {
        "FSI_TOTAL": _series(dates, peak),
        "FSI_CREDIT": _series(dates, peak * 0.8),
        "FSI_FUNDING": _series(dates, peak * 0.7),
        "FSI_VOL": _series(dates, peak * 0.9),
        "FSI_US": _series(dates, peak * 0.8),
        "VIX": _series(dates, vix),
        "VIX3M": _series(dates, np.full(n, 20.0)),
        "VIX9D": _series(dates, vix * np.linspace(1.0, 0.8, n)),
        "VVIX": _series(dates, vix * np.linspace(6.0, 4.0, n)),
        "VXN": _series(dates, vix * np.linspace(1.4, 1.1, n)),
        "MOVE": _series(dates, 100.0 + np.maximum(peak, 0) * 10.0),
        "SOFR": _series(dates, 4.0 + peak * 0.02),
        "SOFR_1P": _series(dates, 3.9 - np.maximum(peak, 0) * 0.02),
        "SOFR_99P": _series(dates, 4.1 + np.maximum(peak, 0) * 0.08),
        "BGCR": _series(dates, 4.0 - np.maximum(peak, 0) * 0.01),
        "DVP_RATE": _series(dates, 4.0 + np.maximum(peak, 0) * 0.07),
        "DVP_VOLUME": _series(dates, np.exp(20.0 + np.maximum(peak, 0) * 0.05)),
        "FAILS_TOTAL": _series(dates, np.exp(18.0 + np.maximum(peak, 0) * 0.3)),
        "FAILS_CORP": _series(dates, np.exp(17.0 + np.maximum(peak, 0) * 0.3)),
    }


def test_strategy_availability_shift_uses_future_session_not_observation_date() -> None:
    dates = pd.Series(pd.date_range("2026-01-05", periods=6, freq="B"))
    raw = pd.DataFrame({"Date": [dates.iloc[0]], "Value": [1.0]})
    shifted = align_to_strategy_sessions(raw, dates, 2)
    assert shifted.iloc[0].Date == dates.iloc[2]


def test_future_stress_values_do_not_change_prior_feature() -> None:
    asset = _asset()
    external = _external(asset)
    lags = {key: 0 for key in external}
    cfg = Config(symbol="QQQ", watch_dd=0.07, start_dd=0.07)
    a = add_stress_features(asset, external, lags, cfg)
    changed = {key: value.copy() for key, value in external.items()}
    for value in changed.values():
        value.loc[value.index > 260, "Value"] *= 10
    b = add_stress_features(asset, changed, lags, cfg)
    pd.testing.assert_series_equal(a.loc[:260, "stress_family_votes"], b.loc[:260, "stress_family_votes"])


def test_composite_requires_two_normalising_families_and_next_open_execution() -> None:
    asset = _asset()
    external = _external(asset)
    lags = {key: 0 for key in external}
    cfg = Config(symbol="QQQ", watch_dd=0.07, start_dd=0.07)
    trades, _, features = run_stress_candidate(asset, cfg, SPECS["QQQ"][3], external, lags)
    assert features.stress_family_votes.max() >= 2
    assert len(trades) <= 1
    if not trades.empty:
        trade = trades.iloc[0]
        assert int(trade.execution_index) == int(trade.signal_index) + 1
        assert int(trade.stress_family_votes) >= 2
        assert float(trade.tranche) == 0.04
