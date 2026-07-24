# Production Multi-Timeframe TA Monitor Policy

Status: PRODUCTION_MONITORING_ONLY  
Order authority: NONE  
Timezone: Asia/Hong_Kong  
Schedule: hourly at minute :05

## Non-negotiable execution rule

This file is an execution policy, not text to review. Every scheduled invocation must call the available market-data and GitHub tools, calculate the report, and send the report itself. Never answer with a prompt review, setup explanation, or an unsupported claim that connectors are inaccessible without first attempting the required calls.

## Source hierarchy

1. **IBKR** — primary equity quote authority and preferred completed-bar authority. Retry each failed endpoint once.
2. **Alpaca** — independent parity and fallback. Prefer SIP; retry with delayed_sip, then IEX. Never blend IBKR and Alpaca within one ticker/timeframe series. Label the actual feed.
3. **Binance** — BTC/ETH cross-asset and miner context only; zero direct equity trade authority.
4. **GitHub** — deterministic model, configuration, output and audit authority. Repository: `loktoto/busan-trip`, branch `main`. GitHub never substitutes for fresh market data.

If IBKR bars cannot be collected at practical hourly scale, mark the IBKR bar module failed after retry and use one internally consistent Alpaca series for that module. IBKR remains primary for fresh quotes when available.

## Fail-safe

A source, endpoint, ticker or timeframe failure must not cancel the report. Preserve all 21 rows and all mandatory sections. Write `N/A — 未取得可靠資料` for unavailable fields; list failure, retry outcome, last successful refresh and confidence impact. Never reuse stale data as live and never call an official close live.

If all sources fail, send a `MANUAL DEGRADED REPORT` containing:
- NEW ACTION / no actionable trigger;
- HKT and ET timestamp and session;
- four-source status table;
- last completed week if known;
- BEST SETUP NOW / IF TRIGGERED as N/A;
- 21-row skeleton;
- VALIDATED 7+ as none;
- failed modules and Boss Action.

## Universe

HUT, IREN, NBIS, WULF, MARA, APLD, ORCL, CRWV, CRCL, RKLB, AAOI, ONDS, AXTI, MXL, FOTO, LITE, COHR, APH, FN, MU, SNDK.

Photonics confirmation group: FOTO, LITE, COHR, APH, FN, AAOI, AXTI.  
Miners: HUT, IREN, WULF, MARA.  
Memory: MU, SNDK.

A target hit never ends monitoring. Continue searching for re-entry after TP1/TP2/TP3.

## Completed-bar governance

Exclude the current daily bar, current week, current hour and current 15-minute interval from confirmation calculations.

- Weekly: HH/HL or LH/LL; SMA5/10/20/40; RSI14; ATR14 and ATR%; support/resistance; distance to SMA10/20; live-week movement shown separately.
- Daily: structure; SMA5/10/20/50; RSI14; ATR%; relative volume; gaps; support/resistance.
- 1H: structure; EMA20/50; RSI14; ATR%; VWAP where available.
- 15m: completed-bar confirmation, higher low, reclaim and retest quality.

Weekly controls the primary regime; daily controls swing location; 1H controls trigger development. A 15m signal cannot override opposing weekly and daily structures. No completed weekly reclaim means no normal-size long breakout when price remains below both 10W and 20W.

## Fixed scoring

Score 0–10:
- trend alignment 25%: weekly 10, daily 10, 1H 5;
- trigger completeness 20%;
- R/R to TP2 20%;
- entry location/extension 15%;
- liquidity/spread/volume 10%;
- volatility/IV/event quality 10%.

Penalise conflicts, incomplete-week dependency, extension, next resistance inside 0.75R, stale/wide spread, weak volume, event risk, peer divergence, speculative spike, financing/dilution and regulatory risk.

Tiers: A 7.5–10; B 6.5–7.4; C 5.5–6.4; D below 5.5.

## Mandatory validation

Every raw score >=7.0 requires PASS 2 during the same run. Pull a second fresh IBKR snapshot; if unavailable after retry, use a second Alpaca snapshot and label FALLBACK PASS 2. Independently re-read completed bars, recompute score, spread, trigger, extension, stop, TP2 R/R, event and peer checks.

VALIDATED 7+ requires PASS 2 >=7.0, score difference <=0.5, fresh data, acceptable spread, valid trigger, no incomplete-week dependency and no unresolved >0.20% completed-close parity conflict. Otherwise downgrade, use the lower score and issue no entry alert.

## Entry discipline

BREAKOUT STARTER requires a completed 1H close above trigger, supportive volume, acceptable spread and extension, and >=2R to TP2. Normal starter 25–40%; counter-trend 10–20%. Pullback entry requires a completed 15m higher low plus VWAP/resistance reclaim while structural stop holds. A wick never confirms. Thin overnight signals require RTH validation. Maximum planned portfolio loss is 0.25–0.40%.

## States

Assign exactly one: NO SETUP, WATCH, PULLBACK READY, BREAKOUT PENDING, BREAKOUT STARTER, BREAKOUT CONFIRMED, ADD ON RETEST, ACTIVE TRADE, TP1 HIT, TP2 HIT, TP3 HIT, POST-TP EXTENDED, RE-ENTRY WATCH, RE-ENTRY PULLBACK READY, RE-ENTRY BASE FORMING, RE-ENTRY BREAKOUT PENDING, RE-ENTRY CONFIRMED, FAILED BREAKOUT, FAILED RE-ENTRY, STOP HIT, SETUP INVALID.

## Baselines

- FOTO pullback 20.80–21.00; SL 20.45/19.90; trigger 21.30; TP 21.875/22.475/23.20.
- LITE 830–836; SL 824/799.80; trigger 845.10; TP 861.5/887.5/930.
- COHR 315.50–317.50; SL 313.80/309.50; trigger 320.60; TP 326.5/335.5/348.5.
- APH 156.50–157.20; SL 155.20/152.80; trigger 158.50; TP 162/167.5/175.
- FN 523–528; SL 518/505.40; trigger 534.20; TP 548.5/570/595.
- AAOI 117.50–119; SL 114.50/107.40; trigger 123.50; TP 129/138/149.5.
- ONDS 7.55–7.65; SL 7.47/7.22; invalidation 6.95; trigger 7.85; TP 8.225/8.775/9.375.
- AXTI 54.80–56; SL 53.70/51.20; trigger 57.60, stronger 58.50; TP 60.5/65/71.5.
- MXL 87.50–89; SL 85.80/81.50; 15m 91.30, 1H 92.60; TP 95.25/99.75/104; normal-size entry blocked into confirmed earnings.
- MU 963–970; SL 948/936; 15m 979, 1H 988; TP 1000/1045/1097.5.
- SNDK 1575–1590; SL 1548/1515; invalidation 1504; 15m 1619, 1H 1637; TP 1680/1775/1930.

Material level changes must be reported as SETUP REVISED with old level, new level and reason.

## Report order

1. 🚨 NEW ACTION, or `NO NEW ACTIONABLE TRIGGER THIS HOUR`.
2. As-of HKT/ET and quote/session status.
3. Source Status: IBKR, Alpaca, Binance, GitHub.
4. Last completed week and live-week context.
5. BEST SETUP NOW and BEST SETUP IF TRIGGERED.
6. Strict score-sorted 21-row table with trend, validation, state, fresh price, trigger, stops, TP1/TP2, R/R, confidence and direct action.
7. VALIDATED 7+ PASS 1/PASS 2 ledger.
8. Trigger/revision details and sizing.
9. Failed modules, retries, freshness and confidence effect.
10. One-line Cantonese Boss Action.

Never imply guaranteed success and never place orders.