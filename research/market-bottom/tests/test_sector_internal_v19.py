from __future__ import annotations

import numpy as np
import pandas as pd

from backtest import Config
from sector_internal_v19 import PANELS, SPECS, add_internal_features, run_internal_candidate


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
            "sma10": 95.0,
            "sma20": 94.0,
            "sma50": 93.0,
            "sma100": 92.0,
            "sma200": 89.0,
            "sma200_slope": 0.01,
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
    frame.loc[260, ["r5", "rv20", "sma10_slope", "confirmation_score", "confirmation"]] = [
        0.04,
        0.20,
        0.02,
        4,
        True,
    ]
    return frame


def _member(dates: pd.Series, phase: float, n: int) -> pd.DataFrame:
    base = np.full(n, 100.0)
    base[230:251] = np.linspace(100.0, 80.0 + phase, 21)
    base[251:261] = np.linspace(81.0 + phase, 100.0 + phase, 10)
    base[261:] = 101.0 + phase
    return pd.DataFrame(
        {
            "Date": dates,
            "Open": base,
            "High": base + 1.0,
            "Low": base - 1.0,
            "Close": base,
            "Volume": 1_000_000.0,
        }
    )


def _members(asset: pd.DataFrame, symbol: str) -> dict[str, pd.DataFrame]:
    return {
        member: _member(asset.Date, index * 0.2, len(asset))
        for index, member in enumerate(PANELS[symbol])
    }


def test_internal_features_are_cross_sectional_and_causal() -> None:
    asset = _asset()
    cfg = Config(symbol="SOXX", watch_dd=0.12, start_dd=0.12)
    members = _members(asset, "SOXX")
    a = add_internal_features(asset, "SOXX", members, cfg)
    changed = {key: value.copy() for key, value in members.items()}
    for frame in changed.values():
        frame.loc[frame.index > 260, "Close"] *= 10
    b = add_internal_features(asset, "SOXX", changed, cfg)
    pd.testing.assert_series_equal(
        a.loc[:260, "internal_breadth_score"],
        b.loc[:260, "internal_breadth_score"],
    )
    assert a.internal_pct_above20.between(0, 1).all()
    assert a.internal_pct_newlow20.between(0, 1).all()


def test_transition_regime_is_blocked() -> None:
    asset = _asset()
    cfg = Config(symbol="SOXX", watch_dd=0.12, start_dd=0.12)
    asset.loc[260, "Close"] = 95.0
    asset.loc[260, "sma200"] = 96.0
    asset.loc[260, "sma200_slope"] = 0.01
    features = add_internal_features(asset, "SOXX", _members(asset, "SOXX"), cfg)
    assert not bool(features.loc[260, "internal_ordinary_regime"])
    assert not bool(features.loc[260, "internal_mature_bear_regime"])
    assert not bool(features.loc[260, "internal_regime_gate"])


def test_internal_candidate_never_executes_same_day() -> None:
    asset = _asset()
    cfg = Config(symbol="SOXX", watch_dd=0.12, start_dd=0.12)
    trades, _, _ = run_internal_candidate(
        asset,
        cfg,
        SPECS["SOXX"][3],
        _members(asset, "SOXX"),
    )
    if not trades.empty:
        assert (trades.execution_index == trades.signal_index + 1).all()
        assert (trades.sessions_since_breach_transition >= 1).all()
        assert (trades.internal_family_votes >= 2).all()
