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

| Underlying sleeve | Product | IBKR contract | Exchange | Corporate actions requiring adjusted prices |
|---|---|---:|---|---|
| SPY | SSO | 39622943 | ARCA | 2-for-1 splits on 2022-01-13 and 2025-11-20; distributions present. |
| QQQ | QLD | 39622938 | ARCA | 2-for-1 split on 2025-11-20; distributions present. |
| SMH/SOXX | USD | 42808834 | ARCA | 2-for-1 splits on 2024-11-07 and 2025-11-20; distributions present. |

The five-year IBKR window is suitable for modern product and recent-regime validation. It is not sufficient by itself to represent dot-com or GFC regimes. Longer external histories must be labelled **LONG-CYCLE STRESS TEST**, not mixed into the same untouched IBKR holdout.

## Labelled validation capacity and leakage correction

A training score uses future prices to determine whether a signal was near the later 42/63/84-session minimum and to measure the broader bear episode. If training signals are followed by a 252-session evaluation tail, the test signal window cannot begin after only an 84-session purge: training selection would already have observed prices inside the test period.

The engine now requires:

```text
purge_days >= evaluation_tail_days
```

For an approximately 1,258-row five-year daily window:

| Protocol | Train | Purge | Test | Step | Approximate fully labelled observations | Role |
|---|---:|---:|---:|---:|---:|---|
| `MODERN_5Y_PRIMARY` | 504 | 252 | 126 | 126 | about 1 | Clean recent holdout only. |
| `MODERN_5Y_DENSE_DIAGNOSTIC` | 315 | 252 | 63 | 63 | about 6 | Rolling sensitivity diagnostic; future label windows overlap, so formal CSCV/PBO is blocked. |
| `LONG_CYCLE` | 1,008 | 252 | 252 | 504 | requires roughly 20+ years for eight partitions | Non-overlapping label protocol for long-cycle CSCV/PBO research. |

The latest 252 trading sessions remain an unlabelled live tail. They can generate current monitor states but cannot be included in completed historical accuracy claims.

## Current volatility cross-check

| ETF | Snapshot price | 52-week high | Distance | 30-day historical vol | Underlying implied vol | 52-week IV percentile |
|---|---:|---:|---:|---:|---:|---:|
| SPY | 745.99 | 760.39 | -1.9% | 17.1% | 14.8% | 65.3% |
| QQQ | 705.50 | 748.65 | -5.8% | 29.5% | 25.4% | 91.2% |
| SMH | 578.22 | 671.83 | -13.9% | 63.4% | 58.4% | 98.8% |
| SOXX | 545.80 | 655.95 | -16.8% | 75.0% | 66.8% | 100.0% |

### Interpretation

1. **High IV percentile is panic intensity, not exhaustion.** Semiconductor realised volatility remained above implied volatility.
2. **Panic and transition remain separate features.** Larger additions require deceleration/divergence rather than a high IV reading alone.
3. **Cross-asset thresholds remain invalid.** QQQ and semiconductor IV percentiles do not imply the same adverse-excursion distribution.

## Option-volume context

| ETF | Calls today | Puts today | Average calls | Average puts |
|---|---:|---:|---:|---:|
| SPY | 6,035,402 | 7,153,955 | 5,913,520 | 6,689,183 |
| QQQ | 3,656,019 | 4,425,618 | 3,853,216 | 4,287,519 |
| SMH | 78,985 | 255,100 | 75,338 | 274,150 |
| SOXX | 13,762 | 48,243 | 22,263 | 50,198 |

Raw put/call volume is context only. SMH normally carries substantially more put volume, and SOXX put volume in this snapshot was close to its own average.

## Data-engineering requirements

- Audit both underlying and leveraged-product files for split-like discontinuities.
- Archive symbol, contract, exchange, bar source, RTH setting, delay, retrieval timestamp and corporate actions.
- Preserve all earlier price history because cycle highs and underwater duration are path-dependent.
- Restrict signals to the requested fold while retaining an evaluation-only forward tail.
- Require the training-label purge to cover the full evaluation tail.
- Block formal CSCV/PBO when OOS future-label windows overlap or fewer than eight independent partitions survive.
- Use actual SSO, QLD and USD adjusted prices and separately report tracking gap and daily-reset path dependence.
- Keep modern five-year validation separate from longer dot-com/GFC stress histories.
- Never store private account, position or order data in this public repository.
