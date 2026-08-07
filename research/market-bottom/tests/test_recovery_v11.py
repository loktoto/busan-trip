from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backtest import Config, episode_ids, indicators
from live_monitor_v11 import validate_payload_v11
from recovery_v11 import (
    add_recovery_features,
    candidate_v11,
    run_v11,
    state_v11,
)


def recovery_prices(n: int = 360, rebound_at_end: bool = True) -> pd.DataFrame:
    """Synthetic uptrend, 20% drawdown and a strong first rebound."""
    dates = pd.bdate_range("2024-01-02", periods=n)
    close = np.empty(n, dtype=float)
    close[0] = 100.0
    for i in range(1, n):
        close[i] = close[i - 1] * 1.0008

    trough_index = n - 3 if rebound_at_end else n - 12
    drop_start = trough_index - 9
    for i in range(drop_start, trough_index + 1):
        close[i] = close[i - 1] * 0.975
    close[trough_index + 1] = close[trough_index] * 1.055
    for i in range(trough_index + 2, n):
        close[i] = close[i - 1] * 1.002

    open_ = close * 0.995
    high = np.maximum(open_, close) * 1.008
    low = np.minimum(open_, close) * 0.975
    volume = np.full(n, 2_000_000.0)
    volume[drop_start : trough_index + 2] = 4_000_000.0
    return pd.DataFrame(
        {
            "Date": dates,
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        }
    )


def soxx_cfg() -> Config:
    return Config(
        symbol="SOXX",
        watch_dd=0.12,
        start_dd=0.12,
        max_dd=0.65,
        max_deploy=0.60,
        power=2.0,
        micro_probe=0.05,
        min_tranche=0.02,
        max_tranche=0.10,
        cooldown=7,
        spacing=0.06,
        long_bear_days=45,
        long_bear_cap=0.20,
    )


def test_recovery_probe_detects_strong_first_rebound() -> None:
    cfg = soxx_cfg()
    x = indicators(recovery_prices(), cfg)
    x = add_recovery_features(x, cfg)
    rebound = x.iloc[-2]
    assert rebound.cycle_dd <= -cfg.start_dd
    assert bool(rebound.recovery_probe)
    assert rebound.recovery_bounce >= rebound.recovery_threshold
    assert rebound.Close > x.iloc[-3].High


def test_recovery_probe_is_at_most_once_per_episode() -> None:
    cfg = soxx_cfg()
    x = indicators(recovery_prices(), cfg)
    trades, _ = run_v11(x, cfg)
    if not trades.empty and "recovery_probe_transition" in trades:
        recovery = trades.loc[trades.recovery_probe_transition.fillna(False)]
        assert (recovery.groupby("episode").size() <= 1).all()
        assert not recovery.long_bear.any()
        assert (recovery.cycle_dd <= -cfg.start_dd + 1e-12).all()


def test_candidate_target_never_falls_below_deployed_capital() -> None:
    cfg = soxx_cfg()
    x = indicators(recovery_prices(), cfg)
    x = add_recovery_features(x, cfg)
    x["episode"] = episode_ids(x, cfg)
    eid = int(x.iloc[-1].episode)
    assert eid > 0
    fake_trades = pd.DataFrame(
        [
            {
                "episode": eid,
                "tranche": 0.225,
                "execution_index": len(x) - 20,
                "execution_price": float(x.iloc[-20].Close),
                "recovery_probe_transition": False,
            }
        ]
    )
    candidate = candidate_v11(x, fake_trades, cfg)
    assert candidate["candidate_target_cumulative"] >= 0.225 - 1e-12
    assert candidate["cumulative_model_deployment"] == pytest.approx(0.225)


def test_active_deployed_episode_does_not_collapse_to_no_setup() -> None:
    cfg = Config(symbol="QQQ", watch_dd=0.07, start_dd=0.07, recovery_dd=0.002)
    latest = pd.Series(
        {
            "cycle_dd": -0.05,
            "episode": 3,
            "credit_veto": False,
            "recovery_probe": False,
            "confirmation": False,
            "exhaustion": False,
            "newlow10": False,
            "newlow20": False,
            "crash": False,
            "r5": 0.02,
            "sma10": 100.0,
            "Close": 101.0,
        }
    )
    prior = latest.copy()
    assert state_v11(latest, prior, cfg, used=0.075) == 5
    assert state_v11(latest, prior, cfg, used=0.0) == 0


def _payload(source: str = "IBKR", expected_shift_days: int = 0) -> dict:
    prices = recovery_prices(340)
    bars = []
    for row in prices.itertuples(index=False):
        bars.append(
            {
                "Date": row.Date.date().isoformat(),
                "Open": float(row.Open),
                "High": float(row.High),
                "Low": float(row.Low),
                "Close": float(row.Close),
                "Volume": float(row.Volume),
            }
        )
    last_date = prices.iloc[-1].Date.date() + pd.Timedelta(days=expected_shift_days)
    return {
        "schema_version": "1.0",
        "request_id": "test-v11",
        "created_at": "2026-07-22T01:00:00Z",
        "source": "IBKR",
        "bar_status": "LATEST_RTH_CLOSE",
        "expected_completed_rth_date": last_date.isoformat(),
        "assets": {
            symbol: {
                "bars": bars,
                "bars_source": source,
                "snapshot": {"historical_bars_source": source},
            }
            for symbol in ("SPY", "QQQ", "SOXX", "SMH")
        },
    }


def test_fresh_ibkr_payload_is_official_eligible() -> None:
    quality = validate_payload_v11(_payload())
    assert quality["freshness_verified"]
    assert quality["ibkr_bars_verified"]
    assert quality["official_eligible"]


def test_public_bootstrap_payload_is_not_official_eligible() -> None:
    quality = validate_payload_v11(_payload("PUBLIC_ADJUSTED_BOOTSTRAP"))
    assert quality["freshness_verified"]
    assert not quality["ibkr_bars_verified"]
    assert not quality["official_eligible"]


def test_stale_completed_bar_is_rejected() -> None:
    with pytest.raises(ValueError, match="expected_completed_rth_date"):
        validate_payload_v11(_payload(expected_shift_days=1))
