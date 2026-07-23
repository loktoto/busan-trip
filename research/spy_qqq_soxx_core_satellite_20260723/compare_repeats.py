from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path("repetitions")
OUT = Path("canonical")
OUT.mkdir(exist_ok=True)


def locate(rep: str, name: str) -> Path:
    matches = sorted(ROOT.glob(f"**/*-{rep}/**/{name}")) + sorted(ROOT.glob(f"**/{rep}/**/{name}"))
    matches = list(dict.fromkeys(matches))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {name} for {rep}; found {matches}")
    return matches[0]


def compare_frame(name: str, keys: list[str], exact: list[str], tolerances: dict[str, float]) -> dict[str, float]:
    a = pd.read_csv(locate("a", name)).sort_values(keys).reset_index(drop=True)
    b = pd.read_csv(locate("b", name)).sort_values(keys).reset_index(drop=True)
    if a[keys].astype(str).to_dict("records") != b[keys].astype(str).to_dict("records"):
        raise RuntimeError(f"{name}: key mismatch")
    for column in exact:
        left = a[column].fillna("").astype(str)
        right = b[column].fillna("").astype(str)
        if not left.equals(right):
            difference = pd.DataFrame({"a": left, "b": right})[left != right]
            raise RuntimeError(f"{name}: exact mismatch {column}: {difference.head().to_dict('records')}")
    maxima: dict[str, float] = {}
    for column, tolerance in tolerances.items():
        left = pd.to_numeric(a[column], errors="coerce")
        right = pd.to_numeric(b[column], errors="coerce")
        both_nan = left.isna() & right.isna()
        difference = (left - right).abs().mask(both_nan, 0.0)
        maximum = float(difference.max(skipna=True) or 0.0)
        maxima[column] = maximum
        if maximum > tolerance:
            raise RuntimeError(f"{name}: {column} max difference {maximum} > {tolerance}")
    a.to_csv(OUT / name, index=False, float_format="%.8f")
    return maxima


manifest_a = json.loads(locate("a", "run_manifest.json").read_text())
manifest_b = json.loads(locate("b", "run_manifest.json").read_text())
for key in ["version", "candidate_count", "family_count", "base_engine_source_sha256", "selection_policy"]:
    if manifest_a.get(key) != manifest_b.get(key):
        raise RuntimeError(f"manifest mismatch {key}: {manifest_a.get(key)} != {manifest_b.get(key)}")

inputs_a = json.loads(locate("a", "input_manifest.json").read_text())
inputs_b = json.loads(locate("b", "input_manifest.json").read_text())
if set(inputs_a) != set(inputs_b):
    raise RuntimeError("input symbol mismatch")
input_differences = {}
for symbol in sorted(inputs_a):
    for key in ["rows", "start", "end"]:
        if inputs_a[symbol][key] != inputs_b[symbol][key]:
            raise RuntimeError(f"input mismatch {symbol} {key}: {inputs_a[symbol][key]} != {inputs_b[symbol][key]}")
    difference = abs(float(inputs_a[symbol]["last_close"]) - float(inputs_b[symbol]["last_close"]))
    input_differences[symbol] = difference
    tolerance = 0.05 if symbol in {"SPY", "QQQ", "SOXX"} else 0.15
    if difference > tolerance:
        raise RuntimeError(f"input last-close mismatch {symbol}: {difference} > {tolerance}")

identity_diff = compare_frame(
    "strategy_identity.csv",
    keys=["classification"],
    exact=["classification", "family", "candidate", "product", "variant", "family_gate", "return_alpha_gate", "start", "end"],
    tolerances={
        "production_sleeve": 0.0,
        "current_spy_weight": 0.005,
        "current_qqq_weight": 0.005,
        "current_soxx_weight": 0.005,
        "current_leveraged_weight": 0.005,
        "current_cash_weight": 0.005,
        "current_effective_soxx_exposure": 0.005,
        "cagr_delta": 0.0015,
        "cagr_delta_vs_402020_buy_hold": 0.0015,
        "sharpe_delta": 0.02,
        "dd_delta": 0.006,
        "annual_alpha": 0.0015,
        "stress_3x_cagr_delta": 0.002,
        "bootstrap_p_positive": 0.06,
        "dsr_probability": 0.08,
        "search_pbo": 0.08,
    },
)
family_diff = compare_frame(
    "family_summary.csv",
    keys=["family"],
    exact=["product", "variant", "family_gate", "central_candidate"],
    tolerances={
        "strict_pass_count": 0.0,
        "positive_cagr_sleeves": 0.0,
        "positive_stress3_sleeves": 0.0,
        "central_cagr_delta": 0.0015,
        "central_sharpe_delta": 0.02,
        "central_dd_delta": 0.006,
        "central_annual_alpha": 0.0015,
        "central_stress3_delta": 0.002,
        "central_bootstrap": 0.06,
        "central_dsr": 0.08,
        "median_quality": 0.004,
    },
)
grid_diff = compare_frame(
    "candidate_grid.csv",
    keys=["candidate"],
    exact=["product", "variant", "family", "policy", "exposure_variant", "return_alpha_gate", "start", "end"],
    tolerances={
        "sleeve": 0.0,
        "cagr": 0.0015,
        "benchmark_cagr": 0.0015,
        "cagr_delta": 0.0015,
        "cagr_delta_vs_402020_buy_hold": 0.0015,
        "sharpe": 0.02,
        "benchmark_sharpe": 0.02,
        "sharpe_delta": 0.02,
        "maxdd": 0.006,
        "benchmark_maxdd": 0.006,
        "dd_delta": 0.006,
        "annual_alpha": 0.0015,
        "beta": 0.02,
        "stress_2x_cagr_delta": 0.002,
        "stress_3x_cagr_delta": 0.002,
        "positive_cagr_blocks": 0.0,
        "positive_sharpe_blocks": 0.0,
        "bootstrap_p_positive": 0.06,
        "dsr_probability": 0.08,
        "search_pbo": 0.08,
        "effective_trials": 0.0,
        "trial_participation_ratio": 0.25,
        "selection_frequency": 0.08,
        "conditional_pbo": 0.08,
        "average_turnover": 0.08,
        "current_signal_exposure": 0.005,
        "terminal": 150.0,
        "benchmark_terminal": 150.0,
        "quality": 0.004,
    },
)
window_diff = compare_frame(
    "window_comparison.csv",
    keys=["candidate", "window"],
    exact=["start", "end"],
    tolerances={
        "cagr": 0.0015,
        "sharpe": 0.02,
        "maxdd": 0.006,
        "vol": 0.004,
        "calmar": 0.02,
        "terminal": 150.0,
        "skew": 0.08,
        "kurt": 0.25,
    },
)
cash_diff = compare_frame(
    "cash_product_validation.csv",
    keys=["start", "end"],
    exact=["start", "end"],
    tolerances={
        "bil_cagr": 0.0005,
        "synthetic_cash_cagr": 0.0005,
        "cagr_difference": 0.0005,
        "daily_return_correlation": 0.02,
    },
)

for name in ["report.md", "run_manifest.json", "input_manifest.json", "block_diagnostics.csv", "current_strategy_weights.csv"]:
    shutil.copy2(locate("a", name), OUT / name)

identity_bytes = (OUT / "strategy_identity.csv").read_bytes()
result = {
    "status": "PASS",
    "canonical_identity_sha256": hashlib.sha256(identity_bytes).hexdigest(),
    "input_last_close_differences": input_differences,
    "identity_metric_max_differences": identity_diff,
    "family_metric_max_differences": family_diff,
    "candidate_metric_max_differences": grid_diff,
    "window_metric_max_differences": window_diff,
    "cash_metric_max_differences": cash_diff,
    "policy": "exact family/candidate identity; fixed 20% production sleeve; neighbouring sleeve robustness; numerical tolerances; matching input dates and base engine source",
}
(OUT / "repeatability.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
