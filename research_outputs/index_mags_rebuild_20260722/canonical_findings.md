# Index + MAGS Strategy Research — Ground-up Rebuild V2

**Completed-close cutoff:** 2026-07-21  
**Canonical workflow:** `Index MAGS research rebuild V2`, run 23  
**Research source SHA-256:** `24cd75f4f5fcec1efb22557a4fc17ee41dca593524c477be485f3df711c36e66`  
**Canonical strategy identity SHA-256:** `2e3b0c2ae933793ffcb3ef85d0eaa465b9713a30a2c24ca86b014a2ae489f426`  
**Canonical artifact digest:** `sha256:1c96eee79c159ff05336b2c30195c7c936e43490255a99a9046efddb19061386`

## Executive conclusion

The conservative production result is **Buy & Hold** for SPY, QQQ, SOXX, SMH and MAGS7. MAGS10 remains **EXPERIMENTAL_SYNTHETIC**. No trend-only, pullback-only or hybrid architecture passed all walk-forward, DSR, bootstrap, CSCV/PBO and transaction-cost stress gates.

The prior production promotions for SOXX, SMH and MAGS7 are withdrawn. The strongest remaining research signal is the MAGS7 pullback overlay, but it remains below the DSR threshold, worsens maximum drawdown and relies on a fixed-current-constituent synthetic history. It may be monitored prospectively but is not production alpha.

All six latest trend states are positive and no pullback add-on is active. Current model exposure is 1.0x for every asset; there is no tactical trade instruction.

## Result by asset

| Asset | Final classification | Latest trend rule | Latest pullback rule | Current hybrid exposure | Key reason |
|---|---|---|---|---:|---|
| SPY | BUY_AND_HOLD | 50/200-day dual MA; 0.5x risk-off | None | 1.0x | Timing reduced CAGR and Sharpe; no drawdown improvement in the walk-forward stream |
| QQQ | BUY_AND_HOLD | 50/200-day dual MA; 0x risk-off | None | 1.0x | Trend reduced drawdown but cost 3.98pp annual CAGR and 0.102 Sharpe |
| SOXX | BUY_AND_HOLD | 50/200-day dual MA; 0x risk-off | None | 1.0x | Trend reduced drawdown but cost 4.71pp annual CAGR; walk-forward selected no pullback overlay |
| SMH | BUY_AND_HOLD | 50/200-day dual MA; 0x risk-off | None | 1.0x | Trend improved Sharpe and drawdown but sacrificed 4.07pp CAGR, beyond the defensive gate |
| MAGS7 | BUY_AND_HOLD | Price above SMA200; 0.5x risk-off | RSI(2) oversold + SMA10 reclaim | 1.0x | Synthetic pullback alpha is statistically close but DSR 0.791 < 0.80 and MaxDD worsened |
| MAGS10 | EXPERIMENTAL_SYNTHETIC | 50/200-day dual MA; 0.5x risk-off | RSI(2) oversold + SMA10 reclaim | 1.0x | Only ~1.55 years of walk-forward OOS and fixed-current-constituent synthetic history |

## Maximum walk-forward OOS comparison — US$10,000

| Asset | OOS period | Buy & Hold | Trend-only | Pullback-only | Hybrid |
|---|---|---:|---:|---:|---:|
| SPY | 2013-01-02 to 2026-07-20 | **$64,761** | $38,201 | **$64,761** | $38,201 |
| QQQ | 2013-01-02 to 2026-07-20 | **$118,403** | $74,957 | **$118,403** | $74,957 |
| SOXX | 2013-01-02 to 2026-07-20 | **$357,449** | $217,020 | **$357,449** | $217,020 |
| SMH | 2013-01-02 to 2026-07-20 | **$403,993** | $263,955 | **$403,993** | $263,955 |
| MAGS7* | 2018-01-02 to 2026-07-20 | $123,283 | $76,392 | **$150,830** | $93,462 |
| MAGS10* | 2025-01-02 to 2026-07-20 | $16,200 | $13,779 | **$17,010** | $14,468 |

\* Fixed-current-constituent hypothetical direct-stock baskets, not product records.

## Risk-adjusted maximum-OOS comparison

| Asset / Strategy | CAGR | Sharpe | MaxDD | DSR probability | Bootstrap P(excess > 0) | Family PBO | 3x-cost CAGR delta | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| SPY Buy & Hold | 14.79% | 0.933 | -32.05% | — | — | — | 0.00% | BASELINE |
| SPY Trend | 10.40% | 0.763 | -32.05% | 0.001% | 0.0% | 30.0% | -3.73% | REJECT |
| QQQ Buy & Hold | 20.02% | 0.986 | -36.69% | — | — | — | 0.00% | BASELINE |
| QQQ Trend | 16.04% | 0.884 | -27.56% | 0.011% | 2.0% | 71.4% | -4.86% | REJECT |
| SOXX Buy & Hold | 30.22% | 1.024 | -47.37% | — | — | — | 0.00% | BASELINE |
| SOXX Trend | 25.51% | 1.008 | -35.18% | 0.272% | 5.7% | 65.7% | -5.62% | REJECT |
| SMH Buy & Hold | 31.40% | 1.075 | -46.91% | — | — | — | 0.00% | BASELINE |
| SMH Trend | 27.34% | 1.084 | -34.02% | 0.594% | 12.2% | 34.3% | -4.60% | REJECT |
| MAGS7 Buy & Hold* | 34.17% | 1.092 | -49.21% | — | — | — | 0.00% | BASELINE |
| MAGS7 Pullback* | 37.38% | 1.129 | -51.19% | 79.14% | 96.3% | 0.0% | +2.79% | REJECT |
| MAGS10 Buy & Hold* | 36.67% | 1.113 | -32.00% | — | — | — | 0.00% | BASELINE |
| MAGS10 Pullback* | 41.06% | 1.145 | -32.92% | 40.70% | 93.1% | 4.3% | +3.63% | REJECT |

## US$10,000 trailing-window comparison

### SPY

| Window | Buy & Hold | Trend / Hybrid |
|---|---:|---:|
| 1Y | $12,001 | $12,001 |
| 3Y | $17,056 | $14,681 |
| 5Y | $18,758 | $16,003 |
| 10Y | $40,525 | $28,463 |
| MAX_OOS | $64,761 | $38,201 |

### QQQ

| Window | Buy & Hold | Trend / Hybrid |
|---|---:|---:|
| 1Y | $12,631 | $12,631 |
| 3Y | $18,790 | $15,815 |
| 5Y | $20,472 | $18,815 |
| 10Y | $67,163 | $51,132 |
| MAX_OOS | $118,403 | $74,957 |

### SOXX

| Window | Buy & Hold | Trend / Hybrid |
|---|---:|---:|
| 1Y | $22,302 | $22,302 |
| 3Y | $32,578 | $30,660 |
| 5Y | $40,015 | $39,064 |
| 10Y | $182,060 | $138,249 |
| MAX_OOS | $357,449 | $217,020 |

### SMH

| Window | Buy & Hold | Trend / Hybrid |
|---|---:|---:|
| 1Y | $20,049 | $20,049 |
| 3Y | $37,836 | $29,757 |
| 5Y | $48,344 | $43,876 |
| 10Y | $207,561 | $161,615 |
| MAX_OOS | $403,993 | $263,955 |

### MAGS7 hypothetical basket

| Window | Buy & Hold | Trend | Pullback | Hybrid |
|---|---:|---:|---:|---:|
| 1Y | $12,047 | $11,585 | **$12,429** | $11,953 |
| 3Y | $22,277 | $18,141 | **$25,372** | $20,662 |
| 5Y | $29,669 | $22,643 | **$37,322** | $28,484 |
| MAX_OOS | $123,283 | $76,392 | **$150,830** | $93,462 |

### MAGS10 hypothetical basket

| Window | Buy & Hold | Trend | Pullback | Hybrid |
|---|---:|---:|---:|---:|
| 1Y | $13,687 | $12,785 | **$14,384** | $13,436 |
| MAX_OOS | $16,200 | $13,779 | **$17,010** | $14,468 |

No 3Y/5Y/10Y result is claimed because the walk-forward OOS stream begins in 2025.

## Retained findings

- Trend rules can reduce drawdowns in higher-volatility indices, especially QQQ, SOXX and SMH.
- Pullback/reclaim logic is more naturally a return-enhancement overlay than a defensive system.
- Completed-close signals with next-open execution, explicit costs and a 1.0x benchmark remain required.
- Current completed-close state is 1.0x for every asset; no tactical add-on is active.

## Updated findings

- Trend is now treated as an optional defensive architecture, not a production recommendation. None passed the complete defensive gate.
- MAGS7 pullback remains the strongest research candidate but is downgraded to prospective monitoring only.
- Actual MAGS fund history is separated from the synthetic direct-stock basket. Since launch, daily-return correlation is 0.946, but the fund lagged the synthetic basket by about 3.55 percentage points annualized.
- Recent monthly MAGS10 basket parity with IBKR MGTN is strong: four-session return correlation 0.9987 and maximum absolute level difference about 0.084% after scaling. This validates construction mechanics only, not long-horizon alpha.

## Corrected findings

- MGTN is monthly equal-weighted, not quarterly. Every prior MAGS10 backtest using quarterly rebalancing is withdrawn.
- Prior 10Y/MAX tables mixed model-selection observations with reporting observations. V2 uses annual anchored walk-forward OOS streams only.
- Pre-BIL cash is no longer assumed to earn 0%; V2 uses FRED DGS3MO.
- Always-on and no-overlay candidates prevent the optimiser from being forced to select timing.
- The prior SOXX, SMH and MAGS7 production promotions are withdrawn.
- The previous DSR approximation and stress-cost slicing were corrected; Buy & Hold 2x/3x cost deltas are now exactly zero.
- The recent 2022-2026 period is not described as untouched holdout data because earlier research repeatedly inspected it.

## Newly added insights

- SPY trend timing failed not only on terminal wealth but also on Sharpe and did not improve maximum drawdown in the annual walk-forward stream.
- QQQ, SOXX and SMH trend filters delivered meaningful drawdown relief, but their return sacrifice exceeded the pre-specified defensive allowance.
- SOXX and SMH walk-forward model selection repeatedly chose the explicit no-pullback baseline. The former strong pullback results were not stable when selection was constrained to prior-year information.
- MAGS7 pullback has favorable bootstrap and PBO diagnostics, but its DSR narrowly misses the gate and drawdown is worse. It is a reasonable prospective hypothesis, not validated alpha.
- MAGS10 pullback appears attractive numerically, but DSR is weak and the OOS history is too short. It remains permanently experimental until a materially longer official live record exists.

## Methodology and limits

- Annual anchored walk-forward selection; each calendar year uses only information available through the previous year-end.
- Signals use completed daily data; execution occurs at the next regular-session open.
- Cash return uses daily FRED DGS3MO.
- Base, 2x and 3x transaction-cost stresses; costs are not re-optimised.
- CSCV/PBO, deflated-Sharpe diagnostic and 20-session block bootstrap.
- Two independent full downloads/calculations; exact source and strategy identity match required.
- IBKR 2026-07-21 completed-close parity required for SPY, QQQ, SOXX, SMH and MAGS.
- MAGS7 and MAGS10 backcasts use current fixed constituents and therefore contain hindsight/survivorship risk.
- No historical test can eliminate data-snooping after repeated research. Prospective paper-live monitoring is still required before promotion.
