#!/usr/bin/env python3
"""Discover official/public stress-series inputs for bottom research v1.7.

The script does not select a trading feature.  It inventories OFR funding series,
inspects the OFR FSI page for machine-readable endpoints, tests public Cboe/Yahoo
volatility symbols, and records historical-data access restrictions.  Results are
archived as evidence before any backtest is implemented.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


USER_AGENT = "Mozilla/5.0 market-bottom-research/1.7"


def _json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.load(response)


def _text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read().decode("utf-8", errors="replace")


def ofr_search(query: str) -> list[dict[str, Any]]:
    url = "https://data.financialresearch.gov/v1/metadata/search?" + urllib.parse.urlencode({"query": query})
    payload = _json(url)
    return payload if isinstance(payload, list) else []


def ofr_metadata(mnemonic: str) -> dict[str, Any]:
    url = "https://data.financialresearch.gov/v1/metadata/query?" + urllib.parse.urlencode({"mnemonic": mnemonic})
    payload = _json(url)
    return payload if isinstance(payload, dict) else {}


def _candidate_rows(query: str) -> list[dict[str, Any]]:
    rows = ofr_search(query)
    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []
    for row in rows:
        mnemonic = str(row.get("mnemonic") or "")
        if not mnemonic or mnemonic.lower() == "none" or mnemonic in seen:
            continue
        seen.add(mnemonic)
        try:
            metadata = ofr_metadata(mnemonic)
        except Exception as exc:  # source discovery must preserve failures
            metadata = {"error": repr(exc)}
        candidates.append(
            {
                "mnemonic": mnemonic,
                "dataset": row.get("dataset"),
                "matched_field": row.get("field"),
                "matched_value": row.get("value"),
                "metadata": metadata,
            }
        )
    return candidates


def inspect_fsi_page() -> dict[str, Any]:
    url = "https://www.financialresearch.gov/financial-stress-index/"
    html = _text(url)
    urls = sorted(
        set(
            re.findall(
                r"https?://[^\"'<>\\s]+|/[A-Za-z0-9_./?=&%+-]+(?:csv|json|xlsx|download)[A-Za-z0-9_./?=&%+-]*",
                html,
                flags=re.IGNORECASE,
            )
        )
    )
    relevant = [u for u in urls if any(k in u.lower() for k in ("fsi", "stress", "csv", "json", "download"))]
    script_src = sorted(set(re.findall(r"<script[^>]+src=[\"']([^\"']+)", html, flags=re.IGNORECASE)))
    return {
        "url": url,
        "html_bytes": len(html.encode("utf-8")),
        "candidate_urls": relevant[:200],
        "script_sources": script_src,
        "contains_download_all_data": "Download all data" in html,
    }


def yahoo_symbol_probe(symbol: str) -> dict[str, Any]:
    params = urllib.parse.urlencode(
        {
            "period1": 0,
            "period2": int(datetime.now(timezone.utc).timestamp()) + 86400,
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
        error = chart.get("error")
        timestamps = [] if result is None else result.get("timestamp") or []
        meta = {} if result is None else result.get("meta") or {}
        return {
            "symbol": symbol,
            "available": bool(result and len(timestamps) >= 260 and not error),
            "row_count": len(timestamps),
            "first_trade_date": meta.get("firstTradeDate"),
            "exchange_timezone": meta.get("exchangeTimezoneName"),
            "instrument_type": meta.get("instrumentType"),
            "error": error,
        }
    except Exception as exc:
        return {"symbol": symbol, "available": False, "error": repr(exc)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    queries = {
        "fails_to_deliver": "*Fails to Deliver*",
        "repo_average_rate": "*Average Rate*",
        "repo_volume": "*Repo*Volume*",
        "secured_financing": "*Secured*Financing*",
        "reference_rates": "*Reference Rate*",
        "primary_dealer_financing": "*Primary Dealer*Financing*",
    }
    ofr: dict[str, Any] = {}
    for key, query in queries.items():
        try:
            ofr[key] = _candidate_rows(query)
        except Exception as exc:
            ofr[key] = {"error": repr(exc)}

    try:
        fsi = inspect_fsi_page()
    except Exception as exc:
        fsi = {"error": repr(exc)}

    yahoo_symbols = ["^VIX", "^VIX3M", "^VIX9D", "^VVIX", "^VXN", "^MOVE", "^SKEW"]
    yahoo = [yahoo_symbol_probe(symbol) for symbol in yahoo_symbols]

    payload = {
        "schema_version": "1.0",
        "classification": "SOURCE DISCOVERY ONLY — NO TRADING FEATURE SELECTED",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "ofr_api": {
            "base_url": "https://data.financialresearch.gov/v1",
            "token_required": False,
            "queries": queries,
            "results": ofr,
        },
        "ofr_fsi_page": fsi,
        "public_volatility_symbol_probes": yahoo,
        "cboe_access_governance": {
            "correlation_indices": ["COR1M", "COR3M"],
            "dispersion_indices": ["DSPX", "VIXEQ"],
            "historical_data_status": "VERIFY_PUBLIC_DOWNLOAD_OR_TREAT_AS_DATASHOP_LICENSED",
            "do_not_scrape_streaming_feed": True,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
