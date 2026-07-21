from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from feature_manifest import (
    FeatureManifestError,
    sha256_file,
    validate_feature_manifest,
)


def feature_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": pd.bdate_range("2020-01-01", periods=5),
            "breadth_score": [0.1, 0.2, 0.3, 0.2, 0.4],
            "downside_vrp": [1.0, 1.2, 1.1, 1.5, 1.4],
            "hy_oas": [3.0, 3.1, 3.2, 3.0, 2.9],
            "ofr_fsi": [0.0, 0.1, 0.2, 0.1, 0.0],
        }
    )


def valid_manifest() -> dict:
    return {
        "schema_version": 1,
        "dataset_id": "unit-test",
        "created_at_utc": "2026-07-21T00:00:00Z",
        "date_semantics": "STRATEGY_AVAILABLE_SESSION",
        "revision_policy": "APPEND_ONLY_VINTAGES",
        "features": {
            "breadth_score": {
                "source": "historical constituent archive",
                "point_in_time": True,
                "historical_constituents": True,
                "availability_lag_business_days": 0,
            },
            "downside_vrp": {
                "source": "option strip and intraday returns",
                "point_in_time": True,
                "method": "model_free_option_strip",
                "realized_variance_frequency": "5min",
                "availability_lag_business_days": 1,
            },
            "hy_oas": {
                "source": "credit spread vintage",
                "point_in_time": True,
                "availability_lag_business_days": 1,
                "publication_timestamp_policy": "next-session availability",
            },
            "ofr_fsi": {
                "source": "OFR vintage archive",
                "point_in_time": True,
                "availability_lag_business_days": 2,
            },
        },
    }


def test_valid_manifest_is_promotable():
    audit = validate_feature_manifest(feature_frame(), valid_manifest())
    assert audit["promotable"] is True
    assert audit["nonpromotable_features"] == {}


def test_proxy_vrp_and_survivorship_breadth_are_blocked_not_mislabeled():
    manifest = valid_manifest()
    manifest["features"]["downside_vrp"]["method"] = "underlying_iv_minus_daily_hv"
    manifest["features"]["downside_vrp"]["realized_variance_frequency"] = "daily"
    manifest["features"]["breadth_score"]["historical_constituents"] = False
    manifest["features"]["breadth_score"]["survivorship_bias"] = "current constituents"
    audit = validate_feature_manifest(feature_frame(), manifest)
    assert audit["promotable"] is False
    assert "downside_vrp" in audit["nonpromotable_features"]
    assert "breadth_score" in audit["nonpromotable_features"]


def test_ofr_fsi_requires_two_business_day_availability_lag():
    manifest = valid_manifest()
    manifest["features"]["ofr_fsi"]["availability_lag_business_days"] = 1
    audit = validate_feature_manifest(feature_frame(), manifest)
    assert audit["promotable"] is False
    assert audit["nonpromotable_features"]["ofr_fsi"] == [
        "OFR_FSI_LAG_LESS_THAN_TWO_BUSINESS_DAYS"
    ]


def test_latest_revised_backfill_is_rejected():
    manifest = valid_manifest()
    manifest["revision_policy"] = "LATEST_REVISED"
    with pytest.raises(FeatureManifestError, match="cannot be backfilled"):
        validate_feature_manifest(feature_frame(), manifest)


def test_csv_hash_mismatch_is_rejected(tmp_path: Path):
    path = tmp_path / "features.csv"
    feature_frame().to_csv(path, index=False)
    manifest = valid_manifest()
    manifest["csv_sha256"] = "0" * 64
    with pytest.raises(FeatureManifestError, match="SHA256"):
        validate_feature_manifest(feature_frame(), manifest, path)
    manifest["csv_sha256"] = sha256_file(path)
    audit = validate_feature_manifest(feature_frame(), manifest, path)
    assert audit["csv_sha256_actual"] == manifest["csv_sha256"]
