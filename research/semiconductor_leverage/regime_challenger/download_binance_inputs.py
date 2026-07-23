from __future__ import annotations

import csv
import hashlib
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


HERE = Path(__file__).resolve().parent
OUT = HERE / "inputs"
OUT.mkdir(parents=True, exist_ok=True)
CUTOFF = "2026-07-22"

SPOT_RANGES = [
    ("2017-08-17", "2020-05-12"),
    ("2020-05-13", "2023-02-06"),
    ("2023-02-07", "2025-11-02"),
    ("2025-11-03", CUTOFF),
]
FUNDING_RANGES = [
    ("2019-09-10", "2020-07-25"),
    ("2020-07-26", "2021-06-10"),
    ("2021-06-11", "2022-04-26"),
    ("2022-04-27", "2023-03-12"),
    ("2023-03-13", "2024-01-26"),
    ("2024-01-27", "2024-12-11"),
    ("2024-12-12", "2025-10-27"),
    ("2025-10-28", CUTOFF),
]


def timestamp_ms(date: str, end: bool = False) -> int:
    parsed = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
    return int(parsed.timestamp() * 1000) + (86_399_999 if end else 0)


def get_json(url: str, params: dict[str, object]) -> object:
    request = Request(
        f"{url}?{urlencode(params)}",
        headers={"User-Agent": "busan-trip-leverage-research/1.0"},
    )
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as error:  # network retry is deliberate and bounded
            last_error = error
            if attempt == 0:
                time.sleep(1)
    raise RuntimeError(f"Binance request failed after one retry: {last_error}")


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> str:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    spot_by_open: dict[int, list[object]] = {}
    for start, end in SPOT_RANGES:
        payload = get_json(
            "https://api.binance.com/api/v3/klines",
            {
                "symbol": "BTCUSDT",
                "interval": "1d",
                "limit": 1000,
                "startTime": timestamp_ms(start),
                "endTime": timestamp_ms(end, end=True),
                "timeZone": "0",
            },
        )
        for row in payload:
            spot_by_open[int(row[0])] = row

    spot_rows: list[list[object]] = []
    for open_time, row in sorted(spot_by_open.items()):
        date = datetime.fromtimestamp(open_time / 1000, tz=timezone.utc).date().isoformat()
        spot_rows.append([date, row[1], row[2], row[3], row[4], row[5], row[7], row[8]])

    funding_by_time: dict[int, dict[str, object]] = {}
    for start, end in FUNDING_RANGES:
        payload = get_json(
            "https://fapi.binance.com/fapi/v1/fundingRate",
            {
                "symbol": "BTCUSDT",
                "limit": 1000,
                "startTime": timestamp_ms(start),
                "endTime": timestamp_ms(end, end=True),
            },
        )
        for row in payload:
            funding_by_time[int(row["fundingTime"])] = row

    funding_daily: dict[str, list[float]] = defaultdict(list)
    for funding_time, row in sorted(funding_by_time.items()):
        date = datetime.fromtimestamp(funding_time / 1000, tz=timezone.utc).date().isoformat()
        funding_daily[date].append(float(row["fundingRate"]))
    funding_rows: list[list[object]] = []
    for date, values in sorted(funding_daily.items()):
        funding_rows.append(
            [
                date,
                format(sum(values) / len(values), ".12g"),
                format(sum(values), ".12g"),
                format(min(values), ".12g"),
                format(max(values), ".12g"),
                len(values),
            ]
        )

    spot_path = OUT / "binance_btcusdt_daily.csv"
    funding_path = OUT / "binance_btcusdt_funding_daily.csv"
    spot_sha = write_csv(
        spot_path,
        ["date", "open", "high", "low", "close", "volume", "quote_volume", "trades"],
        spot_rows,
    )
    funding_sha = write_csv(
        funding_path,
        ["date", "mean_funding", "sum_funding", "min_funding", "max_funding", "observations"],
        funding_rows,
    )
    metadata = {
        "source": "Binance public REST market data",
        "calculation_date": "2026-07-23",
        "cutoff": CUTOFF,
        "btc_spot_rows": len(spot_rows),
        "funding_daily_rows": len(funding_rows),
        "btc_spot_sha256": spot_sha,
        "funding_daily_sha256": funding_sha,
        "timing_rule": "Use only prior fully completed UTC calendar day when aligning to a US equity completed-close signal.",
        "open_interest_rule": "Not persisted or selected: Binance history is limited to the latest 30 days; forward-shadow only.",
        "production_weight": 0,
    }
    (OUT / "binance_source_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
