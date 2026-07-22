#!/usr/bin/env python3
"""Apply asset-level decision gates to dual-path v1.2 backtest output.

The generic validator checks that v1.2 does not materially damage the ordinary
portfolio path.  That is insufficient when a candidate rarely fires.  This
post-processor explicitly evaluates the catch-up trades and the missed-alert
stress test, preventing a no-op strategy from passing by default.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _asset_decision(symbol: str, report: dict[str, Any]) -> dict[str, Any]:
    v12 = report["variants"]["V1_2_POST_THRESHOLD"]
    full_catchup = v12["full_history"]["catchup"]
    recent_stress = report["missed_first_alert_stress"]["ibkr_recent_window"]
    baseline_recent = report["variants"]["BASELINE"]["ibkr_recent_window"]

    failures: list[str] = []
    positives: list[str] = []
    count = int(full_catchup.get("trade_count", 0) or 0)
    distance = _number(full_catchup.get("mean_distance_to_episode_trough"))
    downside = _number(full_catchup.get("mean_additional_downside"))
    forward63 = _number(full_catchup.get("mean_forward_63d"))

    if count < 3:
        failures.append("FEWER_THAN_3_FULL_HISTORY_CATCHUPS")
    if distance is not None and distance > 0.08:
        failures.append(f"CATCHUP_DISTANCE_TOO_HIGH_{distance:.4f}")
    if downside is not None and downside < -0.08:
        failures.append(f"CATCHUP_DOWNSIDE_TOO_HIGH_{downside:.4f}")
    if forward63 is not None and forward63 < 0:
        failures.append(f"NEGATIVE_63D_CATCHUP_RETURN_{forward63:.4f}")
    if count >= 3 and distance is not None and distance <= 0.08 and forward63 is not None and forward63 >= 0:
        positives.append("FULL_HISTORY_CATCHUP_QUALITY_PASS")

    stress_rate = _number(recent_stress.get("second_chance_rate"))
    stress_distance = _number(recent_stress.get("mean_catchup_distance_to_trough"))
    stress_downside = _number(recent_stress.get("mean_catchup_additional_downside"))
    if stress_rate is None or stress_rate < 0.50:
        failures.append("MISSED_ALERT_SECOND_CHANCE_RATE_BELOW_50PCT")
    if stress_distance is not None and stress_distance > 0.15:
        failures.append(f"MISSED_ALERT_DISTANCE_TOO_HIGH_{stress_distance:.4f}")
    if stress_downside is not None and stress_downside < -0.10:
        failures.append(f"MISSED_ALERT_DOWNSIDE_TOO_HIGH_{stress_downside:.4f}")
    if (
        stress_rate is not None
        and stress_rate >= 0.50
        and stress_distance is not None
        and stress_distance <= 0.15
        and stress_downside is not None
        and stress_downside >= -0.10
    ):
        positives.append("MISSED_ALERT_RESILIENCE_PASS")

    first_distance = _number(baseline_recent["path"].get("mean_first_entry_distance"))
    weighted_distance = _number(
        baseline_recent["episode"].get("mean_weighted_distance_complete")
    )
    mean_lead = _number(
        baseline_recent["path"].get("mean_signed_sessions_from_trough")
    )
    precision_limit = {"SPY": 0.08, "QQQ": 0.12, "SOXX": 0.15}[symbol]
    baseline_precision = (
        first_distance is not None and first_distance <= precision_limit
    )

    return {
        "catchup_candidate_pass": not failures,
        "recommendation": (
            "RESEARCH_ONLY_CANDIDATE_NOT_PRODUCTION"
            if not failures
            else "REJECT_CURRENT_POST_THRESHOLD_CATCHUP"
        ),
        "failures": failures,
        "positive_findings": positives,
        "baseline_monitor_diagnosis": {
            "recent_mean_first_entry_distance": first_distance,
            "recent_mean_weighted_distance": weighted_distance,
            "recent_mean_sessions_before_trough": (
                -mean_lead if mean_lead is not None and mean_lead < 0 else 0.0
            ),
            "asset_specific_precision_limit": precision_limit,
            "precision_gate_pass": baseline_precision,
            "interpretation": (
                "STAGED_PARTICIPATION_ACCEPTABLE_BUT_NOT_EXACT_BOTTOM"
                if baseline_precision
                else "ENTRIES_TOO_EARLY_FOR_CLOSE_TO_BOTTOM_CLAIM"
            ),
        },
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Dual-path v1.2 asset-level decision",
        "",
        f"- Overall catch-up promotion: **{payload['overall_promotion_status']}**",
        "",
        "| Asset | Baseline first entry vs trough | Weighted entry vs trough | Mean sessions early | Baseline diagnosis | Catch-up decision |",
        "|---|---:|---:|---:|---|---|",
    ]
    for symbol in ("SPY", "QQQ", "SOXX"):
        d = payload["assets"][symbol]
        b = d["baseline_monitor_diagnosis"]
        lines.append(
            f"| {symbol} | {b['recent_mean_first_entry_distance']:.2%} | "
            f"{b['recent_mean_weighted_distance']:.2%} | "
            f"{b['recent_mean_sessions_before_trough']:.1f} | "
            f"{b['interpretation']} | {d['recommendation']} |"
        )
    for symbol in ("SPY", "QQQ", "SOXX"):
        d = payload["assets"][symbol]
        lines.extend(["", f"## {symbol}"])
        lines.append(f"- Catch-up gate: **{d['catchup_candidate_pass']}**")
        lines.extend(f"- Failure: `{x}`" for x in d["failures"])
        lines.extend(f"- Positive: `{x}`" for x in d["positive_findings"])
        if not d["failures"] and not d["positive_findings"]:
            lines.append("- No qualifying evidence.")
    lines.extend(
        [
            "",
            "> A model ledger is not proof that the user executed an earlier tranche. Production reporting must separate model-simulated deployment from actual confirmed deployment.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    ap.add_argument("--out-md", type=Path, required=True)
    args = ap.parse_args()

    result = json.loads(args.result.read_text())
    assets = {
        symbol: _asset_decision(symbol, result["symbols"][symbol])
        for symbol in ("SPY", "QQQ", "SOXX")
    }
    passed = [s for s, d in assets.items() if d["catchup_candidate_pass"]]
    rejected = [s for s, d in assets.items() if not d["catchup_candidate_pass"]]
    payload = {
        "schema_version": "1.0",
        "classification": "ASSET-LEVEL RESEARCH DECISION — NO AUTOMATIC PROMOTION",
        "assets": assets,
        "candidate_assets": passed,
        "rejected_assets": rejected,
        "overall_promotion_status": (
            "BLOCKED_ASSET_SPECIFIC_ONLY" if passed else "REJECT_V1_2_ALL_ASSETS"
        ),
        "required_production_change": (
            "SEPARATE_MODEL_SIMULATED_DEPLOYMENT_FROM_ACTUAL_CONFIRMED_DEPLOYMENT"
        ),
    }

    # Replace the permissive generic result with the stricter asset-level decision.
    result["asset_level_decision"] = payload
    result["governance"]["candidate_utility_gate_pass"] = not rejected
    result["governance"]["promotion_status"] = payload["overall_promotion_status"]
    result["governance"]["utility_failures"] = [
        f"{symbol}:{failure}"
        for symbol in rejected
        for failure in assets[symbol]["failures"]
    ]
    args.result.write_text(json.dumps(result, indent=2, default=str) + "\n")

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    args.out_md.write_text(_markdown(payload))
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
