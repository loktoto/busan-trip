from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import live_monitor


def _bars(n: int = 340, shock: bool = False) -> list[dict]:
    start = date(2025, 1, 1)
    rows = []
    price = 100.0
    for i in range(n):
        if shock and i > n - 12:
            price *= 0.975
        else:
            price *= 1.0004
        rows.append(
            {
                "Date": (start + timedelta(days=i)).isoformat(),
                "Open": price * 0.998,
                "High": price * 1.01,
                "Low": price * 0.99,
                "Close": price,
                "Volume": 1_000_000 + i * 100,
            }
        )
    return rows


def _payload() -> dict:
    return {
        "schema_version": "1.0",
        "request_id": "test-run",
        "created_at": "2026-07-21T14:00:00Z",
        "source": "IBKR",
        "bar_status": "LATEST_RTH_CLOSE",
        "assets": {
            "SPY": {"bars": _bars()},
            "QQQ": {"bars": _bars(shock=True)},
            "SOXX": {"bars": _bars(shock=True)},
            "SMH": {"bars": _bars(shock=True)},
        },
    }


def test_live_monitor_writes_deterministic_result(tmp_path: Path, monkeypatch) -> None:
    input_path = tmp_path / "input.json"
    result_path = tmp_path / "result.json"
    report_path = tmp_path / "report.md"
    input_path.write_text(json.dumps(_payload()))
    config_path = Path(__file__).resolve().parents[1] / "config.example.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "live_monitor.py",
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
    live_monitor.main()
    result = json.loads(result_path.read_text())
    assert set(result["assets"]) == {"SPY", "QQQ", "SOXX", "SMH"}
    assert result["assets"]["SMH"]["candidate_tranche"] == 0.0
    assert result["assets"]["SMH"]["eligible_at_next_open"] is False
    assert result["semiconductor_pair"]["production_weight"] == 0.0
    assert result["input_sha256"]
    assert "GitHub deterministic result" in report_path.read_text()


def test_payload_rejects_missing_primary_asset() -> None:
    payload = _payload()
    del payload["assets"]["SPY"]
    try:
        live_monitor._validate_payload(payload)
    except ValueError as exc:
        assert "assets must be exactly" in str(exc)
    else:
        raise AssertionError("missing SPY must be rejected")
