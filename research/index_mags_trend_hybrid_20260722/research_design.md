# Index + MAGS trend and pullback hybrid research

Date: 2026-07-22  
Completed-close cutoff: 2026-07-21  
Capital for comparison: US$10,000

## Focused universe

- SPY / S&P 500
- QQQ / Nasdaq-100
- SOXX
- SMH
- MAGS7: fixed AAPL, MSFT, NVDA, AMZN, GOOGL, META and TSLA membership; quarterly equal weight
- MAGS10: Cboe Magnificent 10 proxy — MAGS7 plus AVGO, AMD and PLTR; quarterly equal weight

Current holdings and unrelated ETFs or stocks do not enter the research.

## Strategies compared

1. **Buy & Hold** — continuous 1.0x exposure.
2. **Trend-only** — a development-selected trend state controls exposure between 1.0x and either 0.5x or cash/BIL.
3. **Pullback-only** — continuous 1.0x exposure plus the frozen, previously audited pullback/reclaim add-on for SOXX, SMH and MAGS7. SPY, QQQ and MAGS10 have no approved add-on, so their pullback-only path equals Buy & Hold.
4. **Hybrid** — the trend layer controls the base exposure; the frozen pullback add-on is permitted only while the trend state is positive.

The hybrid therefore separates jobs:

- trend is a risk-state filter intended to improve drawdown and Sharpe;
- pullback/reclaim is a return-enhancement layer intended to add exposure after qualified corrections.

## Trend family

The trend search is deliberately small and interpretable:

- price above SMA100, SMA150, SMA200 or SMA250;
- SMA50 above SMA200;
- SMA100 above SMA200;
- positive 252-session time-series momentum;
- two majority-vote composites combining price, moving-average and momentum states.

Each rule is tested with two risk-off exposures: 0.0x and 0.5x.

A one-basis-point hysteresis band reduces sensitivity to adjusted-price float noise.

## Selection and evaluation

- Trend parameters are selected only on development data ending 2021-12-31 for SPY, QQQ, SOXX, SMH and MAGS7.
- MAGS10 development ends 2024-09-09 because the fixed ten-member proxy begins only when PLTR data are available.
- Development data are divided into three chronological blocks.
- The selected trend rule is frozen before calculating trailing 1-, 3-, 5- and 10-year results and the maximum available sample.
- Each horizon uses the same frozen rule. The strategy is not re-optimised separately for each reporting horizon.
- Signals use completed daily closes and are applied at the next regular-session open.
- Cash earns BIL returns where available; before BIL history, cash return is conservatively set to zero.
- Transaction costs follow the focused configuration: SPY 4 bps, QQQ 5, SOXX 8, SMH 7, MAGS7 10 and MAGS10 12 per unit of turnover.

## Reported measures

For every asset, strategy and horizon:

- terminal value of an initial US$10,000;
- CAGR;
- Sharpe ratio;
- maximum drawdown;
- Calmar ratio;
- average and current exposure;
- exposure changes as a turnover diagnostic.

## Repeatability gate

The GitHub workflow performs two independent downloads and calculations.

Production comparison requires:

- exact agreement on the selected trend rule, risk-off exposure and current strategy identity;
- terminal-value difference no greater than 0.15%;
- CAGR difference no greater than 5 basis points;
- Sharpe and Calmar difference no greater than 0.002;
- maximum-drawdown difference no greater than 5 basis points.

A failed repeatability comparison invalidates the canonical report rather than selecting the more attractive repetition.

## Interpretation

The highest terminal value is not automatically the best strategy. A trend strategy may deliberately surrender upside in exchange for lower drawdown. The report therefore identifies separately:

- return winner;
- risk-adjusted winner;
- whether the hybrid preserves enough pullback alpha to justify its additional complexity.

## Limitations

- Maximum-sample results contain both development and later evaluation periods; they are not entirely out-of-sample.
- MAGS7 and MAGS10 are fixed-current-definition proxies and therefore carry universe-definition and survivorship risk.
- MAGS7 begins in 2012 when all seven current members have common data. MAGS10 begins in 2020 when PLTR data become available.
- Exposure above 1.0x for synthetic MAGS baskets is modelled; this study does not claim that a matching low-cost leveraged product existed throughout history.
- BIL, adjusted OHLC and synthetic basket construction are approximations. Recent completed closes are independently checked against IBKR before live use.
- Trend and pullback systems can underperform Buy & Hold for prolonged periods and future results are not guaranteed.
