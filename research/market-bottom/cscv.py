#!/usr/bin/env python3
"""Combinatorially symmetric cross-validation (CSCV) diagnostic.

Input is the `candidate_fold_matrix.csv` produced by `robust_validation.py`.
Only rows with sample=TEST_ALL are used, so each cell is already an outer
out-of-sample utility for one candidate on one non-overlapping test partition.

The implementation follows the CSCV selection/ranking logic:
1. split an even number of partitions into equal in-sample/out-of-sample halves;
2. select the candidate with the highest mean in-sample utility;
3. rank that selected candidate in the complementary half;
4. PBO is the fraction of splits where the in-sample winner ranks below the
   out-of-sample median.

This does not make a sparse five-year sample large. Fewer than eight usable
partitions is classified as underpowered and no promotable PBO claim is made.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


def build_utility_matrix(
    candidate_rows: pd.DataFrame,
    floor_margin: float = 1.0,
) -> tuple[pd.DataFrame, dict]:
    required = {"fold", "sample", "candidate_index", "robust_mean"}
    missing = required - set(candidate_rows.columns)
    if missing:
        raise ValueError(f"Candidate matrix is missing columns: {sorted(missing)}")
    z = candidate_rows.loc[candidate_rows.sample == "TEST_ALL", list(required)].copy()
    if z.empty:
        raise ValueError("No TEST_ALL rows; rerun robust_validation with the current engine")
    z["robust_mean"] = pd.to_numeric(z.robust_mean, errors="coerce")
    matrix = z.pivot_table(
        index="fold",
        columns="candidate_index",
        values="robust_mean",
        aggfunc="last",
    ).sort_index()
    matrix = matrix.astype(float)

    # A partition with no evaluable market episode for any candidate contains no
    # selection information and is removed. Candidate-specific non-finite values
    # are genuine failures to produce an evaluable result and receive a fold-local
    # penalty below the worst finite candidate rather than being silently dropped.
    all_missing = ~np.isfinite(matrix).any(axis=1)
    removed_folds = matrix.index[all_missing].astype(int).tolist()
    matrix = matrix.loc[~all_missing].copy()
    replacements = 0
    for fold in matrix.index:
        row = matrix.loc[fold].to_numpy(float)
        finite = np.isfinite(row)
        if not finite.any():
            continue
        floor = float(np.min(row[finite]) - abs(floor_margin))
        replacements += int((~finite).sum())
        row[~finite] = floor
        matrix.loc[fold] = row

    if matrix.shape[1] < 2:
        raise ValueError("CSCV requires at least two candidates")
    return matrix, {
        "removed_no_event_folds": removed_folds,
        "candidate_failure_penalties": replacements,
        "floor_margin": floor_margin,
    }


def _even_partition_sets(folds: list[int]) -> list[tuple[int | None, tuple[int, ...]]]:
    """Use all partitions when even; leave each one out in turn when odd."""
    if len(folds) % 2 == 0:
        return [(None, tuple(folds))]
    return [(dropped, tuple(f for f in folds if f != dropped)) for dropped in folds]


def cscv_pbo(
    matrix: pd.DataFrame,
    min_partitions: int = 8,
    max_combinations: int = 100_000,
    seed: int = 7,
) -> tuple[pd.DataFrame, dict]:
    folds = [int(x) for x in matrix.index]
    if len(folds) < min_partitions:
        return pd.DataFrame(), {
            "classification": "CSCV/PBO UNDERPOWERED — NO PROMOTION CLAIM",
            "usable_partitions": len(folds),
            "required_partitions": min_partitions,
            "candidate_count": int(matrix.shape[1]),
            "pbo": np.nan,
        }

    rng = np.random.default_rng(seed)
    records: list[dict] = []
    total_possible = 0
    partition_sets = _even_partition_sets(folds)
    for dropped, active in partition_sets:
        half = len(active) // 2
        combos = list(itertools.combinations(active, half))
        total_possible += len(combos)
        if len(combos) > max_combinations:
            chosen = np.sort(rng.choice(len(combos), size=max_combinations, replace=False))
            combos = [combos[int(i)] for i in chosen]
        active_set = set(active)
        for split_id, insample in enumerate(combos, start=1):
            insample_set = set(insample)
            outsample = tuple(sorted(active_set - insample_set))
            is_mean = matrix.loc[list(insample)].mean(axis=0)
            oos_mean = matrix.loc[list(outsample)].mean(axis=0)
            selected = int(is_mean.idxmax())
            oos_ranks = oos_mean.rank(method="average", ascending=True)
            rank = float(oos_ranks.loc[selected])
            n_candidates = float(len(oos_ranks))
            rank_fraction = (rank - 0.5) / n_candidates
            clipped = float(np.clip(rank_fraction, 1e-9, 1 - 1e-9))
            logit = math.log(clipped / (1 - clipped))
            corr = float(is_mean.corr(oos_mean, method="spearman")) if len(is_mean) > 1 else np.nan
            records.append(
                {
                    "dropped_partition": dropped,
                    "split_id": split_id,
                    "in_sample_partitions": json.dumps(sorted(insample)),
                    "out_of_sample_partitions": json.dumps(list(outsample)),
                    "selected_candidate": selected,
                    "is_selected_utility": float(is_mean.loc[selected]),
                    "oos_selected_utility": float(oos_mean.loc[selected]),
                    "oos_best_utility": float(oos_mean.max()),
                    "oos_rank_fraction": rank_fraction,
                    "logit_rank": logit,
                    "below_oos_median": bool(rank_fraction <= 0.5),
                    "is_oos_spearman": corr,
                    "degradation": float(oos_mean.loc[selected] - is_mean.loc[selected]),
                }
            )

    detail = pd.DataFrame(records)
    if detail.empty:
        raise RuntimeError("CSCV generated no split records")
    pbo = float(detail.below_oos_median.mean())
    summary = {
        "classification": "CSCV/PBO DIAGNOSTIC ON OUTER OOS PARTITIONS — NOT GUARANTEED",
        "usable_partitions": len(folds),
        "candidate_count": int(matrix.shape[1]),
        "partition_set_count": len(partition_sets),
        "total_possible_combinations_before_cap": int(total_possible),
        "evaluated_splits": int(len(detail)),
        "pbo": pbo,
        "median_oos_rank_fraction": float(detail.oos_rank_fraction.median()),
        "median_degradation": float(detail.degradation.median()),
        "negative_oos_selected_fraction": float((detail.oos_selected_utility < 0).mean()),
        "median_is_oos_spearman": float(detail.is_oos_spearman.dropna().median())
        if detail.is_oos_spearman.notna().any()
        else np.nan,
        "interpretation": (
            "PBO is the share of CSCV splits where the in-sample winner ranks below "
            "the median candidate out of sample; lower is better, but no fixed cutoff "
            "overrides sample size, regime coverage or economic significance."
        ),
    }
    return detail, summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate-matrix", type=Path, required=True)
    ap.add_argument("--min-partitions", type=int, default=8)
    ap.add_argument("--floor-margin", type=float, default=1.0)
    ap.add_argument("--max-combinations", type=int, default=100_000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", type=Path, default=Path("cscv-output"))
    a = ap.parse_args()

    raw = pd.read_csv(a.candidate_matrix)
    matrix, audit = build_utility_matrix(raw, a.floor_margin)
    detail, summary = cscv_pbo(matrix, a.min_partitions, a.max_combinations, a.seed)
    summary["matrix_audit"] = audit
    a.out.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(a.out / "cscv_utility_matrix.csv")
    detail.to_csv(a.out / "cscv_splits.csv", index=False)
    (a.out / "cscv_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
