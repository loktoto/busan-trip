# Fresh Multi-Timeframe TA Monitor

- As of: **2026-07-23T12:12:00+08:00 / 2026-07-23T00:12:00-04:00**
- Session: **OVERNIGHT**
- Source: **IBKR snapshot + Yahoo OHLCV fallback**
- Last completed weekly bar: **2026-07-17**
- Limitation: Public extended-hours bars do not cover the full 20:00–04:00 ET overnight session.
- Guardrail: alerts use fresh executable-price R/R, not historical trigger-price R/R.

## BEST SETUP NOW: NONE
## BEST SETUP IF TRIGGERED: ONDS
## VALIDATED 7+: NONE

|#|Ticker|Score|Tier|Weekly|Daily|1H|State|Price|Trigger|SL tactical/structural|TP1/TP2|R/R trigger|R/R executable|Validation|Action|
|---:|---|---:|:---:|---|---|---|---|---:|---:|---|---|---:|---:|---|---|
|1|ONDS|5.55|B|DOWN|RECOVERY|RECOVERY|RE-ENTRY WATCH|8.01|7.85|7.47/7.22|8.22/8.78|2.43|1.42|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|2|LITE|5.53|B|BEARISH/MIXED|RECOVERY|UP|RE-ENTRY WATCH|842.09|845.10|824.00/799.80|861.50/887.50|2.01|2.51|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|3|APH|4.98|D|UP|BEARISH/MIXED|RECOVERY|BREAKOUT PENDING|157.51|158.50|155.20/152.80|162.00/167.50|2.73|4.32|PASS 1|Wait completed 1H and retest|
|4|AXTI|4.77|D|BEARISH/MIXED|DOWN|MIXED|NO SETUP|54.20|57.60|53.70/51.20|60.50/65.00|1.90|21.60|PASS 1|Stand aside|
|5|COHR|4.60|D|BEARISH/MIXED|DOWN|RECOVERY|PULLBACK READY|316.75|320.60|313.80/309.50|326.50/335.50|2.19|6.36|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|6|MU|4.50|D|MIXED|BEARISH/MIXED|RECOVERY|BREAKOUT PENDING|975.00|988.00|948.00/936.00|1000.00/1045.00|1.43|2.59|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|7|CRCL|4.47|D|DOWN|BEARISH/MIXED|MIXED|NO SETUP|66.66|72.86|62.57/58.68|77.34/81.83|0.87|3.71|PASS 1|Stand aside|
|8|ORCL|4.22|D|BEARISH/MIXED|DOWN|MIXED|NO SETUP|126.24|149.07|121.12/117.97|154.97/160.88|0.42|6.76|PASS 1|Stand aside|
|9|RKLB|4.20|D|BEARISH/MIXED|DOWN|BEARISH/MIXED|NO SETUP|69.98|86.30|65.35/62.42|91.80/97.30|0.52|5.90|PASS 1|Stand aside|
|10|SNDK|4.13|D|MIXED|BEARISH/MIXED|RECOVERY|WATCH|1601.00|1637.00|1548.00/1515.00|1680.00/1775.00|1.55|3.28|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|11|AAOI|3.54|D|BEARISH/MIXED|DOWN|MIXED|NO SETUP|112.50|123.50|114.50/107.40|129.00/138.00|1.61|0.00|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|12|HUT|3.19|D|BEARISH/MIXED|RECOVERY|RECOVERY|RE-ENTRY WATCH|111.60|114.60|98.70/83.30|122.69/130.78|1.02|1.49|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|13|FOTO|3.13|D|DATA GAP|BEARISH/MIXED|BEARISH/MIXED|NO SETUP|20.75|21.30|20.45/19.90|21.88/22.48|1.38|5.75|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|14|NBIS|2.93|D|MIXED|DOWN|RECOVERY|BREAKOUT PENDING|227.88|231.75|198.71/164.31|250.05/268.35|1.11|1.39|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|15|MARA|2.90|D|MIXED|DOWN|RECOVERY|WATCH|12.38|14.41|11.70/10.54|15.29/16.18|0.65|5.61|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|16|WULF|2.49|D|MIXED|DOWN|RECOVERY|WATCH|19.83|24.58|18.26/16.55|26.12/27.66|0.49|4.98|PASS 1|Trigger not developed|
|17|IREN|2.34|D|BEARISH/MIXED|DOWN|BEARISH/MIXED|NO SETUP|42.01|45.54|38.73/32.22|48.73/51.91|0.94|3.02|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|18|CRWV|2.29|D|BEARISH/MIXED|DOWN|RECOVERY|NO SETUP|84.88|95.14|78.37/68.51|100.48/105.82|0.64|3.21|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|19|FN|2.05|D|DOWN|RECOVERY|BEARISH/MIXED|RE-ENTRY WATCH|513.67|534.20|518.00/505.40|548.50/570.00|2.21|0.00|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|20|APLD|1.63|D|BEARISH/MIXED|DOWN|BEARISH/MIXED|NO SETUP|30.28|33.56|28.27/24.03|35.82/38.08|0.86|3.88|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|21|MXL|1.63|D|MIXED|BEARISH/MIXED|RECOVERY|NO SETUP|89.01|92.60|85.80/81.50|95.25/99.75|1.05|3.35|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|

## Raw 7+ requiring fresh IBKR PASS 2

- None.

## Group checks

- Photonics compatible completed 1H: **3/7**
- Miners compatible completed 1H: **3/4**; BTC compatible: **False**
- SOXX compatible completed 1H: **True**

## Boss Action

No validated entry. Do not chase overnight prices; wait for completed-bar confirmation, acceptable spread and fresh executable R/R of at least 2R.
