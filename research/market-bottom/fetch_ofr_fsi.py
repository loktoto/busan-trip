#!/usr/bin/env python3
"""Fetch the official OFR Financial Stress Index CSV for research.

The public file is current revised history.  It is useful for reproducible feature
screening but not a point-in-time vintage archive.  Strategy availability must be
shifted by two business days downstream, per OFR's publication note.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


URL = "https://www.financialresearch.gov/financial-stress-index/data/fsi.csv"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "Mozilla/5.0 market-bottom-research/1.7"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        raw = response.read()
    frame = pd.read_csv(pd.io.common.BytesIO(raw))
    required = {
        "Date",
        "OFR FSI",
        "Credit",
        "Equity valuation",
        "Safe assets",
        "Funding",
        "Volatility",
        "United States",
        "Other advanced economies",
        "Emerging markets",
    }
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"OFR FSI missing columns: {sorted(missing)}")
    frame["Date"] = pd.to_datetime(frame.Date, errors="coerce")
    for column in frame.columns:
        if column != "Date":
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = (
        frame.dropna()
        .sort_values("Date")
        .drop_duplicates("Date", keep="last")
        .reset_index(drop=True)
    )
    if len(frame) < 1000:
        raise RuntimeError(f"OFR FSI returned only {len(frame)} rows")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    csv_bytes = frame.to_csv(index=False).encode("utf-8")
    args.out.write_bytes(csv_bytes)
    manifest = {
        "schema_version": 1,
        "source": "Office of Financial Research Financial Stress Index",
        "url": URL,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "row_count": int(len(frame)),
        "start_date": frame.Date.min().date().isoformat(),
        "end_date": frame.Date.max().date().isoformat(),
        "sha256": hashlib.sha256(csv_bytes).hexdigest(),
        "date_semantics_raw": "ECONOMIC_OBSERVATION_DATE",
        "availability_lag_business_days": 2,
        "revision_policy": "CURRENT_REVISED_HISTORY_NOT_VINTAGE_ARCHIVE",
        "production_promotable": False,
        "role": "PUBLIC OFFICIAL RESEARCH PROXY — SHIFT BEFORE STRATEGY USE",
    }
    args.out.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
