from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import leveraged_backtest_v2_20260720 as v2

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "research_outputs" / "leveraged_backtest_20260720"
V3_OUT = ROOT / "research_outputs" / "leveraged_backtest_v3_20260720"
V3_OUT.mkdir(parents=True, exist_ok=True)

NAMED = {
    "MA_5_20",
    "MA_10_20",
    "MA_10_30",
    "MA_20_50",
    "MA_50_200",
    "PRICE_SMA200_H0",
    "PRICE_SMA200_H1",
    "PRICE_SMA200_H2",
    "PRICE_SMA200_H3",
    "MHT_E4_X1",
    "MHT_E4_X2",
    "MHT_E5_X1",
    "MHT_E5_X2",
    "MHT_E6_X1",
    "MHT_E6_X2",
    "TSMOM_E3_X1",
    "TSMOM_E4_X0",
    "TSMOM_E4_X1",
    "MHT_VOL_E4_VR100",
    "MHT_VOL_E5_VR100",
    "MHT_VOL_E5_VR125",
    "BRK50_F200_XMA20",
    "BRK63_F200_XMA20",
    "BRK126_F200_XMA20",
    "RS63_XMA20",
    "RS126_XMA20",
    "RSI2_10_REC5_XR70_T10",
    "RSI2_15_REC3_XR70_T20",
    "RSI2_15_REC5_XR90_T20",
}


def select_candidates() -> set[str]:
    keep = set(NAMED)

    robust_path = V1 / "robust_strategy_ranking.csv"
    if robust_path.exists():
        robust = pd.read_csv(robust_path)
        sort_col = "final_score" if "final_score" in robust.columns else "robust_score"
        for _, part in robust.groupby(["universe", "leverage"]):
            keep.update(part.sort_values(sort_col, ascending=False).head(20)["strategy"].astype(str))

    scored_path = V1 / "synthetic_scored_results.csv"
    if scored_path.exists():
        scored = pd.read_csv(scored_path)
        if "row_score" in scored.columns:
            for _, part in scored.groupby(["asset", "leverage"]):
                keep.update(part.sort_values("row_score", ascending=False).head(8)["strategy"].astype(str))
        # Also preserve best late-sample and stress performers so V1's composite score cannot hide them.
        for col in ("late_cagr", "stress_cagr", "calmar"):
            if col in scored.columns:
                for _, part in scored.groupby(["asset", "leverage"]):
                    keep.update(part.sort_values(col, ascending=False).head(4)["strategy"].astype(str))

    return {x for x in keep if isinstance(x, str) and x}


def main() -> None:
    candidates = select_candidates()
    original = v2.make_strategies

    def shortlisted(features: pd.DataFrame):
        all_rules = original(features)
        selected = [rule for rule in all_rules if rule["strategy"] in candidates]
        missing_named = sorted(NAMED.difference({rule["strategy"] for rule in all_rules}))
        if missing_named:
            print("Named rules not generated:", missing_named)
        return selected

    v2.make_strategies = shortlisted
    v2.OUT = V3_OUT
    print(f"Two-stage shortlist contains {len(candidates)} unique Entry/Exit rules")
    v2.main()

    (V3_OUT / "shortlist_manifest.json").write_text(
        json.dumps(
            {
                "selection_method": "V1 full-grid pooled, per-asset, late-sample and stress shortlist; V2/V3 applies all stop and sizing overlays",
                "candidate_count": len(candidates),
                "named_baselines": sorted(NAMED),
                "candidates": sorted(candidates),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
