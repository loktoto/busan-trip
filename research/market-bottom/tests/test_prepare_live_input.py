from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from prepare_live_input import assemble


def _write_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for i in range(300):
        price = 100 + i * 0.1
        rows.append(
            {
                "Date": f"2025-01-{(i % 28) + 1:02d}",
                "Open": price,
                "High": price + 1,
                "Low": price - 1,
                "Close": price + 0.2,
                "Volume": 1_000_000 + i,
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)


def test_assemble_uses_repo_daily_files(tmp_path: Path) -> None:
    assets = {}
    for symbol in ("SPY", "QQQ", "SOXX", "SMH"):
        rel = Path("runtime/market-bottom/data") / f"{symbol}.csv"
        _write_csv(tmp_path / rel)
        assets[symbol] = {"bars_path": rel.as_posix(), "snapshot": {"last": 123.45}}
    request = {
        "schema_version": "1.0",
        "request_id": "request-1",
        "created_at": "2026-07-21T15:00:00Z",
        "source": "IBKR",
        "bar_status": "LATEST_RTH_CLOSE",
        "assets": assets,
    }
    payload = assemble(request, tmp_path)
    assert payload["request_id"] == "request-1"
    assert len(payload["assets"]["SPY"]["bars"]) == 300
    assert payload["assets"]["SOXX"]["snapshot"]["last"] == 123.45


def test_assemble_rejects_path_outside_runtime_data(tmp_path: Path) -> None:
    assets = {
        symbol: {"bars_path": "research/market-bottom/secret.csv"}
        for symbol in ("SPY", "QQQ", "SOXX", "SMH")
    }
    request = {
        "schema_version": "1.0",
        "request_id": "request-2",
        "created_at": "2026-07-21T15:00:00Z",
        "source": "IBKR",
        "bar_status": "LATEST_RTH_CLOSE",
        "assets": assets,
    }
    try:
        assemble(request, tmp_path)
    except ValueError as exc:
        assert "must be under" in str(exc)
    else:
        raise AssertionError("unsafe path must be rejected")
