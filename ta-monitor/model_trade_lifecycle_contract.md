# Model Trade Lifecycle Timing Contract

Status: AUTHORITATIVE JOURNAL SUPPLEMENT  
Order authority: NONE  
Timezone: Asia/Hong_Kong

## Core rule

The monitor's own published signal defines the model-trade lifecycle timestamp.

- `ENTRY NOW` or validated equivalent becomes the model ENTRY at the exact HKT/ET/KST timestamp when the report containing that action is sent.
- A published TP1, TP2, SL, CLOSE or qualified `INVALIDATED_BEFORE_ENTRY` becomes effective at the exact timestamp when that lifecycle action is sent.
- Do not backdate an entry, target hit, stop, close or invalidation to an earlier bar, quote or chart time.
- Do not claim a model trade, realised profit, return percentage or lifecycle event unless the corresponding GitHub journal record exists.

## Required journal fields

Every genuine model lifecycle event must be written to GitHub with:

- ticker and market;
- direction;
- lifecycle event: ENTRY, TP1, TP2, SL, CLOSE or INVALIDATED_BEFORE_ENTRY;
- exact sent timestamp in HKT, ET and local exchange time;
- report/session identifier where available;
- published entry price or execution reference price;
- published tactical stop;
- published structural stop;
- published TP1 and TP2;
- position size or model units when explicitly defined;
- source label and quote timestamp;
- reason/setup;
- realised and unrealised P&L only when all required prices and size are known.

## Price convention

The model execution reference is the fresh executable market price quoted in the report at send time, unless the report explicitly publishes a conditional trigger price. For conditional trades, no ENTRY exists until a later report explicitly confirms the trigger and sends `ENTRY NOW`.

TP1, TP2 and SL are not automatically journalled merely because an old bar later appears to have crossed them. The monitor must detect the event with fresh data and send the lifecycle action; the send timestamp is the authoritative event time.

## Missing data

If entry price, exit price or size is missing, report P&L as `N/A — insufficient journal fields`. Never estimate or reconstruct realised profit from stale snapshots.

## Routine runs

A routine monitor run with no genuine lifecycle change must not create a trade-journal event or claim a commit.

## AXTI correction

Any prior statement that AXTI reached TP1 or closed is not a verified model lifecycle event unless a matching GitHub ENTRY and subsequent lifecycle record exists. Without those records, AXTI realised P&L is N/A.
