#!/usr/bin/env python3
"""Combinatorially symmetric cross-validation (CSCV) diagnostic.

Input is the `candidate_fold_matrix.csv` produced by `robust_validation.py`.
Only rows with sample=TEST_ALL are used. Formal PBO is calculated only when the
candidate matrix declares independent OOS labels and the recorded label windows
do not overlap. Dense rolling five-year diagnostics therefore fail closed rather
than manufacturing a low PBO from dependent outcomes.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


def _label_independence(candidate_rows: pd.DataFrame) -> dict:
    needed = {"fold", "test_start", "label_end", "independent_oos_labels"}
    if not needed.issubset(candidate_rows.columns):
        return {
            "declared_independent": False,
            "verified_non_overlapping": False,
            "reason": "LABEL_WINDOW_METADATA_MISSING",
            "overlap_pairs": [],
        }
    meta = (
        candidate_rows[["fold", "test_start", "label_end", "independent_oos_labels"]]
        .drop_duplicates("fold")
        .sort_values("test_start")
        .copy()
    )
    meta["test_start"] = pd.to_datetime(meta["test_start"], errors="coerce")
    meta["label_end"] = pd.to_datetime(meta["label_end"], errors="coerce")
    declared = bool(meta["independent_oos_labels"].fillna(False).astype(bool).all())
    overlap_pairs: list[dict] = []
    for i in range(len(meta) - 1):
        left = meta.iloc[i]
        right = meta.iloc[i + 1]
        if pd.isna(left.label_end) or pd.isna(right.test_start) or left.label_end >= right.test_start:
            overlap_pairs.append(
                {
                    "left_fold": int(left.fold),
                    "right_fold": int(right.fold),
                    "left_label_end": str(left.label_end.date()) if not pd.isna(left.label_end) else None,
                    "right_test_start": str(right.test_start.date()) if not pd.isna(right.test_start) else None,
                }
            )
    verified = declared and not overlap_pairs
    return {
        "declared_independent": declared,
        "verified_non_overlapping": verified,
        "reason": "OK" if verified else "DEPENDENT_OR_UNVERIFIED_LABEL_WINDOWS",
        "overlap_pairs": overlap_pairs,
    }


def build_utility_matrix(
    candidate_rows: pd.DataFrame,
    floor_margin: float = 1.0,
) -> tuple[pd.DataFrame, dict]:
    required = {"fold", "sample", "candidate_index", "robust_mean"}
    missing = required - set(candidate_rows.columns)
    if missing:
        raise ValueError(f"Candidate matrix is missing columns: {sorted(missing)}")
    z = candidate_rows.loc[
        candidate_rows["sample"].eq("TEST_ALL"),
        ["fold", "sample", "candidate_index", "robust_mean"],
    ].copy()
    if z.empty:
        raise ValueError("No TEST_ALL rows; rerun robust_validation with the current engine")
    z["robust_mean"] = pd.to_numeric(z["robust_mean"], errors="coerce")
    matrix = z.pivot_table(
        index="fold", columns="candidate_index", values="robust_mean", aggfunc="last"
    ).sort_index().astype(float)

    finite_matrix = np.isfinite(matrix.to_numpy(dtype=float))
    all_missing = ~finite_matrix.any(axis=1)
    removed_folds = matrix.index[all_missing].astype(int).tolist()
    matrix = matrix.loc[~all_missing].copy()
    replacements = 0
    for fold in matrix.index:
        # pandas may expose a read-only NumPy view; penalties require a writable copy.
        row = matrix.loc[fold].to_numpy(dtype=float, copy=True)
        finite = np.isfinite(row)
        if not finite.any():
            continue
        floor = float(np.min(row[finite]) - abs(floor_margin))
        replacements += int((~finite).sum())
        row[~finite] = floor
        matrix.loc[fold] = row

    if matrix.shape[1] < 2:
        raise ValueError("CSCV requires at least two candidates")
    independence = _label_independence(candidate_rows.loc[candidate_rows["sample"].eq("TEST_ALL")])
    matrix.attrs["label_independence"] = independence
    return matrix, {
        "removed_no_event_folds": removed_folds,
        "candidate_failure_penalties": replacements,
        "floor_margin": floor_margin,
        "label_independence": independence,
    }


def _even_partition_sets(folds: list[int]) -> list[tuple[int | None, tuple[int, ...]]]:
    if len(folds) % 2 == 0:
        return [(None, tuple(folds))]
    return [(dropped, tuple(f for f in folds if f != dropped)) for dropped in folds]


def cscv_pbo(
    matrix: pd.DataFrame,
    min_partitions: int = 8,
    max_combinations: int = 100_000,
    seed: int = 7,
) -> tuple[pd.DataFrame, dict]:
    independence = matrix.attrs.get("label_independence", {})
    if not independence.get("verified_non_overlapping", False):
        return pd.DataFrame(), {
            "classification": "CSCV/PBO BLOCKED — DEPENDENT OR UNVERIFIED LABEL WINDOWS",
            "usable_partitions": int(len(matrix)),
            "candidate_count": int(matrix.shape[1]),
            "pbo": np.nan,
            "label_independence": independence,
        }
    folds = [int(x) for x in matrix.index]
    if len(folds) < min_partitions:
        return pd.DataFrame(), {
            "classification": "CSCV/PBO UNDERPOWERED — NO PROMOTION CLAIM",
            "usable_partitions": len(folds),
            "required_partitions": min_partitions,
            "candidate_count": int(matrix.shape[1]),
            "pbo": np.nan,
            "label_independence": independence,
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
            outsample = tuple(sorted(active_set - set(insample)))
            is_mean = matrix.loc[list(insample)].mean(axis=0)
            oos_mean = matrix.loc[list(outsample)].mean(axis=0)
            selected = int(is_mean.idxmax())
            oos_ranks = oos_mean.rank(method="average", ascending=True)
            rank = float(oos_ranks.loc[selected])
            n_candidates = float(len(oos_ranks))
            rank_fraction = (rank - 0.5) / n_candidates
            clipped = float(np.clip(rank_fraction, 1e-9, 1 - 1e-9))
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
                    "logit_rank": math.log(clipped / (1 - clipped)),
                    "below_oos_median": bool(rank_fraction <= 0.5),
                    "is_oos_spearman": corr,
                    "degradation": float(oos_mean.loc[selected] - is_mean.loc[selected]),
                }
            )

    detail = pd.DataFrame(records)
    if detail.empty:
        raise RuntimeError("CSCV generated no split records")
    summary = {
        "classification": "CSCV/PBO ON NON-OVERLAPPING OUTER OOS LABELS — NOT GUARANTEED",
        "usable_partitions": len(folds),
        "candidate_count": int(matrix.shape[1]),
        "partition_set_count": len(partition_sets),
        "total_possible_combinations_before_cap": int(total_possible),
        "evaluated_splits": int(len(detail)),
        "pbo": float(detail["below_oos_median"].mean()),
        "median_oos_rank_fraction": float(detail["oos_rank_fraction"].median()),
        "median_degradation": float(detail["degradation"].median()),
        "negative_oos_selected_fraction": float((detail["oos_selected_utility"] < 0).mean()),
        "median_is_oos_spearman": float(detail["is_oos_spearman"].dropna().median())
        if detail["is_oos_spearman"].notna().any()
        else np.nan,
        "label_independence": independence,
        "interpretation": (
            "PBO is the share of CSCV splits where the in-sample winner ranks below "
            "the median candidate out of sample. It remains a diagnostic, not a "
            "replacement for regime coverage or economic significance."
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
