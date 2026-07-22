#!/usr/bin/env python3
"""Deterministic live monitor v1.5 reporting layer.

Trading calculations remain v1.1.  V1.5 adds a non-trading taxonomy separating
staged participation, local swing recovery and cycle-bottom evidence.  The new
metadata cannot create or resize a tranche and cannot authorise leverage.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from bottom_taxonomy_v15 import classify_bottom_taxonomy
from live_monitor import PRIMARY, REFERENCE, REQUIRED, SCHEMA_VERSION, _canonical_hash, _material_changes, _pair
from live_monitor_v11 import _asset_result_v11, validate_payload_v11


def _taxonomy_change(previous: dict[str, Any] | None, result: dict[str, Any]) -> list[dict[str, Any]]:
    if not previous:
        return []
    changes: list[dict[str, Any]] = []
    for symbol in PRIMARY:
        old = previous.get("assets", {}).get(symbol, {}).get("bottom_taxonomy", {})
        new = result["assets"][symbol]["bottom_taxonomy"]
        for field in ("participation_status", "local_swing_status", "cycle_bottom_status"):
            if old.get(field) != new.get(field):
                changes.append(
                    {
                        "type": "BOTTOM_TAXONOMY",
                        "symbol": symbol,
                        "field": field,
                        "old": old.get(field),
                        "new": new.get(field),
                    }
                )
    return changes


def _markdown(result: dict[str, Any]) -> str:
    q = result["data_quality"]
    lines = [
        "# Bottom Monitor v1.5 — participation, swing and cycle taxonomy",
        "",
        f"- Request: `{result['request_id']}`",
        f"- Input source: `{result['source']}`",
        f"- Trading engine: `{result['trading_engine_version']}`",
        f"- Reporting engine: `{result['engine_version']}`",
        f"- Model commit: `{result['model_commit']}`",
        f"- Input SHA256: `{result['input_sha256']}`",
        f"- Official eligible: `{result['official_eligible']}`",
        f"- Expected completed RTH date: `{q['expected_completed_rth_date']}`",
        "",
        "| Asset | Close | Cycle DD | Trading state | Candidate | Simulated deployment | Participation | Local swing | Cycle bottom |",
        "|---|---:|---:|---|---:|---:|---|---|---|",
    ]
    for symbol in PRIMARY:
        a = result["assets"][symbol]
        t = a["bottom_taxonomy"]
        lines.append(
            f"| {symbol} | {a['official_close']:.2f} | {a['cycle_drawdown']:.2%} | "
            f"{a['state']} {a['state_name']} | {a['candidate_tranche']:.2%} | "
            f"{a['cumulative_model_deployment']:.2%} | {t['participation_status']} | "
            f"{t['local_swing_status']} | {t['cycle_bottom_status']} |"
        )
    lines.extend(["", "## Evidence gaps"])
    for symbol in PRIMARY:
        gaps = result["assets"][symbol]["bottom_taxonomy"]["evidence_gaps"]
        lines.append(f"- **{symbol}:** " + (", ".join(gaps) if gaps else "None"))
    smh = result["assets"][REFERENCE]
    lines.extend(
        [
            "",
            "## SMH reference",
            f"SMH close {smh['official_close']:.2f}; drawdown {smh['cycle_drawdown']:.2%}; "
            "production tranche remains zero.",
            "",
            "## Governance",
            "- Bottom taxonomy is reporting-only and has no trade authority.",
            "- `LOCAL_SWING_RECOVERY` is not equivalent to a confirmed cycle bottom.",
            "- QQQ/SOXX cycle-bottom and leverage rules remain unpromoted pending point-in-time feature ablation.",
            "- Model-simulated deployment is not evidence of user execution.",
            "",
            "## Material changes",
        ]
    )
    if result["material_changes"]:
        lines.extend(
            f"- `{json.dumps(change, ensure_ascii=False, sort_keys=True)}`"
            for change in result["material_changes"]
        )
    else:
        lines.append("- None")
    lines.extend(["", "> Research signal only. No order is created or transmitted."])
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
    previous = (
        json.loads(args.previous.read_text())
        if args.previous and args.previous.exists()
        else None
    )

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

    if not quality["official_eligible"]:
        for symbol in PRIMARY:
            assets[symbol]["candidate_tranche"] = 0.0
            assets[symbol]["eligible_at_next_open"] = False
            assets[symbol]["candidate_reason"] = "INPUT_NOT_OFFICIAL"
            assets[symbol]["candidate_target_cumulative"] = assets[symbol][
                "cumulative_model_deployment"
            ]

    provenance = bool(payload.get("feature_provenance_verified", False))
    for symbol in REQUIRED:
        assets[symbol]["bottom_taxonomy"] = classify_bottom_taxonomy(
            symbol,
            frames[symbol],
            assets[symbol],
            feature_provenance_verified=provenance,
        )

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "engine_version": "1.5-reporting",
        "trading_engine_version": "1.1",
        "request_id": payload.get("request_id", "UNSPECIFIED"),
        "source": payload.get("source", "UNKNOWN"),
        "input_created_at": payload.get("created_at"),
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "bar_status": payload.get("bar_status", "LATEST_RTH_CLOSE"),
        "model_commit": os.environ.get("GITHUB_SHA", payload.get("model_commit", "LOCAL")),
        "input_sha256": _canonical_hash(payload),
        "classification": (
            "AUDITED_PROVISIONAL_RESEARCH_SIGNAL_WITH_TAXONOMY"
            if quality["official_eligible"]
            else "PROVISIONAL_INPUT_NOT_OFFICIAL_WITH_TAXONOMY"
        ),
        "official_eligible": quality["official_eligible"],
        "data_quality": quality,
        "assets": assets,
        "semiconductor_pair": _pair(assets["SOXX"], assets["SMH"], frames),
    }
    result["material_changes"] = _material_changes(previous, result)
    result["material_changes"].extend(_taxonomy_change(previous, result))
    if previous and bool(previous.get("official_eligible")) != bool(result["official_eligible"]):
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
    args.result.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str) + "\n")
    args.report.write_text(_markdown(result))
    print(
        json.dumps(
            {
                "request_id": result["request_id"],
                "official_eligible": result["official_eligible"],
                "material_change": result["material_change"],
                "taxonomy": {
                    s: {
                        "local": assets[s]["bottom_taxonomy"]["local_swing_status"],
                        "cycle": assets[s]["bottom_taxonomy"]["cycle_bottom_status"],
                    }
                    for s in PRIMARY
                },
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
