# Canonical trend + pullback hybrid findings

Date: 2026-07-22  
Completed-close cutoff: 2026-07-21  
Starting capital: US$10,000  
Execution: completed-close signal, next regular-session open

GitHub repeatability: **PASS**. Strategy identity SHA-256: `c6d3d1462db5ad9482357786aacb1f4f55dab10cd19fd453f3f3f5d4e8570b70`.

## Strategies

- Buy & Hold: continuous 1.0x exposure.
- Trend-only: development-selected trend state; risk-off exposure is 0.0x or 0.5x.
- Pullback-only: continuous 1.0x plus the frozen add-on for SOXX, SMH and MAGS7.
- Hybrid: trend controls the base exposure; pullback add-on is allowed only when trend is positive.

## Selected trend identities

| Asset | Trend rule | Risk-off | Current hybrid |
|---|---|---:|---:|
| SPY | price above SMA100 | 0.0x | 1.0x |
| QQQ | price above SMA150 | 0.5x | 1.0x |
| SOXX | SMA50 above SMA200 | 0.5x | 1.0x |
| SMH | slow trend-majority composite | 0.0x | 1.0x |
| MAGS7 | SMA100 above SMA200 | 0.5x | 1.0x |
| MAGS10 | price above SMA150 | 0.0x | 1.0x |

No frozen pullback add-on is active as of the completed 2026-07-21 close.

## US$10,000 terminal values

### 1 year

| Asset | Buy & Hold | Trend | Pullback | Hybrid |
|---|---:|---:|---:|---:|
| SPY | $12,001 | $11,718 | $12,001 | $11,718 |
| QQQ | $12,631 | $12,307 | $12,631 | $12,307 |
| SOXX | $22,302 | $22,302 | $24,683 | $24,683 |
| SMH | $20,049 | $20,049 | $20,049 | $20,049 |
| MAGS7 | $12,047 | $11,604 | $11,966 | $11,526 |
| MAGS10 | $13,962 | $13,015 | $13,962 | $13,015 |

### 3 years

| Asset | Buy & Hold | Trend | Pullback | Hybrid |
|---|---:|---:|---:|---:|
| SPY | $17,056 | $15,838 | $17,056 | $15,838 |
| QQQ | $18,790 | $17,462 | $18,790 | $17,462 |
| SOXX | $32,578 | $32,180 | $39,067 | $38,590 |
| SMH | $37,836 | $34,309 | $40,592 | $36,808 |
| MAGS7 | $22,277 | $20,770 | $23,940 | $22,320 |
| MAGS10 | $32,746 | $25,865 | $32,746 | $25,865 |

### 5 years

| Asset | Buy & Hold | Trend | Pullback | Hybrid |
|---|---:|---:|---:|---:|
| SPY | $18,758 | $17,168 | $18,758 | $17,168 |
| QQQ | $20,472 | $21,234 | $20,472 | $21,234 |
| SOXX | $40,015 | $43,699 | $52,351 | **$57,172** |
| SMH | $48,344 | $39,734 | **$54,358** | $43,080 |
| MAGS7 | $29,669 | $27,983 | **$32,834** | $30,968 |
| MAGS10 | $44,699 | **$46,234** | $44,699 | **$46,234** |

### 10 years

MAGS10 has no valid ten-year history.

| Asset | Buy & Hold | Trend | Pullback | Hybrid |
|---|---:|---:|---:|---:|
| SPY | $40,525 | $32,139 | $40,525 | $32,139 |
| QQQ | $67,163 | $64,375 | $67,163 | $64,375 |
| SOXX | $182,060 | $167,775 | **$330,158** | $295,312 |
| SMH | $207,561 | $150,593 | **$276,146** | $193,192 |
| MAGS7 | $220,826 | $206,886 | **$356,670** | $334,154 |

### Maximum available history

| Asset | History | Buy & Hold | Trend | Pullback | Hybrid |
|---|---|---:|---:|---:|---:|
| SPY | 2005-01-03 to 2026-07-20 | $90,983 | $61,294 | $90,983 | $61,294 |
| QQQ | 2005-01-03 to 2026-07-20 | $207,095 | $172,472 | $207,095 | $172,472 |
| SOXX | 2005-01-03 to 2026-07-20 | $368,883 | $357,238 | **$839,883** | $781,008 |
| SMH | 2005-01-03 to 2026-07-20 | $407,234 | $275,331 | **$624,455** | $362,421 |
| MAGS7 | 2012-05-21 to 2026-07-20 | $871,134 | $783,502 | **$2,099,674** | $1,888,456 |
| MAGS10 | 2020-10-01 to 2026-07-20 | $64,775 | $49,514 | $64,775 | $49,514 |

## Maximum-sample risk comparison

| Asset | Strategy | CAGR | Sharpe | MaxDD | Calmar |
|---|---|---:|---:|---:|---:|
| SPY | Buy & Hold | 10.79% | 0.652 | -55.42% | 0.195 |
| SPY | Trend / Hybrid | 8.78% | 0.829 | -18.11% | 0.485 |
| QQQ | Buy & Hold | 15.11% | 0.766 | -52.28% | 0.289 |
| QQQ | Trend / Hybrid | 14.13% | 0.871 | -37.99% | 0.372 |
| SOXX | Buy & Hold | 18.23% | 0.699 | -65.58% | 0.278 |
| SOXX | Pullback-only | 22.84% | 0.795 | -66.51% | 0.343 |
| SOXX | Hybrid | 22.42% | **0.884** | **-44.97%** | **0.499** |
| SMH | Buy & Hold | 18.78% | 0.735 | -63.05% | 0.298 |
| SMH | Pullback-only | **21.16%** | 0.783 | -64.28% | 0.329 |
| SMH | Hybrid | 18.14% | **0.842** | **-39.71%** | **0.457** |
| MAGS7 | Buy & Hold | 37.08% | 1.272 | -49.21% | 0.754 |
| MAGS7 | Pullback-only | **45.87%** | 1.382 | -49.19% | 0.932 |
| MAGS7 | Hybrid | 44.78% | **1.423** | **-38.34%** | **1.168** |
| MAGS10 | Buy & Hold | **38.02%** | 1.140 | -48.97% | 0.776 |
| MAGS10 | Trend / Hybrid | 31.77% | **1.300** | **-24.62%** | **1.290** |

## Decision

- **SOXX:** Hybrid is the best overall architecture. Pullback-only produces the highest maximum-sample wealth, but Hybrid retains most of the CAGR while materially improving Sharpe and maximum drawdown.
- **MAGS7:** Hybrid is the best risk-adjusted architecture. Pullback-only maximises terminal wealth; Hybrid sacrifices roughly 10% of final wealth to cut maximum drawdown by about 10.8 percentage points.
- **SMH:** Pullback-only is preferred when the objective is maximum wealth. Hybrid is defensible only when drawdown control is prioritised because its trend filter removes substantial upside.
- **SPY and QQQ:** Trend is a defensive overlay, not a return enhancer. Buy & Hold remains preferable for terminal wealth; Trend is preferable only for lower drawdown.
- **MAGS10:** Trend materially improves drawdown and Sharpe but lowers terminal wealth. The sample is short and there is no approved pullback layer.

## Limitations

Maximum-sample figures mix development and later evaluation periods and are not wholly out-of-sample. MAGS7 and MAGS10 are fixed-current-definition synthetic baskets and carry survivorship/universe-definition risk. Leveraged MAGS exposure is modelled rather than validated through a full-history product. Results include configured turnover costs but do not guarantee future performance.
