#!/usr/bin/env python3
"""Inspect exact OFR FSI CSV and STFM API payload schemas before parsing."""
from __future__ import annotations

import argparse
import csv
import io
import json
import urllib.parse
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 market-bottom-research/1.7"


def _bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def _json(url: str):
    return json.loads(_bytes(url))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    fsi_url = "https://www.financialresearch.gov/financial-stress-index/data/fsi.csv"
    raw = _bytes(fsi_url)
    text = raw.decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))

    mnemonics = [
        "FNYR-SOFR-A",
        "FNYR-SOFR_1Pctl-A",
        "FNYR-SOFR_99Pctl-A",
        "FNYR-BGCR-A",
        "REPO-DVP_AR_OO-P",
        "REPO-DVP_OV_OO-P",
        "NYPD-PD_AFtD_TOT-A",
        "NYPD-PD_AFtD_CORS-A",
    ]
    series = {}
    for mnemonic in mnemonics:
        url = "https://data.financialresearch.gov/v1/series/full?" + urllib.parse.urlencode(
            {"mnemonic": mnemonic, "start_date": "2026-06-01"}
        )
        try:
            payload = _json(url)
            series[mnemonic] = {
                "top_type": type(payload).__name__,
                "top_keys": list(payload.keys())[:20] if isinstance(payload, dict) else None,
                "payload": payload,
            }
        except Exception as exc:
            series[mnemonic] = {"error": repr(exc)}

    out = {
        "fsi": {
            "url": fsi_url,
            "bytes": len(raw),
            "header": rows[0] if rows else None,
            "first_rows": rows[:5],
            "last_rows": rows[-5:],
        },
        "ofr_series": series,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, default=str) + "\n")
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
