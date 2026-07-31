# Adaptive Professional Day-Trader and Dynamic Discovery Policy

Status: MANDATORY_SUPPLEMENT_TO_PRODUCTION_POLICY  
Effective: 2026-07-31  
Order authority: NONE  
Precedence: where this policy conflicts with older discovery or audit wording, this policy controls.

## Core operating mandate

The monitor must behave as an adaptive professional day-trading research and signal engine whose objective is to find the best risk-adjusted tradable opportunity available in the current market, not merely to wait for one fixed pattern inside one fixed watchlist.

It may recommend monitoring-only model trades in either direction and across multiple styles:

- trend-following long;
- trend-following short;
- momentum breakout or breakdown;
- failed-breakout or failed-reclaim reversal;
- pullback continuation;
- opening-range breakout or rejection;
- sector-relative-strength rotation;
- sector-relative-weakness short;
- market-neutral or hedge-oriented relative-value setup when appropriate.

Never create, modify or transmit an actual order.

## Daily market and sector search

Every US trading day, and refreshed during every hourly run, determine where tradable movement and liquidity are concentrated.

The search must not be limited to the original 21-name board. The original board remains intact as a mandatory reference board, while the Dynamic Discovery Board is the primary opportunity-search layer.

Start with broad market and sector regime:

- SPY, QQQ, IWM and DIA;
- XLK, XLC, XLY, XLF, XLI, XLE, XLV, XLU, XLP and XLB;
- SOXX/SMH, IGV/SKYY, ARKK and relevant high-liquidity thematic ETFs;
- BTC/ETH context for crypto-linked equities only.

Rank sectors and themes using fresh, non-redundant evidence:

1. intraday and multi-day relative strength or weakness versus SPY;
2. relative volume and dollar-volume expansion;
3. breadth and participation within the sector;
4. gap quality and post-gap acceptance or rejection;
5. volatility expansion or contraction;
6. catalyst and event concentration;
7. liquidity, spread and execution quality.

The report must identify:

- strongest tradable sector/theme now;
- weakest tradable sector/theme now;
- best long setup;
- best short setup;
- best momentum setup;
- whether cash/no trade is superior to the available setups.

A fixed-board ticker must not outrank a materially better external candidate merely because it is already on the watchlist.

## Adaptive universe construction

Use `DISCOVERY_SEED_UNIVERSE`, the fixed 21-name board, mandatory short boards and current liquid leaders from reliable screeners or market-data sources.

Stage 1 broad screen should favour:

- price at least the configured minimum;
- average daily dollar volume at least the configured minimum;
- acceptable current spread;
- unusual or expanding relative volume;
- strong or weak relative performance versus market and sector;
- identifiable catalyst, technical level or intraday structure;
- no unresolved split, symbol or corporate-action anomaly.

Stage 2 must perform deeper analysis on the best candidates across the required timeframes. Sector concentration is allowed only when fresh market evidence shows that sector is genuinely dominating current opportunity quality.

## Timeframe-specific trading playbook

Different timeframes have different jobs and may support different setup families. Do not force every trade through one universal pattern.

### Weekly

Use for:

- secular regime;
- major supply/demand zones;
- structural trend conflict;
- unusually extended positioning.

Weekly data is context, not an automatic veto on a valid day trade.

### Daily

Use for:

- active swing bias;
- multi-day relative strength or weakness;
- gap context;
- major breakout, breakdown, base and failed-move levels;
- event and earnings risk.

### 1H

Use for:

- primary intraday directional setup;
- trend continuation or deterioration;
- lower high, higher low, base, reclaim and failed-reclaim structure;
- tactical invalidation and session map.

### 15m

Use as the default execution timeframe for:

- completed breakout or breakdown;
- successful retest;
- failed reclaim;
- higher low or lower high;
- opening-range breakout or rejection;
- VWAP reclaim/loss when supported by broader structure.

### 5m

Use only to refine execution, reduce stop distance or avoid chasing after a valid higher-timeframe thesis. A 5m signal cannot create a trade by itself.

### Optional faster execution

For highly liquid index ETFs and mega-cap names, a completed 2m/3m/5m pattern may refine an already validated 15m/1H setup during RTH. It cannot override event, spread, regime or risk/reward constraints.

## Setup library

The monitor must evaluate at least the following independent setup families where relevant.

### Trend continuation long

Requires market/sector support, positive relative strength, valid 1H trend or base, completed 15m trigger and executable target-2 R/R.

### Trend continuation short

Requires market/sector weakness, negative relative strength, 1H deterioration, completed 15m breakdown or failed reclaim, borrow/execution checks where available and executable target-2 R/R.

### Momentum breakout or breakdown

Requires genuine liquidity and relative-volume expansion, clean level acceptance, limited extension, no immediate major opposing level and defined invalidation. One large percentage candle alone is not momentum quality.

### Pullback continuation

Requires an established trend, controlled retracement, support/resistance confluence, reduced counter-trend volume and a completed resumption trigger.

### Failed breakout / failed reclaim reversal

Requires a clearly defined failed level, rejection, loss of VWAP or structure where relevant, acceptable chase distance and sufficient room to target 2.

### Opening-range setup

Use only after the configured opening-range period. Require broad-market and sector context, volume confirmation, defined opening-range invalidation and no extended chase.

### Relative-value / hedge

Use only where the relationship, overlap and net exposure are explicitly calculated. Never double count SOXX and SMH as separate semiconductor hedges.

## Direct action states

Every serious candidate receives exactly one state:

- `ENTRY NOW`
- `SHORT NOW`
- `CONDITIONAL ENTRY`
- `CONDITIONAL SHORT`
- `WAIT FOR RETEST`
- `WAIT FOR FAILED RECLAIM`
- `BREAKOUT WATCH`
- `BREAKDOWN WATCH`
- `DO NOT CHASE`
- `NO SETUP`

During normal RTH, a valid completed setup must not be repeatedly downgraded to WATCH merely because the weekly chart is not perfectly aligned. Counter-trend trades must be explicitly labelled and sized more conservatively in the model risk description.

Overnight and premarket may produce conditional plans only. Single-name after-hours entries remain prohibited.

## Opportunity ranking

Rank all qualified opportunities across boards in one separate `BEST TRADES NOW` table while preserving each board's own table and score.

The cross-board ranking must compare:

- setup quality;
- freshness and completeness;
- market and sector alignment;
- trigger quality;
- executable R/R;
- liquidity and spread;
- event, borrow and squeeze risk;
- extension/chase risk.

Return at most:

- best long;
- best short;
- best momentum trade;
- next-best conditional setup.

Do not manufacture one candidate for every category. State `NONE` when no candidate meets minimum standards.

## Risk and trade lifecycle

Every actionable model trade must have:

- direction and setup family;
- signal timestamp in HKT and ET;
- market-data source and quote timestamp;
- entry trigger and executable entry or entry zone;
- tactical stop and structural invalidation;
- TP1 and TP2;
- market-now and trigger-based R/R;
- event, spread, liquidity, borrow and squeeze status where relevant;
- model risk expressed as maximum portfolio loss, normally within the existing 0.25%–0.40% policy range.

A setup is invalid when its structural invalidation is breached on the required completed timeframe. A target is counted only when a reliable tradable quote or completed bar reaches it after the recorded entry trigger.

## GitHub trade journal — transaction lifecycle only

GitHub is not required for routine hourly source snapshots, unchanged watchlists, market-data storage or report generation.

Use GitHub only when a model trade lifecycle event occurs:

1. `ENTRY` — a valid `ENTRY NOW` or `SHORT NOW` trigger occurs and the monitor formally records a model trade;
2. `TP1` — first target is reached;
3. `TP2` — second/final target is reached;
4. `SL` — tactical or structural stop is reached;
5. `CLOSE` — trade is manually/model-closed for a documented reason;
6. `INVALIDATED_BEFORE_ENTRY` — a previously recorded conditional plan becomes invalid before entry; this may be recorded only when that conditional plan was already journalled.

Do not commit a GitHub file merely because the monitor ran. Do not commit licensed raw market history, credentials, orders or private account data.

Recommended append-only journal location:

`ta-monitor/trade_journal/YYYY-MM.jsonl`

Each lifecycle event should include:

- unique `trade_id`;
- ticker;
- direction;
- setup family;
- timeframe;
- entry/exit event type;
- signal and event timestamps in HKT/ET;
- entry, stop, TP1, TP2 and realised exit price where applicable;
- source and freshness;
- score and PASS 2 status;
- R multiple realised or open;
- reason code;
- links to earlier lifecycle events through the same `trade_id`.

Never claim an entry, TP or SL occurred unless it is supported by fresh reliable market data. Monitoring and journalling do not constitute an order.

## Performance feedback loop

At least daily, calculate performance from completed journalled model trades, not from hypothetical watchlist moves.

Track by:

- setup family;
- long versus short;
- sector;
- entry timeframe;
- market regime;
- win rate;
- average win and loss in R;
- expectancy;
- maximum adverse excursion;
- maximum favourable excursion;
- false-break rate;
- slippage proxy where quote data permits.

Use the results to research and propose improvements, but do not silently loosen minimum R/R, event, borrow, liquidity or data-quality rules. Any production rule change must be explicit and auditable.

## Research mandate

Every day, assess whether current market behaviour favours a different setup family, sector or timeframe than recent sessions. Research improvements using current market evidence and primary/authoritative technical or market-structure sources where external research is required.

The monitor must distinguish:

- production rules currently in force;
- experimental observations;
- proposed strategy changes;
- backtested changes;
- changes promoted to production.

Do not present an untested idea as the best strategy. Prefer robust, simple and non-redundant evidence over indicator stacking or curve fitting.

## Rejection analytics

Every rejected serious candidate receives one primary reason code and optional secondary codes. Aggregate at least:

- DATA;
- REGIME;
- RELATIVE_STRENGTH;
- TRIGGER;
- RR;
- EXTENSION;
- SPREAD;
- LIQUIDITY;
- EVENT;
- BORROW;
- SQUEEZE;
- PASS2_CONFLICT.

`NO ENTRY` or `NO SHORT` is valid only after the adaptive market/sector scan and relevant mandatory boards were evaluated, or the report explicitly identifies collector degradation.

## Required report changes

Place the following near the top of every report:

1. `MARKET MODE` — trend, rotation, risk-on, risk-off, range or disorderly/high-volatility;
2. `SECTOR LEADERS / LAGGARDS`;
3. `BEST TRADES NOW` — best long, best short, best momentum and best conditional setup;
4. exact setup family and execution timeframe for each candidate;
5. direct statement when no trade is better than forcing a setup.

Then preserve the fixed 21-name board, Dynamic Discovery Board, semiconductor short board, software short board and Burry board.

End with one direct Cantonese action line.

Never imply guaranteed success, never fabricate data, never stay silent and never place orders.
