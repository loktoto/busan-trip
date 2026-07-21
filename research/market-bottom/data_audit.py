#!/usr/bin/env python3
"""Price-data integrity checks for adjusted ETF OHLCV histories."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def audit_price_continuity(
    prices: pd.DataFrame,
    max_unexplained_jump: float = 0.45,
) -> tuple[pd.DataFrame, dict]:
    """Detect split-like discontinuities and malformed price rows.

    The input is expected to be split-adjusted. A simultaneous overnight and
    close-to-close move beyond the threshold is treated as a likely unadjusted
    corporate action. This is a data-quality veto, not a market signal.
    """
    required = {"Date", "Open", "High", "Low", "Close", "Volume"}
    missing = required - set(prices)
    if missing:
        raise ValueError(f"Missing price columns: {sorted(missing)}")
    x = prices.copy().sort_values("Date").reset_index(drop=True)
    x["Date"] = pd.to_datetime(x.Date).dt.tz_localize(None)
    prev = x.Close.shift(1)
    x["overnight_jump"] = x.Open / prev - 1
    x["close_jump"] = x.Close / prev - 1
    split_like = (
        x.overnight_jump.abs().gt(max_unexplained_jump)
        & x.close_jump.abs().gt(max_unexplained_jump)
    )
    malformed = (
        (x[["Open", "High", "Low", "Close"]] <= 0).any(axis=1)
        | (x.Volume < 0)
        | (x.High < x[["Open", "Close", "Low"]].max(axis=1))
        | (x.Low > x[["Open", "Close", "High"]].min(axis=1))
    )
    duplicate = x.Date.duplicated(keep=False)
    issues = x.loc[split_like | malformed | duplicate, [
        "Date", "Open", "High", "Low", "Close", "Volume", "overnight_jump", "close_jump"
    ]].copy()
    issues["split_like"] = split_like.loc[issues.index].to_numpy(bool)
    issues["malformed_ohlcv"] = malformed.loc[issues.index].to_numpy(bool)
    issues["duplicate_date"] = duplicate.loc[issues.index].to_numpy(bool)
    summary = {
        "classification": "DATA INTEGRITY AUDIT — NOT A TRADING SIGNAL",
        "rows": int(len(x)),
        "start": str(x.Date.min().date()) if len(x) else None,
        "end": str(x.Date.max().date()) if len(x) else None,
        "issue_count": int(len(issues)),
        "split_like_count": int(split_like.sum()),
        "malformed_count": int(malformed.sum()),
        "duplicate_count": int(duplicate.sum()),
        "max_unexplained_jump": max_unexplained_jump,
        "clean": bool(issues.empty),
    }
    return issues, summary


def assert_price_continuity(prices: pd.DataFrame, max_unexplained_jump: float = 0.45) -> None:
    issues, summary = audit_price_continuity(prices, max_unexplained_jump)
    if not issues.empty:
        dates = ", ".join(str(d.date()) for d in issues.Date.head(5))
        raise ValueError(
            "Price continuity audit failed; likely unadjusted split/corporate action "
            f"or malformed OHLCV near {dates}. Summary={summary}"
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, required=True)
    ap.add_argument("--max-jump", type=float, default=0.45)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    prices = pd.read_csv(a.csv)
    issues, summary = audit_price_continuity(prices, a.max_jump)
    payload = json.dumps(summary, indent=2)
    if a.out:
        a.out.mkdir(parents=True, exist_ok=True)
        issues.to_csv(a.out / "data_issues.csv", index=False)
        (a.out / "data_audit.json").write_text(payload)
    print(payload)
    if not summary["clean"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
