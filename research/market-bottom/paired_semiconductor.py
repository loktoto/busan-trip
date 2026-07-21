#!/usr/bin/env python3
"""Causal paired semiconductor-bottom research: SOXX is traded, SMH is reference only.

The module tests whether an independently calculated SMH bottom state adds useful
out-of-sample information to the SOXX bottom model. SMH can corroborate or veto a
larger SOXX tranche but can never create its own trade or double semiconductor
capital.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from backtest import Config, evaluate, indicators, load_config, load_prices, run
from data_audit import assert_price_continuity

VARIANTS = (
    "SOXX_ONLY",
    "SMH_SOFT_CONFIRM",
    "SMH_VETO_ONLY",
    "SMH_HARD_CONFIRM",
)


def align_histories(soxx: pd.DataFrame, smh: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Inner-align completed daily bars; no stale/asynchronous reference values."""
    dates = pd.DataFrame({"Date": sorted(set(soxx["Date"]) & set(smh["Date"]))})
    if len(dates) < 260:
        raise ValueError("Aligned SMH/SOXX history requires at least 260 daily rows")
    soxx_a = dates.merge(soxx, on="Date", how="left").reset_index(drop=True)
    smh_a = dates.merge(smh, on="Date", how="left").reset_index(drop=True)
    return soxx_a, smh_a


def _recent_true(s: pd.Series, window: int) -> pd.Series:
    return s.fillna(False).astype(int).rolling(window, min_periods=1).max().astype(bool)


def build_pair_indicators(
    soxx: pd.DataFrame,
    smh: pd.DataFrame,
    soxx_cfg: Config,
    smh_cfg: Config,
    recent_window: int = 5,
) -> pd.DataFrame:
    """Calculate independent states first, then causal same-date pair features."""
    soxx_a, smh_a = align_histories(soxx, smh)
    sx = indicators(soxx_a, soxx_cfg)
    mx = indicators(smh_a, smh_cfg)

    reference_columns = [
        "cycle_dd",
        "dd_52w",
        "r5z",
        "rv20",
        "atrp",
        "sell_pressure",
        "newlow10",
        "newlow20",
        "exhaustion",
        "confirmation",
        "confirmation_score",
        "exhaustion_score",
        "long_bear",
    ]
    for column in reference_columns:
        sx[f"smh_{column}"] = mx[column].to_numpy()

    sx["smh_exhaustion_recent"] = _recent_true(sx["smh_exhaustion"], recent_window)
    sx["smh_confirmation_recent"] = _recent_true(sx["smh_confirmation"], recent_window)

    smh_prior_r5z_min = sx["smh_r5z"].shift(1).rolling(20, min_periods=5).min()
    smh_prior_rv_max = sx["smh_rv20"].shift(1).rolling(20, min_periods=5).max()
    smh_prior_sell_max = sx["smh_sell_pressure"].shift(1).rolling(20, min_periods=5).max()
    sx["smh_worsening"] = sx["smh_newlow20"].fillna(False) & (
        (sx["smh_r5z"] <= smh_prior_r5z_min)
        | (sx["smh_rv20"] >= smh_prior_rv_max)
        | (sx["smh_sell_pressure"] >= smh_prior_sell_max)
    )
    sx["smh_improving"] = (
        (sx["smh_r5z"] > sx["smh_r5z"].shift(5))
        & (sx["smh_rv20"] < sx["smh_rv20"].shift(5))
        & (sx["smh_sell_pressure"] < sx["smh_sell_pressure"].shift(5))
    )

    sx["pair_confirms"] = (
        (sx["exhaustion"] & sx["smh_exhaustion_recent"])
        | (sx["confirmation"] & sx["smh_confirmation_recent"])
    )
    sx["pair_positive_divergence"] = (
        sx["newlow20"].fillna(False)
        & sx["smh_improving"].fillna(False)
        & ~sx["smh_worsening"].fillna(False)
    )
    sx["pair_veto"] = sx["smh_worsening"].fillna(False) & (
        sx["smh_cycle_dd"] <= -smh_cfg.watch_dd
    )
    state_gap = (
        sx["cycle_dd"].abs() / max(soxx_cfg.watch_dd, 1e-9)
        - sx["smh_cycle_dd"].abs() / max(smh_cfg.watch_dd, 1e-9)
    ).abs()
    sx["pair_diverges"] = (
        (state_gap >= 0.75)
        | (sx["confirmation"] ^ sx["smh_confirmation_recent"])
    ) & ~sx["pair_confirms"] & ~sx["pair_veto"]

    conditions = [
        sx["pair_veto"],
        sx["pair_confirms"],
        sx["pair_positive_divergence"],
        sx["pair_diverges"],
    ]
    labels = ["VETO", "CONFIRMS", "POSITIVE_DIVERGENCE", "DIVERGES"]
    sx["pair_status"] = np.select(conditions, labels, default="NEUTRAL")
    return sx


def apply_variant(x: pd.DataFrame, cfg: Config, variant: str) -> pd.DataFrame:
    """Alter only SOXX exhaustion/confirmation gates; never add SMH trades."""
    if variant not in VARIANTS:
        raise ValueError(f"Unknown paired variant {variant!r}")
    z = x.copy()
    if variant == "SOXX_ONLY":
        return z

    veto = z["pair_veto"].fillna(False)
    if variant == "SMH_VETO_ONLY":
        z["exhaustion"] = z["exhaustion"] & ~veto
        z["confirmation"] = z["confirmation"] & ~veto
        return z

    if variant == "SMH_HARD_CONFIRM":
        z["exhaustion"] = z["exhaustion"] & z["smh_exhaustion_recent"] & ~veto
        z["confirmation"] = z["confirmation"] & z["smh_confirmation_recent"] & ~veto
        return z

    # Soft confirmation can lower the SOXX vote hurdle by one, but only when SOXX
    # already has its own new-low/recovery evidence. It cannot manufacture State 2.
    soft_exhaustion = (
        z["newlow20"]
        & z["smh_exhaustion_recent"]
        & (z["exhaustion_score"] >= max(1, cfg.exhaustion_votes - 1))
    )
    soft_confirmation = (
        z["smh_confirmation_recent"]
        & (z["confirmation_score"] >= max(1, cfg.confirmation_votes - 1))
        & (z["cycle_dd"] <= -cfg.start_dd)
    )
    z["exhaustion"] = (z["exhaustion"] | soft_exhaustion) & ~veto
    z["confirmation"] = (z["confirmation"] | soft_confirmation) & ~veto
    return z


def _restrict_signal_start(
    x: pd.DataFrame,
    trades: pd.DataFrame,
    catalog: pd.DataFrame,
    signal_start: pd.Timestamp | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if signal_start is None:
        return trades, catalog
    valid_index = x.index[x["Date"] >= signal_start]
    if len(valid_index) == 0:
        return trades.iloc[0:0].copy(), catalog.iloc[0:0].copy()
    start_i = int(valid_index.min())
    catalog = catalog.loc[catalog["start_index"] >= start_i].copy()
    allowed = set(catalog["episode"].astype(int))
    if trades.empty:
        return trades, catalog
    trades = trades.loc[
        (trades["signal_index"] >= start_i) & trades["episode"].astype(int).isin(allowed)
    ].copy()
    return trades, catalog


def run_variant(
    base: pd.DataFrame,
    cfg: Config,
    variant: str,
    signal_start: pd.Timestamp | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    x = apply_variant(base, cfg, variant)
    trades, catalog = run(x, cfg)
    trades, catalog = _restrict_signal_start(x, trades, catalog, signal_start)
    if not trades.empty:
        trades = trades.copy()
        trades["pair_status"] = [x.loc[int(i), "pair_status"] for i in trades["signal_index"]]
        trades["paired_variant"] = variant
        # Governance assertion: every row is a SOXX trade from the primary config.
        if set(trades["symbol"]) != {cfg.symbol}:
            raise AssertionError("SMH reference generated a non-SOXX trade")
    detail, episodes, summary = evaluate(x, trades, catalog, cfg)
    summary.update(
        {
            "variant": variant,
            "primary_symbol": cfg.symbol,
            "reference_symbol": "SMH",
            "smh_creates_trades": False,
        }
    )
    return trades, episodes, summary


def comparison_table(results: dict[str, tuple[pd.DataFrame, pd.DataFrame, dict]]) -> pd.DataFrame:
    rows = []
    for variant, (_, _, summary) in results.items():
        rows.append(
            {
                "variant": variant,
                "trade_count": summary.get("trade_count"),
                "episode_count_complete": summary.get("episode_count_complete"),
                "missed_rate_complete": summary.get("missed_rate_complete"),
                "any_within_5_rate_complete": summary.get("any_within_5_rate_complete"),
                "any_within_8_rate_complete": summary.get("any_within_8_rate_complete"),
                "mean_weighted_distance_complete": summary.get("mean_weighted_distance_complete"),
                "mean_worst_additional_downside_complete": summary.get(
                    "mean_worst_additional_downside_complete"
                ),
                "mean_deployment_complete": summary.get("mean_deployment_complete"),
            }
        )
    return pd.DataFrame(rows)


def promotion_decision(table: pd.DataFrame) -> dict:
    """Conservative diagnostic gate; not a formal multi-fold promotion test."""
    base = table.loc[table["variant"] == "SOXX_ONLY"]
    if base.empty:
        raise ValueError("SOXX_ONLY baseline missing")
    b = base.iloc[0]
    candidates = []
    for _, r in table.loc[table["variant"] != "SOXX_ONLY"].iterrows():
        if pd.isna(r["missed_rate_complete"]) or pd.isna(b["missed_rate_complete"]):
            continue
        improves_proximity = (
            r["any_within_8_rate_complete"] >= b["any_within_8_rate_complete"]
            and r["mean_weighted_distance_complete"] <= b["mean_weighted_distance_complete"]
        )
        controls_risk = (
            r["missed_rate_complete"] <= b["missed_rate_complete"]
            and r["mean_worst_additional_downside_complete"]
            >= b["mean_worst_additional_downside_complete"] - 0.01
        )
        if bool(improves_proximity and controls_risk):
            candidates.append(str(r["variant"]))
    return {
        "classification": "PAIRED SEMICONDUCTOR DIAGNOSTIC — NOT FORMAL PROMOTION",
        "eligible_variants": candidates,
        "promote": False,
        "reason": (
            "A full-sample or single modern holdout comparison cannot promote a feature. "
            "The paired rule must also pass non-overlapping outer folds and long-cycle stress tests."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--soxx-csv", type=Path, required=True)
    ap.add_argument("--smh-csv", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--signal-start")
    ap.add_argument("--recent-window", type=int, default=5)
    ap.add_argument("--out", type=Path, default=Path("paired-semiconductor-output"))
    a = ap.parse_args()

    soxx = load_prices(a.soxx_csv)
    smh = load_prices(a.smh_csv)
    assert_price_continuity(soxx)
    assert_price_continuity(smh)
    soxx_cfg = load_config(a.config, "SOXX")
    smh_cfg = load_config(a.config, "SMH")
    base = build_pair_indicators(soxx, smh, soxx_cfg, smh_cfg, a.recent_window)
    signal_start = pd.Timestamp(a.signal_start) if a.signal_start else None

    results = {
        variant: run_variant(base, soxx_cfg, variant, signal_start) for variant in VARIANTS
    }
    table = comparison_table(results)
    decision = promotion_decision(table)

    a.out.mkdir(parents=True, exist_ok=True)
    base.to_csv(a.out / "paired_indicators.csv", index=False)
    table.to_csv(a.out / "paired_variant_comparison.csv", index=False)
    for variant, (trades, episodes, summary) in results.items():
        d = a.out / variant
        d.mkdir(parents=True, exist_ok=True)
        trades.to_csv(d / "trades.csv", index=False)
        episodes.to_csv(d / "episodes.csv", index=False)
        (d / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    report = {
        "classification": "SOXX PRIMARY / SMH REFERENCE — CAUSAL PAIRED RESEARCH",
        "signal_start": str(signal_start.date()) if signal_start is not None else None,
        "recent_window": a.recent_window,
        "soxx_config": asdict(soxx_cfg),
        "smh_config": asdict(smh_cfg),
        "promotion_decision": decision,
        "comparison": table.to_dict(orient="records"),
    }
    (a.out / "paired_summary.json").write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
