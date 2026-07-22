# Focused index + MAGS7 / MAGS10 entry and exit research

Date: 2026-07-22

## Fixed universe

1. SPY — S&P 500 proxy.
2. QQQ — Nasdaq-100 proxy.
3. SOXX — semiconductor index proxy.
4. SMH — semiconductor index proxy with different construction and concentration.
5. MAGS7 — AAPL, MSFT, NVDA, AMZN, GOOGL, META and TSLA, equal weighted and rebalanced quarterly.
6. MAGS10 — Cboe Magnificent 10 composition: MAGS7 plus AVGO, AMD and PLTR, equal weighted and rebalanced quarterly.

No current portfolio holding, unrelated ETF, regional ETF or other individual stock is part of the research universe.

## Basket construction

MAGS7 and MAGS10 are synthetic adjusted-OHLC indices constructed from their fixed members. They reset to equal weights at each calendar-quarter boundary and otherwise allow weights to drift with relative performance. The common-history start is determined by the latest-listed required constituent; therefore MAGS10 begins only when PLTR data is available. The model does not backfill PLTR or change constituents before its listing.

MAGS and the official Cboe MGTN index are used only as recent live-parity references. Their short histories are not used as the sole optimisation sample.

## Candidate entry families

- Pullback and short-moving-average reclaim inside a rising 100/200-day trend.
- Trend mean reversion using RSI(2) and 20-day z-score.
- 63-day drawdown and EMA reclaim.
- Trend-confirmed 20/50/100-day breakout.
- Pullback near the prior 252-day high followed by EMA reclaim.
- Undercut and reclaim of a prior 20/50-day low.

Signals use completed daily closes and execute at the next session open.

## Candidate exits

- 10/20/30/40/60-session time exits.
- Completed close below SMA10/20/50.
- RSI recovery or moving-average failure.
- Recovery to the pre-entry 252-day high.
- +10%, +15% and +20% take-profit exits.
- 2.5/3/4 ATR chandelier exits.
- Profit lock after a two-entry-ATR favourable move.
- No-progress timeout.
- Universal 12% catastrophic close stop.

## Exposure modes

- 0 to 1x swing.
- 1x core plus a 0.5x tactical overlay.
- 1x core plus a 1.0x tactical overlay.

For SPY, QQQ and semiconductor indices, the overlay can be mapped to liquid 2x/3x ETFs after live parity and liquidity checks. MAGS7 and MAGS10 leveraged modes are modelled exposure only; they are not assumed to be directly implementable through a clean leveraged ETF.

## Validation

- Development-only ranking.
- Purged development blocks.
- Frozen final holdout.
- Normal and doubled transaction costs.
- Deflated Sharpe and PBO controls inherited from V5.
- Block bootstrap probability of positive excess return.
- Direct comparison with the frozen V4 result for the same asset.
- Two independent downloads and calculations. All six assets must match on decision, entry, exit, overlay, mode and exposure.

A higher single-run CAGR is not sufficient for promotion.
