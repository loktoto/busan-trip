# Frozen SOXX leverage challenger methodology

## Research question

Can a simple SOXX-only pullback/reclaim signal identify periods when raising exposure from
1.0x to 1.5x improves return without sacrificing the risk controls of the production
annual-anchored trend-vol signal?

Capital allocation is not a model-selection variable. SMH is a diagnostic reference only and
cannot create a trade row, entry rule, position size, or invalidation rule.

## Frozen design

- Signal input: adjusted SOXX daily OHLC.
- Signal timing: completed US regular-session close; next-open execution.
- Development cutoff: 2012-12-31.
- OOS start: 2013-01-01.
- Family size: 81 candidates.
- RSI2 five-session minimum: 5, 7, or 10.
- Reclaim average: SMA5, SMA10, or SMA15.
- Maximum hold: 30, 40, or 50 sessions.
- Latched trailing stop: none, 12%, or 16%.
- Trend prerequisite: SOXX SMA50 above SMA200.
- Exposure: 1.0x normally and 1.5x only when the frozen signal is active.

The exit is stateful and latched. A stopped trade cannot silently reactivate inside the same
holding window merely because price later recovers.

## Actual-product validation

The signal-level winner is selected without using an investor allocation. It is then evaluated
using adjusted prices for both execution routes:

- SOXX + USD to reproduce 1.5x exposure with a 2x product.
- SOXX + SOXL to reproduce 1.5x exposure with a 3x product.

Base one-way cost assumptions are 9 bps for SOXX, 25 bps for USD, and 18 bps for SOXL.
The promotion gate also requires positive CAGR alpha at three times those costs.

## Mandatory promotion gate

Every route must pass all of the following:

- OOS CAGR advantage of at least 0.5 percentage points versus same-period SOXX Buy & Hold.
- Non-negative OOS Sharpe difference.
- OOS maximum drawdown no more than 3 percentage points worse.
- Positive CAGR advantage at 3x transaction costs.
- Moving-block bootstrap probability of positive excess return of at least 80%.
- Corrected deflated-Sharpe probability of at least 80%.
- CSCV/search PBO no greater than 30%.
- Full return/Sharpe/drawdown gate in at least three of four non-overlapping blocks.
- Full gate pass rate of at least 60% in rolling three-year windows and 70% in rolling five-year windows.
- At least 30% of neighbouring parameters improve CAGR, Sharpe, and maximum drawdown.

A high aggregate CAGR cannot override a failed stability, drawdown, DSR, or PBO gate.

## Binance ablation

BTC spot and perpetual funding are zero-production-weight research features. A full UTC crypto
bar dated t is shifted by one calendar day before it can be aligned to a US equity session,
preventing use of information that was incomplete at the US signal time.

Four fixed layers are evaluated, not mined:

- BTC above SMA100.
- BTC above SMA200.
- BTC not more than 20% below its prior 63-day high.
- BTC above SMA100 while seven-day funding is not above its expanding 90th percentile.

A layer must improve the unfiltered frozen candidate in aggregate and in at least two of three
non-overlapping blocks without worsening maximum drawdown by more than 3 percentage points.
Binance open interest is excluded from historical selection because the official endpoint
retains only the latest 30 days; it remains forward-shadow only.

## Production boundary

`main:production/leverage_signal.json` remains the sole production authority. This experiment
cannot alter production automatically and creates no order authority.
