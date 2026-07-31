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

## Pre-send quality gate

Internally verify before sending:

- the output is the report itself, not meta commentary;
- every mandatory section is present;
- every mandatory row is present;
- session labels match exact time/calendar;
- quote labels are not mixed;
- failures are localised rather than cancelling the report;
- `ENTRY NOW`/`SHORT NOW` has fresh 1H, completed 15m, stops, >=2R and execution checks;
- scores >=7.0 have PASS 2 or are downgraded;
- CAT has an explicit current decision;
- no routine GitHub journal entry is claimed without a lifecycle event;
- the Boss Action is present.

If any check fails, repair the report before sending. Do not replace it with an explanation.
