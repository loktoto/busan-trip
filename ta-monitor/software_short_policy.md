# Overpriced Software Short Board Policy

Status: PRODUCTION_MONITORING_ONLY  
Order authority: NONE  
Relationship to main policy: supplementary mandatory day-trading board. `production_policy.md` remains authoritative for source hierarchy, completed bars, scoring, PASS 2, fail-safe and delivery.

## Purpose

Scan liquid US-listed software companies for tactical intraday short setups where valuation is extreme **and** price/fundamental evidence is deteriorating. High valuation alone is never a short signal.

This board is independent from the fixed 21-name long board, Dynamic Discovery Board, semiconductor short board and Burry relative-value board. Scores must never be averaged, overwritten or double-counted across boards.

## Mandatory universe

Use `SOFTWARE_SHORT_CORE`, `SOFTWARE_SHORT_DYNAMIC_SEED`, `SOFTWARE_BENCHMARKS`, `SOFTWARE_VALUATION_FACTORS` and `SOFTWARE_SHORT_RULES` from `config.py`.

Every run must preserve all core rows. Dynamically qualified names are additive and must be ranked separately or appended below the core rows.

## Valuation qualification

A name may be labelled `OVERPRICED SOFTWARE CANDIDATE` only when reliable fresh or recently published data support at least the configured minimum number of independent valuation/fundamental flags, such as:

- NTM EV/Sales or forward P/E at or above the configured own-history or peer percentile;
- very low or negative forward free-cash-flow yield;
- growth-adjusted sales multiple materially above peers;
- stock-based compensation burden unusually high versus revenue or free cash flow;
- revenue, billings, RPO, NRR or earnings-estimate deceleration;
- downward revisions or weakening guidance while valuation remains elevated.

Use one internally consistent valuation horizon/source set within a comparison. Never mix stale FY1 with fresh NTM metrics without disclosure. If reliable valuation data are unavailable, write `VALUATION N/A` and keep the row as a technical watch only; do not call it overpriced.

## Tactical short requirements

A software short may be `SHORT NOW` only during normal US RTH and only when all are true:

1. the 1H setup is bearish or clearly deteriorating, or at minimum not opposing the short;
2. a completed 15m breakdown, failed reclaim or lower-high rejection has occurred;
3. relative weakness versus at least one configured software benchmark and QQQ is present;
4. executable R/R to cover target 2 is at least 2R;
5. spread/liquidity are acceptable and the entry is not more than one ATR below the breakdown;
6. earnings, guidance, product event, lock-up, index inclusion, takeover and major conference risks are checked;
7. borrow/shortability/fee/SSR/locate and squeeze evidence are checked when available and are not disqualifying;
8. at least three independent confirmations are present; valuation counts as only one confirmation;
9. raw score meets the main policy threshold and PASS 2 is completed whenever required.

Overnight and premarket may produce `CONDITIONAL SHORT` only. After-hours may not create a new single-name short because of spread and gap risk.

## Day-trader anti-chase discipline

- Prefer failed reclaim into VWAP, opening-range low, prior-day support turned resistance, 1H resistance or a broken base.
- Do not short a large opening gap-down at the low. Wait for a rebound failure or a fresh completed breakdown.
- Do not short solely because a company has a high multiple, negative narrative or social-media attention.
- A strong software/QQQ regime materially reduces the score unless the name shows clear idiosyncratic relative weakness.
- If price rises between PASS 1 and PASS 2, rebuild entry, stop and targets. Preserve a valid conditional failed-reclaim setup but prohibit chasing.

## Scoring

Use the main short score with software-specific evidence:

- bearish trend / 1H deterioration: 20%;
- completed 15m breakdown or failed reclaim: 20%;
- relative weakness versus IGV/SKYY/QQQ: 15%;
- R/R to cover target 2: 15%;
- liquidity, spread, borrow and squeeze: 10%;
- valuation extremity and growth-adjusted valuation: 10%;
- estimate revisions, billings/RPO/NRR and event risk: 10%.

Penalise strong benchmark momentum, crowded short interest, expensive borrow, imminent earnings, takeover risk, high positive gamma, wide spreads, low volume and missing valuation data.

## Required decisions and fields

Every core and dynamically qualified row must receive one state:

- SHORT NOW
- CONDITIONAL SHORT
- WAIT FOR FAILED RECLAIM
- BREAKDOWN WATCH
- DO NOT CHASE
- DO NOT SHORT
- DATA UNAVAILABLE

For every serious candidate report fresh price/source, valuation evidence and date, nearest rejection/reclaim zone, breakdown trigger, invalidation, cover TP1/TP2, market-now and preferred-zone R/R, relative-strength evidence, spread/liquidity, borrow/SSR/locate, squeeze/event status, raw score, PASS 2 status and one direct reason.

## Report placement

Insert `OVERPRICED SOFTWARE SHORT BOARD` after the semiconductor short board and before the Burry relative-value board. State explicitly whether any software name is `SHORT NOW`. If none qualifies, name the best failed-reclaim or breakdown watch rather than outputting a generic no-short statement.

If a module fails, preserve every core row with `N/A — 未取得可靠資料`, list retries and confidence impact, and continue the full hourly report.
