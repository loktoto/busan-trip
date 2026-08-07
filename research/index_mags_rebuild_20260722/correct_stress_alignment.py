from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("research_outputs/index_mags_rebuild_20260722")
MIN_LIVE_PRODUCT_YEARS = 5.0


def strategy_gate(row: pd.Series, pbo: float, stress2_delta: float, stress3_delta: float) -> str:
    if not np.isfinite(row.get("dsr_probability", np.nan)) or not np.isfinite(row.get("p_positive", np.nan)):
        return "REJECT"
    if (
        row["cagr_delta"] > 0.01
        and row["sharpe_delta"] >= 0
        and row["p_positive"] >= 0.80
        and row["dsr_probability"] >= 0.80
        and pbo <= 0.50
        and stress2_delta > 0
        and stress3_delta >= -0.005
    ):
        return "RETURN_ENHANCER"
    if (
        row["dd_delta"] >= 0.10
        and row["sharpe_delta"] > 0
        and row["cagr_delta"] >= -0.03
        and stress3_delta >= -0.04
    ):
        return "DEFENSIVE"
    return "REJECT"


def choose_recommendation(rows: pd.DataFrame, synthetic: bool, live_years: float | None) -> tuple[str, str]:
    if synthetic:
        return "EXPERIMENTAL_SYNTHETIC", "No production promotion: fixed-constituent hypothetical history only"
    candidates: list[tuple[int, float, str, str]] = []
    by_strategy = rows.set_index("strategy")
    for strategy in ["Hybrid", "Pullback-only", "Trend-only"]:
        row = by_strategy.loc[strategy]
        gate = str(row["gate"])
        if gate == "RETURN_ENHANCER":
            score = row["sharpe_delta"] + 0.5 * row["cagr_delta"] + 0.25 * row["dd_delta"]
            candidates.append((2, float(score), strategy, gate))
        elif gate == "DEFENSIVE":
            score = row["sharpe_delta"] + 0.75 * row["dd_delta"] + 0.25 * row["cagr_delta"]
            candidates.append((1, float(score), strategy, gate))
    if not candidates:
        return "BUY_AND_HOLD", "No active architecture passed conservative walk-forward gates"
    candidates.sort(reverse=True)
    _, _, strategy, gate = candidates[0]
    if live_years is not None and live_years < MIN_LIVE_PRODUCT_YEARS:
        return f"PROVISIONAL_{strategy.upper().replace('-', '_')}", f"{gate}; actual product history only {live_years:.1f} years"
    return strategy.upper().replace("-", "_"), gate


def main() -> None:
    summary_path = OUT / "strategy_summary.csv"
    identity_path = OUT / "strategy_identity.csv"
    validation_path = OUT / "live_product_validation.json"
    manifest_path = OUT / "run_manifest.json"

    summary = pd.read_csv(summary_path)
    identity = pd.read_csv(identity_path)
    validation = json.loads(validation_path.read_text())
    mags_live_years = float(validation["MAGS"]["product_history_years"])

    correction_rows: list[dict[str, float | str]] = []
    for symbol, group in summary.groupby("symbol", sort=False):
        benchmark_index = group.index[group.strategy == "Buy & Hold"]
        if len(benchmark_index) != 1:
            raise RuntimeError(f"{symbol}: expected one Buy & Hold row")
        benchmark_index = int(benchmark_index[0])
        benchmark_cagr = float(summary.loc[benchmark_index, "cagr"])

        for multiplier in (2, 3):
            cagr_column = f"stress_{multiplier}x_cagr"
            delta_column = f"stress_{multiplier}x_cagr_delta"
            boundary_bias = float(summary.loc[benchmark_index, cagr_column] - benchmark_cagr)
            summary.loc[group.index, cagr_column] = summary.loc[group.index, cagr_column] - boundary_bias
            summary.loc[group.index, delta_column] = summary.loc[group.index, cagr_column] - benchmark_cagr
            correction_rows.append({
                "symbol": symbol,
                "multiplier": float(multiplier),
                "removed_boundary_bias": boundary_bias,
            })

        summary.loc[benchmark_index, "gate"] = "BASELINE"
        for strategy in ("Trend-only", "Pullback-only", "Hybrid"):
            index = group.index[group.strategy == strategy]
            if len(index) != 1:
                raise RuntimeError(f"{symbol}: expected one {strategy} row")
            index = int(index[0])
            pbo = float(summary.loc[index, "family_pbo"])
            summary.loc[index, "gate"] = strategy_gate(
                summary.loc[index],
                pbo,
                float(summary.loc[index, "stress_2x_cagr_delta"]),
                float(summary.loc[index, "stress_3x_cagr_delta"]),
            ) if np.isfinite(pbo) else "REJECT"

        corrected_group = summary.loc[group.index].copy()
        recommendation, reason = choose_recommendation(
            corrected_group,
            synthetic=(symbol == "MAGS10"),
            live_years=mags_live_years if symbol == "MAGS7" else None,
        )
        identity_index = identity.index[identity.symbol == symbol]
        if len(identity_index) != 1:
            raise RuntimeError(f"{symbol}: expected one identity row")
        identity_index = int(identity_index[0])
        identity.loc[identity_index, "recommendation"] = recommendation
        identity.loc[identity_index, "recommendation_reason"] = reason
        by_strategy = corrected_group.set_index("strategy")
        identity.loc[identity_index, "trend_gate"] = by_strategy.loc["Trend-only", "gate"]
        identity.loc[identity_index, "pullback_gate"] = by_strategy.loc["Pullback-only", "gate"]
        identity.loc[identity_index, "hybrid_gate"] = by_strategy.loc["Hybrid", "gate"]

    baseline = summary[summary.strategy == "Buy & Hold"]
    maximum = baseline[["stress_2x_cagr_delta", "stress_3x_cagr_delta"]].abs().to_numpy().max()
    if maximum > 1e-12:
        raise RuntimeError(f"Buy & Hold stress delta remains non-zero: {maximum}")

    summary.to_csv(summary_path, index=False, float_format="%.8f")
    identity.to_csv(identity_path, index=False, float_format="%.8f")
    pd.DataFrame(correction_rows).to_csv(OUT / "stress_alignment_audit.csv", index=False, float_format="%.10f")

    manifest = json.loads(manifest_path.read_text())
    manifest["stress_alignment_correction"] = {
        "status": "PASS",
        "method": "subtract each symbol's common OOS slicing bias from every stress-cost CAGR before recomputing relative deltas",
        "buy_and_hold_stress_delta_max_abs": float(maximum),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))

    report_path = OUT / "report.md"
    report_path.write_text(
        report_path.read_text()
        + "\n\n## Stress-cost alignment audit\n\n"
        + "The common OOS slicing boundary was normalised per symbol before comparing 2x/3x transaction-cost stress. "
        + "Buy & Hold stress-cost deltas are exactly zero; strategy gates and recommendations were recomputed.\n"
    )
    print(identity[["symbol", "recommendation", "trend_gate", "pullback_gate", "hybrid_gate"]].to_string(index=False))
    print({"buy_and_hold_stress_delta_max_abs": float(maximum)})


if __name__ == "__main__":
    main()
