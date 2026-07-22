#!/usr/bin/env python3
"""Fetch one OFR Short-term Funding Monitor series with an audit manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


BASE = "https://data.financialresearch.gov/v1/series/full"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mnemonic", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--availability-lag-business-days", type=int, required=True)
    args = ap.parse_args()
    if args.availability_lag_business_days < 0:
        raise ValueError("availability lag cannot be negative")

    url = BASE + "?" + urllib.parse.urlencode({"mnemonic": args.mnemonic})
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 market-bottom-research/1.7", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    root = payload.get(args.mnemonic) or payload.get(args.mnemonic.upper())
    if not isinstance(root, dict):
        raise RuntimeError(f"OFR payload missing {args.mnemonic}")
    aggregation = (root.get("timeseries") or {}).get("aggregation")
    if not isinstance(aggregation, list):
        raise RuntimeError("OFR aggregation series is missing")
    frame = pd.DataFrame(aggregation, columns=["Date", "Value"])
    frame["Date"] = pd.to_datetime(frame.Date, errors="coerce")
    frame["Value"] = pd.to_numeric(frame.Value, errors="coerce")
    frame = (
        frame.dropna()
        .sort_values("Date")
        .drop_duplicates("Date", keep="last")
        .reset_index(drop=True)
    )
    if len(frame) < 50:
        raise RuntimeError(f"OFR series returned only {len(frame)} rows")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    csv_bytes = frame.to_csv(index=False).encode("utf-8")
    args.out.write_bytes(csv_bytes)
    metadata = root.get("metadata") or {}
    description = metadata.get("description") or {}
    schedule = metadata.get("schedule") or {}
    manifest = {
        "schema_version": 1,
        "source": "Office of Financial Research Short-term Funding Monitor API",
        "url": url,
        "mnemonic": args.mnemonic,
        "name": description.get("name"),
        "description": description.get("description"),
        "subtype": description.get("subtype"),
        "vintage": description.get("vintage"),
        "vintage_approach": description.get("vintage_approach"),
        "observation_frequency": schedule.get("observation_frequency"),
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "row_count": int(len(frame)),
        "start_date": frame.Date.min().date().isoformat(),
        "end_date": frame.Date.max().date().isoformat(),
        "sha256": hashlib.sha256(csv_bytes).hexdigest(),
        "date_semantics_raw": "ECONOMIC_OBSERVATION_DATE",
        "availability_lag_business_days": args.availability_lag_business_days,
        "revision_policy": (
            "PRELIMINARY_REVISED" if str(description.get("vintage")).lower() == "preliminary"
            else "CURRENT_VINTAGE_NOT_RELEASE_ARCHIVE"
        ),
        "production_promotable": False,
        "role": "OFFICIAL PUBLIC RESEARCH SERIES — SHIFT BEFORE STRATEGY USE",
    }
    args.out.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    print(json.dumps(manifest, indent=2, default=str))


if __name__ == "__main__":
    main()
