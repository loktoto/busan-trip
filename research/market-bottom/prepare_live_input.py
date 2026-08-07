#!/usr/bin/env python3
"""Assemble a strict compact runtime request plus repository-stored IBKR bars.

The caller must update all completed daily files before writing latest-request.json.
This assembler never downloads or substitutes public history. It validates the
expected completed-RTH date and fails closed when any asset is stale or has an
unapproved bars source.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

ASSETS = ("SPY", "QQQ", "SOXX", "SMH")
ALLOWED_DATA_ROOT = Path("runtime/market-bottom/data")
REQUIRED_BARS = ["Date", "Open", "High", "Low", "Close", "Volume"]
ALLOWED_BARS_SOURCE = "IBKR"


def _safe_repo_path(repo_root: Path, raw: str) -> Path:
    rel = Path(raw)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"unsafe repository path: {raw}")
    resolved = (repo_root / rel).resolve()
    allowed = (repo_root / ALLOWED_DATA_ROOT).resolve()
    if allowed not in resolved.parents:
        raise ValueError(f"data path must be under {ALLOWED_DATA_ROOT}: {raw}")
    return resolved


def _normalise_bars(df: pd.DataFrame, label: str) -> pd.DataFrame:
    missing = set(REQUIRED_BARS) - set(df.columns)
    if missing:
        raise ValueError(f"{label} missing {sorted(missing)}")
    out = df[REQUIRED_BARS].copy()
    out["Date"] = (
        pd.to_datetime(out["Date"], utc=True, errors="raise", format="mixed")
        .dt.tz_convert(None)
        .dt.date.astype(str)
    )
    for col in REQUIRED_BARS[1:]:
        out[col] = pd.to_numeric(out[col], errors="raise")
    out = out.sort_values("Date").drop_duplicates("Date", keep="last").reset_index(drop=True)
    if len(out) < 260:
        raise ValueError(f"{label} requires at least 260 rows")
    if (out[["Open", "High", "Low", "Close"]] <= 0).any().any():
        raise ValueError(f"{label} requires positive prices")
    if (out["Volume"] < 0).any():
        raise ValueError(f"{label} requires non-negative volume")
    if (out["High"] < out[["Open", "Close", "Low"]].max(axis=1)).any():
        raise ValueError(f"{label} has inconsistent high")
    if (out["Low"] > out[["Open", "Close", "High"]].min(axis=1)).any():
        raise ValueError(f"{label} has inconsistent low")
    return out


def _bars(path: Path) -> list[dict[str, Any]]:
    return _normalise_bars(pd.read_csv(path), str(path)).to_dict(orient="records")


def _merge_completed_bar(rows: list[dict[str, Any]], snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    completed = snapshot.get("completed_rth_bar")
    if not completed:
        return rows
    if not isinstance(completed, dict):
        raise ValueError("completed_rth_bar must be an object")
    missing = set(REQUIRED_BARS) - set(completed)
    if missing:
        raise ValueError(f"completed_rth_bar missing {sorted(missing)}")
    merged = pd.DataFrame(rows + [{key: completed[key] for key in REQUIRED_BARS}])
    return _normalise_bars(merged, "completed bars").to_dict(orient="records")


def _features(path: Path) -> list[dict[str, Any]]:
    df = pd.read_csv(path)
    if "Date" not in df:
        raise ValueError(f"{path} feature file requires Date")
    return df.to_dict(orient="records")


def assemble(request: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    if request.get("schema_version") != "1.0":
        raise ValueError("schema_version must be 1.0")
    if request.get("source") != "IBKR":
        raise ValueError("source must be IBKR")
    expected = request.get("expected_completed_rth_date")
    if not expected:
        raise ValueError("expected_completed_rth_date is required")
    expected = pd.Timestamp(expected).date().isoformat()

    assets = request.get("assets")
    if not isinstance(assets, dict) or set(assets) != set(ASSETS):
        raise ValueError(f"assets must be exactly {ASSETS}")

    payload = {
        "schema_version": "1.0",
        "request_id": request["request_id"],
        "created_at": request["created_at"],
        "source": "IBKR",
        "bar_status": request.get("bar_status", "LATEST_RTH_CLOSE"),
        "expected_completed_rth_date": expected,
        "model_commit": request.get("model_commit", ""),
        "assets": {},
    }
    latest_dates: dict[str, str] = {}
    for symbol in ASSETS:
        item = assets[symbol]
        bars_source = item.get("bars_source")
        if bars_source != ALLOWED_BARS_SOURCE:
            raise ValueError(f"{symbol} bars_source must be {ALLOWED_BARS_SOURCE}")
        bars_path = _safe_repo_path(repo_root, item["bars_path"])
        snapshot = item.get("snapshot", {})
        bars = _merge_completed_bar(_bars(bars_path), snapshot)
        latest = str(bars[-1]["Date"])
        latest_dates[symbol] = latest
        if latest != expected:
            raise ValueError(
                f"{symbol} latest completed bar {latest} does not match expected {expected}"
            )
        out = {
            "bars": bars,
            "bars_source": bars_source,
            "snapshot": snapshot,
        }
        if item.get("features_path"):
            out["features"] = _features(_safe_repo_path(repo_root, item["features_path"]))
        payload["assets"][symbol] = out

    if len(set(latest_dates.values())) != 1:
        raise ValueError("completed daily bars are not aligned across assets")
    payload["latest_completed_bar_dates"] = latest_dates
    return payload


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", type=Path, required=True)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    request = json.loads(args.request.read_text())
    payload = assemble(request, args.repo_root.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n")
    print(
        json.dumps(
            {
                "request_id": payload["request_id"],
                "expected_completed_rth_date": payload["expected_completed_rth_date"],
                "assets": list(payload["assets"]),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
