#!/usr/bin/env python3
"""Final deterministic governance pass for live bottom results.

This stage does not create new signals. It corrects provenance labelling and
prevents an active, previously deployed episode from being displayed as
NO_SETUP merely because the drawdown recovered above the watch threshold.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


PRIMARY = ("SPY", "QQQ", "SOXX")


def finalize(result: dict) -> dict:
    assets = result.get("assets", {})
    public_bootstrap = any(
        str(assets.get(symbol, {}).get("snapshot", {}).get("historical_bars_source", "")).startswith("PUBLIC_")
        for symbol in assets
    )
    if public_bootstrap:
        result["source"] = "IBKR_SNAPSHOT_PUBLIC_ADJUSTED_BOOTSTRAP"
        result["classification"] = "AUDITED_PROVISIONAL_MIXED_SOURCE_BOOTSTRAP"
        result["data_provenance"] = {
            "live_snapshot": "IBKR",
            "historical_daily_bars": "PUBLIC_ADJUSTED_BOOTSTRAP",
            "promotion_eligible": False,
        }
    else:
        result["data_provenance"] = {
            "live_snapshot": "IBKR",
            "historical_daily_bars": "IBKR_OR_PREVIOUSLY_AUDITED_RUNTIME_FILE",
            "promotion_eligible": True,
        }

    adjustments = []
    for symbol in PRIMARY:
        asset = assets.get(symbol, {})
        used = float(asset.get("cumulative_model_deployment", 0.0) or 0.0)
        target = float(asset.get("candidate_target_cumulative", used) or 0.0)
        if target < used:
            asset["candidate_target_cumulative"] = used
            adjustments.append({"type": "TARGET_FLOOR", "symbol": symbol, "value": used})

        active_episode = int(asset.get("current_episode", 0) or 0) > 0
        recovery_dd = float(asset.get("model", {}).get("recovery_dd", 0.002) or 0.002)
        cycle_dd = float(asset.get("cycle_drawdown", 0.0) or 0.0)
        if (
            asset.get("state") == 0
            and active_episode
            and used > 0
            and cycle_dd < -recovery_dd
        ):
            asset["state"] = 5
            asset["state_name"] = "RECOVERY_UNDERWAY"
            asset["state_adjustment"] = "ACTIVE_DEPLOYED_EPISODE_ABOVE_WATCH_THRESHOLD"
            adjustments.append({"type": "ACTIVE_EPISODE_RECOVERY", "symbol": symbol, "old": 0, "new": 5})

    result["governance_adjustments"] = adjustments
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", type=Path, required=True)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()

    result = finalize(json.loads(args.result.read_text()))
    args.result.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str) + "\n")

    if args.report and args.report.exists():
        text = args.report.read_text()
        text = text.replace("- Input source: `IBKR`", f"- Input source: `{result['source']}`")
        if result.get("governance_adjustments"):
            text += "\n## Governance adjustments\n"
            for item in result["governance_adjustments"]:
                text += f"- `{json.dumps(item, ensure_ascii=False, sort_keys=True)}`\n"
        args.report.write_text(text)

    print(json.dumps({"source": result["source"], "adjustments": result["governance_adjustments"]}, sort_keys=True))


if __name__ == "__main__":
    main()
