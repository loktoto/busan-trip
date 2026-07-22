from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from prepare_live_input import assemble

ASSETS = ("SPY", "QQQ", "SOXX", "SMH")


def _write_csv(path: Path, last_shift: int = 0) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    dates = pd.bdate_range("2025-01-02", periods=300)
    if last_shift:
        dates = dates[:-1].append(pd.DatetimeIndex([dates[-1] + pd.Timedelta(days=last_shift)]))
    rows = []
    for i, dt in enumerate(dates):
        price = 100 + i * 0.1
        rows.append(
            {
                "Date": dt.date().isoformat(),
                "Open": price,
                "High": price + 1,
                "Low": price - 1,
                "Close": price + 0.2,
                "Volume": 1_000_000 + i,
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)
    return dates[-1].date().isoformat()


def _request(tmp_path: Path, bars_source: str = "IBKR") -> dict:
    assets = {}
    expected = None
    for symbol in ASSETS:
        rel = Path("runtime/market-bottom/data") / f"{symbol}.csv"
        last = _write_csv(tmp_path / rel)
        expected = expected or last
        assets[symbol] = {
            "bars_path": rel.as_posix(),
            "bars_source": bars_source,
            "snapshot": {"last": 123.45},
        }
    return {
        "schema_version": "1.0",
        "request_id": "request-1",
        "created_at": "2026-07-21T15:00:00Z",
        "source": "IBKR",
        "bar_status": "LATEST_RTH_CLOSE",
        "expected_completed_rth_date": expected,
        "assets": assets,
    }


def test_assemble_uses_aligned_ibkr_daily_files(tmp_path: Path) -> None:
    request = _request(tmp_path)
    payload = assemble(request, tmp_path)
    assert payload["request_id"] == "request-1"
    assert len(payload["assets"]["SPY"]["bars"]) == 300
    assert payload["assets"]["SOXX"]["snapshot"]["last"] == 123.45
    assert payload["assets"]["SOXX"]["bars_source"] == "IBKR"
    assert payload["expected_completed_rth_date"] == request["expected_completed_rth_date"]


def test_assemble_rejects_path_outside_runtime_data(tmp_path: Path) -> None:
    assets = {
        symbol: {
            "bars_path": "research/market-bottom/secret.csv",
            "bars_source": "IBKR",
            "snapshot": {},
        }
        for symbol in ASSETS
    }
    request = {
        "schema_version": "1.0",
        "request_id": "request-2",
        "created_at": "2026-07-21T15:00:00Z",
        "source": "IBKR",
        "bar_status": "LATEST_RTH_CLOSE",
        "expected_completed_rth_date": "2026-01-01",
        "assets": assets,
    }
    with pytest.raises(ValueError, match="must be under"):
        assemble(request, tmp_path)


def test_assemble_rejects_public_bars_source(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="bars_source must be IBKR"):
        assemble(_request(tmp_path, bars_source="PUBLIC_ADJUSTED"), tmp_path)


def test_assemble_rejects_stale_asset(tmp_path: Path) -> None:
    request = _request(tmp_path)
    spy_path = tmp_path / request["assets"]["SPY"]["bars_path"]
    df = pd.read_csv(spy_path)
    df = df.iloc[:-1]
    df.to_csv(spy_path, index=False)
    with pytest.raises(ValueError, match="does not match expected"):
        assemble(request, tmp_path)
