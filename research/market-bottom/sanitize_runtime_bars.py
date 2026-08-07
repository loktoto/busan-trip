#!/usr/bin/env python3
"""Remove incomplete current-session bars before official live calculation."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

ASSETS = ("SPY", "QQQ", "SOXX", "SMH")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", type=Path, required=True)
    ap.add_argument("--data-dir", type=Path, required=True)
    args = ap.parse_args()

    request = json.loads(args.request.read_text())
    if request.get("bar_status") != "INTRADAY_CONTEXT":
        print(json.dumps({"status": "NO_DROP_LATEST_RTH_CLOSE"}))
        return

    created = datetime.fromisoformat(request["created_at"].replace("Z", "+00:00"))
    market_date = created.astimezone(ZoneInfo("America/New_York")).date()
    report = {}
    for symbol in ASSETS:
        path = args.data_dir / f"{symbol}.csv"
        df = pd.read_csv(path)
        dates = pd.to_datetime(df["Date"], utc=True, errors="raise").dt.date
        keep = dates < market_date
        dropped = int((~keep).sum())
        clean = df.loc[keep].copy()
        if len(clean) < 260:
            raise ValueError(f"{symbol}: fewer than 260 completed bars after intraday drop")
        clean.to_csv(path, index=False)
        report[symbol] = {
            "market_date": market_date.isoformat(),
            "dropped_rows": dropped,
            "last_completed_date": str(pd.to_datetime(clean["Date"], utc=True).dt.date.iloc[-1]),
        }
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
