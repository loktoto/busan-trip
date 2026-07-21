#!/usr/bin/env python3
"""Authoritative research universe for the Bottom Zone Monitor.

The bottom model deliberately supports exactly three unleveraged underlyings.
Other symbols may be useful as context, but must not be reported or optimised as
independent bottom targets without an explicit scope change and new validation.
"""
from __future__ import annotations

import json
from pathlib import Path

BOTTOM_UNIVERSE = ("SPY", "QQQ", "SOXX")
BOTTOM_UNIVERSE_SET = frozenset(BOTTOM_UNIVERSE)
TACTICAL_LEVERAGE = {
    "SPY": "SSO",
    "QQQ": "QLD",
    "SOXX": "USD",
}


def normalize_symbol(symbol: str) -> str:
    value = str(symbol).strip().upper()
    if not value:
        raise ValueError("Symbol cannot be blank")
    return value


def require_bottom_symbol(symbol: str) -> str:
    value = normalize_symbol(symbol)
    if value not in BOTTOM_UNIVERSE_SET:
        raise ValueError(
            f"Unsupported bottom target {value!r}; allowed universe is "
            f"{', '.join(BOTTOM_UNIVERSE)}"
        )
    return value


def leverage_product(symbol: str) -> str:
    return TACTICAL_LEVERAGE[require_bottom_symbol(symbol)]


def audit_config_scope(path: Path) -> dict:
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError("Config root must be an object")
    configured = {normalize_symbol(k) for k in raw if k != "default"}
    missing = BOTTOM_UNIVERSE_SET - configured
    extra = configured - BOTTOM_UNIVERSE_SET
    if missing or extra:
        raise ValueError(
            f"Config universe mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
        )
    return {
        "bottom_universe": list(BOTTOM_UNIVERSE),
        "tactical_leverage": dict(TACTICAL_LEVERAGE),
        "configured_symbols": sorted(configured),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit_config_scope(args.config), indent=2))
