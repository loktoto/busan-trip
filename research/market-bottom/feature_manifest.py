#!/usr/bin/env python3
"""Audit point-in-time feature datasets before model promotion.

A column name is not evidence of data quality. In particular, `downside_vrp`
must not receive full model weight unless its manifest documents a model-free
option-strip construction and intraday realised variance. Breadth built from
current constituents is a survivorship-biased proxy unless explicitly labelled.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


class FeatureManifestError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _require(mapping: dict, key: str, where: str):
    if key not in mapping:
        raise FeatureManifestError(f"Missing {where}.{key}")
    return mapping[key]


def validate_feature_manifest(
    features: pd.DataFrame,
    manifest: dict,
    csv_path: Path | None = None,
) -> dict:
    if "Date" not in features.columns:
        raise FeatureManifestError("Feature data requires Date")
    if manifest.get("schema_version") != 1:
        raise FeatureManifestError("feature manifest schema_version must equal 1")
    if manifest.get("date_semantics") != "STRATEGY_AVAILABLE_SESSION":
        raise FeatureManifestError(
            "date_semantics must be STRATEGY_AVAILABLE_SESSION, not observation date"
        )
    revision_policy = str(_require(manifest, "revision_policy", "manifest"))
    if revision_policy.upper() in {"LATEST", "LATEST_REVISED", "BACKFILL_LATEST"}:
        raise FeatureManifestError("Revised latest values cannot be backfilled into history")
    specs = _require(manifest, "features", "manifest")
    if not isinstance(specs, dict):
        raise FeatureManifestError("manifest.features must be an object")

    expected_hash = manifest.get("csv_sha256")
    actual_hash = sha256_file(csv_path) if csv_path is not None else None
    if expected_hash and actual_hash and expected_hash.lower() != actual_hash.lower():
        raise FeatureManifestError("Feature CSV SHA256 does not match immutable manifest")

    issues: list[dict] = []
    nonpromotable: dict[str, list[str]] = {}
    feature_columns = [c for c in features.columns if c != "Date"]
    for column in feature_columns:
        spec = specs.get(column)
        if not isinstance(spec, dict):
            raise FeatureManifestError(f"Missing manifest specification for {column}")
        _require(spec, "source", f"features.{column}")
        if spec.get("point_in_time") is not True:
            raise FeatureManifestError(f"{column} is not declared point-in-time")
        if int(spec.get("availability_lag_business_days", 0)) < 0:
            raise FeatureManifestError(f"{column} has a negative availability lag")

        reasons: list[str] = []
        if column == "downside_vrp":
            method = str(spec.get("method", "")).lower()
            frequency = str(spec.get("realized_variance_frequency", "")).lower()
            if method != "model_free_option_strip":
                reasons.append("VRP_METHOD_NOT_MODEL_FREE_OPTION_STRIP")
            if frequency not in {"intraday", "1min", "5min", "10min", "15min"}:
                reasons.append("REALIZED_VARIANCE_NOT_INTRADAY")
        elif column == "breadth_score":
            historical = spec.get("historical_constituents") is True
            bias_note = str(spec.get("survivorship_bias", "")).strip()
            if not historical:
                reasons.append("BREADTH_NOT_BUILT_FROM_HISTORICAL_CONSTITUENTS")
                if not bias_note:
                    reasons.append("SURVIVORSHIP_BIAS_NOT_DOCUMENTED")
        elif column == "ofr_fsi":
            if int(spec.get("availability_lag_business_days", 0)) < 2:
                reasons.append("OFR_FSI_LAG_LESS_THAN_TWO_BUSINESS_DAYS")
        elif column == "hy_oas":
            if "publication_timestamp_policy" not in spec:
                reasons.append("HY_OAS_PUBLICATION_POLICY_NOT_DOCUMENTED")

        if reasons:
            nonpromotable[column] = reasons
            issues.append(
                {
                    "feature": column,
                    "severity": "NONPROMOTABLE_PROXY",
                    "reasons": reasons,
                }
            )

    return {
        "classification": "POINT-IN-TIME FEATURE MANIFEST AUDIT",
        "dataset_id": manifest.get("dataset_id"),
        "created_at_utc": manifest.get("created_at_utc"),
        "revision_policy": revision_policy,
        "csv_sha256_expected": expected_hash,
        "csv_sha256_actual": actual_hash,
        "feature_count": len(feature_columns),
        "promotable": not nonpromotable,
        "nonpromotable_features": nonpromotable,
        "issues": issues,
    }


def load_and_validate_feature_manifest(
    features: pd.DataFrame,
    manifest_path: Path,
    csv_path: Path | None = None,
) -> dict:
    manifest = json.loads(manifest_path.read_text())
    return validate_feature_manifest(features, manifest, csv_path)
