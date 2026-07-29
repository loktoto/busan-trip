# Dynamic Discovery and Tiered Entry Policy

Status: MANDATORY_SUPPLEMENT_TO_PRODUCTION_POLICY
Effective: 2026-07-29
Order authority: NONE

## Purpose

The fixed 21-name long board remains mandatory, but it is not the whole opportunity set. Every run must also execute an additive Dynamic Discovery Board so that a weak or highly correlated fixed universe cannot force repeated false `NONE` conclusions.

## Evidence hierarchy

The model must prefer robust, economically interpretable features over indicator stacking:

1. Market and sector regime.
2. Cross-sectional and time-series relative strength.
3. Base, pullback, breakout and volatility-contraction structure.
4. Completed 1H setup and completed 15m execution trigger.
5. Volatility-adjusted stop, liquidity, event risk and executable R/R.

RSI is a location/divergence feature only. MACD is secondary confirmation only. Neither may create an entry by itself. Do not award multiple independent confirmations to mathematically redundant indicators derived from the same price series.

## Dynamic universe

Use `DISCOVERY_SEED_UNIVERSE` plus current liquid US leaders when a reliable screener is available. Preserve the original 21 rows separately.

Minimum discovery eligibility:

- price at least the configured minimum;
- average daily dollar volume at least the configured minimum;
- acceptable same-session spread;
- reliable completed daily and 1H series;
- no unresolved symbol, split or corporate-action anomaly;
- event risk identified;
- not merely a one-bar percentage gainer.

Scan across sectors. Do not allow AI, semiconductor, optical or crypto names to dominate the shortlist solely because they dominate the fixed board.

## Two-stage collection

Stage 1 is a cheap broad screen using completed daily data:

- positive or improving 20D/60D relative strength versus SPY and sector ETF;
- price/trend regime, including 50D/200D and weekly 10W/20W context;
- liquidity and spread;
- distance from support and extension in ATR units;
- gap/event status.

Stage 2 performs full weekly, daily, 1H and relevant 15m analysis only for the best configured candidates. A failure for one candidate must not invalidate other candidates.

## Entry states

Every candidate receives exactly one direct state:

- `ENTRY NOW`
- `CONDITIONAL ENTRY`
- `WAIT FOR RETEST`
- `BREAKOUT WATCH`
- `DO NOT CHASE`
- `NO SETUP`

`NONE` is allowed only after both the fixed board and Dynamic Discovery Board have been evaluated successfully, or after an explicit data-degraded conclusion.

## Tiered entry architecture

### ANTICIPATORY STARTER

Purpose: participate near a defined support or orderly pullback before full lower-timeframe confirmation.

Requirements:

- daily regime is not bearish;
- relative strength is stable or improving;
- clear support and structural invalidation;
- preferred-zone R/R to TP2 at least 2.5R;
- acceptable liquidity, spread and event risk;
- no uncontrolled gap or speculative spike.

This is a 20–30% model starter label, not an order instruction.

### CONFIRMED STARTER

Requirements:

- completed 1H setup remains valid;
- completed 15m reclaim, higher low, breakout/retest or equivalent trigger;
- current executable R/R to TP2 at least 2R;
- score at least 7.0 and mandatory PASS 2.

### CONFIRMED ADD

Requirements:

- an existing model signal is active;
- successful completed retest or continuation base;
- no new event, spread or parity conflict;
- score at least 7.0 and mandatory PASS 2;
- remaining R/R to TP2 normally at least 1.5R.

## Three-price R/R contract

For every serious candidate calculate separately:

1. `market_now_rr` — executable at the current reliable quote;
2. `preferred_pullback_rr` — executable only inside a defined pullback zone;
3. `breakout_confirmation_rr` — executable after a defined confirmation trigger.

A candidate with poor market-now R/R but valid pullback R/R must be labelled `CONDITIONAL ENTRY` or `WAIT FOR RETEST`, not discarded as `NO SETUP`.

Targets and stops must be rebuilt from current completed structure and ATR. Stale baseline targets may be context but cannot control current R/R.

## PASS 2 correction

PASS 2 validates the setup, not blind entry at any price.

Allowed outcomes:

- `VALIDATED ENTRY NOW`
- `VALIDATED CONDITIONAL ENTRY`
- `VALIDATED WAIT FOR RETEST / DO NOT CHASE`
- `VALIDATION FAILED`

A favourable move between PASS 1 and PASS 2 does not automatically fail the setup. If market-now R/R deteriorates but the original pullback zone remains valid, preserve the conditional setup and prohibit chasing.

## Timeframe responsibilities

- Weekly: regime and major structural conflict.
- Daily: swing direction, relative strength and setup location.
- 1H: setup development and invalidation.
- 15m: primary execution trigger.
- 5m: optional execution refinement only; it cannot create or reverse the thesis.

A completed 15m trigger does not need to wait for a completed 1H breakout when the 1H setup was already valid before the trigger.

## Rejection analytics

Every rejected candidate must record one primary reason code from `REJECTION_REASON_CODES` and optional secondary reasons. The hourly report must aggregate counts for:

- DATA
- REGIME
- RELATIVE_STRENGTH
- TRIGGER
- RR
- EXTENSION
- SPREAD
- LIQUIDITY
- EVENT
- PASS2_CONFLICT

This separates a genuine absence of setups from collector failure or over-restrictive execution logic.

## Report insertion

After the strict 21-name long table, include `DYNAMIC DISCOVERY BOARD` with no more than the configured display maximum. Show ticker, sector, current source/time, daily and 1H regime, relative strength, state, market-now entry, preferred entry zone, stop/invalidation, TP1/TP2, all three R/R values, event risk, PASS status and direct action.

The Executive Dashboard must state separately:

- best fixed-board long;
- best dynamic-discovery long;
- whether an entry exists now;
- whether a conditional entry exists;
- dominant rejection reasons.

Never create or transmit orders.