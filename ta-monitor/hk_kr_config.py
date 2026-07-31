# Hong Kong / Korea market configuration for the global day-trader monitor.
# Symbols are exchange-qualified to prevent cross-market ambiguity.

HK_FIXED_CORE = [
    "0700@SEHK",  # Tencent
    "9988@SEHK",  # Alibaba
    "3690@SEHK",  # Meituan
    "1810@SEHK",  # Xiaomi
    "9618@SEHK",  # JD.com
    "9999@SEHK",  # NetEase
    "1024@SEHK",  # Kuaishou
    "9888@SEHK",  # Baidu
    "1211@SEHK",  # BYD
    "0981@SEHK",  # SMIC
    "2382@SEHK",  # Sunny Optical
    "0388@SEHK",  # HKEX
    "2318@SEHK",  # Ping An
    "1299@SEHK",  # AIA
    "2015@SEHK",  # Li Auto
    "9866@SEHK",  # NIO
]

KR_FIXED_CORE = [
    "005930@KRX",  # Samsung Electronics
    "000660@KRX",  # SK hynix
    "035420@KRX",  # NAVER
    "035720@KRX",  # Kakao
    "005380@KRX",  # Hyundai Motor
    "000270@KRX",  # Kia
    "068270@KRX",  # Celltrion
    "373220@KRX",  # LG Energy Solution
    "207940@KRX",  # Samsung Biologics
    "006400@KRX",  # Samsung SDI
    "051910@KRX",  # LG Chem
    "012450@KRX",  # Hanwha Aerospace
    "042700@KRX",  # Hanmi Semiconductor
    "034020@KRX",  # Doosan Enerbility
    "009150@KRX",  # Samsung Electro-Mechanics
]

HK_DISCOVERY_SEED = [
    "2800@SEHK", "3033@SEHK", "2828@SEHK",
    "0700@SEHK", "9988@SEHK", "3690@SEHK", "1810@SEHK", "9618@SEHK",
    "9999@SEHK", "1024@SEHK", "9888@SEHK", "1211@SEHK", "0981@SEHK",
    "2382@SEHK", "0388@SEHK", "2318@SEHK", "1299@SEHK", "2015@SEHK",
    "9866@SEHK", "2269@SEHK", "9961@SEHK", "6690@SEHK", "1177@SEHK",
]

KR_DISCOVERY_SEED = [
    "069500@KRX", "229200@KRX", "091160@KRX",
    "005930@KRX", "000660@KRX", "035420@KRX", "035720@KRX",
    "005380@KRX", "000270@KRX", "068270@KRX", "373220@KRX",
    "207940@KRX", "006400@KRX", "051910@KRX", "012450@KRX",
    "042700@KRX", "034020@KRX", "009150@KRX", "010140@KRX",
    "329180@KRX", "086520@KOSDAQ", "247540@KOSDAQ",
]

HK_BENCHMARKS = [
    "2800@SEHK",  # broad Hong Kong
    "3033@SEHK",  # Hang Seng TECH proxy
    "2828@SEHK",  # China enterprises proxy
]

KR_BENCHMARKS = [
    "069500@KRX",  # KOSPI 200 proxy
    "229200@KRX",  # KOSDAQ 150 proxy
    "091160@KRX",  # semiconductor proxy
]

ASIA_KNOWN_CONTRACTS = {
    "7709@SEHK": 822454733,
    "7747@SEHK": 784207148,
    "000660@KRX": 17382246,
    "005930@KRX": 17382528,
}

ASIA_COMPLEX_PRODUCTS = {
    "7709@SEHK": {
        "underlying": "000660@KRX",
        "product_type": "daily leveraged ETF / structured exposure",
        "direction": "long_only_monitoring",
        "require_official_inav": True,
        "max_entry_premium_pct": 1.50,
        "max_rth_spread_pct": 0.80,
        "min_turnover_hkd": 5_000_000,
        "do_not_short_product": True,
        "separate_premium_rotation_rules": True,
    },
    "7747@SEHK": {
        "underlying": "005930@KRX",
        "product_type": "daily leveraged ETF / structured exposure",
        "direction": "long_only_monitoring",
        "require_official_inav": True,
        "max_entry_premium_pct": 1.50,
        "max_rth_spread_pct": 0.80,
        "min_turnover_hkd": 5_000_000,
        "do_not_short_product": True,
        "separate_premium_rotation_rules": True,
    },
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
    "preferred_weekly_bars": 60,
    "preferred_daily_bars": 252,
    "preferred_1h_bars": 80,
    "preferred_15m_bars": 100,
    "hk": {
        "timezone": "Asia/Hong_Kong",
        "preopen": ["09:00", "09:30"],
        "rth_sessions": [["09:30", "12:00"], ["13:00", "16:00"]],
        "lunch": ["12:00", "13:00"],
        "no_new_single_name_entry_after": "15:50",
        "max_rth_spread_pct": 0.50,
        "min_avg_daily_turnover_hkd": 20_000_000,
        "opening_range_wait_minutes": 15,
        "half_day_and_weather_from_official_calendar": True,
    },
    "kr": {
        "timezone": "Asia/Seoul",
        "rth_session_kst": ["09:00", "15:30"],
        "rth_session_hkt": ["08:00", "14:30"],
        "no_new_single_name_entry_after_hkt": "14:15",
        "max_rth_spread_pct": 0.45,
        "min_avg_daily_turnover_krw": 5_000_000_000,
        "opening_range_wait_minutes": 15,
        "official_calendar_required": True,
    },
}

ASIA_DISCOVERY_RULES = {
    "max_display_names_per_market": 10,
    "max_deep_analysis_names_per_market": 12,
    "min_price_local": {"HKD": 2.0, "KRW": 2_000},
    "require_current_turnover_rank": True,
    "require_relative_strength_or_weakness": True,
    "require_completed_1h": True,
    "use_completed_15m_for_execution": True,
    "exclude_suspended_or_vi_names": True,
    "exclude_unresolved_corporate_action": True,
    "event_blackout_sessions": 2,
    "session_filter_cross_market_ranking": True,
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
    "require_exact_contract": True,
    "require_shortable_status": True,
    "require_exchange_short_sale_eligibility_check": True,
    "require_borrow_fee_when_available": True,
    "require_available_quantity_when_available": True,
    "if_borrow_or_eligibility_unavailable": "CONDITIONAL SHORT ONLY",
    "event_blackout_sessions": 3,
    "do_not_assume_us_short_sale_rules": True,
}

ASIA_REPORT_ORDER = [
    "HONG KONG DAY-TRADE BOARD",
    "KOREA DAY-TRADE BOARD",
    "ASIA COMPLEX / LEVERAGED PRODUCT BOARD",
]

ASIA_OUTPUT_STATES = [
    "ENTRY NOW", "SHORT NOW", "CONDITIONAL ENTRY", "CONDITIONAL SHORT",
    "WAIT FOR RETEST", "WAIT FOR FAILED RECLAIM", "BREAKOUT WATCH",
    "BREAKDOWN WATCH", "DO NOT CHASE", "DO NOT SHORT", "NO SETUP",
    "DATA UNAVAILABLE", "MARKET CLOSED",
]
