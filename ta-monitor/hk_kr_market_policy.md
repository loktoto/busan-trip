# Hong Kong / Korea Sector-First Intraday Day-Trader Policy

Status: MANDATORY_SUPPLEMENT_TO_PRODUCTION_POLICY  
Effective: 2026-07-31  
Order authority: NONE  
Timezone: Asia/Hong_Kong

## Objective

HK and KR remain eligible trading markets, but they are no longer mandatory full fixed-row boards. The monitor must first identify the best sector to enter and the best sector to short, then analyse only the most liquid stocks inside those sectors.

Do not force a HK/KR single-name report when no sector edge exists. Cash/no trade may rank first.

## Mandatory configuration

Fetch `ta-monitor/hk_kr_config.py` every run and execute:

- `HK_SECTOR_GROUPS`;
- `KR_SECTOR_GROUPS`;
- `GLOBAL_SECTOR_BENCHMARKS_US`;
- `SECTOR_FIRST_RULES`;
- `HK_LIQUID_SEED` and `KR_LIQUID_SEED` only as candidate pools;
- `ASIA_DAY_TRADER_RULES` and `ASIA_SHORT_RULES`.

`ASIA_COMPLEX_PRODUCTS_ENABLED` is false. Do not run a dedicated 7709/7747 day-trade board. If either product is actually held, show it only in Existing-Position Risk.

## Sector-first process

Every hourly run must rank sectors independently for long and short across the currently open markets.

### Stage 1 — sector scan

For each region, calculate a sector score using non-redundant evidence:

1. relative strength/weakness versus the broad local market;
2. breadth and participation within the sector;
3. relative volume, turnover and dollar-volume expansion;
4. gap acceptance, failed gap or failed reclaim quality;
5. 1H trend or deterioration;
6. completed 15m trigger availability;
7. liquidity, spread and execution quality;
8. event, suspension, VI, price-limit and corporate-action risk.

Return separately:

- best sector to enter;
- best sector to short;
- strongest momentum sector;
- sector where cash/no trade is superior.

A sector is not tradable merely because one stock has a large move. Require at least three independent sector confirmations and evidence from more than one constituent where possible.

### Stage 2 — stock selection inside chosen sectors

Deep-analyse at most three stocks from each selected sector. A stock must not receive `ENTRY NOW` when its sector is materially weak, and must not receive `SHORT NOW` when its sector is materially strong, unless explicitly labelled counter-trend with reduced model risk.

External liquid names may outrank the seed list. The seed list is not a mandatory display board.

## Market sessions

Resolve actual exchange state, holidays, half-days and severe-weather arrangements.

### Hong Kong

- PRE-OPEN / AUCTION: 09:00-09:30 HKT — conditional states only.
- CONTINUOUS RTH: 09:30-12:00 and 13:00-16:00 HKT.
- LUNCH: 12:00-13:00 — no new ordinary single-name entry.
- CLOSING AUCTION: no new single-name entry.

### South Korea

- KRX regular session: 09:00-15:30 KST / 08:00-14:30 HKT.
- Pre/post-market: conditional states only.
- Avoid new entries inside the configured final closing-risk window.

A valid HK/KR regular-session setup may produce `ENTRY NOW` or `SHORT NOW` while the US is closed.

## Source hierarchy

1. IBKR is primary for exact contract, exchange, currency, fresh quote, completed bars, positions and borrow/shortability. Retry once.
2. Alpaca has no HK/KR authority.
3. On IBKR failure, use an official exchange, issuer or reliable public source as `PUBLIC FALLBACK`. Never splice sources within one series.
4. GitHub is policy and transaction-journal authority only.

## Data completeness

Preferred completed coverage per serious candidate:

- weekly 60 bars;
- daily 252 bars;
- 1H 80 bars;
- 15m 100 bars.

Verify count, first/last timestamp, sorted/unique, exchange timezone and completed-interval status. Exclude auction-only, incomplete and synthetic zero-volume intervals.

## Long execution

During valid HK/KR regular session, issue `ENTRY NOW` only when:

- selected sector has a positive tradable score and is not materially weakening;
- fresh 1H setup is valid;
- completed 15m breakout, reclaim, higher low or successful retest exists;
- market-now R/R to TP2 is at least 2R;
- spread, liquidity and event conditions are acceptable;
- tactical and structural stops are defined;
- stock score is at least 6.5.

Scores 6.5-6.9 may be actionable without PASS 2. Scores at or above 7.0 require a second fresh IBKR snapshot or labelled public fallback validation.

## Short execution

A HK/KR single-stock `SHORT NOW` additionally requires:

- selected sector is genuinely weak;
- exact shortable/borrow status;
- exchange short-sale eligibility and restrictions checked;
- fresh 1H deterioration;
- completed 15m breakdown or failed reclaim;
- at least three independent confirmations;
- R/R to cover target 2 at least 2R;
- acceptable squeeze, event and execution risk.

If borrow or eligibility is unavailable, use conditional/watch only.

## Report requirements

Near the top of every report show:

1. `GLOBAL SECTOR ROTATION BOARD` — best long sector and best short sector across open markets;
2. `HK SECTOR BOARD` — maximum five sector rows;
3. `KR SECTOR BOARD` — maximum five sector rows;
4. `TOP HK/KR STOCK CANDIDATES` — only stocks from qualified sectors, maximum three per selected sector.

Do not print full HK/KR fixed-core tables. Do not print a 7709/7747 trade board. Positions in those products may appear only in overlap/risk.

For each serious candidate show sector, setup family, source/time, entry or rejection zone, tactical/structural stop, TP1, TP2, three-price R/R, spread/turnover, event/borrow/squeeze and rejection code.

## Trade journal

Record genuine lifecycle events only under `dynamic_discovery_policy.md`, using exchange-qualified tickers. Routine sector scans and unchanged conditional plans do not create GitHub commits.

Never fabricate data, never call a close live, never stay silent and never place orders.
