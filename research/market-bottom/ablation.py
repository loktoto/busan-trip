#!/usr/bin/env python3
"""Run feature-family ablations on identical purged walk-forward folds."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from backtest import load_config, load_features, load_prices
from data_audit import assert_price_continuity
from robust_validation import robust_walk_forward
from selection import feature_promotion_decision
from validation import parameter_grid


VARIANTS = {
    "PRICE_VOLUME": [],
    "PRICE_VOLUME_BREADTH": ["breadth_score", "relative_strength"],
    "PRICE_VOLUME_VRP": ["downside_vrp"],
    "PRICE_VOLUME_CREDIT": ["hy_oas", "ofr_fsi"],
    "PRICE_VOLUME_BREADTH_VRP": ["breadth_score", "relative_strength", "downside_vrp"],
    "FULL_ENSEMBLE": ["breadth_score", "relative_strength", "downside_vrp", "hy_oas", "ofr_fsi"],
}


def feature_subset(features: pd.DataFrame | None, columns: list[str]) -> pd.DataFrame | None:
    if not columns or features is None:
        return None
    available = [c for c in columns if c in features]
    if not available:
        return None
    return features[["Date", *available]].copy()


def run_ablation(
    prices: pd.DataFrame,
    features: pd.DataFrame | None,
    base,
    candidates,
    train_days: int,
    test_days: int,
    purge_days: int,
) -> tuple[pd.DataFrame, dict]:
    rows: list[pd.DataFrame] = []
    fold_series: dict[str, pd.Series] = {}
    availability: dict[str, list[str]] = {}
    for name, requested in VARIANTS.items():
        subset = feature_subset(features, requested)
        availability[name] = [] if subset is None else [c for c in subset.columns if c != "Date"]
        folds, _, _ = robust_walk_forward(
            prices, subset, base, candidates, train_days, test_days, purge_days
        )
        if folds.empty:
            continue
        f = folds.copy()
        f["variant"] = name
        f["available_features"] = json.dumps(availability[name])
        rows.append(f)
        fold_series[name] = f.set_index("fold").test_utility

    result_df = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    decisions = {}
    baseline = fold_series.get("PRICE_VOLUME", pd.Series(dtype=float))
    for name, series in fold_series.items():
        if name == "PRICE_VOLUME":
            continue
        decisions[name] = feature_promotion_decision(baseline, series)
        decisions[name]["available_features"] = availability[name]
    summary = {
        "classification": "FEATURE ABLATION — IDENTICAL OUTER FOLDS — NOT GUARANTEED",
        "baseline": "PRICE_VOLUME",
        "availability": availability,
        "promotion_decisions": decisions,
    }
    if not result_df.empty:
        by_variant = result_df.groupby("variant").test_utility.agg(["count", "median", "min", "mean"])
        summary["variant_statistics"] = json.loads(by_variant.to_json(orient="index"))
    return result_df, summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, required=True)
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--grid", type=Path, required=True)
    ap.add_argument("--features-csv", type=Path, required=True)
    ap.add_argument("--train-days", type=int, default=1008)
    ap.add_argument("--test-days", type=int, default=252)
    ap.add_argument("--purge-days", type=int, default=84)
    ap.add_argument("--max-unexplained-jump", type=float, default=0.45)
    ap.add_argument("--out", type=Path, default=Path("ablation-output"))
    a = ap.parse_args()

    prices = load_prices(a.csv)
    assert_price_continuity(prices, a.max_unexplained_jump)
    features = load_features(a.features_csv)
    base = load_config(a.config, a.symbol)
    candidates = parameter_grid(base, json.loads(a.grid.read_text()))
    folds, summary = run_ablation(
        prices, features, base, candidates, a.train_days, a.test_days, a.purge_days
    )
    out = a.out / a.symbol
    out.mkdir(parents=True, exist_ok=True)
    folds.to_csv(out / "feature_ablation_folds.csv", index=False)
    (out / "feature_ablation_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
