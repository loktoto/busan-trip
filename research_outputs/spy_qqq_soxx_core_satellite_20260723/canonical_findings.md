# Canonical findings — SPY/QQQ core with SOXX risk-budget satellite

**Completed-close cutoff:** 2026-07-21  
**Canonical workflow:** `SPY QQQ core with SOXX risk-budget satellite`, run 6 — PASS  
**Canonical identity SHA-256:** `7becccab73dbb1d376b2695f909384fa35a3acb6ea5ef8e6b470bbed9bf84247`  
**Canonical artifact digest:** `sha256:08d5307fb6421639df1c02b25353846c82d4b42808f86da1e9a01e03f8c3e43d`

## Final classification

`RESEARCH_ONLY`

The selected diagnostic family was `USD_corr_cap_band10`, evaluated at the pre-specified 20% SOXX satellite. It uses the already validated SOXX trend-vol exposure, caps the satellite when SOXX correlation and volatility are simultaneously high, and refreshes monthly or when effective exposure changes by at least 0.10.

## Central 20% result

| Metric | Strategy | Matched static core/satellite | Difference |
|---|---:|---:|---:|
| CAGR | 22.22% | 20.17% | +2.04pp |
| Sharpe | 1.091 | 1.024 | +0.067 |
| Maximum drawdown | -32.55% | -34.73% | +2.18pp improvement |
| Beta-adjusted annual alpha | — | — | +1.61% |
| 3x-cost CAGR difference | — | — | +1.86pp |
| Moving-block P(excess > 0) | — | — | 99.25% |
| Corrected DSR | — | — | 80.28% |
| Twelve-family CSCV/PBO | — | — | **90.0% — fail** |

The strategy CAGR was also only 0.41pp above an initial 40% SPY / 40% QQQ / 20% SOXX Buy & Hold portfolio without rebalancing.

## Current model weights

| Asset | Weight |
|---|---:|
| SPY | 40.81% |
| QQQ | 39.80% |
| SOXX | 11.13% |
| USD | 0.00% |
| BIL / cash sleeve | 8.26% |

Current effective SOXX exposure was approximately 11.13% of total portfolio capital. No leveraged ETF weight was active.

## Robustness

- All five satellite sizes from 10% to 30% retained positive CAGR and positive 3x-cost excess versus their matched static policies.
- Both independent downloads selected the same family and 20% candidate.
- All current weights matched exactly across repetitions.
- Maximum numerical differences were negligible and well inside fixed tolerances.
- PBO was computed only across the twelve economic families at the fixed 20% production sleeve. The 10%, 15%, 25% and 30% sleeves were robustness diagnostics and were not included in the selection universe.

## Why it is rejected

The family-level PBO of 90% means that the apparent best overlay family changes too often across regime partitions. Strong CAGR, alpha, bootstrap and cost-stress results are not sufficient to override this pre-specified stability failure.

The correct interpretation is:

- the validated standalone SOXX trend-vol signal remains useful;
- embedding it as a 20% satellite improves several portfolio metrics;
- choosing among correlation caps, volatility caps and rebalance variants is not yet stable enough for production;
- the next research step should manage total portfolio exposure using a small number of fixed portfolio-level volatility rules, rather than search among SOXX sleeve variants.

## Cash-product validation

From 2013-01-02 through 2026-07-21:

- BIL adjusted-price CAGR: 1.63%
- synthetic three-month Treasury series CAGR: 1.83%
- difference: -0.21pp annually
- daily-return correlation: 0.478

BIL remains the actual tradable cash-path benchmark; the synthetic series is not treated as equivalent.

No IBKR order instruction was created.
