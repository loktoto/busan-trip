# Adaptive Entry and Expanded Discovery Policy

Status: PRODUCTION SUPPLEMENT  
Order authority: NONE  
Timezone: Asia/Hong_Kong  
Effective from: 2026-08-05 15:05 HKT, the next scheduled hourly run after approval.

This supplement is mandatory for every Global Sector-First Day-Trade TA monitor run after the effective time. It does not weaken the existing `ENTRY NOW`, `SHORT NOW`, PASS 2, liquidity, event, borrow or risk controls.

## 1. Entry architecture

Every serious long candidate must be assessed separately for participation and confirmation. Use the following states where applicable:

- `ANTICIPATORY STARTER NOW`
- `ENTRY NOW`
- `CONFIRMED STARTER NOW`
- `ADD NOW`
- `WAIT FOR RETEST`
- `BREAKOUT WATCH`
- `DO NOT CHASE`
- `NO SETUP`

### Anticipatory starter

May be issued during the permitted continuous/RTH session when all of the following are satisfied:

- sector direction and breadth are supportive;
- daily regime is not bearish;
- the stock has stable or improving relative strength;
- entry is near defined support rather than after an extended impulse;
- tactical and structural invalidation are explicit;
- preferred-entry R/R to TP2 is at least 2.5R;
- spread, liquidity and event risk are acceptable;
- score is at least 6.5.

Monitoring size label: 20–30% of planned exposure. A starter does not waive the need for a fresh completed trigger before a normal full entry.

### Normal entry

`ENTRY NOW` remains governed by the existing production rules: fresh valid 1H setup, completed 15m trigger, defined stops, market-now TP2 R/R at least 2R, acceptable execution and score at least 6.5. Score at or above 7.0 requires PASS 2.

### Confirmed starter and add

- `CONFIRMED STARTER NOW`: score at least 7.0, completed 15m trigger, valid 1H setup, PASS 2 and at least 2R.
- `ADD NOW`: an existing active model signal, successful completed retest or continuation, no new conflict, score at least 7.0, PASS 2 and normally at least 1.5R remaining.

Never add merely because price rose after the first signal.

## 2. Two-axis diagnostics

Keep the official production score unchanged, but also report:

### Opportunity Quality, 0–10

- sector regime and breadth: 25%;
- stock relative strength/weakness: 20%;
- liquidity and relative volume: 15%;
- daily/1H structure: 20%;
- catalyst and gap quality: 10%;
- extension and available price space: 10%.

### Execution Readiness, 0–10

- completed 15m trigger: 30%;
- stop clarity: 20%;
- market-now R/R: 20%;
- spread and depth: 15%;
- event/borrow restrictions: 10%;
- 5m refinement: 5%.

These are diagnostic fields and never replace the official score or mandatory execution rules.

## 3. Discovery expansion

The fixed 21-name board remains mandatory and unchanged. Dynamic Discovery must search beyond it and must not be dominated by AI, semiconductor, optical or crypto themes merely because those names dominate the fixed board.

Retain the existing liquid seed universe and add research coverage for the following buckets when reliable data is available:

- data-centre power/electrification: VRT, ETN, PWR, GEV, CEG, VST, NRG, DELL, SMCI;
- aerospace/defence/space: AVAV, KTOS, RDW, ASTS, PL, RTX, LHX, NOC;
- cybersecurity/cloud: RBRK, ZS, NET, DDOG, SNOW, MDB, OKTA, GTLB;
- storage/memory adjacencies: WDC, STX, MRVL, QCOM, AVGO, MCHP;
- financial trading beta: HOOD, COIN, IBKR, CME, CBOE, SCHW;
- industrials/transport: CAT, DE, URI, CARR, TT, UBER, FDX, UPS;
- liquid healthcare leaders: LLY, NVO, VRTX, REGN, ISRG, TMO.

Default ordinary dynamic filters remain:

- price at least US$10;
- average daily dollar volume at least US$50 million;
- RTH spread no wider than 0.35%;
- completed daily and 1H data;
- no unresolved corporate action;
- no disqualifying near-term event.

Use a broad lightweight scan as capacity permits, but deep-analyse no more than 15 names and display no more than 10 dynamic names per run.

## 4. Strategy priority

Evaluate these setup families independently in this order:

1. sector-leader pullback continuation;
2. failed-reclaim short in a weak sector;
3. relative-strength continuation;
4. opening-range retest;
5. power-hour ETF momentum;
6. momentum breakout/breakdown;
7. catalyst-gap acceptance or rejection.

Opening-range retest, power-hour momentum and pure VWAP-reclaim ideas remain experimental. They may not override the normal 1H/15m, R/R, spread, event and borrow requirements.

## 5. ETF execution track

Maintain a separate liquid ETF candidate track using, where available:

- SPY, QQQ, IWM, DIA;
- XLK, XLF, XLI, XLE, XLV, XLY, XLP, XLU, XLB, XLC;
- SOXX/SMH as one semiconductor sleeve;
- IGV, SKYY and ARKK.

Report the best liquid ETF trade independently from the best single-name trade. Faster bars may refine an already valid setup but may never create a trade alone.

## 6. Sector participation evidence

For each selected sector, attempt to report:

- sector ETF relative return versus the broad benchmark;
- percentage of tracked constituents above VWAP;
- percentage above the opening-range midpoint;
- median constituent return;
- fraction with relative volume above 1.5;
- equal-weight versus cap-weight confirmation;
- leader-laggard dispersion.

A sector driven by one constituent receives a breadth penalty. Missing metrics must be labelled N/A rather than inferred.

## 7. No-chase and false-start controls

Use the tightest applicable chase limit among:

- one configured ATR;
- half of the current 15m impulse leg;
- the distance consistent with a structural stop and at least 2R;
- the configured spread-adjusted loss limit.

Starter controls:

- maximum two starter attempts per ticker per session;
- maximum one re-entry after a full structural stop;
- no immediate re-entry without a newly completed 15m structure;
- cap aggregate starter risk within one sector;
- never journal a starter unless the report explicitly issued the live lifecycle event.

## 8. Reporting requirements

Every run after the effective time must show, for the leading candidates:

- official production score;
- Opportunity Quality;
- Execution Readiness;
- exact state: starter, normal entry, confirmed starter, add, conditional, wait, no chase or no setup;
- market-now, preferred-zone and confirmation-entry R/R;
- tactical and structural invalidation;
- primary rejection code where not actionable.

The Boss Action must distinguish clearly between a starter opportunity and a confirmed entry.

## 9. Research integrity

Do not lower the anticipatory-starter threshold below 2.5R without a cost-adjusted, journal-backed backtest. Do not claim that more trades improve profitability. Evaluate expectancy net of spread, slippage, fees, missed fills and borrow costs.
