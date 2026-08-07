# Index + MAGS Research Rebuild V2

## Scope

The research universe is strictly limited to SPY, QQQ, SOXX, SMH, MAGS7 and MAGS10. Current portfolio holdings and unrelated securities are excluded.

- **MAGS7 scenario:** fixed AAPL, MSFT, NVDA, AMZN, GOOGL, META and TSLA, equal-weighted quarterly.
- **MAGS10 scenario:** fixed MAGS7 plus AVGO, AMD and PLTR, equal-weighted monthly from 2021-03-19.

The synthetic histories are direct-stock implementation scenarios, not claimed product track records. MAGS is validated separately after its 2023 launch; MGTN is used for recent index parity only because its official live history is short.

## Material corrections to the superseded report

1. Cboe MGTN is monthly equal-weighted. The prior quarterly MAGS10 model is withdrawn.
2. Prior 10-year and maximum-history tables mixed model-selection observations with performance reporting. V2 reports annual anchored walk-forward observations only.
3. Cash before BIL inception is no longer assumed to return zero. V2 accrues the Federal Reserve/FRED DGS3MO 3-month Treasury constant-maturity yield.
4. No-action candidates are included. The optimiser may select buy-and-hold or no pullback overlay instead of being forced to choose a timing rule.
5. MAGS7 and MAGS10 backcasts use current fixed constituents and are explicitly labelled hypothetical. They cannot independently support production promotion.
6. The previous 2022-2026 segment is no longer treated as untouched holdout data because it was repeatedly inspected during earlier research iterations.
7. The earlier approximate deflated-Sharpe implementation is replaced with a dimensionally consistent diagnostic based on the Probabilistic/Deflated Sharpe framework.

## Evidence hierarchy

1. **Official definitions:** Roundhill/SEC for MAGS; Cboe for MGTN; Federal Reserve/FRED for cash.
2. **IBKR:** contract resolution, completed 2026-07-21 closes, current liquidity/spread calibration and recent MGTN closes.
3. **Reproducible long history:** adjusted and raw OHLC downloaded independently in two GitHub Actions repetitions.
4. **Academic controls:** anchored walk-forward evaluation, CSCV/PBO, deflated-Sharpe diagnostic, block bootstrap and multiple cost stresses.

## Strategy architectures

- Buy & Hold: 1.0x exposure.
- Trend-only: 1.0x in a positive trend and 0.0x/0.5x in risk-off, with an always-on baseline.
- Pullback-only: 1.0x core plus a 0.5x tactical add-on, with an explicit no-overlay candidate.
- Hybrid: trend controls the base exposure; the pullback add-on is permitted only while the selected trend state is positive.

Signals are calculated from completed daily data and executed at the next regular-session open. Base transaction costs are stress-tested at 2x and 3x without re-selecting rules.

## Pre-specified rule families

Trend candidates are deliberately small and interpretable:

- price above 200-day SMA;
- 50-day SMA above 200-day SMA;
- 12-month excess time-series momentum over cash;
- two-of-three composite;
- always-on baseline.

Pullback candidates:

- RSI(2) oversold followed by a 10-day moving-average reclaim;
- 20-day z-score reversal;
- at least 10% 63-day drawdown followed by a 20-day moving-average reclaim;
- no-overlay baseline.

## Walk-forward protocol

At each calendar year, the rule is selected using only observations through the prior December 31, then frozen for the next year. Standard assets require at least roughly six years/1,000 observations of training. MAGS10 is permitted a four-year/750-observation low-confidence diagnostic because the scenario begins in 2021; it remains permanently experimental.

The same walk-forward return stream is used to calculate the latest 1-, 3-, 5-, 10-year and maximum-OOS tables. No horizon-specific parameter selection is allowed.

## Statistical and robustness controls

- CSCV/PBO for the full pre-specified trend and pullback families;
- deflated-Sharpe-style probability for excess-return Sharpe after the declared number of trials;
- 20-session block bootstrap confidence interval and probability of positive annualized excess return;
- base, 2x and 3x transaction-cost stress;
- exact strategy-identity agreement across two independent downloads and calculations;
- numerical tolerances for return, risk and terminal-value differences;
- IBKR close-parity gate for directly observed ETFs.

These controls reduce but do not eliminate data-snooping. Because earlier research repeatedly inspected recent history, every conclusion receives a lower confidence level than a genuinely untouched prospective test.

## Official and primary references

- Roundhill MAGS official page and current SEC summary prospectus.
- Cboe Magnificent 10 Index official product/methodology pages.
- Federal Reserve Bank of St. Louis FRED series DGS3MO.
- Moskowitz, Ooi and Pedersen, *Time Series Momentum*.
- Bailey et al., *The Probability of Backtest Overfitting*.
- Bailey and López de Prado, *The Deflated Sharpe Ratio*.
- White, *A Reality Check for Data Snooping*.

## Promotion policy

A return-enhancing strategy must show positive walk-forward CAGR and Sharpe deltas, bootstrap support, DSR support, PBO at or below 50%, and resilience under 2x/3x costs. A defensive strategy may sacrifice no more than three percentage points of CAGR while improving Sharpe and maximum drawdown materially. Synthetic MAGS10 cannot be promoted. MAGS7 can be no more than provisional until actual MAGS product history is sufficiently long and confirms the synthetic signal behavior.

No IBKR order instruction is created by this research.
