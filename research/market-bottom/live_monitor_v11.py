#!/usr/bin/env python3
"""Deterministic market-bottom live engine v1.1.

v1.1 retains the audited indicators and adds:
- strict completed-bar freshness metadata;
- monotonic deployment targets;
- coherent active-episode recovery state;
- one volatility-normalised recovery micro-probe per episode.

It never connects to IBKR and never creates an order.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from backtest import episode_ids, indicators, load_config
from live_monitor import (
    PRIMARY,
    REQUIRED,
    REFERENCE,
    SCHEMA_VERSION,
    STATE_NAMES,
    _bars_frame,
    _canonical_hash,
    _features_frame,
    _finite,
    _material_changes,
    _pair,
    _validate_payload,
)
from recovery_v11 import add_recovery_features, candidate_v11, run_v11, state_v11


def _date_only(value: Any) -> str:
    return pd.Timestamp(value).date().isoformat()


def _data_quality(payload: dict[str, Any]) -> dict[str, Any]:
    expected = payload.get("expected_completed_rth_date")
    latest_dates: dict[str, str] = {}
    bars_sources: dict[str, str] = {}

    for symbol in REQUIRED:
        item = payload["assets"][symbol]
        bars = _bars_frame(item["bars"])
        latest_dates[symbol] = _date_only(bars.iloc[-1].Date)
        snapshot = item.get("snapshot") or {}
        bars_sources[symbol] = str(
            item.get("bars_source")
            or snapshot.get("historical_bars_source")
            or "UNSPECIFIED"
        )

    same_completed_date = len(set(latest_dates.values())) == 1
    freshness_verified = bool(
        expected
        and same_completed_date
        and all(d == str(expected) for d in latest_dates.values())
    )
    ibkr_bars_verified = all(
        source == "IBKR" or source.startswith("IBKR_")
        for source in bars_sources.values()
    )
    official_eligible = bool(
        payload.get("source") == "IBKR"
        and freshness_verified
        and ibkr_bars_verified
    )
    return {
        "expected_completed_rth_date": expected,
        "latest_completed_bar_dates": latest_dates,
        "bars_sources": bars_sources,
        "same_completed_date": same_completed_date,
        "freshness_verified": freshness_verified,
        "ibkr_bars_verified": ibkr_bars_verified,
        "official_eligible": official_eligible,
    }


def validate_payload_v11(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate the legacy payload plus v1.1 freshness requirements."""
    _validate_payload(payload)
    quality = _data_quality(payload)
    expected = quality["expected_completed_rth_date"]
    if expected and not quality["same_completed_date"]:
        raise ValueError(
            "completed daily bars are not aligned across SPY, QQQ, SOXX and SMH"
        )
    if expected and not quality["freshness_verified"]:
        raise ValueError(
            "latest completed bar date does not match expected_completed_rth_date"
        )
    return quality


def _asset_result_v11(
    symbol: str,
    item: dict[str, Any],
    config_path: Path,
) -> tuple[dict[str, Any], pd.DataFrame]:
    cfg = load_config(config_path, symbol)
    df = _bars_frame(item["bars"])
    features = _features_frame(item.get("features"))
    x = indicators(df, cfg, features)
    x = add_recovery_features(x, cfg)
    x["episode"] = episode_ids(x, cfg)
    trades, _ = run_v11(x, cfg)
    candidate = candidate_v11(x, trades, cfg)

    latest, prior = x.iloc[-1], x.iloc[-2]
    state = state_v11(
        latest,
        prior,
        cfg,
        float(candidate["cumulative_model_deployment"]),
    )
    cycle_high = float(latest.cycle_high)
    atr = float(latest.atr14)
    prior_low20 = _finite(latest.prior_low20)

    result = {
        "symbol": symbol,
        "official_bar_date": latest.Date.date().isoformat(),
        "official_close": float(latest.Close),
        "state": state,
        "state_name": STATE_NAMES[state],
        "cycle_high": cycle_high,
        "cycle_drawdown": float(latest.cycle_dd),
        "drawdown_52w": float(latest.dd_52w),
        "returns": {
            f"r{n}": _finite(latest.get(f"r{n}"))
            for n in (1, 3, 5, 10, 20, 63)
        },
        "atr14": atr,
        "atr_percent": float(latest.atrp),
        "realized_vol_20d": float(latest.rv20),
        "volume_ratio_20d": float(latest.vol_ratio),
        "close_location": float(latest.close_loc),
        "sell_pressure": float(latest.sell_pressure),
        "underwater_days": int(latest.underwater),
        "long_bear": bool(latest.long_bear),
        "new_low_10d": bool(latest.newlow10),
        "new_low_20d": bool(latest.newlow20),
        "crash": bool(latest.crash),
        "exhaustion": bool(latest.exhaustion),
        "exhaustion_score": int(latest.exhaustion_score),
        "confirmation": bool(latest.confirmation),
        "confirmation_score": int(latest.confirmation_score),
        "credit_veto": bool(latest.credit_veto),
        "levels": {
            "watch": cycle_high * (1 - cfg.watch_dd),
            "probe_start": cycle_high * (1 - cfg.start_dd),
            "prior_low_20d": prior_low20,
            "reclaim_sma10": _finite(latest.sma10),
            "reclaim_sma20": _finite(latest.sma20),
            "provisional_failure_close": (
                None if prior_low20 is None else prior_low20 - atr
            ),
        },
        "model": asdict(cfg),
        "snapshot": item.get("snapshot", {}),
        **candidate,
    }
    return result, x


def _markdown_v11(result: dict[str, Any]) -> str:
    q = result["data_quality"]
    lines = [
        "# Bottom Zone Monitor v1.1 — deterministic result",
        "",
        f"- Request: `{result['request_id']}`",
        f"- Input source: `{result['source']}`",
        f"- Model commit: `{result['model_commit']}`",
        f"- Input SHA256: `{result['input_sha256']}`",
        f"- Official eligible: `{result['official_eligible']}`",
        f"- Expected completed RTH date: `{q['expected_completed_rth_date']}`",
        f"- Latest bar dates: `{json.dumps(q['latest_completed_bar_dates'], sort_keys=True)}`",
        f"- Bars sources: `{json.dumps(q['bars_sources'], sort_keys=True)}`",
        "",
        "| Asset | Close | Cycle DD | State | Candidate | Cumulative | Recovery probe |",
        "|---|---:|---:|---|---:|---:|---|",
    ]
    for symbol in PRIMARY:
        a = result["assets"][symbol]
        lines.append(
            f"| {symbol} | {a['official_close']:.2f} | {a['cycle_drawdown']:.2%} | "
            f"{a['state']} {a['state_name']} | {a['candidate_tranche']:.2%} | "
            f"{a['cumulative_model_deployment']:.2%} | {a['recovery_probe']} |"
        )
    smh = result["assets"][REFERENCE]
    lines.extend(
        [
            "",
            "## SMH reference",
            f"SMH close {smh['official_close']:.2f}; drawdown "
            f"{smh['cycle_drawdown']:.2%}; state {smh['state']} "
            f"{smh['state_name']}; production tranche remains zero.",
            "",
            "## Semiconductor pair",
            f"`{result['semiconductor_pair']['classification']}` — informational only.",
            "",
            "## Material changes",
        ]
    )
    if result["material_changes"]:
        lines.extend(
            f"- `{json.dumps(c, ensure_ascii=False, sort_keys=True)}`"
            for c in result["material_changes"]
        )
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "> Research signal only. No order is created or transmitted.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--previous", type=Path)
    ap.add_argument("--result", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()

    payload = json.loads(args.input.read_text())
    quality = validate_payload_v11(payload)
    previous = None
    if args.previous and args.previous.exists():
        previous = json.loads(args.previous.read_text())

    assets: dict[str, Any] = {}
    frames: dict[str, pd.DataFrame] = {}
    for symbol in REQUIRED:
        assets[symbol], frames[symbol] = _asset_result_v11(
            symbol,
            payload["assets"][symbol],
            args.config,
        )

    assets[REFERENCE]["candidate_tranche"] = 0.0
    assets[REFERENCE]["eligible_at_next_open"] = False
    assets[REFERENCE]["candidate_reason"] = "REFERENCE_ONLY"

    # A calculation may still be useful as a provisional fallback when data quality
    # is not official.  It must not manufacture an official tranche.
    if not quality["official_eligible"]:
        for symbol in PRIMARY:
            assets[symbol]["candidate_tranche"] = 0.0
            assets[symbol]["eligible_at_next_open"] = False
            assets[symbol]["candidate_reason"] = "INPUT_NOT_OFFICIAL"
            assets[symbol]["candidate_target_cumulative"] = assets[symbol][
                "cumulative_model_deployment"
            ]

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "engine_version": "1.1",
        "request_id": payload.get("request_id", "UNSPECIFIED"),
        "source": payload.get("source", "UNKNOWN"),
        "input_created_at": payload.get("created_at"),
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "bar_status": payload.get("bar_status", "LATEST_RTH_CLOSE"),
        "model_commit": os.environ.get(
            "GITHUB_SHA",
            payload.get("model_commit", "LOCAL"),
        ),
        "input_sha256": _canonical_hash(payload),
        "classification": (
            "AUDITED_PROVISIONAL_RESEARCH_SIGNAL"
            if quality["official_eligible"]
            else "PROVISIONAL_INPUT_NOT_OFFICIAL"
        ),
        "official_eligible": quality["official_eligible"],
        "data_quality": quality,
        "assets": assets,
        "semiconductor_pair": _pair(
            assets["SOXX"],
            assets["SMH"],
            frames,
        ),
    }
    result["material_changes"] = _material_changes(previous, result)
    if previous and bool(previous.get("official_eligible")) != bool(
        result["official_eligible"]
    ):
        result["material_changes"].append(
            {
                "type": "DATA_QUALITY",
                "old": previous.get("official_eligible"),
                "new": result["official_eligible"],
            }
        )
    result["material_change"] = bool(result["material_changes"])

    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, default=str) + "\n"
    )
    args.report.write_text(_markdown_v11(result))
    print(
        json.dumps(
            {
                "request_id": result["request_id"],
                "official_eligible": result["official_eligible"],
                "material_change": result["material_change"],
                "states": {s: assets[s]["state"] for s in PRIMARY},
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
