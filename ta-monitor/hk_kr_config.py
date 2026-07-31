# Hong Kong / Korea market configuration for the global day-trader monitor.
# Sector-first dynamic discovery. Symbols are exchange-qualified.

# HK/KR are no longer mandatory full fixed-row boards. These lists are liquid seeds only.
HK_LIQUID_SEED = [
    "0700@SEHK", "9988@SEHK", "3690@SEHK", "1810@SEHK", "9618@SEHK",
    "9999@SEHK", "1024@SEHK", "9888@SEHK", "1211@SEHK", "0981@SEHK",
    "2382@SEHK", "0388@SEHK", "2318@SEHK", "1299@SEHK", "2015@SEHK",
    "9866@SEHK", "2269@SEHK", "9961@SEHK", "6690@SEHK", "1177@SEHK",
]

KR_LIQUID_SEED = [
    "005930@KRX", "000660@KRX", "035420@KRX", "035720@KRX", "005380@KRX",
    "000270@KRX", "068270@KRX", "373220@KRX", "207940@KRX", "006400@KRX",
    "051910@KRX", "012450@KRX", "042700@KRX", "034020@KRX", "009150@KRX",
    "010140@KRX", "329180@KRX", "086520@KOSDAQ", "247540@KOSDAQ",
]

HK_BROAD_BENCHMARKS = ["2800@SEHK", "3033@SEHK", "2828@SEHK"]
KR_BROAD_BENCHMARKS = ["069500@KRX", "229200@KRX"]

# Sector proxies / representative baskets. Use official or reliable market-data mapping when available.
HK_SECTOR_GROUPS = {
    "internet_platforms": ["0700@SEHK", "9988@SEHK", "3690@SEHK", "9618@SEHK", "9999@SEHK", "1024@SEHK", "9888@SEHK"],
    "ev_auto": ["1211@SEHK", "2015@SEHK", "9866@SEHK", "1810@SEHK"],
    "semiconductor_optical": ["0981@SEHK", "2382@SEHK"],
    "financials_insurance": ["0388@SEHK", "2318@SEHK", "1299@SEHK"],
    "healthcare_biotech": ["2269@SEHK", "9961@SEHK", "6690@SEHK", "1177@SEHK"],
}

KR_SECTOR_GROUPS = {
    "semiconductor_memory": ["005930@KRX", "000660@KRX", "042700@KRX", "009150@KRX"],
    "internet_platforms": ["035420@KRX", "035720@KRX"],
    "auto": ["005380@KRX", "000270@KRX"],
    "battery_chemicals": ["373220@KRX", "006400@KRX", "051910@KRX", "247540@KOSDAQ"],
    "biopharma": ["068270@KRX", "207940@KRX"],
    "defense_shipbuilding_power": ["012450@KRX", "010140@KRX", "034020@KRX"],
    "kosdaq_growth": ["086520@KOSDAQ", "247540@KOSDAQ"],
}

GLOBAL_SECTOR_BENCHMARKS_US = [
    "SPY", "QQQ", "IWM", "DIA",
    "XLK", "XLC", "XLY", "XLF", "XLI", "XLE", "XLV", "XLU", "XLP", "XLB",
    "SOXX", "SMH", "IGV", "SKYY", "ARKK", "KRE", "XBI", "ITA", "PAVE", "COPX",
]

SECTOR_FIRST_RULES = {
    "enabled": True,
    "sector_scan_precedes_single_name_scan": True,
    "rank_long_and_short_sectors_independently": True,
    "max_sector_rows_per_region": 5,
    "max_stock_candidates_per_selected_sector": 3,
    "minimum_sector_confirmations": 3,
    "long_features": [
        "relative_strength_vs_broad_market",
        "breadth_participation",
        "relative_volume_and_turnover",
        "gap_acceptance",
        "1h_trend",
        "completed_15m_trigger",
        "liquidity_and_spread",
    ],
    "short_features": [
        "relative_weakness_vs_broad_market",
        "negative_breadth",
        "distribution_volume",
        "failed_gap_or_failed_reclaim",
        "1h_deterioration",
        "completed_15m_breakdown",
        "borrow_and_event_quality",
    ],
    "min_sector_score_for_trade_search": 6.0,
    "entry_now_min_stock_score": 6.5,
    "pass2_threshold": 7.0,
    "min_market_rr_to_tp2": 2.0,
    "avoid_longing_weak_sector_stock": True,
    "avoid_shorting_strong_sector_stock": True,
    "cash_when_no_sector_edge": True,
}

ASIA_DAY_TRADER_RULES = {
    "entry_now_min_score": 6.5,
    "pass2_threshold": 7.0,
    "require_fresh_1h_setup": True,
    "require_completed_15m_trigger": True,
    "allow_5m_execution_refinement": True,
    "min_market_rr_to_tp2": 2.0,
    "max_chase_distance_atr": 1.0,
    "max_portfolio_loss_pct": [0.25, 0.40],
    "hk": {
        "timezone": "Asia/Hong_Kong",
        "preopen": ["09:00", "09:30"],
        "rth_sessions": [["09:30", "12:00"], ["13:00", "16:00"]],
        "lunch": ["12:00", "13:00"],
        "no_new_single_name_entry_after": "15:50",
        "max_rth_spread_pct": 0.50,
        "min_avg_daily_turnover_hkd": 20_000_000,
        "opening_range_wait_minutes": 15,
    },
    "kr": {
        "timezone": "Asia/Seoul",
        "rth_session_kst": ["09:00", "15:30"],
        "rth_session_hkt": ["08:00", "14:30"],
        "no_new_single_name_entry_after_hkt": "14:15",
        "max_rth_spread_pct": 0.45,
        "min_avg_daily_turnover_krw": 5_000_000_000,
        "opening_range_wait_minutes": 15,
    },
}

ASIA_SHORT_RULES = {
    "entry_now_min_score": 6.5,
    "pass2_threshold": 7.0,
    "minimum_short_confirmations": 3,
    "min_rr_to_tp2": 2.0,
    "max_chase_distance_atr": 1.0,
    "require_fresh_1h_deterioration": True,
    "require_completed_15m_breakdown_or_failed_reclaim": True,
    "require_relative_weakness_vs_local_benchmark": True,
    "require_shortable_status": True,
    "require_exchange_short_sale_eligibility_check": True,
    "if_borrow_or_eligibility_unavailable": "CONDITIONAL SHORT ONLY",
    "do_not_assume_us_short_sale_rules": True,
}

# 7709 / 7747 are removed from trade discovery and reporting.
# They may appear only in Existing-Position Risk when actually held.
ASIA_COMPLEX_PRODUCTS_ENABLED = False
ASIA_COMPLEX_PRODUCTS_RISK_ONLY = ["7709@SEHK", "7747@SEHK"]

ASIA_REPORT_ORDER = [
    "GLOBAL SECTOR ROTATION BOARD",
    "HK SECTOR BOARD",
    "KR SECTOR BOARD",
    "TOP HK/KR STOCK CANDIDATES",
]
