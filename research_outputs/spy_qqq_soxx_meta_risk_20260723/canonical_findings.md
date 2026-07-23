# SPY + QQQ + SOXX Meta Risk Strategy — Canonical Findings

**Completed-close cutoff:** 2026-07-22  
**Pseudo-OOS return period:** 2013-01-02 through 2026-07-21, with next-open execution  
**Canonical workflow:** `SPY QQQ SOXX meta risk strategy`, run 10 — PASS  
**Canonical artifact digest:** `sha256:b5ece2748ef35a737456d83be858f9fd67c8209c4fd0fac1f9805a4c8eec4e29`  
**Canonical identity SHA-256:** `9867143dbf162766c08afe9f194d80a47518fc1bc106815e057cc9edba5f361c`

## Final classification

`RETURN_ALPHA`

The production candidate was fixed before the canonical run:

- 20% SPY capital sleeve
- 20% QQQ capital sleeve
- 60% SOXX capital sleeve
- SOXX inherits the annual anchored trend-vol rules validated in PR #13
- whole-portfolio target volatility: 30%
- realised-volatility lookback: 40 sessions, EWM span 5
- portfolio scale constrained to 0.75x-1.35x
- total effective gross exposure capped at 1.50x
- actual product path: SPY/SSO, QQQ/QLD, SOXX/USD and 3-month Treasury cash

## Primary comparison: literal Buy & Hold

The primary benchmark invests the strategic SPY/QQQ/SOXX weights once at the first OOS open and allows the weights to drift. It is not a daily-rebalanced constant-mix benchmark.

| Metric | Meta strategy | Literal 20/20/60 Buy & Hold | Difference |
|---|---:|---:|---:|
| CAGR | 31.82% | 26.71% | +5.11pp |
| Sharpe | 1.118 | 1.020 | +0.098 |
| Maximum drawdown | -36.33% | -43.99% | +7.66pp improvement |
| Beta-adjusted annual alpha | 5.04% | — | positive |
| CAGR difference after 3x costs | — | — | +3.76pp |
| Bootstrap P(excess > 0) | 95.25% | — | pass |
| Corrected DSR | 87.57% | — | pass |
| CSCV/search PBO | 0.00% | — | pass |

US$10,000 grew to approximately US$421,864 under the strategy versus US$246,967 under literal Buy & Hold over the maximum pseudo-OOS period.

## Additional dominance test: SOXX Buy & Hold

| Metric | Meta strategy | SOXX Buy & Hold |
|---|---:|---:|
| CAGR | 31.82% | 30.03% |
| Sharpe | 1.118 | 1.019 |
| Maximum drawdown | -36.33% | -47.37% |
| US$10,000 terminal value | US$421,864 | US$350,712 |

The production candidate therefore passed the pre-specified requirement to exceed SOXX Buy & Hold on CAGR and Sharpe while also producing a smaller maximum drawdown over the same period.

## Window results

| Window | Meta strategy | Literal Buy & Hold | SOXX Buy & Hold | Result |
|---|---:|---:|---:|---|
| 1 year CAGR | 69.20% | 96.46% | 118.82% | Strategy lagged |
| 3 year CAGR | 48.90% | 42.73% | 47.95% | Strategy led |
| 5 year CAGR | 38.54% | 27.19% | 30.59% | Strategy led |
| 10 year CAGR | 34.94% | 29.53% | 33.36% | Strategy led |
| Maximum pseudo-OOS CAGR | 31.82% | 26.71% | 30.03% | Strategy led |

The strategy is not expected to outperform every year. Its evidence is multi-cycle and risk-adjusted; the latest one-year window favoured unscaled Buy & Hold.

## Strategic-weight robustness

All four allocations passed the same return-alpha gate against their own literal initial-weight Buy & Hold benchmark:

| SPY / QQQ / SOXX | Strategy CAGR | Benchmark CAGR | CAGR difference | Sharpe difference | MaxDD improvement | 3x-cost difference |
|---|---:|---:|---:|---:|---:|---:|
| 30 / 30 / 40 | 30.18% | 24.52% | +5.66pp | +0.089 | +3.87pp | +4.61pp |
| 25 / 25 / 50 | 31.24% | 25.67% | +5.57pp | +0.098 | +6.01pp | +4.37pp |
| **20 / 20 / 60** | **31.82%** | **26.71%** | **+5.11pp** | **+0.098** | **+7.66pp** | **+3.76pp** |
| 15 / 15 / 70 | 32.11% | 27.64% | +4.46pp | +0.093 | +8.88pp | +2.98pp |

The production allocation was not selected from these results; 20/20/60 was fixed before the run. The neighbouring allocations were used only as robustness checks.

## Current target weights

Signal date: **2026-07-22 completed close**. These are target weights for next-RTH-open implementation, not orders.

| Product | Target portfolio weight |
|---|---:|
| SPY | 17.56% |
| SSO | 0.00% |
| QQQ | 17.56% |
| QLD | 0.00% |
| SOXX | 29.74% |
| USD | 0.00% |
| 3-month Treasury cash | 35.15% |

Supporting state:

- whole-portfolio scale: 0.8778x
- SOXX alpha exposure inside its sleeve: 0.5647x
- effective portfolio gross exposure: 0.6485x
- no leveraged ETF is active at the current signal

## IBKR completed-close parity

The run required parity against the completed 2026-07-22 RTH closes:

- SPY 747.41
- QQQ 705.35
- SOXX 555.52
- SSO 67.27
- QLD 88.28
- USD 92.55

The 2026-07-23 intraday bars were excluded from signal generation and backtest returns.

## Corrected findings

1. The initial version reported the current target weights one session late. Returns were unaffected; the reporting path was corrected and the canonical run now hard-requires a 2026-07-22 signal date.
2. The initial primary benchmark was a daily constant-mix portfolio. It was replaced by literal initial-weight Buy & Hold. The strategy remained classified as `RETURN_ALPHA` under the stricter benchmark.
3. Long base64 retransmission was abandoned after an integrity failure. The canonical version uses a previously verified raw source plus a deterministic one-for-one benchmark patch, with both raw and patched SHA checks.

## Limitations

- The 2013-2026 period is pseudo-OOS, not untouched prospective evidence; prior research has already inspected portions of this history.
- The SOXX sleeve inherits an annually selected family rule. Its search-risk diagnostics are included, but live forward evidence remains necessary.
- Leveraged ETFs reset daily; the backtest uses their actual adjusted-price histories, but future financing costs and tracking can differ.
- Tax, investor-specific funding costs, fractional-share constraints and market-impact costs are not modelled beyond the stated transaction-cost stresses.
- PBO of zero is based on the pre-specified four strategic allocations and should not be interpreted as proof that overfitting risk is literally zero.
- No IBKR order instruction was created.
