#!/usr/bin/env python3
"""Non-trading taxonomy for staged participation, local recovery and cycle bottoms.

The price-only engine is useful for risk-managed participation but the v1.2-v1.4
research did not validate it as a precise QQQ/SOXX cycle-bottom detector.  This
module therefore separates three questions which must not be conflated:

1. Has the drawdown model unlocked a small staged participation tranche?
2. Is a tradable local swing recovery developing on completed daily bars?
3. Is there enough independent point-in-time evidence to call a cycle bottom?

The taxonomy never creates, enlarges or revokes a tranche.  It is reporting and
governance metadata only.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


PRIMARY_STRICT = {"QQQ", "SOXX"}


def _bool(value: Any) -> bool:
    try:
        return bool(value) and not pd.isna(value)
    except (TypeError, ValueError):
        return False


def _finite(value: Any) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if np.isfinite(x) else None


def _latest_pair(frame: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    if len(frame) < 6:
        raise ValueError("Bottom taxonomy requires at least six completed rows")
    return frame.iloc[-1], frame.iloc[-6]


def _participation_status(asset: dict[str, Any]) -> str:
    if bool(asset.get("credit_veto")):
        return "BLOCKED_CREDIT_VETO"
    if float(asset.get("candidate_tranche", 0.0)) > 0:
        return "NEW_STAGED_PARTICIPATION"
    if float(asset.get("cumulative_model_deployment", 0.0)) > 0:
        return "MODEL_STAGED_PARTICIPATION_ACTIVE"
    state = int(asset.get("state", 0))
    if state in (2, 3, 4, 5):
        return "STAGED_PARTICIPATION_WATCH"
    return "NO_PARTICIPATION_SETUP"


def _local_swing(frame: pd.DataFrame) -> dict[str, Any]:
    latest, five_back = _latest_pair(frame)
    low_now = frame.Low.tail(5).min()
    low_prior = frame.Low.iloc[-10:-5].min() if len(frame) >= 10 else np.nan
    higher_low = bool(np.isfinite(low_prior) and low_now > low_prior)
    rv_now = _finite(latest.get("rv20"))
    rv_then = _finite(five_back.get("rv20"))
    rv_contracting = bool(
        rv_now is not None and rv_then is not None and rv_now <= rv_then
    )
    checks = {
        "close_above_sma10": bool(latest.Close > latest.sma10),
        "positive_sma10_slope": bool(latest.sma10_slope > 0),
        "positive_5d_return": bool(latest.r5 > 0),
        "higher_low_5d": higher_low,
        "realized_vol_contracting": rv_contracting,
        "confirmation_score_at_least_3": bool(latest.confirmation_score >= 3),
        "no_fresh_20d_low": not bool(latest.newlow20),
    }
    votes = int(sum(checks.values()))
    strong = votes >= 6 and checks["close_above_sma10"] and checks[
        "realized_vol_contracting"
    ]
    watch = votes >= 4 and checks["positive_5d_return"]
    status = (
        "LOCAL_SWING_RECOVERY"
        if strong
        else "LOCAL_SWING_RECOVERY_WATCH"
        if watch
        else "LOCAL_SWING_NOT_CONFIRMED"
    )
    return {
        "status": status,
        "votes": votes,
        "checks": checks,
    }


def _independent_evidence(frame: pd.DataFrame) -> dict[str, Any]:
    latest = frame.iloc[-1]
    five_back = frame.iloc[-6]
    evidence: dict[str, Any] = {}

    if "breadth_score_z" in frame and pd.notna(latest.get("breadth_score_z")):
        evidence["breadth"] = {
            "available": True,
            "supportive": bool(latest.breadth_score_z > five_back.breadth_score_z),
            "latest_z": float(latest.breadth_score_z),
        }
    else:
        evidence["breadth"] = {"available": False, "supportive": False}

    if "downside_vrp_z" in frame and pd.notna(latest.get("downside_vrp_z")):
        evidence["downside_vrp"] = {
            "available": True,
            "supportive": bool(latest.downside_vrp_z < five_back.downside_vrp_z),
            "latest_z": float(latest.downside_vrp_z),
        }
    else:
        evidence["downside_vrp"] = {"available": False, "supportive": False}

    credit_columns = [c for c in ("hy_oas_z", "ofr_fsi_z") if c in frame]
    valid_credit = [c for c in credit_columns if pd.notna(latest.get(c))]
    if valid_credit:
        latest_credit = max(float(latest[c]) for c in valid_credit)
        prior_credit = max(float(five_back[c]) for c in valid_credit)
        evidence["credit"] = {
            "available": True,
            "supportive": bool(latest_credit < prior_credit),
            "latest_z": latest_credit,
            "columns": valid_credit,
        }
    else:
        evidence["credit"] = {"available": False, "supportive": False}

    available = [k for k, v in evidence.items() if v["available"]]
    supportive = [k for k, v in evidence.items() if v["available"] and v["supportive"]]
    return {
        "families": evidence,
        "available_count": len(available),
        "supportive_count": len(supportive),
        "available_families": available,
        "supportive_families": supportive,
    }


def classify_bottom_taxonomy(
    symbol: str,
    frame: pd.DataFrame,
    asset: dict[str, Any],
    feature_provenance_verified: bool = False,
) -> dict[str, Any]:
    """Return reporting-only bottom taxonomy for one asset."""
    local = _local_swing(frame)
    independent = _independent_evidence(frame)
    evidence_gaps: list[str] = []

    for family in ("breadth", "downside_vrp", "credit"):
        if not independent["families"][family]["available"]:
            evidence_gaps.append(f"MISSING_{family.upper()}")
    if not feature_provenance_verified:
        evidence_gaps.append("POINT_IN_TIME_PROVENANCE_NOT_VERIFIED")

    price_structure = local["status"] == "LOCAL_SWING_RECOVERY"
    independent_ready = independent["available_count"] == 3
    independent_support = independent["supportive_count"] >= 2

    if not price_structure:
        cycle_status = "CYCLE_BOTTOM_UNCONFIRMED_PRICE_STRUCTURE"
    elif not independent_ready:
        cycle_status = "CYCLE_BOTTOM_UNCONFIRMED_MISSING_EVIDENCE"
    elif not independent_support:
        cycle_status = "CYCLE_BOTTOM_UNCONFIRMED_DIVERGENT_EVIDENCE"
    elif not feature_provenance_verified:
        cycle_status = "CYCLE_BOTTOM_RESEARCH_CONFIRMATION_ONLY"
    else:
        # The feature families still require formal identical-fold ablation before
        # they may authorise a production cycle-bottom label or leverage tranche.
        cycle_status = "CYCLE_BOTTOM_RESEARCH_CONFIRMATION_ONLY"
        evidence_gaps.append("FEATURE_ABLATION_NOT_PROMOTED")

    if symbol in PRIMARY_STRICT and cycle_status.startswith("CYCLE_BOTTOM_RESEARCH"):
        evidence_gaps.append("QQQ_SOXX_CYCLE_BOTTOM_RULE_NOT_PROMOTED")

    return {
        "schema_version": "1.0",
        "reporting_only": True,
        "trade_authority": "NONE",
        "participation_status": _participation_status(asset),
        "local_swing_status": local["status"],
        "local_swing_votes": local["votes"],
        "local_swing_checks": local["checks"],
        "cycle_bottom_status": cycle_status,
        "independent_evidence": independent,
        "feature_provenance_verified": bool(feature_provenance_verified),
        "evidence_gaps": sorted(set(evidence_gaps)),
        "leverage_authority": "NONE_FROM_TAXONOMY",
    }
