#!/usr/bin/env python3
"""Audit tactical leveraged-product mappings with actual adjusted prices.

This module separates two questions:
1. Did the tactical signal make or lose money in the actual listed product?
2. Is the listed product designed to deliver 2x the same benchmark family as the
   signal ETF?

For SOXX -> USD the answer to (2) is no.  USD targets the Dow Jones U.S.
Semiconductors Index while SOXX tracks the NYSE Semiconductor Index.  Therefore
an actual USD return minus a theoretical 2x SOXX path is a cross-index plus
product gap, not product tracking error.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest import load_config, load_prices
from leverage import LeverageConfig, align_histories, tactical_backtest


def daily_mapping_metrics(underlying: pd.DataFrame, leveraged: pd.DataFrame) -> dict[str, Any]:
    x = align_histories(underlying, leveraged)
    u = x.Close.pct_change()
    l = x.lev_Close.pct_change()
    target = 2.0 * u
    z = pd.DataFrame({"underlying": u, "actual": l, "target": target}).dropna()
    gap = z.actual - z.target
    x_mean = float(z.underlying.mean())
    var = float(((z.underlying - x_mean) ** 2).sum())
    beta = (
        float(((z.underlying - x_mean) * (z.actual - z.actual.mean())).sum() / var)
        if var > 0
        else np.nan
    )
    return {
        "aligned_daily_observations": int(len(z)),
        "actual_vs_underlying_daily_correlation": float(z.actual.corr(z.underlying)),
        "actual_daily_beta_to_underlying": beta,
        "mean_daily_gap_vs_two_times_signal_etf": float(gap.mean()),
        "daily_gap_standard_deviation": float(gap.std(ddof=0)),
        "daily_gap_rmse": float(np.sqrt(np.mean(gap.to_numpy(float) ** 2))),
        "actual_daily_return_mean": float(z.actual.mean()),
        "two_times_signal_etf_daily_return_mean": float(z.target.mean()),
    }


def audit_pair(
    signal_symbol: str,
    product_symbol: str,
    data_dir: Path,
    config_path: Path,
    mapping: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    underlying = load_prices(data_dir / f"{signal_symbol}.csv")
    leveraged = load_prices(data_dir / f"{product_symbol}.csv")
    cfg = load_config(config_path, signal_symbol)
    trades, tactical = tactical_backtest(
        underlying,
        leveraged,
        cfg,
        LeverageConfig(),
        features=None,
    )
    metrics = daily_mapping_metrics(underlying, leveraged)
    relationship = mapping["relationship"]
    interpretation = (
        "PRODUCT_TRACKING_AND_PATH_DIAGNOSTIC_WITHIN_SAME_BENCHMARK_FAMILY"
        if relationship == "SAME_BENCHMARK_FAMILY"
        else "CROSS_INDEX_PLUS_PRODUCT_GAP_NOT_TRACKING_ERROR"
    )
    result = {
        "signal_asset": signal_symbol,
        "leveraged_product": product_symbol,
        "signal_asset_benchmark": mapping["signal_asset_benchmark"],
        "leveraged_product_benchmark": mapping["leveraged_product_benchmark"],
        "benchmark_relationship": relationship,
        "daily_target": float(mapping["daily_target"]),
        "comparison_interpretation": interpretation,
        "daily_mapping_metrics": metrics,
        "tactical_actual_product": tactical,
        "promotion_eligible_from_mapping_audit": False,
        "promotion_blockers": [
            "TACTICAL_RULE_NOT_FORMALLY_PROMOTED",
            "DAILY_RESET_PATH_DEPENDENCY",
        ]
        + (["SIGNAL_AND_PRODUCT_BENCHMARK_MISMATCH"] if relationship != "SAME_BENCHMARK_FAMILY" else []),
        "official_sources": {
            "product": mapping["official_product_source"],
            "signal_asset": mapping["official_signal_source"],
        },
    }
    return result, trades


def markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Leveraged-product mapping audit v2.0",
        "",
        "Actual adjusted product prices are used for every tactical P&L calculation.",
        "A theoretical 2x signal-ETF path is diagnostic only.",
        "",
        "| Mapping | Benchmark relationship | Daily corr. | Daily beta | Gap RMSE | Tactical trades | Mean trade return | Worst trade | Promotion |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for key, row in payload["mappings"].items():
        m = row["daily_mapping_metrics"]
        t = row["tactical_actual_product"]
        fmt = lambda value: "n/a" if value is None else f"{float(value):.4f}"
        lines.append(
            f"| {key} | {row['benchmark_relationship']} | "
            f"{fmt(m['actual_vs_underlying_daily_correlation'])} | "
            f"{fmt(m['actual_daily_beta_to_underlying'])} | "
            f"{fmt(m['daily_gap_rmse'])} | {t.get('trade_count', 0)} | "
            f"{fmt(t.get('mean_return'))} | {fmt(t.get('worst_return'))} | BLOCKED |"
        )
    lines.extend(
        [
            "",
            "## Critical interpretation",
            "",
            "- SPY→SSO and QQQ→QLD are same-benchmark-family mappings, although the signal ETF and leveraged ETF still have separate fees, financing and tracking effects.",
            "- SOXX→USD is a cross-index tactical proxy. USD targets the Dow Jones U.S. Semiconductors Index; SOXX tracks the NYSE Semiconductor Index.",
            "- For SOXX→USD, the reported gap versus a theoretical 2x SOXX path is not USD tracking error and cannot support promotion.",
            "- All listed products have daily objectives; multi-day outcomes remain path-dependent.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    mapping_payload = json.loads(args.mapping.read_text())
    pairs = (("SPY", "SSO"), ("QQQ", "QLD"), ("SOXX", "USD"))
    results: dict[str, Any] = {}
    args.out.mkdir(parents=True, exist_ok=True)
    for signal, product in pairs:
        row, trades = audit_pair(
            signal,
            product,
            args.data_dir,
            args.config,
            mapping_payload["products"][product],
        )
        key = f"{signal}->{product}"
        results[key] = row
        trades.to_csv(args.out / f"{signal}-{product}-trades.csv", index=False)

    payload = {
        "schema_version": "1.0",
        "classification": "ACTUAL-PRODUCT TACTICAL MAPPING AUDIT — NO PROMOTION",
        "mappings": results,
        "general_daily_reset_source": mapping_payload["general_daily_reset_source"],
        "production_promotion": False,
        "orders_created_or_transmitted": False,
    }
    (args.out / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    (args.out / "summary.md").write_text(markdown(payload))
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
