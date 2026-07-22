# SPY + QQQ + SOXX Expanded Alpha Search V2

## Purpose

Search beyond simple moving-average exits without forcing a winner. PR #11 remains the production baseline unless this search passes every pre-specified gate.

## Raw candidate families

1. Fixed trend rules: price/MA, dual-MA and 12-month time-series momentum.
2. Continuous volatility targeting with 0.5x-2.0x exposure caps.
3. Trend-gated volatility targeting.
4. Multi-regime voting: own trend, equal-weight breadth, credit, VIX/VIX3M term structure and realised-volatility ratio.
5. Drawdown recovery and RSI(2) reclaim overlays.
6. Donchian breakout add-ons.
7. Overnight-versus-RTH decompositions with explicit daily handoff costs.

## Anchored walk-forward construction

- Each family is evaluated independently for SPY, QQQ and SOXX.
- At the start of each calendar year from 2013 onward, parameter selection uses only observations available through the previous December 31.
- Buy & Hold is included as an annual option inside every family, preventing forced timing.
- The selected raw rule is frozen for the following calendar year.
- Annual out-of-sample returns are concatenated into one family-level walk-forward stream.
- Final comparison therefore uses approximately eleven family/ensemble streams per asset rather than selecting directly from roughly two hundred raw parameter combinations.
- The 2013-2026 period is labelled anchored pseudo-OOS, not untouched holdout data, because earlier research has already inspected parts of it.

## Execution and costs

- Completed daily-close information only; next regular-session-open execution.
- Cash return uses the daily Federal Reserve three-month Treasury yield series.
- Base, 2x and 3x transaction-cost stresses are applied without re-optimisation.
- Annual family switching incurs the resulting exposure turnover; session strategies also incur a conservative switching charge.
- IBKR 2026-07-21 completed-close parity is mandatory. The 2026-07-22 intraday observations are audit-only and excluded.

## Multiple-testing controls

- Four contiguous OOS blocks test regime consistency.
- Moving-block bootstrap tests the sign of mean excess return.
- Deflated-Sharpe probability uses the full raw parameter count as the trial penalty.
- CSCV/PBO is applied to the final family-level search set.
- Two independent full downloads must agree exactly on every annual family choice, final strategy identity and current model exposure.

## Promotion gates

### Return alpha

- CAGR at least 0.5 percentage point above Buy & Hold.
- Sharpe no lower than Buy & Hold.
- Maximum drawdown no more than 3 percentage points worse.
- Beta-adjusted annual alpha at least 0.5 percentage point.
- Positive excess CAGR in at least three of four OOS blocks.
- Positive excess remains after 3x transaction costs.
- Bootstrap P(excess > 0) at least 80%.
- Deflated-Sharpe probability at least 80%.
- Search PBO no more than 30%.

### Defensive alpha

- Sharpe at least 0.10 above Buy & Hold.
- Maximum drawdown improves by at least 20%.
- CAGR sacrifice no greater than 2 percentage points.
- Sharpe improves in at least three of four OOS blocks.
- Search PBO no more than 40%.

## Interpretation

A high terminal value caused only by higher average exposure is not sufficient. Return-alpha promotion additionally requires positive beta-adjusted alpha, Sharpe preservation, block consistency and 3x-cost survival. A RESEARCH_ONLY result leaves production exposure at 1.0x.

## Primary research references

- Moreira and Muir, “Volatility-Managed Portfolios,” Journal of Finance 72(4), 2017, DOI 10.1111/jofi.12513.
- Cederburg, O'Doherty, Wang and Yan, “On the Performance of Volatility-Managed Portfolios,” Journal of Financial Economics 138(1), 2020.
- Moskowitz, Ooi and Pedersen, “Time Series Momentum,” Journal of Financial Economics 104(2), 2012.
- Lou, Polk and Skouras, “A Tug of War: Overnight Versus Intraday Expected Returns,” Journal of Financial Economics 134(1), 2019.
- Cboe VIX and VIX3M term-structure indices.
