#!/usr/bin/env python3
"""Validate the compact live request before deterministic calculation."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


def validate(request: dict, schema: dict) -> None:
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(request)
    created = datetime.fromisoformat(request["created_at"].replace("Z", "+00:00"))
    if created.tzinfo is None:
        raise ValueError("created_at must include a timezone")
    if created > datetime.now(timezone.utc):
        raise ValueError("created_at cannot be in the future")
    if not request["request_id"].startswith("bottom-"):
        raise ValueError("request_id must start with bottom-")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", type=Path, required=True)
    ap.add_argument("--schema", type=Path, required=True)
    args = ap.parse_args()
    request = json.loads(args.request.read_text())
    schema = json.loads(args.schema.read_text())
    validate(request, schema)
    print(
        json.dumps(
            {
                "request_id": request["request_id"],
                "expected_completed_rth_date": request["expected_completed_rth_date"],
                "source": request["source"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
