# Burry Relative-Value / Hedge Board Policy

Status: PRODUCTION_MONITORING_ONLY  
Order authority: NONE  
Relationship to main policy: supplementary mandatory board; `production_policy.md` remains authoritative for source hierarchy, completed bars, scoring, validation, fail-safe and delivery.

## Purpose

Track the user-requested Burry disclosure basket without converting a contextual long/short portfolio update into blind naked-short instructions.

This board is separate from:
1. the original 21-name long board; and
2. the semiconductor core-short board.

It must not overwrite, average, net or inflate either board's score.

## Disclosure interpretation

- Do not call the disclosed basket a complete latest Form 13F short-position record.
- Form 13F does not provide a complete view of ordinary equity short positions.
- Treat the 2026-07-24 disclosure as a self-disclosed trade/research update and relative-value portfolio context.
- The monitor does not know the full portfolio, actual sizing, other hedges, borrow cost, option structure or stop rules unless independently sourced.
- Do not infer that the portfolio is a one-way market-crash bet. Evaluate long and short legs as a possible relative-value / hedged portfolio.
- If disclosure verification is unavailable in a run, label the disclosure details `USER-SUPPLIED HISTORICAL CONTEXT — NOT REVERIFIED THIS RUN`.

## Mandatory coverage

New-short disclosure context:
- SOXX
- MU
- NVDA
- CAT

Legacy / unchanged short context, not a new disclosure signal:
- TSLA
- PLTR
- QQQ

Reference prices and zones live in `config.py`. They are historical reference only and must never be presented as live prices or permanent triggers.

## Default interpretation

- Blindly copying the naked shorts: historical reference assessment **3/10**.
- Using one SOXX sleeve as a portfolio hedge: historical reference assessment **6.5/10**.
- Default action in the absence of a fresh validated trigger: **WAIT — DO NOT CHASE**.

These are research-reference assessments, not current raw scores. Every run must calculate current scores from fresh data.

## Portfolio hedge hierarchy

1. First assess whether reducing existing leveraged semiconductor / high-beta long exposure is cleaner than opening a new naked short.
2. If an additional hedge is still justified, prefer one SOXX or SMH semiconductor sleeve, not simultaneous duplicated ETF exposure.
3. Do not simultaneously copy SOXX, MU, NVDA and CAT naked shorts merely because they appeared in the same disclosure.
4. Initial monitoring label is one-third of the planned hedge only after a validated trigger.
5. Maximum planned loss reference for this hedge board is 0.50% of total portfolio value. This is a monitoring/risk label only, never an order instruction.
6. For single-name shorts, defined-risk option structures are preferred when practical, but current IV, skew, expiry liquidity and bid/ask must be freshly checked. Historical option IV or spread observations must not be reused as current.

## Burry board scoring

Calculate a separate 0–10 score using the main short-scoring framework, with additional penalties for:
- copying a disclosed position without knowing full portfolio hedges;
- naked-short risk where the disclosed implementation may have used puts or spreads;
- chasing a large red candle or Monday/opening gap;
- current price already materially below the disclosed reference price;
- event, borrow, SSR, locate or squeeze uncertainty;
- duplicated semiconductor exposure;
- conflict with existing long positions.

No Burry-board entry alert may be issued unless:
- raw score is at least 7.0;
- PASS 2 is completed under the main policy;
- current multi-timeframe trigger is valid;
- invalidation and cover TP1/TP2 are defined;
- executable R/R to cover TP2 is at least 2R;
- borrow/event/squeeze checks are not disqualifying;
- the proposed hedge does not accidentally duplicate SOXX and SMH or conceal an existing long offset.

## Instrument-specific discipline

### SOXX / SMH

- Preferred use: portfolio hedge, not automatic directional naked short.
- Treat SOXX and SMH as one sleeve.
- Historical SOXX reference zone from the 2026-07-24 note: rebound 545–555, breakdown reference 520, cover reference 500–505, invalidation reference 560.
- Rebuild all levels from current completed weekly/daily/1H/15m bars every run. Retire historical levels when structure changes.
- Do not chase near support or after a large downside session.

### CAT

- Tactical small-short watch only.
- Historical reference: wait for 900–920 rebound failure; thesis weakens on a sustained reclaim above approximately 930.
- Refresh current trend, valuation, revisions, infrastructure/data-centre catalyst risk, earnings date and borrow before any score.

### MU

- Cyclical memory / AI-capex thesis may be monitored, but high volatility and news sensitivity require strict anti-chase discipline.
- Historical reference: wait for 960–1,000 rebound resistance rather than shorting a large red candle.
- Rebuild levels dynamically and check memory-pricing/news catalyst risk.

### NVDA

- Lowest-priority naked short in this board because earnings quality, cash flow, product cycle and institutional ownership can sustain valuation.
- Historical reference: watch 212–215 failed rebound or a breakdown below 200 followed by failed reclaim.
- Defined-risk structure preferred when current options execution is acceptable.

### TSLA / PLTR / QQQ

- These are legacy/unchanged context, not new disclosure triggers.
- Never open a new short solely because the prior position was described as maintained.
- Require a completely fresh setup, current R/R and squeeze/event review.

## Mandatory report section

Every hourly report must include a concise `BURRY RELATIVE-VALUE / HEDGE BOARD` after the core semiconductor short board with:
- disclosure/source status;
- `COPY NAKED SHORTS: ENTER / WAIT / AVOID`;
- `SOXX HEDGE: ENTER / WAIT / AVOID`;
- current score and confidence for SOXX, MU, NVDA, CAT, TSLA, PLTR and QQQ;
- fresh price, current trigger/rejection zone, invalidation, cover TP1/TP2 and R/R;
- current position overlap and whether the action would reduce an existing long or create net short exposure;
- borrow, event and squeeze status;
- clear distinction between historical disclosure price and fresh market price;
- one-line conclusion stating whether the best response is reducing leveraged longs, adding one hedge sleeve, or doing nothing.

If fresh data are unavailable, preserve all seven rows and write `N/A — 未取得可靠資料`. Never reuse the 2026-07-24 reference prices as live data.
