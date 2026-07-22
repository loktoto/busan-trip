from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import live_monitor_v15


def _payload() -> dict:
    dates = pd.bdate_range("2024-01-02", periods=340)
    close = np.linspace(100.0, 130.0, len(dates))
    close[-12:] = close[-13] * np.cumprod(np.full(12, 0.98))
    bars = []
    for date, price in zip(dates, close):
        bars.append(
            {
                "Date": date.date().isoformat(),
                "Open": float(price * 0.998),
                "High": float(price * 1.01),
                "Low": float(price * 0.99),
                "Close": float(price),
                "Volume": 1_000_000.0,
            }
        )
    last_date = dates[-1].date().isoformat()
    return {
        "schema_version": "1.0",
        "request_id": "test-v15",
        "created_at": "2026-07-22T01:00:00Z",
        "source": "IBKR",
        "bar_status": "LATEST_RTH_CLOSE",
        "expected_completed_rth_date": last_date,
        "assets": {
            symbol: {
                "bars": bars,
                "bars_source": "IBKR",
                "snapshot": {"historical_bars_source": "IBKR"},
            }
            for symbol in ("SPY", "QQQ", "SOXX", "SMH")
        },
    }


def test_live_v15_adds_reporting_taxonomy_without_trade_authority(
    tmp_path: Path, monkeypatch
) -> None:
    input_path = tmp_path / "input.json"
    result_path = tmp_path / "result.json"
    report_path = tmp_path / "report.md"
    input_path.write_text(json.dumps(_payload()))
    config_path = Path(__file__).resolve().parents[1] / "config.example.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "live_monitor_v15.py",
            "--input",
            str(input_path),
            "--config",
            str(config_path),
            "--result",
            str(result_path),
            "--report",
            str(report_path),
        ],
    )
    live_monitor_v15.main()
    result = json.loads(result_path.read_text())
    assert result["engine_version"] == "1.5-reporting"
    assert result["trading_engine_version"] == "1.1"
    assert result["official_eligible"] is True
    for symbol in ("SPY", "QQQ", "SOXX"):
        taxonomy = result["assets"][symbol]["bottom_taxonomy"]
        assert taxonomy["reporting_only"] is True
        assert taxonomy["trade_authority"] == "NONE"
        assert taxonomy["leverage_authority"] == "NONE_FROM_TAXONOMY"
        assert taxonomy["cycle_bottom_status"].startswith("CYCLE_BOTTOM_")
    assert result["assets"]["SMH"]["candidate_tranche"] == 0.0
    assert result["semiconductor_pair"]["production_weight"] == 0.0
    text = report_path.read_text()
    assert "participation, swing and cycle taxonomy" in text
    assert "LOCAL_SWING_RECOVERY" in text or "LOCAL_SWING_NOT_CONFIRMED" in text
