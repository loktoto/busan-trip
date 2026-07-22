from __future__ import annotations

import numpy as np
import pandas as pd

from backtest import Config
from stress_cycle_maturity_v18 import PARAMS, SPECS, add_maturity_features, run_mature_stress_candidate


def _asset(n: int = 360) -> pd.DataFrame:
    dates = pd.date_range("2019-01-01", periods=n, freq="B")
    close = np.full(n, 100.0)
    close[210:281] = np.linspace(100.0, 75.0, 71)
    close[281:301] = np.linspace(75.0, 82.0, 20)
    close[301:] = 83.0
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
            "rv20": 0.30,
            "atr14": 2.0,
            "atrp": 0.025,
            "sma10": close - 1.0,
            "sma20": close + 1.0,
            "sma50": close + 4.0,
            "sma100": close + 7.0,
            "sma200": np.full(n, 95.0),
            "sma200_slope": -0.05,
            "sma10_slope": -0.01,
            "prior_low10": close - 1.0,
            "prior_low20": close - 1.0,
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
    frame.loc[211:, "underwater"] = np.arange(1, n - 210)
    frame.loc[230, ["newlow10", "newlow20"]] = [True, True]
    frame.loc[280, ["newlow10", "newlow20"]] = [True, True]
    frame.loc[300, ["r5", "rv20", "sma10_slope", "confirmation_score", "confirmation"]] = [
        0.05,
        0.24,
        0.02,
        4,
        True,
    ]
    frame.loc[280, "sma200_slope"] = -0.07
    frame.loc[300, "sma200_slope"] = -0.02
    return frame


def _series(dates: pd.Series, values: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({"Date": dates, "Value": values})


def _external(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    n = len(frame)
    dates = frame.Date
    stress = np.zeros(n)
    stress[220:241] = np.concatenate([np.linspace(0.0, 3.0, 11), np.linspace(2.7, 0.2, 10)])
    stress[270:301] = np.concatenate([np.linspace(0.0, 3.5, 16), np.linspace(3.2, 0.0, 15)])
    vix = 15.0 + stress * 8.0
    return {
        "FSI_TOTAL": _series(dates, stress),
        "FSI_CREDIT": _series(dates, stress * 0.8),
        "FSI_FUNDING": _series(dates, stress * 0.7),
        "FSI_VOL": _series(dates, stress * 0.9),
        "FSI_US": _series(dates, stress * 0.8),
        "VIX": _series(dates, vix),
        "VIX3M": _series(dates, np.full(n, 20.0)),
        "VIX9D": _series(dates, vix * np.linspace(1.1, 0.8, n)),
        "VVIX": _series(dates, vix * np.linspace(6.0, 4.0, n)),
        "VXN": _series(dates, vix * np.linspace(1.4, 1.1, n)),
        "MOVE": _series(dates, 100.0 + stress * 10.0),
        "SOFR": _series(dates, 4.0 + stress * 0.02),
        "SOFR_1P": _series(dates, 3.9 - stress * 0.02),
        "SOFR_99P": _series(dates, 4.1 + stress * 0.08),
        "BGCR": _series(dates, 4.0 - stress * 0.01),
        "DVP_RATE": _series(dates, 4.0 + stress * 0.07),
        "DVP_VOLUME": _series(dates, np.exp(20.0 + stress * 0.05)),
        "FAILS_TOTAL": _series(dates, np.exp(18.0 + stress * 0.3)),
        "FAILS_CORP": _series(dates, np.exp(17.0 + stress * 0.3)),
    }


def test_breach_age_measures_transition_not_every_day_below_threshold() -> None:
    frame = _asset()
    cfg = Config(symbol="QQQ", watch_dd=0.07, start_dd=0.07)
    external = _external(frame)
    features = add_maturity_features(frame, external, {key: 0 for key in external}, cfg, PARAMS["QQQ"])
    transitions = features.index[features.maturity_breach_transition].tolist()
    assert len(transitions) == 1
    first = transitions[0]
    assert features.loc[first, "maturity_sessions_since_breach"] == 0
    assert features.loc[first + 10, "maturity_sessions_since_breach"] == 10


def test_early_bear_normalisation_is_blocked_without_maturity() -> None:
    frame = _asset()
    cfg = Config(symbol="QQQ", watch_dd=0.07, start_dd=0.07)
    external = _external(frame)
    features = add_maturity_features(frame, external, {key: 0 for key in external}, cfg, PARAMS["QQQ"])
    assert not bool(features.loc[240, "maturity_bear_regime"])


def test_mature_candidate_never_confirms_on_breach_day() -> None:
    frame = _asset()
    cfg = Config(symbol="QQQ", watch_dd=0.07, start_dd=0.07)
    external = _external(frame)
    trades, _, _ = run_mature_stress_candidate(
        frame,
        cfg,
        SPECS["QQQ"][3],
        external,
        {key: 0 for key in external},
        PARAMS["QQQ"],
    )
    if not trades.empty:
        assert (trades.sessions_since_breach_transition >= 1).all()
        assert (trades.execution_index == trades.signal_index + 1).all()
        mature = trades.loc[trades.mature_bear_regime]
        if not mature.empty:
            assert (mature.cycle_dd <= -PARAMS["QQQ"].deep_bear_drawdown).all()
            assert (mature.underwater >= PARAMS["QQQ"].min_underwater_days).all()
            assert (mature.prior_stress_event_count >= PARAMS["QQQ"].min_prior_stress_events).all()
            assert (mature.stress_family_votes >= 2).all()
