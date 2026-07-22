#!/usr/bin/env python3
"""Fetch public adjusted daily OHLCV for reproducibility diagnostics.

This is not a substitute for the audited IBKR holdout. It exists so CI can run a
transparent long-history diagnostic without committing licensed market data.
Source availability failures are explicit and never silently replaced.

A chart provider may expose a provisional daily bar while the exchange session is
still open.  Research signals are completed-close only, so the current exchange-
local session is removed until a conservative post-close buffer has elapsed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, time as clock_time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import numpy as np
import pandas as pd


def _remove_unfinished_exchange_session(
    frame: pd.DataFrame,
    exchange_timezone: str | None,
    now_utc: datetime | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Remove a provisional current-session bar before a 16:30 local cutoff.

    The 30-minute buffer is deliberately conservative.  It prevents a provider's
    intraday aggregate from entering a completed-close backtest while allowing a
    same-day completed bar to be used after the regular session has settled.
    """
    now_utc = now_utc or datetime.now(timezone.utc)
    timezone_name = exchange_timezone or "America/New_York"
    try:
        local_now = now_utc.astimezone(ZoneInfo(timezone_name))
    except ZoneInfoNotFoundError:
        timezone_name = "America/New_York"
        local_now = now_utc.astimezone(ZoneInfo(timezone_name))

    local_date = local_now.date()
    conservative_close = clock_time(16, 30)
    before_close_buffer = local_now.time().replace(tzinfo=None) < conservative_close
    last_date = frame["Date"].max().date() if not frame.empty else None
    drop_current = bool(before_close_buffer and last_date == local_date)

    removed_rows = 0
    removed_date = None
    if drop_current:
        keep = frame["Date"].dt.date < local_date
        removed_rows = int((~keep).sum())
        removed_date = local_date.isoformat()
        frame = frame.loc[keep].copy().reset_index(drop=True)

    return frame, {
        "completed_session_policy": "DROP_CURRENT_EXCHANGE_DATE_BEFORE_16_30_LOCAL",
        "exchange_timezone_effective": timezone_name,
        "retrieval_local_time": local_now.isoformat(),
        "unfinished_session_rows_removed": removed_rows,
        "unfinished_session_date_removed": removed_date,
    }


def yahoo_chart(symbol: str, start: int, end: int) -> tuple[pd.DataFrame, dict]:
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
    if not timestamps or not quotes or not adjusted:
        raise RuntimeError("Yahoo chart response is missing OHLCV or adjusted close")

    raw_close = np.asarray(quotes.get("close"), dtype=float)
    adj_close = np.asarray(adjusted.get("adjclose"), dtype=float)
    factor = np.divide(
        adj_close,
        raw_close,
        out=np.full_like(adj_close, np.nan),
        where=np.isfinite(raw_close) & (raw_close != 0),
    )
    raw_volume = np.asarray(quotes.get("volume"), dtype=float)
    # Inverse adjustment maintains approximate split continuity. Dividend factors
    # slightly rescale old volume and are documented in the manifest.
    adj_volume = np.divide(
        raw_volume,
        factor,
        out=np.full_like(raw_volume, np.nan),
        where=np.isfinite(factor) & (factor != 0),
    )
    frame = pd.DataFrame(
        {
            "Date": pd.to_datetime(timestamps, unit="s", utc=True).tz_convert(None),
            "Open": np.asarray(quotes.get("open"), dtype=float) * factor,
            "High": np.asarray(quotes.get("high"), dtype=float) * factor,
            "Low": np.asarray(quotes.get("low"), dtype=float) * factor,
            "Close": adj_close,
            "Volume": adj_volume,
        }
    )
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna().sort_values("Date")
    # The adjusted close and adjusted high/low can differ by ~1e-15 because the
    # provider serialises them through separate floating-point paths. Clamp only
    # to the mathematically required OHLC envelope; this does not conceal jumps or
    # change any economically meaningful price.
    frame["High"] = frame[["Open", "High", "Low", "Close"]].max(axis=1)
    frame["Low"] = frame[["Open", "High", "Low", "Close"]].min(axis=1)
    frame = frame.drop_duplicates("Date", keep="last").reset_index(drop=True)

    metadata = result.get("meta") or {}
    frame, completed_session_audit = _remove_unfinished_exchange_session(
        frame,
        metadata.get("exchangeTimezoneName"),
    )
    if len(frame) < 260:
        raise RuntimeError(f"Only {len(frame)} complete daily rows returned")
    events = result.get("events") or {}
    manifest = {
        "source": "Yahoo Finance chart API",
        "request_url_without_query": f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
        "symbol": symbol,
        "exchange_timezone": metadata.get("exchangeTimezoneName"),
        "instrument_type": metadata.get("instrumentType"),
        "first_trade_date": metadata.get("firstTradeDate"),
        "events": events,
        "price_adjustment": "OHLC multiplied by AdjClose/Close",
        "ohlc_rounding_clamp": "High=max(OHLC), Low=min(OHLC) after adjustment; floating-point envelope only",
        "volume_adjustment": "raw volume divided by AdjClose/Close; approximate split continuity",
        "role": "PUBLIC REPRODUCIBILITY / LONG-HISTORY DIAGNOSTIC — NOT IBKR HOLDOUT",
    }
    manifest.update(completed_session_audit)
    return frame, manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=0)
    args = ap.parse_args()

    end = args.end or int(time.time()) + 86400
    frame, manifest = yahoo_chart(args.symbol, args.start, end)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    csv_bytes = frame.to_csv(index=False).encode("utf-8")
    args.out.write_bytes(csv_bytes)
    manifest.update(
        {
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "row_count": len(frame),
            "start_date": str(frame["Date"].min().date()),
            "end_date": str(frame["Date"].max().date()),
            "sha256": hashlib.sha256(csv_bytes).hexdigest(),
        }
    )
    manifest_path = args.out.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str))
    print(json.dumps(manifest, indent=2, default=str))


if __name__ == "__main__":
    main()
