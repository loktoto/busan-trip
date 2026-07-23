# Frozen SOXX leverage challenger — regime/pullback audit

**Equity cutoff:** 2026-07-21  
**Frozen development cutoff:** 2012-12-31  
**OOS start:** 2013-01-01  
**Decision:** `REJECT_CHALLENGER_RETAIN_PRODUCTION`

## What was tested

- Signal authority is SOXX only. SMH is retained as a diagnostic reference and cannot create a trade row.
- 81 pre-registered RSI2 pullback/reclaim variants use a genuinely latched hold/stop state.
- One signal was selected only on data through 2012-12-31, then frozen.
- OOS validation uses actual adjusted USD and SOXL paths with next-open execution.
- The overlay raises exposure from 1.0x to 1.5x only while the signal is active; capital allocation is not a selection variable.
- Binance data is a separate lagged ablation. Open interest is forward-shadow only because long history is unavailable.

Frozen candidate: `SOXX_RSI10_R5_H40_LSTOP12`

## Actual-product OOS results versus SOXX Buy & Hold

| route | cagr | benchmark_cagr | cagr_delta | sharpe_delta | maxdd_improvement | stress_3x_cost_cagr_delta | bootstrap_p_positive_excess | dsr_vs_cash_probability | search_pbo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USD_2X | 0.3648 | 0.3029 | 0.0619 | 0.0015 | -0.0075 | 0.0285 | 0.9840 | 0.6934 | 0.4000 |
| SOXL_3X | 0.3673 | 0.3029 | 0.0644 | 0.0040 | -0.0396 | 0.0511 | 0.9970 | 0.6972 | 0.4000 |

## Direct comparison with canonical production evidence

| route | challenger_cagr | production_cagr | challenger_minus_production_cagr | challenger_sharpe_delta | production_sharpe_delta | challenger_maxdd_improvement | production_maxdd_improvement |
| --- | --- | --- | --- | --- | --- | --- | --- |
| USD_2X | 0.3648 | 0.3957 | -0.0309 | 0.0015 | 0.1030 | -0.0075 | 0.0354 |
| SOXL_3X | 0.3673 | 0.3576 | 0.0097 | 0.0040 | 0.0320 | -0.0396 | 0.0433 |

The canonical figures come from `main:production/leverage_signal.json`; windows differ by one completed session, so this is a decision audit rather than a return-series splice.

## Diagnostic comparison to the static current-rule formula

| comparison | cagr_delta | sharpe_delta | maxdd_improvement |
| --- | --- | --- | --- |
| Frozen challenger vs static current-rule proxy | 0.0221 | -0.0378 | -0.1209 |

The proxy applies the current 2026 formula unchanged over history. It is not the canonical annual-anchored production path.

## Production gate

| route | neighbour_all_three_pass_rate | gate_oos_return | gate_oos_sharpe | gate_oos_drawdown | gate_cost_stress | gate_bootstrap | gate_dsr | gate_search_pbo | gate_blocks | gate_rolling_3y | gate_rolling_5y | gate_neighbours | all_gates_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USD_2X | 0.0864 | True | True | True | True | True | False | False | False | False | False | False | False |
| SOXL_3X | 0.1235 | True | True | False | True | True | False | False | False | False | False | False | False |

## Binance ablation gate

| route | layer | improved_nonoverlap_blocks | ablation_pass |
| --- | --- | --- | --- |
| USD_2X | BTC_ABOVE_SMA100 | 1 | False |
| USD_2X | BTC_ABOVE_SMA200 | 1 | False |
| USD_2X | BTC_NOT_IN_20PCT_63D_CRASH | 1 | False |
| USD_2X | BTC_TREND_AND_FUNDING_NOT_EXTREME | 1 | False |
| SOXL_3X | BTC_ABOVE_SMA100 | 1 | False |
| SOXL_3X | BTC_ABOVE_SMA200 | 2 | False |
| SOXL_3X | BTC_NOT_IN_20PCT_63D_CRASH | 0 | False |
| SOXL_3X | BTC_TREND_AND_FUNDING_NOT_EXTREME | 1 | False |

## Interpretation

- A candidate is not promoted because it looks good in aggregate. Every mandatory gate must pass.
- The static current-rule proxy is only an implementation cross-check; the canonical anchored production evidence remains the manifest pinned on main.
- No production file was changed and no order or order instruction was created.