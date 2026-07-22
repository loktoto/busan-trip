from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

FOCUSED_MEMBERS = {
    "MAGS7": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA"],
    "MAGS10": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "AMD", "PLTR"],
}

_base_download_all = download_all


def _quarterly_equal_weight_ohlc(data: dict[str, pd.DataFrame], members: list[str], name: str) -> pd.DataFrame:
    missing = [member for member in members if member not in data]
    if missing:
        raise RuntimeError(f"{name}: missing members {missing}")

    common = data[members[0]].index
    for member in members[1:]:
        common = common.intersection(data[member].index)
    common = common.sort_values()
    if len(common) < 252:
        raise RuntimeError(f"{name}: only {len(common)} common bars")

    fields: dict[str, pd.DataFrame] = {}
    for field in ["Open", "High", "Low", "Close", "Volume"]:
        fields[field] = pd.concat(
            {member: data[member][field].reindex(common) for member in members}, axis=1
        )

    previous_close = fields["Close"].shift(1)
    valid = previous_close.notna().all(axis=1) & fields["Close"].notna().all(axis=1)
    common = common[valid]
    for field in fields:
        fields[field] = fields[field].reindex(common)
    previous_close = fields["Close"].shift(1)

    output = pd.DataFrame(index=common, columns=["Open", "High", "Low", "Close", "Volume"], dtype=float)
    weights = np.full(len(members), 1.0 / len(members))
    level = 100.0
    previous_quarter: tuple[int, int] | None = None

    for position, date in enumerate(common):
        quarter = (date.year, (date.month - 1) // 3 + 1)
        if position == 0:
            output.iloc[position] = [level, level, level, level, float(fields["Volume"].iloc[position].fillna(0).sum())]
            previous_quarter = quarter
            continue
        if quarter != previous_quarter:
            weights = np.full(len(members), 1.0 / len(members))
            previous_quarter = quarter

        prior = previous_close.iloc[position].to_numpy(dtype=float)
        ratios = {
            field: fields[field].iloc[position].to_numpy(dtype=float) / prior
            for field in ["Open", "High", "Low", "Close"]
        }
        if not np.isfinite(prior).all() or (prior <= 0).any() or not all(
            np.isfinite(values).all() for values in ratios.values()
        ):
            continue

        open_ratio = float(np.dot(weights, ratios["Open"]))
        high_ratio = float(np.dot(weights, ratios["High"]))
        low_ratio = float(np.dot(weights, ratios["Low"]))
        close_ratio = float(np.dot(weights, ratios["Close"]))
        basket_open = level * open_ratio
        basket_close = level * close_ratio
        output.iloc[position] = [
            basket_open,
            level * max(high_ratio, open_ratio, close_ratio),
            level * min(low_ratio, open_ratio, close_ratio),
            basket_close,
            float(fields["Volume"].iloc[position].fillna(0).sum()),
        ]

        drifted = weights * ratios["Close"]
        weights = drifted / drifted.sum()
        level = basket_close

    frame = output.dropna().copy()
    if len(frame) < 252:
        raise RuntimeError(f"{name}: synthetic frame too short ({len(frame)})")
    return frame


def download_all(config: dict[str, Any]) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    synthetic_symbols = set(FOCUSED_MEMBERS)
    download_config = copy.deepcopy(config)
    download_config["assets"] = [
        asset for asset in download_config["assets"] if asset["symbol"] not in synthetic_symbols
    ]

    # Force all basket members into the base downloader without adding them to the research universe.
    for basket_name, members in FOCUSED_MEMBERS.items():
        for member in members:
            download_config["assets"].append(
                {
                    "symbol": member,
                    "kind": "STOCK",
                    "class": f"{basket_name.lower()}_member",
                    "signal": member,
                    "regime": "QQQ",
                    "breadth_num": "QQEW",
                    "breadth_den": "QQQ",
                    "cost_bps": 5,
                    "experimental": True,
                }
            )

    data, manifest = _base_download_all(download_config)
    manifest.setdefault("synthetic", {})
    for basket_name, members in FOCUSED_MEMBERS.items():
        frame = _quarterly_equal_weight_ohlc(data, members, basket_name)
        data[basket_name] = frame
        digest = frame_hash(frame)
        frame.to_csv(INPUT_DIR / f"{basket_name}.csv.gz", compression="gzip")
        manifest["synthetic"][basket_name] = {
            "members": members,
            "method": "equal weight, quarterly rebalance, adjusted OHLC approximation",
            "rows": len(frame),
            "start": str(frame.index.min().date()),
            "end": str(frame.index.max().date()),
            "sha256": digest,
            "last_close": float(frame.Close.iloc[-1]),
        }

    aggregate_lines = []
    for ticker in sorted(manifest.get("tickers", {})):
        aggregate_lines.append(f"{ticker}:{manifest['tickers'][ticker]['sha256']}")
    for ticker in sorted(manifest.get("synthetic", {})):
        aggregate_lines.append(f"{ticker}:{manifest['synthetic'][ticker]['sha256']}")
    manifest["aggregate_sha256"] = hashlib.sha256(("\n".join(aggregate_lines) + "\n").encode()).hexdigest()
    (OUT / "input_manifest.json").write_text(json.dumps(manifest, indent=2))
    return data, manifest
