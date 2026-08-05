# Mandatory Report Delivery Contract

Status: HIGHEST-PRIORITY DELIVERY SUPPLEMENT  
Order authority: NONE  
Timezone: Asia/Hong_Kong

## Only valid final output

Every scheduled or manually invoked run must immediately execute data collection and return the monitor report itself. The only valid final output is the complete report for that run.

Never return:

- confirmation;
- prompt review;
- settings summary;
- improvement suggestions;
- execution explanation;
- capability disclaimer;
- tool-unavailable-only response;
- refusal or meta commentary instead of the report.

If a source fails, degrade the affected field or row and continue. A source failure is report content, not a reason to replace the report.

## Independent module execution

All collection modules are independent. Failure of one module must never cancel later modules.

Execute, where applicable:

1. session clocks and calendars;
2. IBKR account/positions/quotes/history/borrow modules;
3. Alpaca market clock, snapshots and bars for US fallback;
4. official/public HK/KR fallback modules;
5. sector calculations;
6. fixed long board;
7. Dynamic Discovery;
8. semiconductor short board;
9. software short board;
10. Burry board;
11. PASS 2 modules;
12. position-overlap analysis;
13. GitHub lifecycle journal only when a genuine lifecycle event exists.

Every failed module must record attempts, last reliable freshness when known and confidence effect, then execution must continue.

## Fixed-board research and catalyst escalation

Every configured fixed-board symbol is a mandatory research target, not merely a display row. A fixed name must never be omitted, treated as newly discovered, or ranked from a quote alone.

For every fixed-board symbol, attempt and record independently:

- exact contract resolution;
- fresh quote and spread;
- prior completed daily bar and current-session gap;
- relative performance versus its sector benchmark;
- known earnings, company release, SEC filing or other material catalyst;
- fresh 1H and completed 15m evidence when the market/session permits.

Deep-dive escalation is mandatory before ranking when any fixed-board name has one or more of the following:

- absolute current-session gap of at least 5%;
- prior-session move of at least 8%;
- current or prior-session volume materially above its recent norm;
- a scheduled earnings event within five trading sessions;
- a fresh official filing, earnings release, guidance change, supply agreement or material corporate event;
- leadership in the strongest or weakest sector of the run.

A deep-dive escalated fixed name must receive:

1. IBKR snapshot;
2. a second-source US parity check where permitted;
3. 1H and 15m structure attempts;
4. official catalyst verification;
5. direct comparison with the strongest relevant peer or competing setup.

When two fixed-board names compete for Best Trade Now, compare them on the same timestamp and fields: gap, spread percentage, liquidity/dollar volume, volatility, catalyst quality, event risk, sector confirmation, trigger quality, extension, market-now R/R and portfolio overlap. Do not switch the preferred name merely because the user mentions it; show what new evidence changed the ranking.

If any mandatory field is unavailable, state the missing field and confidence penalty. Missing research must never be silently converted into `NO SETUP`.

## Minimum output contract

Even when every IBKR, Alpaca, public fallback and GitHub module fails, return the complete report skeleton in the mandatory order. Preserve every mandatory US fixed-board row and every mandatory software-core row. Use `N/A — 未取得可靠資料`; never guess.

The minimum report must still include:

1. headline action or `NO NEW ACTIONABLE TRIGGER`;
2. exact HKT/ET/KST and market states;
3. Global Sector Rotation Board;
4. Executive Dashboard and Best Trades Now;
5. Source Status/Data Coverage;
6. completed-week/live-week context or explicit N/A;
7. all 21 US fixed long rows;
8. US Dynamic Discovery section;
9. HK sector section;
10. KR sector section;
11. semiconductor short section;
12. full software-core short section;
13. all seven Burry rows with explicit CAT decision;
14. PASS 1/PASS 2 ledger;
15. existing-position overlap/risk or N/A;
16. failed modules/retries/freshness/confidence effect;
17. one-line Cantonese Boss Action.

When execution evidence is insufficient, use `CASH / NO TRADE`, not a missing report.

## Data labels

Use only:

- LIVE;
- DELAYED-LIVE;
- OFFICIAL CLOSE;
- PUBLIC FALLBACK;
- PREVIOUS SNAPSHOT;
- STALE;
- N/A.

Never call a close live. Never use a previous snapshot to calculate current position size or current market-now R/R. Never invent missing values.

## Tool-use requirement

Before rendering a non-holiday run, make actual source attempts rather than inferring unavailability:

- attempt IBKR first;
- retry/recover according to `source_escalation_policy.md`;
- attempt Alpaca for permitted US modules;
- attempt reliable public fallback for unresolved modules;
- then render the report regardless of outcome.

The presence of a working IBKR account endpoint, Alpaca clock or GitHub read proves the connector class is available; failure of a different endpoint must be treated as a local module failure rather than global tool unavailability.

## Adaptive entry and expanded discovery supplement

Effective from the scheduled run at **2026-08-05 15:05 HKT** and every run thereafter, fetch and obey `ta-monitor/adaptive_entry_and_expanded_discovery_policy.md` in addition to the existing mandatory policy set.

The supplement is binding for production reporting and model-state decisions. It introduces explicit anticipatory-starter, confirmed-starter and add states; Opportunity Quality and Execution Readiness diagnostics; broader sector-balanced Dynamic Discovery; a separate liquid-ETF track; sector-participation metrics; and false-start/no-chase controls.

It does not reduce any existing requirement for normal `ENTRY NOW`, `SHORT NOW`, PASS 2, 2R market-now R/R, 2.5R anticipatory-starter preferred-entry R/R, fresh bars, spread, liquidity, event or borrow checks.

## Pre-send quality gate

Internally verify before sending:

- the output is the report itself, not meta commentary;
- every mandatory section is present;
- every mandatory row is present;
- each fixed-board name was researched rather than merely displayed;
- every gap >=5%, prior-session move >=8%, near-term event or fresh catalyst received deep-dive escalation;
- competing fixed-board candidates were compared on the same timestamp and evidence fields;
- session labels match exact time/calendar;
- quote labels are not mixed;
- failures are localised rather than cancelling the report;
- `ENTRY NOW`/`SHORT NOW` has fresh 1H, completed 15m, stops, >=2R and execution checks;
- every anticipatory starter has supportive sector evidence, defined support/stops and preferred-entry R/R >=2.5R;
- every leading candidate shows the official score, Opportunity Quality, Execution Readiness, exact entry state and three-price R/R where data permits;
- scores >=7.0 have PASS 2 or are downgraded;
- CAT has an explicit current decision;
- no routine GitHub journal entry is claimed without a lifecycle event;
- the Boss Action distinguishes starter versus confirmed entry and is present.

If any check fails, repair the report before sending. Do not replace it with an explanation.
