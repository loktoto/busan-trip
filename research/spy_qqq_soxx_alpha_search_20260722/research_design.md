# SPY + QQQ + SOXX Expanded Alpha Search

## Purpose

Continue beyond simple moving-average and pullback timing while preserving the conservative baseline established by PR #11. The search is allowed to conclude that no production alpha exists.

## Candidate families

1. Fixed trend rules: price/MA, dual-MA, 12-month time-series momentum.
2. Continuous volatility targeting with 0.5x-2.0x exposure caps.
3. Trend-gated volatility targeting.
4. Multi-regime voting: own trend, equal-weight breadth, credit, VIX/VIX3M term structure, and realised-volatility ratio.
5. Drawdown recovery and RSI(2) reclaim overlays.
6. Donchian breakout add-ons.
7. Overnight-versus-RTH decompositions with explicit daily handoff costs.

## Research discipline

- SPY, QQQ and SOXX are evaluated independently.
- Completed daily close signals; next regular-session open execution.
- 1.0x Buy & Hold is always a candidate.
- Candidate families and parameter grids are fixed before the canonical run.
- Four contiguous market blocks test regime consistency.
- Moving-block bootstrap, deflated-Sharpe diagnostic and family-level CSCV/PBO.
- Base, 2x and 3x transaction-cost stress.
- Two independent full downloads and calculations must agree on strategy identity.
- IBKR 2026-07-21 completed-close parity is mandatory. 2026-07-22 intraday data is audit-only and excluded.

## Promotion gates

### Return alpha

- CAGR at least 0.5 percentage point above Buy & Hold.
- Sharpe no lower than Buy & Hold.
- Maximum drawdown no more than 3 percentage points worse.
- Positive excess CAGR in at least three of four blocks.
- Positive excess remains after 3x costs.
- Bootstrap P(excess > 0) >= 80%.
- Deflated-Sharpe probability >= 80%.
- Family PBO <= 30%.

### Defensive alpha

- Sharpe at least 0.10 above Buy & Hold.
- Maximum drawdown improves by at least 20%.
- CAGR sacrifice no greater than 2 percentage points.
- Sharpe improves in at least three of four blocks.
- Family PBO <= 40%.

## Primary research references

- Moreira and Muir, “Volatility-Managed Portfolios,” Journal of Finance 72(4), 2017, DOI 10.1111/jofi.12513.
- Cederburg, O'Doherty, Wang and Yan, “On the Performance of Volatility-Managed Portfolios,” Journal of Financial Economics 138(1), 2020.
- Moskowitz, Ooi and Pedersen, “Time Series Momentum,” Journal of Financial Economics 104(2), 2012.
- Lou, Polk and Skouras, “A Tug of War: Overnight Versus Intraday Expected Returns,” Journal of Financial Economics 134(1), 2019.
- Cboe VIX term-structure indices: VIX and VIX3M.
