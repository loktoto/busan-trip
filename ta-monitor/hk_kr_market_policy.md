# Hong Kong / Korea Intraday Day-Trader Policy

Status: MANDATORY_SUPPLEMENT_TO_PRODUCTION_POLICY  
Effective: 2026-07-31  
Order authority: NONE  
Timezone: Asia/Hong_Kong  
Precedence: this policy controls HKEX/KRX collection, session classification and execution whenever older US-only wording conflicts.

## Objective

Add Hong Kong and South Korea cash equities and exchange-traded products to the existing global day-trading monitor without weakening or replacing any US board. HK and KR boards are independent from the US fixed long, US Dynamic Discovery, semiconductor short, software short and Burry boards. Scores must never be averaged across boards.

Every hourly run must determine whether HKEX, KRX and the US market are open. A valid HK or KR RTH setup may produce `ENTRY NOW` or `SHORT NOW` even while the US market is closed.

## Mandatory configuration

Fetch and obey `ta-monitor/hk_kr_config.py` every run. Execute:

- `HK_FIXED_CORE`;
- `KR_FIXED_CORE`;
- `HK_DISCOVERY_SEED` and `KR_DISCOVERY_SEED`;
- `HK_BENCHMARKS` and `KR_BENCHMARKS`;
- `ASIA_COMPLEX_PRODUCTS`;
- `ASIA_DAY_TRADER_RULES` and `ASIA_SHORT_RULES`.

The monitor must preserve every configured fixed-core row even when data fail.

## Market sessions

Resolve holidays, half-days, severe-weather arrangements and actual exchange state from IBKR and official exchange calendars where available. Do not infer that a weekday is automatically open.

### Hong Kong

- PRE-OPEN / AUCTION: 09:00-09:30 HKT. Conditional states only.
- CONTINUOUS RTH: 09:30-12:00 and 13:00-16:00 HKT on full trading days.
- 12:00-13:00 must be labelled `HK LUNCH / EXTENDED MORNING`; do not create a new ordinary single-stock entry from a synthetic lunch bar.
- CLOSING AUCTION: from 16:00 to the exchange close. No new single-stock day-trade entries.
- Half-day schedules and severe-weather sessions must follow the current official HKEX calendar.

### South Korea

- KRX REGULAR SESSION: 09:00-15:30 KST, equivalent to 08:00-14:30 HKT.
- Pre-market and post-market sessions are context only; new single-stock day-trade entries require the regular session.
- Avoid new entries during the final configured closing-risk window unless the setup is an explicit index/ETF execution plan with reliable liquidity.

## Source hierarchy

### HK and KR equities

1. IBKR is the primary quote, contract, position and completed-bar authority. Resolve exact contract, exchange and currency. Retry a failed endpoint once.
2. Alpaca has no HK/KR equity authority and must not be used as an Asia-market quote or historical fallback.
3. If IBKR fails, use the official exchange, issuer, ETF manager or another reliable public market-data source available to the run. Label the exact source, delay and timestamp. Public fallback may support a degraded row but must not be blended into an IBKR historical series.
4. Never splice sources within one ticker/timeframe series. Replace the complete affected series and label `PUBLIC FALLBACK`.
5. GitHub is policy and journal authority only, never fresh market data.

For HK/KR public fallback, retry the exact symbol once, then a benchmark/cross-check source once. If reliability remains inadequate, use `N/A — 未取得可靠資料` and continue.

## Data completeness

Preferred completed coverage per symbol remains:

- weekly: 60 bars;
- daily: 252 bars;
- 1H: 80 bars;
- 15m: 100 bars.

Verify count, first/last timestamp, sorted/unique status, exchange timezone and completed-interval status. Exclude auction-only, incomplete current and synthetic zero-volume intervals from confirmation calculations.

For HK lunchtime, do not treat a bar spanning the midday break as a normal continuous 1H/15m confirmation unless the data source explicitly represents valid exchange trades and the bar construction is understood.

## Asia day-trader execution

Use the same evidence-weighted model as production:

- weekly/daily: regime, major levels and event context;
- 1H: active direction and setup;
- completed 15m: execution trigger;
- 5m: refinement only.

During HK or KR regular trading, issue `ENTRY NOW` when all conditions hold:

- fresh valid 1H setup aligned or not clearly opposing;
- completed 15m breakout, reclaim, higher low or successful retest;
- market-now R/R to TP2 at least 2R;
- executable spread and liquidity within market-specific limits;
- defined tactical and structural stops;
- no disqualifying event, suspension, volatility-interruption or product-structure risk;
- score at least 6.5.

Scores 6.5-6.9 may be actionable without mandatory PASS 2 when every execution condition is satisfied. Scores at or above 7.0 require PASS 2 with a second fresh IBKR snapshot. If IBKR retry fails, use a second independent public quote only as `PUBLIC FALLBACK PASS 2`; withhold action on conflict.

Pre-open, lunch, closing auction and post-market may issue conditional states only. Do not repeatedly output WATCH when a valid regular-session trigger meets policy.

## Asia short discipline

High valuation, a large gap or a weak candle alone is never a short signal.

A HK/KR single-stock `SHORT NOW` requires:

- exact exchange contract;
- current shortable/borrow status where available;
- borrow fee and available quantity where available;
- current exchange short-sale eligibility, price-test or other applicable restriction check;
- fresh 1H deterioration;
- completed 15m breakdown or failed reclaim;
- relative weakness versus the local benchmark/sector;
- at least three independent confirmations;
- market-now R/R to cover target 2 at least 2R;
- acceptable spread, event and squeeze risk;
- score at least 6.5.

If shortability, borrow or exchange eligibility is unavailable, do not issue a single-stock `SHORT NOW`; retain `CONDITIONAL SHORT`, `BREAKDOWN WATCH` or `DATA UNAVAILABLE`. Never assume US short-sale rules apply to HKEX or KRX.

## Dynamic Discovery — Asia

Run HK and KR discovery independently every hour during the relevant market day.

Stage 1 should screen current liquid leaders and laggards using:

- turnover and dollar-volume;
- relative volume;
- gap quality;
- relative strength/weakness versus local benchmark;
- sector breadth;
- clean technical level and catalyst;
- spread and tradability;
- suspension, volatility interruption, corporate action and event risk.

Stage 2 performs weekly/daily/1H/15m analysis on the best candidates. The fixed core remains intact; external candidates may outrank it in `BEST TRADES NOW` when objectively superior.

## Leveraged and complex products

Products in `ASIA_COMPLEX_PRODUCTS` are not ordinary equities.

For 7709 and 7747:

- use the underlying KRX stock as the primary directional signal;
- obtain the current official fund iNAV/NAV chain when available;
- calculate executable premium/discount from a reliable tradable bid or midpoint only under the configured rules;
- check product spread, turnover, leverage reset, tracking, swap/options structure and volatility drag;
- no `ENTRY NOW` when official iNAV is required but unavailable, or when premium/spread exceeds configured limits;
- do not short these leveraged products as a substitute for a bearish underlying view;
- keep their existing dedicated premium/rotation rules separate from ordinary TA scoring.

## Risk and market microstructure

- Use local tick size, board lot, currency and settlement context.
- Detect suspensions, trading halts, volatility interruption and price-limit conditions.
- Do not chase a limit-up/limit-down or volatility-interruption release.
- Penalise low free float, placement/rights-issue risk, regulatory headlines and overnight gap risk.
- For cross-listed or ADR relationships, use them as context only unless timestamps overlap and the conversion basis is explicit.
- Model maximum portfolio loss remains within the production 0.25%-0.40% range; Asia FX and overnight risk must be stated.

## Report requirements

Near the top, show separate market states:

- `HK MARKET MODE`;
- `KR MARKET MODE`;
- `US MARKET MODE`.

Add these sections after the US Dynamic Discovery Board and before the US semiconductor short board:

1. `HONG KONG DAY-TRADE BOARD` — every `HK_FIXED_CORE` row plus qualified dynamic names;
2. `KOREA DAY-TRADE BOARD` — every `KR_FIXED_CORE` row plus qualified dynamic names;
3. `ASIA COMPLEX / LEVERAGED PRODUCT BOARD` — every configured product including 7709 and 7747.

For each serious Asia candidate show:

- exact code, exchange and currency;
- fresh price and quote status;
- local session;
- setup family;
- score and direct state;
- entry/trigger zone;
- tactical and structural stop;
- TP1 and TP2;
- three-price R/R;
- spread, volume and relative-strength status;
- event, suspension, borrow and squeeze status;
- rejection code when not actionable.

`BEST TRADES NOW` may compare US, HK and KR opportunities, but must preserve each board's independent raw score and apply a session filter. A closed-market candidate cannot outrank a valid open-market executable setup merely because its historical score is higher.

## Trade journal

Follow `dynamic_discovery_policy.md`: GitHub records transaction lifecycle events only. Use the exchange-qualified ticker in `trade_id` and journal fields, for example `0700@SEHK` or `005930@KRX`. Never record an Asia `ENTRY`, `TP` or `SL` without fresh reliable local-market data.

Never fabricate data, never call an official close live, never stay silent and never place orders.
