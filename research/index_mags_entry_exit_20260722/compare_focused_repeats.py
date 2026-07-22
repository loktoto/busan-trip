from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    files = sorted(Path("aggregates").glob("*/focused_summary_*.csv"))
    if len(files) != 2:
        raise RuntimeError(f"Expected two repetition summaries, found {len(files)}")

    frames = [pd.read_csv(path).sort_values("symbol").reset_index(drop=True) for path in files]
    expected = ["MAGS10", "MAGS7", "QQQ", "SMH", "SOXX", "SPY"]
    for frame in frames:
        if frame.symbol.astype(str).tolist() != expected:
            raise RuntimeError(f"Unexpected universe: {frame.symbol.tolist()}")

    left, right = frames
    final_identity_columns = [
        "symbol", "decision", "production_action", "diagnostic_action", "mode",
        "entry_family", "entry_params", "exit_family", "exit_params", "overlay", "stop",
        "current_state", "v5_replace_v4", "v5_decision", "v5_production_action",
        "v5_diagnostic_action", "v5_mode", "v5_current_exposure",
    ]
    missing = [
        column for column in final_identity_columns
        if column not in left.columns or column not in right.columns
    ]
    if missing:
        raise RuntimeError(f"Missing final identity columns: {missing}")

    left_identity = left[final_identity_columns].fillna("").astype(str)
    right_identity = right[final_identity_columns].fillna("").astype(str)
    unequal = left_identity.ne(right_identity)
    if unequal.any().any():
        differences = []
        for row_index, column_index in zip(*unequal.to_numpy().nonzero()):
            differences.append({
                "symbol": left_identity.iloc[row_index]["symbol"],
                "column": final_identity_columns[column_index],
                "left": left_identity.iloc[row_index, column_index],
                "right": right_identity.iloc[row_index, column_index],
            })
        raise RuntimeError(f"Final production identity mismatch: {differences[:30]}")

    v4_metric_tolerances = {
        "holdout_excess": 0.0005,
        "holdout_sharpe_delta": 0.002,
        "holdout_dd_delta": 0.0005,
        "stress_full_excess": 0.0005,
    }
    production_metric_differences: dict[str, dict[str, float]] = {}
    for column, tolerance in v4_metric_tolerances.items():
        delta = (
            pd.to_numeric(left[column], errors="coerce")
            - pd.to_numeric(right[column], errors="coerce")
        ).abs()
        bad = delta > tolerance
        if bad.fillna(False).any():
            production_metric_differences[column] = {
                left.iloc[index]["symbol"]: float(delta.iloc[index])
                for index in delta.index[bad.fillna(False)]
            }
    if production_metric_differences:
        raise RuntimeError(f"Production metric instability: {production_metric_differences}")

    diagnostic_columns = ["v5_components", "v5_ensemble_size"]
    diagnostic_status: dict[str, str] = {}
    diagnostic_differences: dict[str, dict[str, object]] = {}
    replacement_mask = left["v5_replace_v4"].fillna(False).astype(bool)

    for index, symbol in enumerate(expected):
        differences: dict[str, object] = {}
        for column in diagnostic_columns:
            left_value = "" if pd.isna(left.iloc[index][column]) else str(left.iloc[index][column])
            right_value = "" if pd.isna(right.iloc[index][column]) else str(right.iloc[index][column])
            if left_value != right_value:
                differences[column] = {"a": left_value, "b": right_value}
        if differences:
            diagnostic_differences[symbol] = differences
            if bool(replacement_mask.iloc[index]):
                raise RuntimeError(
                    f"Replacement challenger identity is unstable for {symbol}: {differences}"
                )
            diagnostic_status[symbol] = "UNSTABLE_DIAGNOSTIC"
        else:
            diagnostic_status[symbol] = "PASS"

    v5_metric_tolerances = {
        "v5_holdout_excess": 0.0005,
        "v5_holdout_sharpe_delta": 0.002,
        "v5_holdout_dd_delta": 0.0005,
        "v5_stress_full_excess": 0.0005,
    }
    v5_metric_differences: dict[str, dict[str, float]] = {}
    for column, tolerance in v5_metric_tolerances.items():
        delta = (
            pd.to_numeric(left[column], errors="coerce")
            - pd.to_numeric(right[column], errors="coerce")
        ).abs()
        for index, value in delta.items():
            if pd.isna(value) or value <= tolerance:
                continue
            symbol = str(left.iloc[index]["symbol"])
            v5_metric_differences.setdefault(symbol, {})[column] = float(value)
            if bool(replacement_mask.iloc[index]):
                raise RuntimeError(
                    f"Replacement challenger metrics are unstable for {symbol}: "
                    f"{column} delta {value:.8f}"
                )
            diagnostic_status[symbol] = "UNSTABLE_DIAGNOSTIC"

    canonical = left.copy()
    canonical["production_repeatability_status"] = "PASS"
    canonical["v5_repeatability_status"] = canonical["symbol"].map(diagnostic_status)
    canonical["v5_use_allowed"] = (
        canonical["v5_replace_v4"].fillna(False).astype(bool)
        & canonical["v5_repeatability_status"].eq("PASS")
    )
    canonical.to_csv("focused_summary.csv", index=False, float_format="%.8f")

    canonical_identity = canonical[
        final_identity_columns
        + ["production_repeatability_status", "v5_repeatability_status", "v5_use_allowed"]
    ].fillna("").astype(str).to_csv(index=False)
    digest = hashlib.sha256(canonical_identity.encode()).hexdigest()
    result = {
        "status": "PASS",
        "assets": expected,
        "production_identity_sha256": digest,
        "production_repeatability": "PASS",
        "v5_repeatability": diagnostic_status,
        "diagnostic_identity_differences": diagnostic_differences,
        "diagnostic_metric_differences": v5_metric_differences,
        "source_summaries": [str(path) for path in files],
        "policy": (
            "An unstable V5 diagnostic may not replace the stable V4 production rule. "
            "Any future V5 replacement must match across both repetitions."
        ),
    }
    Path("focused_repeatability.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
