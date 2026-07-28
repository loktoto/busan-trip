UNIVERSE = [
    "HUT", "IREN", "NBIS", "WULF", "MARA", "APLD", "ORCL", "CRWV", "CRCL",
    "RKLB", "AAOI", "ONDS", "AXTI", "MXL", "FOTO", "LITE", "COHR", "APH",
    "FN", "MU", "SNDK",
]
PHOTONICS = ["FOTO", "LITE", "COHR", "APH", "FN", "AAOI", "AXTI"]
MINERS = ["HUT", "IREN", "WULF", "MARA"]
MEMORY = ["MU", "SNDK"]

# Short-side coverage is a separate board. It does not replace or dilute the 21-name long board.
# User-facing "Intel" is represented by its listed ticker INTC.
SHORT_CORE = ["SOXX", "SMH", "MU", "SNDK", "AMD", "INTC", "ARM"]

# Liquid semiconductor names to screen dynamically for excessive valuation plus deteriorating price/fundamental evidence.
# Inclusion here means SCREEN ONLY; it does not assert that the name is currently overvalued or shortable.
HIGH_MULTIPLE_SEMI_SCREEN = [
    "NVDA", "AVGO", "MRVL", "ALAB", "CRDO", "MPWR", "MCHP", "ADI", "ON", "NXPI",
    "QCOM", "AMAT", "LRCX", "KLAC", "ASML", "TSM",
]

SHORT_SCREEN_RULES = {
    "min_price": 5.0,
    "max_spread_pct": 0.75,
    "min_rr_to_tp2": 2.0,
    "earnings_blackout_sessions": 5,
    "pass2_threshold": 7.0,
    "valuation_percentile_threshold": 80,
    "minimum_short_confirmations": 3,
    "require_borrow_check_when_available": True,
    "require_rth_validation_for_overnight_signal": True,
}

# Burry disclosure / relative-value board. This is an independent research and hedge board.
# It must never overwrite the core long or semiconductor-short scores, and it is not an instruction to copy trades.
BURRY_NEW_SHORT_DISCLOSURE = ["SOXX", "MU", "NVDA", "CAT"]
BURRY_LEGACY_SHORT_CONTEXT = ["TSLA", "PLTR", "QQQ"]
BURRY_BOARD_UNIVERSE = BURRY_NEW_SHORT_DISCLOSURE + BURRY_LEGACY_SHORT_CONTEXT

# User-supplied historical reference only. These values are never live market data and must be labelled as such.
BURRY_DISCLOSURE_CONTEXT = {
    "reference_date": "2026-07-24",
    "source_type": "self-disclosed trade update / research context; not a complete Form 13F short-position record",
    "portfolio_style": "relative-value long/short; do not infer naked-short sizing, full hedges, borrow cost or stop rules",
    "reference_entry_prices": {
        "MU": 933.86,
        "NVDA": 210.28,
        "CAT": 893.49,
        "SOXX": 535.83,
    },
    "legacy_reference_prices": {
        "TSLA": 313.03,
        "PLTR": 122.92,
        "QQQ": 684.23,
    },
    "reference_scores_only": {
        "copy_naked_short": 3.0,
        "soxx_portfolio_hedge": 6.5,
    },
}

BURRY_HEDGE_RULES = {
    "preferred_single_hedge": "SOXX",
    "never_copy_all_naked_shorts": True,
    "do_not_chase_open_or_large_red_candle": True,
    "prefer_reduce_leveraged_long_before_adding_naked_short": True,
    "max_portfolio_loss_pct": 0.50,
    "initial_fraction_of_planned_hedge": 1.0 / 3.0,
    "treat_soxx_and_smh_as_one_sleeve": True,
    "defined_risk_options_preferred_for_single_name_when_practical": True,
    "option_iv_and_spread_must_be_refreshed": True,
    "require_dynamic_borrow_event_squeeze_checks": True,
}

# Historical reference zones from the 2026-07-24 research note. Rebuild dynamically every run.
# A current completed-bar setup may revise or retire any of these levels.
BURRY_REFERENCE_ZONES = {
    "SOXX": {
        "preferred_rebound_zone": [545.0, 555.0],
        "breakdown_reference": 520.0,
        "cover_reference": [500.0, 505.0],
        "invalidation_reference": 560.0,
        "role": "preferred portfolio hedge, not an automatic naked short",
    },
    "CAT": {
        "preferred_rebound_zone": [900.0, 920.0],
        "invalidation_reference": 930.0,
        "role": "small tactical short watch only",
    },
    "MU": {
        "preferred_rebound_zone": [960.0, 1000.0],
        "role": "cyclical thesis watch; do not chase a large red candle",
    },
    "NVDA": {
        "preferred_rebound_zone": [212.0, 215.0],
        "breakdown_reference": 200.0,
        "role": "lowest-priority naked short; defined-risk structure preferred",
    },
}

EVENTS = {
    "MXL": {"date": "2026-07-23", "label": "Q2 2026 results after close"},
    "APLD": {"date": "2026-07-27", "label": "FY2026 Q4/full-year results after close"},
    "SNDK": {"date": "2026-08-05", "label": "FY2026 Q4/full-year results after close"},
}

BASELINES = {
    "FOTO": {"pullback": [20.80, 21.00], "tactical": 20.45, "structural": 19.90, "trigger": 21.30, "tp": [21.875, 22.475, 23.20]},
    "LITE": {"pullback": [830.0, 836.0], "tactical": 824.0, "structural": 799.80, "trigger": 845.10, "tp": [861.5, 887.5, 930.0]},
    "COHR": {"pullback": [315.50, 317.50], "tactical": 313.80, "structural": 309.50, "trigger": 320.60, "tp": [326.5, 335.5, 348.5]},
    "APH": {"pullback": [156.50, 157.20], "tactical": 155.20, "structural": 152.80, "trigger": 158.50, "tp": [162.0, 167.5, 175.0]},
    "FN": {"pullback": [523.0, 528.0], "tactical": 518.0, "structural": 505.40, "trigger": 534.20, "tp": [548.5, 570.0, 595.0]},
    "AAOI": {"pullback": [117.50, 119.00], "tactical": 114.50, "structural": 107.40, "trigger": 123.50, "tp": [129.0, 138.0, 149.5]},
    "ONDS": {"pullback": [7.55, 7.65], "tactical": 7.47, "structural": 7.22, "invalidation": 6.95, "trigger": 7.85, "tp": [8.225, 8.775, 9.375]},
    "AXTI": {"pullback": [54.80, 56.00], "tactical": 53.70, "structural": 51.20, "trigger": 57.60, "strong_trigger": 58.50, "tp": [60.5, 65.0, 71.5]},
    "MXL": {"pullback": [87.50, 89.00], "tactical": 85.80, "structural": 81.50, "trigger15": 91.30, "trigger": 92.60, "tp": [95.25, 99.75, 104.0]},
    "MU": {"pullback": [963.0, 970.0], "tactical": 948.0, "structural": 936.0, "trigger15": 979.0, "trigger": 988.0, "tp": [1000.0, 1045.0, 1097.5]},
    "SNDK": {"pullback": [1575.0, 1590.0], "tactical": 1548.0, "structural": 1515.0, "invalidation": 1504.0, "trigger15": 1619.0, "trigger": 1637.0, "tp": [1680.0, 1775.0, 1930.0]},
}
