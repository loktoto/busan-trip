from __future__ import annotations

import numpy as np
import pandas as pd

from leverage_mapping_audit_v20 import daily_mapping_metrics


def _prices() -> tuple[pd.DataFrame, np.ndarray]:
    dates = pd.date_range("2020-01-01", periods=300, freq="B")
    # Deterministic, bounded positive/negative returns avoid the near-zero variance
    # correlation pathology produced by a constant-return fixture.
    phase = np.arange(300, dtype=float)
    returns = 0.0004 + 0.006 * np.sin(phase / 7.0) + 0.003 * np.cos(phase / 19.0)
    returns[0] = 0.0
    close = 100.0 * np.cumprod(1.0 + returns)
    frame = pd.DataFrame(
        {
            "Date": dates,
            "Open": close,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": 1_000_000.0,
        }
    )
    return frame, returns


def test_daily_mapping_metrics_detect_near_two_times_path() -> None:
    underlying, daily = _prices()
    leveraged = underlying.copy()
    leveraged["Close"] = 100.0 * np.cumprod(1.0 + 2.0 * daily)
    leveraged["Open"] = leveraged.Close
    leveraged["High"] = leveraged.Close * 1.01
    leveraged["Low"] = leveraged.Close * 0.99
    metrics = daily_mapping_metrics(underlying, leveraged)
    assert metrics["aligned_daily_observations"] >= 299
    assert metrics["actual_vs_underlying_daily_correlation"] > 0.999999
    assert abs(metrics["actual_daily_beta_to_underlying"] - 2.0) < 1e-10
    assert metrics["daily_gap_rmse"] < 1e-12
