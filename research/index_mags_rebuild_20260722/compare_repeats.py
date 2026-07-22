from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("repetitions")
OUT = Path("canonical")
OUT.mkdir(exist_ok=True)


def locate(rep: str, name: str) -> Path:
    matches = sorted(ROOT.glob(f"**/{rep}/**/{name}")) + sorted(ROOT.glob(f"**/*-{rep}/**/{name}"))
    if not matches:
        matches = sorted(ROOT.glob(f"**/{name}"))
        matches = [path for path in matches if f"-{rep}" in str(path.parent) or f"/{rep}/" in str(path)]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {name} for repetition {rep}; found {matches}")
    return matches[0]


def compare_frame(name: str, keys: list[str], exact: list[str], tolerances: dict[str, float]) -> dict[str, float]:
    left = pd.read_csv(locate("a", name)).sort_values(keys).reset_index(drop=True)
    right = pd.read_csv(locate("b", name)).sort_values(keys).reset_index(drop=True)
    if left[keys].astype(str).to_dict("records") != right[keys].astype(str).to_dict("records"):
        raise RuntimeError(f"{name}: key mismatch")
    for column in exact:
        a = left[column].fillna("").astype(str)
        b = right[column].fillna("").astype(str)
        if not a.equals(b):
            diff = pd.DataFrame({"a": a, "b": b})[a != b]
            raise RuntimeError(f"{name}: identity mismatch in {column}: {diff.head().to_dict('records')}")
    maxima: dict[str, float] = {}
    for column, tolerance in tolerances.items():
        a = pd.to_numeric(left[column], errors="coerce")
        b = pd.to_numeric(right[column], errors="coerce")
        both_nan = a.isna() & b.isna()
        difference = (a - b).abs().mask(both_nan, 0.0)
        maximum = float(difference.max(skipna=True) or 0.0)
        maxima[column] = maximum
        if maximum > tolerance:
            raise RuntimeError(f"{name}: {column} max difference {maximum} exceeds {tolerance}")
    left.to_csv(OUT / name, index=False, float_format="%.8f")
    return maxima


identity_diff = compare_frame(
    "strategy_identity.csv",
    keys=["symbol"],
    exact=[
        "recommendation", "recommendation_reason", "latest_trend_rule",
        "latest_pullback_rule", "trend_gate", "pullback_gate", "hybrid_gate",
        "oos_start", "oos_end",
    ],
    tolerances={
        "latest_off_exposure": 1e-12,
        "current_buy_hold_exposure": 1e-12,
        "current_trend_exposure": 1e-12,
        "current_pullback_exposure": 1e-12,
        "current_hybrid_exposure": 1e-12,
        "trend_family_pbo": 0.05,
        "pullback_family_pbo": 0.05,
    },
)
summary_diff = compare_frame(
    "strategy_summary.csv",
    keys=["symbol", "strategy"],
    exact=["oos_start", "oos_end", "gate"],
    tolerances={
        "cagr": 0.00075, "sharpe": 0.0075, "maxdd": 0.003,
        "terminal": 40.0, "cagr_delta": 0.00075, "sharpe_delta": 0.0075,
        "dd_delta": 0.003, "dsr_probability": 0.06, "p_positive": 0.04,
        "family_pbo": 0.05, "stress_2x_cagr_delta": 0.001,
        "stress_3x_cagr_delta": 0.0015,
    },
)
window_diff = compare_frame(
    "window_comparison.csv",
    keys=["symbol", "strategy", "window"],
    exact=["start", "end"],
    tolerances={"cagr": 0.001, "sharpe": 0.01, "maxdd": 0.004, "terminal": 50.0},
)
compare_frame(
    "ibkr_close_parity.csv",
    keys=["symbol"], exact=[],
    tolerances={"model_raw_close": 0.05, "absolute_pct_diff": 0.0002},
)

parity = pd.read_csv(OUT / "ibkr_close_parity.csv")
if (parity.absolute_pct_diff > 0.003).any():
    raise RuntimeError(f"IBKR close parity failed: {parity[parity.absolute_pct_diff > 0.003].to_dict('records')}")

for name in [
    "walk_forward_choices.csv", "mgtn_recent_parity.csv", "live_product_validation.json",
    "run_manifest.json", "input_manifest.json", "report.md",
]:
    source = locate("a", name)
    shutil.copy2(source, OUT / name)

identity_bytes = (OUT / "strategy_identity.csv").read_bytes()
canonical_sha = hashlib.sha256(identity_bytes).hexdigest()
result = {
    "status": "PASS",
    "canonical_identity_sha256": canonical_sha,
    "identity_metric_max_differences": identity_diff,
    "summary_metric_max_differences": summary_diff,
    "window_metric_max_differences": window_diff,
    "policy": "strategy identity must match exactly; numerical differences must remain within fixed tolerances",
}
(OUT / "repeatability.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
