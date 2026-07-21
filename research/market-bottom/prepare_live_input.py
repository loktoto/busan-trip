#!/usr/bin/env python3
"""Assemble a compact runtime request plus repository-stored IBKR daily files.

This keeps hourly commits small: completed daily OHLCV files change only after a
new RTH close, while latest-request.json may change hourly for snapshot context.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

ASSETS = ("SPY", "QQQ", "SOXX", "SMH")
ALLOWED_DATA_ROOT = Path("runtime/market-bottom/data")


def _safe_repo_path(repo_root: Path, raw: str) -> Path:
    rel = Path(raw)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"unsafe repository path: {raw}")
    resolved = (repo_root / rel).resolve()
    allowed = (repo_root / ALLOWED_DATA_ROOT).resolve()
    if allowed not in resolved.parents:
        raise ValueError(f"data path must be under {ALLOWED_DATA_ROOT}: {raw}")
    return resolved


def _bars(path: Path) -> list[dict[str, Any]]:
    required = ["Date", "Open", "High", "Low", "Close", "Volume"]
    df = pd.read_csv(path)
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"{path} missing {sorted(missing)}")
    df = df[required].copy()
    if len(df) < 260:
        raise ValueError(f"{path} requires at least 260 rows")
    return df.to_dict(orient="records")


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
    assets = request.get("assets")
    if not isinstance(assets, dict) or set(assets) != set(ASSETS):
        raise ValueError(f"assets must be exactly {ASSETS}")

    payload = {
        "schema_version": "1.0",
        "request_id": request["request_id"],
        "created_at": request["created_at"],
        "source": "IBKR",
        "bar_status": request.get("bar_status", "LATEST_RTH_CLOSE"),
        "model_commit": request.get("model_commit", ""),
        "assets": {},
    }
    for symbol in ASSETS:
        item = assets[symbol]
        bars_path = _safe_repo_path(repo_root, item["bars_path"])
        out = {"bars": _bars(bars_path), "snapshot": item.get("snapshot", {})}
        if item.get("features_path"):
            out["features"] = _features(_safe_repo_path(repo_root, item["features_path"]))
        payload["assets"][symbol] = out
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
    print(json.dumps({"request_id": payload["request_id"], "assets": list(payload["assets"])}, sort_keys=True))


if __name__ == "__main__":
    main()
