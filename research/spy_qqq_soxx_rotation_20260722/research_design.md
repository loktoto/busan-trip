# SPY + QQQ + SOXX Relative-Strength Rotation

## Objective

Test whether alpha exists at the portfolio-allocation level even when SPY and QQQ do not individually pass timing gates. The primary benchmark is an initial one-third allocation to each ETF held without rebalancing.

## Fixed candidates

- equal-weight core benchmark
- top-one and top-two composite momentum
- top-one and top-two volatility-adjusted momentum
- 50% equal-weight core plus 50% momentum tilts
- validated SOXX trend-vol as a one-third sleeve
- blended relative-strength rotation plus SOXX-alpha sleeve

Composite momentum uses fixed 63-, 126- and 252-session returns with weights 45%, 35% and 20%. Eligibility requires positive composite momentum and price above SMA200. Target weights are smoothed with a five-session EWM and executed at the next regular-session open.

## Validation

- Daily completed-close signals and next-open execution.
- Cash accrues the Federal Reserve three-month Treasury yield.
- Asset-specific costs for SPY, QQQ and SOXX with base, 2x and 3x stress.
- Four contiguous OOS blocks, moving-block bootstrap, corrected DSR and CSCV/PBO.
- Beta-adjusted alpha versus the one-third Buy & Hold portfolio.
- Side-by-side terminal values versus SPY, QQQ and SOXX individual Buy & Hold.
- Two independent full downloads and calculations must agree on winner, classification and current weights.

## Promotion gate

Return alpha requires at least +1.0 percentage point CAGR versus the one-third benchmark, non-negative Sharpe delta, no more than three percentage points worse maximum drawdown, at least +1.0% annual beta-adjusted alpha, positive CAGR delta in at least three of four blocks, positive 3x-cost delta, bootstrap probability at least 80%, DSR at least 80% and search PBO at most 30%.

The 2013-2026 period is pseudo-OOS, not untouched holdout data. No IBKR order instruction is created.
