# IBKR Data and Model Validation — 2026-07-21

> Classification: **MARKET-DATA AUDIT / RESEARCH INPUT, NOT A TRADING SIGNAL**  
> Snapshot timestamps: approximately 2026-07-21 18:38–18:44 HKT.  
> Historical bars: IBKR `Last`, regular trading hours only, 900-second delay reported by the history endpoint.

## Instruments and five-year daily windows

| Symbol | IBKR contract | Primary exchange used | Daily window returned | Corporate-action note |
|---|---:|---|---|---|
| SPY | 756733 | ARCA | 2021-07-23 to 2026-07-20 | Cash distributions present. |
| QQQ | 320227571 | NASDAQ | 2021-07-23 to 2026-07-20 | Cash distributions present. |
| SMH | 229725622 | NASDAQ | 2021-07-23 to 2026-07-20 | 2-for-1 split dated 2023-05-05 plus distributions. |
| SOXX | 12658194 | NASDAQ | 2021-07-23 to 2026-07-20 | 3-for-1 split dated 2024-03-07 plus distributions. |

Actual tactical leveraged products resolved and rechecked through IBKR:

| Underlying sleeve | Product | IBKR contract | Exchange | Five-year corporate actions requiring adjusted prices |
|---|---|---:|---|---|
| SPY | SSO | 39622943 | ARCA | 2-for-1 splits on 2022-01-13 and 2025-11-20; distributions present. |
| QQQ | QLD | 39622938 | ARCA | 2-for-1 split on 2025-11-20; distributions present. |
| SMH/SOXX | USD | 42808834 | ARCA | 2-for-1 splits on 2024-11-07 and 2025-11-20; distributions present. |

The five-year IBKR window is suitable for modern product validation and rolling walk-forward tests. It is not sufficient by itself to represent dot-com or GFC regimes. Longer external histories must therefore be labelled **LONG-CYCLE STRESS TEST**, not mixed into the same untouched IBKR holdout.

## Labelled validation capacity

A historical signal cannot be scored against a future 42/63/84-session trough until that future path exists. The engine now reserves a full 252-session evaluation tail rather than treating the latest year as already labelled.

For an approximately 1,258-row five-year daily window:

| Protocol | Train | Purge | Test | Step | Fully labelled folds | Role |
|---|---:|---:|---:|---:|---:|---|
| `MODERN_5Y_PRIMARY` | 504 | 84 | 126 | 126 | about 3 | Primary one-SE model selection. |
| `MODERN_5Y_DENSE_DIAGNOSTIC` | 315 | 84 | 63 | 63 | about 9 | CSCV/PBO and selection-instability diagnostic only. |
| Old default | 1,008 | 84 | 252 | 252 | 0 before label-tail correction | Invalid for the five-year IBKR window. |

The dense protocol is not allowed to promote live parameters by itself: shorter training windows increase estimator variance and may contain too few distinct drawdown regimes. It exists to expose instability, not manufacture additional evidence.

## Current volatility cross-check

| ETF | Snapshot price | 52-week high | Distance | 30-day historical vol | Underlying implied vol | 52-week IV percentile |
|---|---:|---:|---:|---:|---:|---:|
| SPY | 745.99 | 760.39 | -1.9% | 17.1% | 14.8% | 65.3% |
| QQQ | 705.50 | 748.65 | -5.8% | 29.5% | 25.4% | 91.2% |
| SMH | 578.22 | 671.83 | -13.9% | 63.4% | 58.4% | 98.8% |
| SOXX | 545.80 | 655.95 | -16.8% | 75.0% | 66.8% | 100.0% |

### Interpretation

1. **High IV percentile is panic intensity, not exhaustion.** SMH and SOXX are near the top of their own one-year implied-volatility ranges, but realised volatility remains higher than implied volatility. Actual selling volatility is still outrunning option-implied volatility.
2. **The model must separate panic from transition.** A first ordinary-ETF probe may use drawdown and liquidation intensity, but an exhaustion tranche requires deceleration/divergence rather than merely a high IV reading.
3. **Cross-asset thresholds are invalid.** A QQQ IV percentile above 90% and a semiconductor IV percentile near 100% do not represent the same realised-volatility regime or expected adverse excursion.

## Option-volume context

| ETF | Calls today | Puts today | Average calls | Average puts |
|---|---:|---:|---:|---:|
| SPY | 6,035,402 | 7,153,955 | 5,913,520 | 6,689,183 |
| QQQ | 3,656,019 | 4,425,618 | 3,853,216 | 4,287,519 |
| SMH | 78,985 | 255,100 | 75,338 | 274,150 |
| SOXX | 13,762 | 48,243 | 22,263 | 50,198 |

Raw put/call volume is not a clean capitulation indicator. SMH normally has substantially more put than call volume, and SOXX put volume in this snapshot is close to its own average. The engine therefore retains option volume as context only and does not convert it into a standalone bottom vote.

## Data-engineering changes required by the IBKR audit

- Run a split-like discontinuity audit on both the underlying and leveraged product before every backtest.
- Archive symbol, contract, exchange, bar source, regular-hours setting, delay, retrieval timestamp and corporate actions.
- Reject unadjusted split jumps before calculating drawdown, ATR, new lows, volatility or leveraged P&L.
- Preserve the complete historical price path before each fold because cycle highs and underwater duration are path-dependent.
- Restrict signals to the train/test window while allowing an evaluation-only forward tail; never allow tail trades into the fold.
- Use actual SSO, QLD and USD histories for tactical leverage performance and separately report tracking gap and daily-reset path dependence.
- Keep the modern five-year IBKR validation separate from longer stress-test datasets.
- Never store private account, position or order data in this public repository.
