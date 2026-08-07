from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scope import (
    BOTTOM_UNIVERSE,
    TACTICAL_LEVERAGE,
    audit_config_scope,
    leverage_product,
    require_bottom_symbol,
)


def test_bottom_universe_is_exactly_three_assets():
    assert BOTTOM_UNIVERSE == ("SPY", "QQQ", "SOXX")
    assert set(TACTICAL_LEVERAGE) == set(BOTTOM_UNIVERSE)
    assert TACTICAL_LEVERAGE == {"SPY": "SSO", "QQQ": "QLD", "SOXX": "USD"}


def test_smh_is_not_a_bottom_target():
    with pytest.raises(ValueError, match="Unsupported bottom target"):
        require_bottom_symbol("SMH")


def test_symbol_normalisation_and_leverage_mapping():
    assert require_bottom_symbol(" qqq ") == "QQQ"
    assert leverage_product("soxx") == "USD"


def test_config_scope_rejects_missing_or_extra_symbols(tmp_path):
    valid = tmp_path / "valid.json"
    valid.write_text(json.dumps({"default": {}, "SPY": {}, "QQQ": {}, "SOXX": {}}))
    audit = audit_config_scope(valid)
    assert audit["configured_symbols"] == ["QQQ", "SOXX", "SPY"]

    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps({"default": {}, "SPY": {}, "QQQ": {}, "SMH": {}, "SOXX": {}}))
    with pytest.raises(ValueError, match="extra=.*SMH"):
        audit_config_scope(invalid)
