# SPY + QQQ Core with SOXX Risk-Budget Satellite

## Purpose

Test whether the standalone SOXX trend-vol alpha validated in PR #13 can improve a diversified SPY/QQQ core without using full-portfolio rotation or optimizing the production sleeve after observing out-of-sample results.

## Portfolio architecture

- Core: equal split between SPY and QQQ.
- Satellite: SOXX risk-budget sleeve.
- Production sleeve: fixed at 20% of capital.
- Robustness sleeves: 10%, 15%, 20%, 25% and 30%.
- Risk-off capital: 1-3 month Treasury-bill ETF return, using BIL adjusted prices from 2013 onward.
- Leveraged implementation:
  - USD for a 2x daily semiconductor route.
  - SOXL for a 3x daily semiconductor route using a smaller capital weight.

The core does not rotate. Only the SOXX satellite changes effective exposure.

## Fixed candidate families

The search contains twelve economic families:

1. Original validated SOXX trend-vol exposure, daily execution.
2. Original exposure with a 0.10 no-trade band and mandatory monthly refresh.
3. Portfolio-volatility cap at 30%, daily execution.
4. Portfolio-volatility cap at 30% plus no-trade band.
5. Correlation/volatility concentration cap, daily execution.
6. Correlation/volatility concentration cap plus no-trade band.

Each family is tested with USD and SOXL. Each is evaluated at five sleeve sizes, producing 60 pre-specified candidates.

## Anti-overfit policy

- The production sleeve is fixed at 20%; it is not selected from the best backtest.
- A family is eligible only if the 20% candidate passes the full return-alpha gate.
- The 15%, 20% and 25% neighbouring sleeves must all retain positive CAGR, positive 3x-cost excess and non-negative Sharpe improvement.
- At least four of five sleeve sizes must retain positive CAGR, alpha and 3x-cost excess.
- Buy & Hold and matched static core-satellite policies remain explicit benchmarks.
- Two independent downloads and calculations must agree on family, candidate, classification and current weights.

## Primary benchmark

The matched benchmark uses the same core/satellite starting allocation and the same rebalance dates, but keeps the satellite at 1.0x SOXX. This isolates the value of the SOXX exposure signal from ordinary rebalancing.

A second benchmark is an initial 40% SPY / 40% QQQ / 20% SOXX Buy & Hold portfolio without rebalancing.

## Execution and costs

- Signals use completed daily closes.
- Trades execute at the next regular-session open.
- Cost assumptions:
  - SPY 4 bps
  - QQQ 5 bps
  - SOXX 9 bps
  - BIL 2 bps
  - USD 25 bps
  - SOXL 18 bps
- Base, 2x and 3x cost stress are evaluated.
- Leveraged ETF adjusted prices are used directly; no synthetic long-horizon multiple is assumed.

## Promotion gate

The fixed 20% candidate must satisfy all of:

- CAGR at least 0.5 percentage point above the matched static benchmark.
- CAGR no lower than the 40/40/20 drift Buy & Hold benchmark.
- Sharpe no lower than the matched benchmark.
- Maximum drawdown no more than 3 percentage points worse.
- Beta-adjusted alpha at least 0.5% annually.
- Positive excess CAGR in at least three of four contiguous blocks.
- Positive excess after 3x transaction-cost stress.
- Moving-block bootstrap P(excess > 0) at least 80%.
- Corrected deflated-Sharpe probability at least 80%.
- CSCV probability of backtest overfitting no more than 30%.
- Neighbouring-sleeve robustness requirements described above.

## Evidence base

- Moreira and Muir, *Volatility-Managed Portfolios*, NBER Working Paper 22208 / Journal of Finance.
- DeMiguel, Garlappi and Uppal, *Optimal Versus Naive Diversification*, Review of Financial Studies.
- Direxion SOXL official product documentation: daily 3x objective and explicit warning that cumulative returns over periods longer than one day need not equal 3x.
- ProShares USD official product documentation: daily 2x semiconductor objective.

## Interpretation

This is a pseudo-out-of-sample historical study, not a pristine untouched holdout. No result becomes an order instruction. A passing result would be classified as research alpha and would still require prospective paper-live monitoring before capital deployment.
