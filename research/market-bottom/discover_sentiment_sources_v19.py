#!/usr/bin/env python3
"""Discover reproducible options-sentiment inputs for bottom research v1.9."""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UA = "Mozilla/5.0 market-bottom-research/1.9"


def _json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def _text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read().decode("utf-8", errors="replace")


def yahoo_probe(symbol: str) -> dict[str, Any]:
    params = urllib.parse.urlencode(
        {
            "period1": 0,
            "period2": int(time.time()) + 86400,
            "interval": "1d",
            "events": "div,splits",
            "includeAdjustedClose": "true",
        }
    )
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?{params}"
    try:
        payload = _json(url)
        chart = payload.get("chart", {})
        result = (chart.get("result") or [None])[0]
        timestamps = [] if result is None else result.get("timestamp") or []
        meta = {} if result is None else result.get("meta") or {}
        return {
            "symbol": symbol,
            "available": bool(result and len(timestamps) >= 260 and not chart.get("error")),
            "row_count": len(timestamps),
            "first_trade_date": meta.get("firstTradeDate"),
            "instrument_type": meta.get("instrumentType"),
            "error": chart.get("error"),
        }
    except Exception as exc:
        return {"symbol": symbol, "available": False, "error": repr(exc)}


def cboe_page(date: str) -> dict[str, Any]:
    url = "https://www.cboe.com/markets/us/options/market-statistics/daily?" + urllib.parse.urlencode({"dt": date})
    try:
        html = _text(url)
        labels = [
            "TOTAL PUT/CALL RATIO",
            "INDEX PUT/CALL RATIO",
            "EXCHANGE TRADED PRODUCTS PUT/CALL RATIO",
            "EQUITY PUT/CALL RATIO",
            "CBOE VOLATILITY INDEX (VIX) PUT/CALL RATIO",
        ]
        values = {}
        for label in labels:
            pattern = re.compile(re.escape(label) + r".{0,300}?([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE | re.DOTALL)
            match = pattern.search(html)
            values[label] = None if not match else float(match.group(1))
        links = sorted(set(re.findall(r"href=[\"']([^\"']+)", html, flags=re.IGNORECASE)))
        csv_links = [link for link in links if "csv" in link.lower() or "download" in link.lower()]
        return {
            "date": date,
            "url": url,
            "html_bytes": len(html.encode("utf-8")),
            "ratios": values,
            "csv_or_download_links": csv_links,
        }
    except Exception as exc:
        return {"date": date, "url": url, "error": repr(exc)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    yahoo_symbols = ["^CPC", "^CPCE", "^CPCI", "^SKEW", "^VIX9D", "^VVIX"]
    dates = ["2019-12-31", "2020-03-16", "2022-06-16", "2024-08-05", "2025-03-10"]
    payload = {
        "schema_version": "1.0",
        "classification": "OPTIONS SENTIMENT SOURCE DISCOVERY — NO FEATURE SELECTED",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "yahoo_symbol_probes": [yahoo_probe(symbol) for symbol in yahoo_symbols],
        "cboe_daily_page_probes": [cboe_page(date) for date in dates],
        "governance": {
            "official_cboe_daily_page": True,
            "bulk_history_verified": False,
            "date_by_date_scrape_allowed_for_production": False,
            "third_party_or_yahoo_symbols_are_research_proxies_only": True,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
