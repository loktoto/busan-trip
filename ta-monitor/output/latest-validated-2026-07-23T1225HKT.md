# Corrected Fresh Multi-Timeframe TA Monitor

- As of: **2026-07-23 12:25 HKT / 00:25 ET**
- Session: **IBKR Overnight**
- Quote source: **IBKR live/near-live snapshots**
- OHLCV source: **Yahoo fallback for first pass; IBKR completed bars for mandatory ONDS second pass**
- Last completed weekly bar: **week ending 2026-07-17**
- Final validated 7+: **NONE**
- New model entries written to `ta-performance/signals.csv`: **NONE**

## Correction to the first-pass output

The first pass ranked ONDS at 7.05 because R/R was calculated from the old 7.85 trigger. Mandatory second-pass validation used the fresh executable price of 8.02. Executable R/R to TP2 fell to approximately 1.37R and TP1 was only approximately 0.24R away. ONDS also remained in a completed-week LH/LL structure below both 10W and 20W, while the live week was already extended approximately 0.74 weekly ATR. It was therefore downgraded to 5.55 and no entry alert was issued.

LITE is also corrected from `RE-ENTRY CONFIRMED` to `RE-ENTRY BREAKOUT PENDING`, because the fresh price 842.09 remained below the stated completed-1H trigger of 845.10.

## Best setups

- **BEST SETUP NOW:** None validated.
- **BEST SETUP IF TRIGGERED:** MU, provided a completed 15m close above 979, a completed 1H close above 988, acceptable retest quality and recalculated executable R/R of at least 2R.
- **Best pullback watch:** COHR around 315.50–317.50, but only with completed 15m higher-low/reclaim and RTH confirmation.

| Rank | Ticker | Final score | Tier | Weekly | Daily | 1H | Final state | Fresh price | Trigger | Tactical / structural SL | TP1 / TP2 | R/R to TP2 | Direct action |
|---:|---|---:|:---:|---|---|---|---|---:|---:|---|---|---:|---|
|1|LITE|6.53|B|Bearish/mixed|Recovery|Up|RE-ENTRY BREAKOUT PENDING|842.09|845.10|824.00 / 799.80|861.50 / 887.50|2.01 from trigger|Wait completed 1H above trigger and retest; counter-trend only.|
|2|ONDS|5.55|C|Down, LH/LL|Recovery|Fading LH/LL|RE-ENTRY WATCH|8.02|7.85|7.47 / 7.22|8.15–8.30 / 8.65–8.90|1.37 from fresh price|VALIDATION FAILED; wait for new base/retest.|
|3|COHR|5.10|D|Bearish/mixed|Down|Recovery|PULLBACK READY — UNVALIDATED|316.75|320.60|313.80 / 309.50|326.50 / 335.50|2.19 from trigger|Only after completed 15m higher low plus RTH reclaim.|
|4|MU|5.00|D|Mixed|Bearish/mixed|Recovery|BREAKOUT PENDING|975.00|15m 979; 1H 988|948.00 / 936.00|1000.00 / 1045.00|1.43 from 988 baseline|No entry; fresh executable R/R must improve to at least 2R.|
|5|APH|4.98|D|Up|Bearish/mixed|Recovery|WATCH — STALE/WIDE QUOTE|157.51 close|158.50|155.20 / 152.80|162.00 / 167.50|2.73 from trigger|Wait liquid RTH quote and completed 1H confirmation.|
|6|AXTI|4.77|D|Bearish/mixed|Down|Mixed|NO SETUP|54.20|57.60|53.70 / 51.20|60.50 / 65.00|1.90|Stand aside; weekly/daily opposition and extreme volatility.|
|7|SNDK|4.63|D|Mixed|Bearish/mixed|Recovery|WATCH|1601.00|15m 1619; 1H 1637|1548.00 / 1515.00|1680.00 / 1775.00|1.55|No entry; high ATR/IV and event window.|
|8|AAOI|4.54|D|Bearish/mixed|Down|Mixed|NO SETUP|112.50|123.50|114.50 / 107.40|129.00 / 138.00|1.61|Below reclaim zone; stand aside.|
|9|CRCL|4.47|D|Down|Bearish/mixed|Mixed|NO SETUP|66.66|72.86|62.57 / 58.68|77.34 / 81.83|0.87|No long setup.|
|10|ORCL|4.22|D|Bearish/mixed|Down|Mixed|NO SETUP|126.24|Re-entry 128.85; stronger daily 131.64|Recent low / structural low|131.64 / 138–140|Below requirement|Counter-trend only; wait for completed reclaim.|
|11|RKLB|4.20|D|Bearish/mixed|Down|Bearish/mixed|NO SETUP|69.98|86.30 provisional|65.35 / 62.42|91.80 / 97.30|0.52|No entry; rebuild a base first.|
|12|HUT|4.19|D|Bearish/mixed|Recovery|Recovery|RE-ENTRY WATCH|111.60|114.60|98.70 / 83.30|122.69 / 130.78|1.02|Weekly opposition and insufficient R/R.|
|13|NBIS|3.93|D|Mixed|Down|Recovery|BREAKOUT PENDING|227.88|231.75|198.71 / 164.31|250.05 / 268.35|1.11|Extended and IV extreme; no chase.|
|14|FOTO|3.63|D|Weekly data gap|Bearish/mixed|Bearish/mixed|NO SETUP / ACTIVE POSITION MANAGEMENT|20.75|21.30|20.45 / 19.90|21.88 / 22.48|1.38|Hold 90 shares; no add without completed 15m reclaim.|
|15|MARA|3.40|D|Mixed|Down|Recovery|WATCH|12.38|14.41|11.70 / 10.54|15.29 / 16.18|0.65|BTC confirmation absent; no entry.|
|16|FN|3.05|D|Down|Recovery|Bearish/mixed|RE-ENTRY WATCH — STALE/WIDE QUOTE|513.67 close|534.20|518.00 / 505.40|548.50 / 570.00|2.21 from trigger|No overnight action; require liquid RTH confirmation.|
|17|IREN|2.84|D|Bearish/mixed|Down|Bearish/mixed|NO SETUP|42.01|45.54|38.73 / 32.22|48.73 / 51.91|0.94|Stand aside; IV extreme.|
|18|CRWV|2.79|D|Bearish/mixed|Down|Recovery|NO SETUP|84.88|95.14|78.37 / 68.51|100.48 / 105.82|0.64|Overnight rebound only; no entry.|
|19|WULF|2.49|D|Mixed|Down|Recovery|WATCH|19.83|24.58|18.26 / 16.55|26.12 / 27.66|0.49|No entry.|
|20|APLD|2.13|D|Bearish/mixed|Down|Bearish/mixed|NO SETUP|30.28|33.56|28.27 / 24.03|35.82 / 38.08|0.86|Event-adjusted block/reduction; stand aside.|
|21|MXL|2.13|D|Mixed|Bearish/mixed|Recovery|NO SETUP — EVENT BLOCK|89.01|15m 91.30; 1H 92.60|85.80 / 81.50|95.25 / 99.75|1.05|Same-day earnings block; recalculate after results.|

## Mandatory second pass — ONDS

- PASS 1: **7.05** at 12:12 HKT.
- PASS 2: **5.55** at 12:25 HKT.
- Score difference: **1.50**, exceeding the allowed 0.50.
- Completed week: close 6.525; SMA5W/10W/20W/40W 7.659/9.096/9.423/9.291; weekly RSI14 40.79; weekly ATR14 2.014; structure LH/LL.
- Completed day: close 8.00; SMA5D/10D/20D/50D 7.141/7.199/7.473/9.121; RSI14 50.91; ATR14 0.689.
- Completed 1H: close 8.0098; EMA20/EMA50 7.9315/7.5570; RSI14 57.53; structure LH/LL.
- Completed 15m: close 8.0098; EMA20/EMA50 8.0253/8.0207; RSI14 46.84; structure mixed.
- Result: **VALIDATION FAILED / DOWNGRADED; NO ENTRY ALERT.**

## Boss Action

No new trade. Do not chase ONDS, LITE, NBIS or the overnight photonics bounce. The nearest disciplined watches are MU only after 979/988 completed-bar confirmation with fresh >=2R, and COHR only after an RTH pullback reclaim.
