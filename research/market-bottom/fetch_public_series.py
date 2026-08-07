#!/usr/bin/env python3
"""Fetch public adjusted close-only daily series for reproducibility research.

Unlike fetch_public_prices.py this helper accepts indices such as VIX/VXN whose
Yahoo chart payloads may omit volume.  It is research-only and never substitutes
for IBKR or a licensed point-in-time feature dataset in production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def yahoo_series(symbol: str, start: int, end: int) -> tuple[pd.DataFrame, dict]:
    params = urllib.parse.urlencode(
        {
            "period1": start,
            "period2": end,
            "interval": "1d",
            "events": "div,splits",
            "includeAdjustedClose": "true",
        }
    )
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?{params}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 market-bottom-research/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    chart = payload.get("chart", {})
    if chart.get("error"):
        raise RuntimeError(f"Yahoo chart error: {chart['error']}")
    result = (chart.get("result") or [None])[0]
    if not result:
        raise RuntimeError("Yahoo chart returned no result")
    timestamps = result.get("timestamp") or []
    quotes = ((result.get("indicators") or {}).get("quote") or [None])[0]
    adjusted = ((result.get("indicators") or {}).get("adjclose") or [None])[0]
    if not timestamps or not quotes:
        raise RuntimeError("Yahoo chart response is missing timestamps/quotes")
    close = np.asarray(quotes.get("close"), dtype=float)
    if adjusted and adjusted.get("adjclose") is not None:
        adj = np.asarray(adjusted.get("adjclose"), dtype=float)
        close = np.where(np.isfinite(adj), adj, close)
    frame = pd.DataFrame(
        {
            "Date": pd.to_datetime(timestamps, unit="s", utc=True).tz_convert(None),
            "Close": close,
        }
    )
    frame = (
        frame.replace([np.inf, -np.inf], np.nan)
        .dropna()
        .sort_values("Date")
        .drop_duplicates("Date", keep="last")
        .reset_index(drop=True)
    )
    if len(frame) < 260:
        raise RuntimeError(f"Only {len(frame)} complete daily rows returned")
    metadata = result.get("meta") or {}
    return frame, {
        "source": "Yahoo Finance chart API",
        "request_url_without_query": f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
        "symbol": symbol,
        "exchange_timezone": metadata.get("exchangeTimezoneName"),
        "instrument_type": metadata.get("instrumentType"),
        "first_trade_date": metadata.get("firstTradeDate"),
        "role": "PUBLIC CLOSE-ONLY REPRODUCIBILITY PROXY — NOT IBKR / NOT LICENSED PIT FEATURE",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=0)
    args = ap.parse_args()

    end = args.end or int(time.time()) + 86400
    frame, manifest = yahoo_series(args.symbol, args.start, end)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    csv_bytes = frame.to_csv(index=False).encode("utf-8")
    args.out.write_bytes(csv_bytes)
    manifest.update(
        {
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "row_count": len(frame),
            "start_date": str(frame.Date.min().date()),
            "end_date": str(frame.Date.max().date()),
            "sha256": hashlib.sha256(csv_bytes).hexdigest(),
        }
    )
    args.out.with_suffix(".manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str)
    )
    print(json.dumps(manifest, indent=2, default=str))


if __name__ == "__main__":
    main()
