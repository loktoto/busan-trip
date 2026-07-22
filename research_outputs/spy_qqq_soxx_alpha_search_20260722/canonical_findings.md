# SPY + QQQ + SOXX Expanded Alpha Search — Canonical Findings

**Completed-close cutoff:** 2026-07-21  
**Canonical workflow run:** 26 — PASS  
**Raw engine SHA-256:** `d72007c2fded90ac5282e222b40f76a97f1619871d601c644fa018daff7e2e4a`  
**Patched engine SHA-256:** `2ee009cf9f0ccb6e0ad41e3f6327e90813d3327beb18204a5a34ab6cbf11c3aa`  
**Canonical identity SHA-256:** `99e3b0c13f6be6c85d8b461b553deb52a8dda6b54405a1c5f4cb36e2261c6aee`  
**Artifact digest:** `sha256:3c29290abee56686b4d512f59e3f519d8c7e4f1baf50075f0a491989abb9c717`

## Executive conclusion

- **SOXX:** validated RETURN_ALPHA at the signal level and through two actual-product paths using adjusted USD and SOXL prices.
- **QQQ:** economically promising but remains RESEARCH_ONLY because corrected DSR is below 80% and search PBO is 55.7%.
- **SPY:** no alpha in the tested families; remains Buy & Hold.

The 2013-2026 record is anchored pseudo-OOS, not untouched holdout data. Every calendar year selects raw parameters using information available only through the previous year-end. Buy & Hold is an allowed annual choice inside every family.

## Signal-level result

| Asset | Classification | Candidate | CAGR delta | Sharpe delta | MaxDD delta | Beta-adjusted alpha | 3x-cost CAGR delta | Bootstrap P(positive) | Corrected DSR | Search PBO | Current model exposure |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SPY | RESEARCH_ONLY | anchored vol-target | -0.47pp | -0.008 | +5.43pp | +0.54% | -0.73pp | 35.4% | 71.3% | 8.6% | 1.133x |
| QQQ | RESEARCH_ONLY | anchored trend-vol | +2.74pp | +0.027 | +8.25pp | +2.12% | +2.41pp | 89.7% | 75.8% | 55.7% | 0.965x |
| SOXX | **RETURN_ALPHA** | anchored trend-vol | **+5.81pp** | **+0.039** | **+4.33pp** | **+4.08%** | **+5.39pp** | **95.7%** | **85.6%** | **2.9%** | **0.566x** |

Positive MaxDD delta means a less severe drawdown.

## US$10,000 comparison

| Asset | Window | Buy & Hold | Best anchored candidate |
|---|---|---:|---:|
| SPY | 10Y | $40,525 | $39,790 |
| SPY | MAX_WF | $64,761 | $61,270 |
| QQQ | 10Y | $67,163 | $86,122 |
| QQQ | MAX_WF | $118,403 | $160,704 |
| SOXX | 10Y | $182,060 | $293,080 |
| SOXX | MAX_WF | $357,449 | $645,863 |

## SOXX current rule

For calendar year 2026, the prior-year selection chose:

`trendvol_dual50_200_rv40_t0.40_c1.5`

- Trend gate: SOXX SMA50 above SMA200.
- Base exposure: 40% annual volatility target divided by 40-day realised volatility.
- Exposure smoothing: EWM span 5.
- Exposure range: 0.5x to 1.5x.
- Trend OFF: 0.5x.
- Completed-close exposure at 2026-07-21: approximately 0.566x.

## Actual-product validation

| Implementation | CAGR | Buy & Hold CAGR | CAGR delta | Sharpe delta | MaxDD improvement | Annual alpha | 3x-cost CAGR delta | Bootstrap | DSR | Product gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| SOXX + SOXL 3x path | 35.76% | 30.22% | +5.54pp | +0.032 | +4.33pp | +3.91% | +5.09pp | 95.0% | 85.5% | PASS |
| SOXX + USD 2x path | 39.57% | 30.22% | +9.35pp | +0.103 | +3.54pp | +7.26% | +8.40pp | 99.1% | 88.0% | PASS |

Both implementations inherit the signal-family search PBO of 2.9% and independently pass the return-alpha gate using actual adjusted product prices.

### Current weights

Current effective exposure is approximately 0.568x. Because exposure is below 1.0x, neither implementation currently holds a leveraged semiconductor ETF:

- approximately 56.7% SOXX;
- approximately 43.3% cash / Treasury-bill equivalent;
- 0% USD or SOXL.

When exposure rises above 1.0x:

- 2x route: combine SOXX and USD to reproduce the target exposure;
- 3x route: combine SOXX and a smaller SOXL weight to reproduce the same target exposure.

IBKR liquidity audit favours SOXL for capacity: approximately US$10.1bn versus US$97m 90-day average USD volume for USD at the audit snapshot. The USD route nevertheless produced the stronger historical adjusted-price result and lower model beta.

## Pre-2013 single-selection diagnostic

A separate test selected one raw rule using data only through 2012-12-31 and then froze it through 2026:

| Asset | Frozen rule | CAGR delta | Sharpe delta | MaxDD delta | Annual alpha | Result |
|---|---|---:|---:|---:|---:|---|
| SPY | SMA50 > SMA200; otherwise cash | -4.58pp | -0.160 | 0.00pp | -0.30% | Reject |
| QQQ | RV10 target 20%, 0.5x-2.0x | +2.19pp | +0.005 | +6.16pp | +1.98% | Promising diagnostic; not yet promoted |
| SOXX | Close > SMA100; otherwise cash | -11.77pp | -0.180 | +0.72pp | +1.34% | Reject |

## Production interpretation

- SOXX is the only asset in this search that passed both signal-level and actual-product gates.
- QQQ has a plausible volatility-management hypothesis but failed the full multiple-testing stability gate; continue with parameter-free or frozen-ensemble research.
- SPY remains Buy & Hold under the tested families.
- No IBKR order instruction was created.
