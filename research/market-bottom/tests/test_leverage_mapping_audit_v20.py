from __future__ import annotations

import numpy as np
import pandas as pd

from leverage_mapping_audit_v20 import daily_mapping_metrics


def _prices(multiplier: float = 1.0) -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=300, freq="B")
    close = 100.0 * np.cumprod(np.full(300, 1.001))
    return pd.DataFrame(
        {
            "Date": dates,
            "Open": close,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close * multiplier,
            "Volume": 1_000_000.0,
        }
    )


def test_daily_mapping_metrics_detect_near_two_times_path() -> None:
    underlying = _prices()
    daily = underlying.Close.pct_change().fillna(0.0)
    leveraged = underlying.copy()
    leveraged["Close"] = 100.0 * (1.0 + 2.0 * daily).cumprod()
    leveraged["Open"] = leveraged.Close
    leveraged["High"] = leveraged.Close * 1.01
    leveraged["Low"] = leveraged.Close * 0.99
    metrics = daily_mapping_metrics(underlying, leveraged)
    assert metrics["aligned_daily_observations"] >= 299
    assert metrics["actual_vs_underlying_daily_correlation"] > 0.999
    assert abs(metrics["actual_daily_beta_to_underlying"] - 2.0) < 1e-6
    assert metrics["daily_gap_rmse"] < 1e-10
