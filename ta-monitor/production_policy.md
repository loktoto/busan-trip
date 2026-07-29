# Production Multi-Timeframe TA Monitor Policy

Status: PRODUCTION_MONITORING_ONLY  
Order authority: NONE  
Timezone: Asia/Hong_Kong  
Schedule: hourly at minute :05

## Mandatory policy set

Every run must fetch and obey, from `loktoto/busan-trip` branch `main`:

1. `ta-monitor/production_policy.md`
2. `ta-monitor/dynamic_discovery_policy.md`
3. `ta-monitor/burry_relative_value_policy.md`
4. `ta-monitor/config.py`

The fixed 21-name board, Dynamic Discovery Board, semiconductor short board and Burry relative-value board are independent. None may overwrite another board's score.

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

A collector failure for one name must not make all boards N/A. Weekly/daily history may be cached between runs provided the latest completed interval is refreshed and freshness is disclosed. 1H and 15m trigger data must be refreshed each run.

## Evidence-weighted TA model

Do not stack redundant indicators. Use the weights and features in `TA_RESEARCH_MODEL`.

Primary evidence order:

1. market/sector regime;
2. time-series and cross-sectional relative strength;
3. base, pullback, breakout and volatility-contraction structure;
4. completed 1H setup and completed 15m execution trigger;
5. volatility-adjusted stop, executable R/R, liquidity and event risk.

RSI is a location/divergence feature only. MACD is secondary confirmation only. Neither may trigger a trade alone.

Timeframe responsibilities:

- weekly: regime and major structural conflict;
- daily: swing direction, relative strength and setup location;
- 1H: setup development and invalidation;
- 15m: primary execution trigger;
- 5m: optional execution refinement only.

A completed 15m trigger may act when the 1H setup was already valid; it does not need to wait for a new completed 1H breakout. A 15m signal still cannot override clearly opposing weekly and daily regimes except as a labelled, smaller counter-trend setup.

## Long scoring

Long score 0–10:

- regime/trend: 20%;
- relative strength: 20%;
- setup quality/location: 20%;
- completed trigger: 15%;
- R/R: 15%;
- execution/event quality: 10%.

Tiers: A 7.5–10; B 6.5–7.4; C 5.5–6.4; D below 5.5.

Penalise extension, nearby resistance, weak volume, stale/wide spread, event risk, peer divergence, financing/dilution, regulatory risk and incomplete data. Do not treat several correlated oscillators as separate confirmations.

## Tiered long entries

Every serious candidate receives one direct output state:

- ENTRY NOW
- CONDITIONAL ENTRY
- WAIT FOR RETEST
- BREAKOUT WATCH
- DO NOT CHASE
- NO SETUP

Apply `ENTRY_LAYERS`:

### ANTICIPATORY STARTER

Requires non-bearish daily regime, stable/improving relative strength, defined support and structural stop, acceptable execution/event risk and preferred-entry R/R to TP2 at least 2.5R. Monitoring label: 20–30% of planned exposure.

### CONFIRMED STARTER

Requires valid completed 1H setup, completed 15m trigger, current executable R/R to TP2 at least 2R, score at least 7.0 and PASS 2. Monitoring label: 25–40% of planned exposure.

### CONFIRMED ADD

Requires an existing active model signal, successful completed retest/continuation, no new conflict, score at least 7.0, PASS 2 and remaining R/R normally at least 1.5R. Monitoring label: 20–35% of planned exposure.

Maximum planned portfolio loss remains 0.25–0.40%. These are monitoring labels only.

## Three-price R/R contract

For every serious long and short candidate calculate separately:

1. market-now executable R/R;
2. preferred pullback/rebound-zone R/R;
3. breakout/breakdown-confirmation R/R.

If market-now R/R is poor but a valid preferred zone offers sufficient R/R, output CONDITIONAL ENTRY or WAIT FOR RETEST instead of discarding the setup. Rebuild stops and targets from current completed structure and ATR; stale baselines are context only.

## PASS 2

Every raw score at or above 7.0 requires a second fresh IBKR snapshot; after retry failure use a second Alpaca snapshot labelled FALLBACK PASS 2. Re-read completed bars, parity, spread, trigger, extension, stops, targets, event and peer evidence.

Allowed outcomes:

- VALIDATED ENTRY NOW
- VALIDATED CONDITIONAL ENTRY
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

High valuation or a disclosed position alone is never a short signal. Require at least three independent confirmations, valid deterioration or failed reclaim, defined invalidation, acceptable execution, event/borrow/squeeze checks and at least 2R to cover target 2. Do not mechanically invert stale long levels. Do not chase more than one ATR below breakdown.

Treat SOXX and SMH as one semiconductor sleeve. Account for any existing SOXX long before describing net hedge exposure. Never blindly copy all disclosed naked shorts.

CAT must receive a fresh explicit decision every run: SHORT NOW, WAIT FOR FAILED RECLAIM, BREAKDOWN WATCH or DO NOT SHORT, including fresh price/source, resistance/reclaim zone, trigger, invalidation, cover targets, target-2 R/R, event, IV and borrow status.

## Rejection analytics

Every rejected serious candidate must record one primary code from `REJECTION_REASON_CODES` and optional secondary codes. Aggregate counts each run for DATA, REGIME, RELATIVE_STRENGTH, TRIGGER, RR, EXTENSION, SPREAD, LIQUIDITY, EVENT and PASS2_CONFLICT.

`NO ENTRY` is valid only after both the fixed long board and Dynamic Discovery Board were evaluated successfully, or when the report explicitly states that collector degradation prevented a conclusion.

## Audit

Build and commit a fresh JSON snapshot containing HKT/ET time, session, source status, quotes, events, optional positions/borrow/options, calculation metadata, completeness metadata, board scores, three-price R/R and rejection codes. Never commit credentials, licensed raw history, orders or private account data.

## Report order

1. NEW LONG/SHORT ACTION or NO NEW ACTIONABLE TRIGGER.
2. As-of HKT/ET, session and quote status.
3. Executive Dashboard: best fixed-board long, best dynamic-discovery long, entry-now status, conditional-entry status, best short stance and dominant rejection reasons.
4. Source Status and DATA COVERAGE.
5. Last completed week/live-week context.
6. Strict 21-row fixed long board.
7. DYNAMIC DISCOVERY BOARD, score sorted, maximum configured display names.
8. Semiconductor short board.
9. BURRY RELATIVE-VALUE / HEDGE BOARD and explicit CAT decision.
10. PASS 1/PASS 2 ledger.
11. Existing-position overlap/risk where available.
12. Failed modules, retries, freshness and confidence effect.
13. One-line Cantonese Boss Action.

Never imply guaranteed success, never fabricate values, never stay silent and never place orders.