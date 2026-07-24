# NO NEW ACTIONABLE TRIGGER THIS HOUR

- As of: **2026-07-24T10:16:48+08:00 / 2026-07-23T22:16:48-04:00**
- Session: **OVERNIGHT**
- Calculation source: **IBKR snapshot + Yahoo OHLCV fallback**
- Last completed weekly bar: **2026-07-17**
- Live-week / limitation: Public extended-hours bars do not cover the full 20:00–04:00 ET overnight session.
- Stale-last normalization: **IREN, ORCL, CRCL, MXL, FOTO, APH, FN, SNDK**

## Source Status

|Source|Status|Timestamp / latest bar|Feed / quality|Purpose|Confidence impact|
|---|---|---|---|---|---|
|IBKR|SUCCESS|2026-07-24T10:16:00+08:00|live/near-live overnight snapshots; ticker-level stale/wide flags retained|Primary equity quote authority|21/21 contracts and snapshots succeeded; no endpoint retry required|
|Alpaca|RETRIED SUCCESS — SNAPSHOT / BARS DEGRADED|2026-07-23T23:59:59Z|delayed_sip snapshot; SIP entitlement failed; historical delayed_sip rejected; IEX weekly batch incomplete|Independent equity parity and fallback|Quote fallback/parity available; completed-bar confidence reduced|
|Binance|SUCCESS|2026-07-24T02:16:09Z|spot plus USD-M mark/funding and 1H klines|BTC/ETH cross-asset context only|BTC weak/sideways recovery; ETH weaker; zero direct equity authority|
|GitHub|SUCCESS|2026-07-24T10:16:48+08:00|main branch production policy/config fetched|Deterministic model and audit|Fresh snapshot committed to trigger engine|

## BEST SETUP NOW: NONE
## BEST SETUP IF TRIGGERED: ONDS
## VALIDATED 7+: NONE

|#|Ticker|Score|Tier|Weekly|Daily|1H|State|Price|Trigger|SL tactical/structural|TP1/TP2|R/R trigger|R/R executable|Validation|Action|
|---:|---|---:|:---:|---|---|---|---|---:|---:|---|---|---:|---:|---|---|
|1|ONDS|5.55|C|DOWN|RECOVERY|RECOVERY|RE-ENTRY WATCH|7.94|7.85|7.47/7.22|8.22/8.78|2.43|1.78|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|2|APH|4.98|D|UP|BEARISH/MIXED|RECOVERY|BREAKOUT PENDING|157.50|158.50|155.20/152.80|162.00/167.50|2.73|4.35|PASS 1|Wait completed 1H and retest|
|3|RKLB|4.12|D|BEARISH/MIXED|DOWN|MIXED|NO SETUP|69.77|86.30|65.35/62.42|91.80/97.30|0.52|6.23|PASS 1|Stand aside|
|4|LITE|3.78|D|BEARISH/MIXED|RECOVERY|MIXED|RE-ENTRY WATCH|823.44|845.10|824.00/799.80|861.50/887.50|2.01|0.00|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|5|MU|3.60|D|MIXED|BEARISH/MIXED|RECOVERY|BREAKOUT PENDING|981.50|988.00|948.00/936.00|1000.00/1045.00|1.43|1.90|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|6|AAOI|3.54|D|BEARISH/MIXED|DOWN|MIXED|NO SETUP|111.98|123.50|114.50/107.40|129.00/138.00|1.61|0.00|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|7|FOTO|3.51|D|DATA GAP|BEARISH/MIXED|UP|NO SETUP|20.68|21.30|20.45/19.90|21.88/22.48|1.38|7.80|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|8|AXTI|3.50|D|BEARISH/MIXED|DOWN|BEARISH/MIXED|NO SETUP|52.70|57.60|53.70/51.20|60.50/65.00|1.90|0.00|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|9|SNDK|3.33|D|MIXED|BEARISH/MIXED|MIXED|WATCH|1596.97|1637.00|1548.00/1515.00|1680.00/1775.00|1.55|3.64|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|10|COHR|3.28|D|BEARISH/MIXED|DOWN|MIXED|NO SETUP|311.50|320.60|313.80/309.50|326.50/335.50|2.19|0.00|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|11|IREN|3.14|D|BEARISH/MIXED|DOWN|MIXED|NO SETUP|40.49|45.54|38.73/32.22|48.73/51.91|0.94|6.49|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|12|CRWV|2.99|D|BEARISH/MIXED|DOWN|MIXED|NO SETUP|80.78|95.14|78.37/68.51|100.48/105.82|0.64|10.37|PASS 1|Stand aside|
|13|FN|2.87|D|DOWN|RECOVERY|UP|RE-ENTRY WATCH|517.73|534.20|518.00/505.40|548.50/570.00|2.21|0.00|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|14|CRCL|2.82|D|DOWN|BEARISH/MIXED|MIXED|NO SETUP|62.85|72.86|62.57/58.68|77.34/81.83|0.87|67.65|PASS 1|Stand aside|
|15|ORCL|2.57|D|BEARISH/MIXED|DOWN|MIXED|NO SETUP|122.25|149.07|121.12/117.97|154.97/160.88|0.42|34.07|PASS 1|Stand aside|
|16|APLD|2.56|D|BEARISH/MIXED|DOWN|MIXED|NO SETUP|29.80|33.56|28.27/24.03|35.82/38.08|0.86|5.41|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|17|NBIS|2.34|D|MIXED|DOWN|MIXED|WATCH|217.64|230.22|198.71/164.31|248.52/266.82|1.16|2.60|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|18|MARA|1.85|D|MIXED|DOWN|RECOVERY|WATCH|12.78|14.41|11.70/10.54|15.29/16.18|0.65|3.15|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|19|WULF|1.29|D|MIXED|DOWN|RECOVERY|WATCH|20.06|24.58|18.26/16.55|26.12/27.66|0.49|4.22|PASS 1|Trigger not developed|
|20|HUT|1.22|D|BEARISH/MIXED|RECOVERY|RECOVERY|RE-ENTRY BREAKOUT PENDING|118.77|120.38|98.70/83.30|128.47/136.56|0.75|0.89|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|
|21|MXL|0.08|D|MIXED|BEARISH/MIXED|MIXED|NO SETUP|83.95|92.60|85.80/81.50|95.25/99.75|1.05|0.00|GUARDRAIL DOWNGRADED — NO ENTRY ALERT|Wait for a new base/retest and fresh executable R/R >=2R|

## VALIDATED 7+ — PASS 1 / PASS 2

- None.

## Failed modules / retries

- None reported.

## Boss Action

今個鐘冇validated entry；等completed-bar confirmation、正常spread同至少2R。
