# Production Multi-Timeframe Day-Trader TA Monitor Policy

Status: PRODUCTION_MONITORING_ONLY  
Order authority: NONE  
Timezone: Asia/Hong_Kong  
Schedule: hourly at minute :05

## Mandatory policy set

Every run must fetch and obey, from `loktoto/busan-trip` branch `main`:

1. `ta-monitor/production_policy.md`
2. `ta-monitor/dynamic_discovery_policy.md`
3. `ta-monitor/burry_relative_value_policy.md`
4. `ta-monitor/software_short_policy.md`
5. `ta-monitor/config.py`

The fixed 21-name long board, Dynamic Discovery Board, semiconductor short board, overpriced-software short board and Burry relative-value board are independent. None may overwrite, average or inflate another board's score.

## Execution and source hierarchy

This is an execution policy. Every scheduled invocation must attempt the available tools, calculate the report and send the report itself. Never create or transmit orders.

1. IBKR is primary equity quote authority and preferred completed-bar authority. Retry each failed endpoint once.
2. Alpaca is parity/fallback. Use SIP, then delayed SIP, then IEX. Never splice feeds inside one ticker/timeframe series.
3. Binance supplies BTC/ETH context only and has zero equity authority.
4. GitHub supplies policy, deterministic model and audit material only; it is never fresh market data.

A source, ticker or timeframe failure must not cancel the report. Degrade only the affected row/module. Never reuse stale data as live or call a close live.

## Mandatory boards

### Fixed 21-name long board

HUT, IREN, NBIS, WULF, MARA, APLD, ORCL, CRWV, CRCL, RKLB, AAOI, ONDS, AXTI, MXL, FOTO, LITE, COHR, APH, FN, MU, SNDK.

### Dynamic Discovery Board

Run every hour in addition to the fixed board. Use `DISCOVERY_SEED_UNIVERSE` plus reliable current liquid leaders where a screener is available. Scan across sectors and prevent AI, semiconductor, optical and crypto concentration from dominating merely because those themes dominate the fixed board.

### Semiconductor short board

Core: SOXX, SMH, MU, SNDK, AMD, INTC, ARM. Also apply `HIGH_MULTIPLE_SEMI_SCREEN` and `SHORT_SCREEN_RULES`.

### Overpriced software short board

Execute `SOFTWARE_SHORT_CORE`, `SOFTWARE_SHORT_DYNAMIC_SEED`, `SOFTWARE_BENCHMARKS`, `SOFTWARE_VALUATION_FACTORS` and `SOFTWARE_SHORT_RULES` under `software_short_policy.md`. High valuation alone is never a short signal.

### Burry board

SOXX, MU, NVDA, CAT, TSLA, PLTR and QQQ under the supplementary Burry policy. Historical disclosure prices and zones are context only.

## Collector and completeness

Exclude incomplete current weekly, daily, 1H and 15m intervals from confirmation calculations.

Preferred minimum completed coverage per symbol:

- weekly: 60 bars;
- daily: 252 bars;
- 1H: 80 bars;
- relevant 15m: 100 bars.

Before bulk requests, size limits for the full universe or use deterministic chunks of no more than five symbols. Verify every symbol separately for count, first/last timestamp, sorted/unique status and completed-interval status. Retry a deficient symbol individually on the same feed, then replace the whole series with the next permitted feed if required. Label SHORT HISTORY, THIN LIQUIDITY, LIMIT TRUNCATION RECOVERED, FEED FALLBACK or DATA UNAVAILABLE accurately.

Weekly/daily history may be cached between runs provided the latest completed interval is refreshed and freshness is disclosed. Fresh 1H and 15m data are mandatory for an RTH `ENTRY NOW` or `SHORT NOW` decision.

## Day-trader operating mode

This monitor is an intraday trading monitor, not a swing-only audit monitor.

- Weekly and daily data define regime, structural conflict and major levels. They are context and risk modifiers, not automatic blockers when fresh 1H and 15m evidence is available.
- The 1H chart defines the active intraday setup, direction and invalidation.
- The completed 15m chart is the primary execution trigger.
- The 5m chart may refine entry after a valid 15m trigger but may never create a trade alone.
- During normal US RTH, a valid setup must be labelled `ENTRY NOW` or `SHORT NOW` rather than repeatedly downgraded to WATCH merely because weekly/daily coverage is imperfect.
- Overnight and premarket may issue `CONDITIONAL ENTRY` or `CONDITIONAL SHORT` only. Single-name after-hours entries are prohibited because of gap/spread risk.
- Wait at least the configured opening-range period after the RTH open unless a completed 15m bar already exists and the setup is not an extended opening chase.

Missing weekly/daily data lowers confidence and score. It does not automatically block an RTH day trade if fresh 1H, completed 15m, spread, event, stop and R/R evidence are reliable. Clear opposing weekly/daily structure still requires a smaller counter-trend label or rejection.

## Evidence-weighted TA model

Do not stack redundant indicators. Use the weights and features in `TA_RESEARCH_MODEL`.

Primary evidence order:

1. market/sector regime;
2. time-series and cross-sectional relative strength;
3. base, pullback, breakout, failed reclaim and volatility-contraction structure;
4. active 1H setup and completed 15m execution trigger;
5. volatility-adjusted stop, executable R/R, liquidity and event risk.

RSI is a location/divergence feature only. MACD is secondary confirmation only. Neither may trigger a trade alone.

## Long scoring

Long score 0–10:

- regime/trend: 20%;
- relative strength: 20%;
- setup quality/location: 20%;
- completed trigger: 15%;
- R/R: 15%;
- execution/event quality: 10%.

Tiers: A 7.5–10; B 6.5–7.4; C 5.5–6.4; D below 5.5.

Penalise extension, nearby resistance, weak volume, stale/wide spread, event risk, peer divergence, financing/dilution, regulatory risk and incomplete data.

## RTH long entries

Every serious candidate receives one direct state:

- ENTRY NOW
- CONDITIONAL ENTRY
- WAIT FOR RETEST
- BREAKOUT WATCH
- DO NOT CHASE
- NO SETUP

### RTH DAY-TRADE ENTRY NOW

Requires all of the following:

- normal US RTH;
- fresh valid 1H setup that is aligned or at least not clearly opposing;
- completed 15m breakout, reclaim, higher low or successful retest;
- market-now executable R/R to TP2 at least 2R;
- acceptable spread/liquidity and no disqualifying event risk;
- defined tactical and structural invalidation;
- score at least the configured day-trade entry threshold.

A score from 6.5 to 6.9 may issue `ENTRY NOW` when all execution conditions are satisfied. A score at or above 7.0 additionally requires PASS 2. Do not withhold a valid 6.5–6.9 RTH day trade merely because PASS 2 is not mandatory.

### ANTICIPATORY STARTER

Requires non-bearish daily regime, stable/improving relative strength, defined support and structural stop, acceptable execution/event risk and preferred-entry R/R to TP2 at least 2.5R. Monitoring label: 20–30% of planned exposure.

### CONFIRMED ADD

Requires an existing active model signal, successful completed retest/continuation, no new conflict, score at least 7.0, PASS 2 and remaining R/R normally at least 1.5R. Monitoring label: 20–35% of planned exposure.

Maximum planned portfolio loss remains 0.25–0.40%. These are monitoring labels only.

## Three-price R/R contract

For every serious long and short candidate calculate separately:

1. market-now executable R/R;
2. preferred pullback/rebound-zone R/R;
3. breakout/breakdown-confirmation R/R.

If market-now R/R is poor but a valid preferred zone offers sufficient R/R, output CONDITIONAL ENTRY, CONDITIONAL SHORT or WAIT FOR RETEST instead of discarding the setup. Rebuild stops and targets from current completed structure and ATR; stale baselines are context only.

## PASS 2

Every raw score at or above 7.0 requires a second fresh IBKR snapshot; after retry failure use a second Alpaca snapshot labelled FALLBACK PASS 2. Re-read completed bars, parity, spread, trigger, extension, stops, targets, event and peer evidence.

Allowed outcomes:

- VALIDATED ENTRY NOW
- VALIDATED SHORT NOW
- VALIDATED CONDITIONAL ENTRY / SHORT
- VALIDATED WAIT FOR RETEST / DO NOT CHASE
- VALIDATION FAILED

A favourable move between passes does not automatically invalidate the setup. If market-now R/R deteriorates but the preferred zone remains valid, preserve the conditional setup and prohibit chasing. Withhold action on unresolved conflict.

## Short policy

Short score remains separate:

- bearish trend/breakdown: 25%;
- trigger completeness: 20%;
- R/R to cover target 2: 20%;
- entry/chase risk: 10%;
- liquidity/spread/borrow/squeeze: 15%;
- valuation/revisions/event/sector evidence: 10%.

A normal RTH `SHORT NOW` may be issued at score 6.5–6.9 when a fresh 1H deterioration and completed 15m breakdown/failed reclaim are present, at least three independent confirmations exist, market-now R/R to TP2 is at least 2R, execution is acceptable and event/borrow/squeeze checks are not disqualifying. Scores at or above 7.0 require PASS 2.

High valuation or a disclosed position alone is never a short signal. Do not chase more than one ATR below breakdown. Prefer a failed reclaim or lower high after the break.

Treat SOXX and SMH as one semiconductor sleeve. Account for any existing SOXX long before describing net hedge exposure. Never blindly copy all disclosed naked shorts.

CAT must receive a fresh explicit decision every run: SHORT NOW, WAIT FOR FAILED RECLAIM, BREAKDOWN WATCH or DO NOT SHORT, including fresh price/source, resistance/reclaim zone, trigger, invalidation, cover targets, target-2 R/R, event, IV and borrow status.

## Rejection analytics

Every rejected serious candidate must record one primary code from `REJECTION_REASON_CODES` and optional secondary codes. Aggregate counts each run for DATA, REGIME, RELATIVE_STRENGTH, TRIGGER, RR, EXTENSION, SPREAD, LIQUIDITY, EVENT, BORROW, SQUEEZE, VALUATION and PASS2_CONFLICT.

`NO ENTRY` is valid only after the fixed long board and Dynamic Discovery Board were evaluated, and `NO SHORT` is valid only after the semiconductor and software short boards were evaluated, or the report explicitly states that collector degradation prevented a conclusion.

## Audit

Build and commit a fresh JSON snapshot containing HKT/ET time, session, source status, quotes, events, optional positions/borrow/options, calculation metadata, completeness metadata, all board scores, three-price R/R and rejection codes. Never commit credentials, licensed raw history, orders or private account data.

## Report order

1. NEW LONG/SHORT ACTION or NO NEW ACTIONABLE TRIGGER.
2. As-of HKT/ET, session and quote status.
3. Executive Dashboard: best fixed-board long, best dynamic-discovery long, `ENTRY NOW`, `SHORT NOW`, conditional states and dominant rejection reasons.
4. Source Status and DATA COVERAGE.
5. Last completed week/live-week context.
6. Strict 21-row fixed long board.
7. DYNAMIC DISCOVERY BOARD, score sorted, maximum configured display names.
8. Semiconductor short board.
9. OVERPRICED SOFTWARE SHORT BOARD.
10. BURRY RELATIVE-VALUE / HEDGE BOARD and explicit CAT decision.
11. PASS 1/PASS 2 ledger.
12. Existing-position overlap/risk where available.
13. Failed modules, retries, freshness and confidence effect.
14. One-line Cantonese Boss Action.

Never imply guaranteed success, never fabricate values, never stay silent and never place orders.
