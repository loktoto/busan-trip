# Semiconductor Leveraged ETF Daily Audit

Data through **2026-07-21**.

## Method
- Completed daily close generates the signal; execution occurs at the next open.
- 10 bps per position change; no cash yield; adjusted OHLC.
- SOXX and SMH tested independently as signals; USD and SOXL tested independently as products.
- 1Y results are reported but excluded from model selection.

## Robust selected candidates

| Product | Selection | Signal | Family | Strategy | Median CAGR | Worst CAGR | Median Sharpe | Median Calmar | Worst MaxDD | Exposure |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| USD | ROBUST_OVERALL | SMH | PULLBACK_RECLAIM | RSI5_R10_H40 | 83.4% | 30.7% | 2.02 | 3.89 | -36.4% | 28.9% |
| USD | BEST_MA_REGIME | SMH | MA_REGIME | MA63_EXIT250 | 73.2% | 34.7% | 1.21 | 1.34 | -54.8% | 81.5% |
| USD | BEST_BREAKOUT | SMH | BREAKOUT_RSI | B20_RSI92 | 45.6% | 14.0% | 1.05 | 0.81 | -61.4% | 45.7% |
| USD | BEST_MHT | SOXX | MHT | MHT6_3 | 44.1% | 16.8% | 1.02 | 0.96 | -51.3% | 53.0% |
| SOXL | ROBUST_OVERALL | SMH | PULLBACK_RECLAIM | RSI5_R10_H40 | 115.8% | 45.2% | 1.84 | 3.84 | -53.7% | 28.9% |
| SOXL | BEST_MA_REGIME | SMH | MA_REGIME | MA63_EXIT250 | 81.2% | 48.1% | 1.13 | 1.22 | -73.0% | 82.7% |
| SOXL | BEST_BREAKOUT | SMH | BREAKOUT_RSI | B20_RSI92 | 42.6% | 19.2% | 0.85 | 0.59 | -84.9% | 47.1% |
| SOXL | BEST_MHT | SOXX | MHT | MHT6_3 | 54.0% | 30.6% | 0.97 | 0.98 | -60.4% | 54.4% |

## Guardrails
- The exact top parameter is not adopted unless its neighboring parameter family is also robust.
- SOXL benchmark history changed; no pre-inception synthetic SOXL is used here.
- These are historical results, not guaranteed alpha.