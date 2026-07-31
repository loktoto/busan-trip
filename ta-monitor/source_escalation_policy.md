# Source Escalation and Guaranteed-Delivery Policy

Status: MANDATORY_SUPPLEMENT_TO_PRODUCTION_POLICY  
Effective: 2026-07-31  
Order authority: NONE

## Objective

The monitor must complete and deliver the report even when one or more connected sources fail. Source failure may degrade only the affected field, ticker or timeframe; it must never terminate the run or replace the report with a refusal or error-only response.

"Keep trying until the report is done" means continue through the bounded source-escalation ladder below and then render the full report with explicit N/A fields where reliable data remain unavailable. Do not retry indefinitely and delay delivery.

## Source priority

1. Interactive Brokers (IBKR) — first and primary equity/account source for US, HK and KR.
2. Alpaca — second source for US equities only.
3. Reliable public fallback — official exchange, issuer, ETF/fund manager, regulator or another reputable market-data source available to the run.
4. Binance — optional crypto context only; never a blocking dependency and zero equity authority.
5. GitHub — policy, calculation identity and transaction-journal record only; never fresh market data.

## IBKR multi-retry contract

Every required IBKR module is independent. Failure of one module must not cancel later modules.

For each required endpoint or ticker/timeframe, allow up to three total attempts:

1. Primary attempt using the exact resolved contract and preferred exchange/routing.
2. Retry after refreshing contract resolution, exchange, security type and currency; use the same requested data definition.
3. Recovery attempt using a technically equivalent IBKR request where available, such as a smaller symbol batch, smaller bar window, `step_count` instead of `period`, native exchange instead of SMART, or a reduced market-data field bundle.

Do not call incompatible requests equivalent. Never mix two IBKR series inside one ticker/timeframe calculation. Replace the whole affected series if the recovery method changes its construction.

Account Summary, Balances, Positions, Orders, Trades, Performance, Allocation, Price Snapshot, Price History, option data and borrow/shortability checks must run independently. Record attempt count, final error/status, retrieval timestamp and confidence impact.

## Alpaca second-source ladder

Alpaca has authority for US equities only and must not be used for HK/KR quotes or bars.

For US snapshots and completed bars:

1. SIP;
2. delayed SIP;
3. IEX.

Overnight/BOATS feeds may be used only for clearly labelled overnight context. They may not replace completed RTH bars for a formal RTH-derived signal.

When an Alpaca series changes feed, replace the whole ticker/timeframe series. Never splice feeds. Retry truncated or deficient bulk responses ticker-by-ticker on the same feed before falling to the next feed.

## Public fallback ladder

When IBKR and permitted Alpaca attempts fail, actively use the best reliable method available rather than stopping.

US priority:

1. official exchange, ETF sponsor, issuer investor-relations or regulator data;
2. exchange-linked or institutional market-data source;
3. reputable public quote/history source, preferably cross-checked against a second independent source.

HK/KR priority:

1. HKEX/KRX official data or calendar;
2. issuer or ETF/fund-manager official data;
3. reliable public market-data source with exact exchange-qualified symbol and timestamp.

Label every non-IBKR/Alpaca value `PUBLIC FALLBACK`, including source, delay, quote type and timestamp. A public fallback may support a formal signal only when timestamp, session, adjustment treatment, spread and latest completed interval are reliable and there is no material cross-source conflict. Otherwise downgrade to conditional/watch or N/A.

Never average conflicting sources. Never use a previous snapshot, official close or search-result snippet as a live quote.

## Binance

Binance is optional. Skip it when unavailable or when it adds no relevant context. A Binance failure must never delay or reduce the equity report. Crypto data cannot create, cancel or modify an equity entry, short or hedge signal.

## GitHub record policy

GitHub is used for:

- policies and configuration;
- deterministic calculation identity;
- genuine model-trade lifecycle journal events;
- optional compact failure/audit metadata where current policy permits.

GitHub is not used as fresh quote/history data. Do not commit credentials, account details, licensed raw bars, orders or private position data. A GitHub read/write failure must not block the report; state the failure and continue.

## Guaranteed report output

After the escalation ladder, always render the complete required report.

- Preserve mandatory boards/sections.
- Use `N/A — 未取得可靠資料` only after the relevant IBKR attempts, Alpaca attempts where permitted and public-fallback attempts have failed or conflicted.
- State retries, source tier, last reliable timestamp and confidence impact.
- Calculate and rank every independently valid module.
- If all market-data sources fail, issue the complete manual degraded skeleton with no fabricated prices or signals and a conservative CASH / NO TRADE conclusion.
- Never answer only that tools are unavailable.

## Pre-send gate

Before delivery confirm:

1. IBKR was attempted first with the multi-retry contract.
2. Alpaca was attempted second for US data where needed.
3. Public fallback was attempted for unresolved required fields.
4. Optional Binance failure did not block delivery.
5. GitHub was treated as record/policy only.
6. The report itself, not a refusal or prompt explanation, is being delivered.
