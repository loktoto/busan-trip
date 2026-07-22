# Universal ETF and stock entry/exit challenger V5

Date: 2026-07-22  
Frozen benchmark: Universal V4.1, PR #7  
Universe: the same 85 ETFs, leveraged ETFs and stocks; no asset is removed because its V4.1 result is inconvenient.

## Objective

V5 is not another unrestricted parameter search. It asks whether a diversified, path-aware challenger can improve the frozen V4.1 rule for each asset after accounting for multiple testing. V5 can replace V4.1 only; the V4.1 result remains the source of truth when the challenger fails.

## New entry families

1. **Undercut and reclaim** — failed 20/50-day breakdown followed by a bullish reclaim inside a rising 100/200-day trend.
2. **52-week-high pullback** — price remains near the prior 252-day high, touches EMA10/20 and then reclaims it.
3. **Gap-volume drift proxy for stocks** — positive overnight information shock, bullish close and abnormal volume inside a positive trend. This is a price/volume proxy, not proof of an earnings surprise.

These are added to V4.1's pullback/reclaim, trend mean reversion, volatility-compression breakout, drawdown reclaim, relative-strength breakout and time-series momentum families.

## New exits

1. 2.5 ATR chandelier trail.
2. Profit lock: after reaching +2 entry ATR, trail by 1.5 current ATR.
3. No-progress timeout: exit after ten sessions when maximum favourable excursion has not reached one entry ATR.
4. Longer 15/30/60-session time exits and RSI(5)/EMA exits.

## Ensemble selection

- Stage A ranks individual entry/exit pairs only on development data.
- Stage B adds regime, realised-volatility, relative-strength, credit/volatility and stock event-safe overlays plus path-dependent stops.
- Candidates are diversified by entry family and rejected when state correlation exceeds 0.90.
- V5 tests two- and three-component ensembles. Activity is the mean vote, producing fractional exposure rather than an all-or-nothing switch.
- Core ETF overlays remain capped at 1.5x. Tactical stocks and leveraged ETFs remain between cash and 1.0x.

## Event handling

For stocks, a gap larger than 4% or 1.5 prior ATR with at least 1.5x median volume creates a three-session event embargo for ordinary technical entries. The dedicated positive gap-volume drift family can enter after the event-day close. Any live stock entry still requires an actual earnings and corporate-event calendar check.

## Anti-overfitting controls

- V4.1 is frozen before V5 is run.
- Completed-close signals and next-open execution.
- Development-only ranking; holdout cannot rank or select challengers.
- Twenty-session purge/embargo inside development blocks.
- Deflated Sharpe probability adjusts for the number of stage-two candidates and non-normal returns.
- PBO proxy measures how often the development winner ranks below the median across purged blocks.
- Stressed transaction costs, final holdout, block bootstrap and direct V4.1 comparison.
- A replacement requires its own production gates and at least +0.5 percentage point holdout CAGR improvement over V4.1 without materially worse Sharpe or drawdown.
- Experimental and specialist assets cannot receive production promotion.

## Research basis

- Bailey, Borwein, López de Prado and Zhu, *The Probability of Backtest Overfitting*, Journal of Computational Finance: combinatorially symmetric validation is designed for investment backtests where a simple holdout may be insufficient.
- Bailey and López de Prado, *The Deflated Sharpe Ratio*: reported Sharpe must be corrected for selection bias, multiple trials and non-normality.
- Hung, Li and Wang, *Post-Earnings-Announcement Drift in Global Markets*, Review of Financial Studies: information diffusion and limits to arbitrage affect post-announcement drift.
- Zhong, *Innovation and Informed Trading: Evidence from Industry ETFs*, Review of Financial Studies: industry ETFs can accelerate information incorporation around member-stock earnings, supporting separate stock and ETF event handling.
- Moreira and Muir, *Volatility-Managed Portfolios*: realised-volatility scaling can improve risk-adjusted performance but remains subject to implementation and turnover costs.

## Replacement interpretation

- `REPLACE_V4`: V5 passed its own development, purged-block, DSR, PBO, stress, holdout and bootstrap gates and beat the frozen V4.1 result by the replacement margin.
- `KEEP_V4`: V5 failed its own statistical gates or did not improve enough to justify changing the audited rule.
- A replacement is still historical evidence, not guaranteed future outperformance.
