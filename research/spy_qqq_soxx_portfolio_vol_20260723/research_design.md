# SPY + QQQ + SOXX Portfolio-Level Volatility Management

## Purpose

Test whether total-portfolio exposure management can improve a fixed 40% SPY / 40% QQQ / 20% SOXX portfolio more robustly than choosing among SOXX satellite overlays. The standalone SOXX signal from PR #13 is not re-optimized or reused as a selection shortcut in this study.

## Fixed production specification

- Strategic reference allocation: 40% SPY, 40% QQQ and 20% SOXX.
- Production volatility target: fixed at 25% annualised.
- Robustness targets: 22% and 28% annualised; neither can be selected as production.
- Total effective equity exposure range: 0.5x to 1.5x.
- Completed daily-close signal; next regular-session-open execution.
- Rebalance monthly or when total exposure or strategic weights move by at least 0.10.
- Risk-off capital earns the actual BIL adjusted-price return where available.

## Economic families

Six fixed families are evaluated:

1. `fixed_vol`: fixed 40/40/20 strategic weights with continuous 40-day portfolio-volatility targeting.
2. `fixed_trend`: fixed weights and volatility targeting, capped by the number of indices above SMA200.
3. `fixed_trend_corr`: trend-volatility exposure plus a fixed high-correlation/high-volatility concentration cap.
4. `fixed_trend_drawdown`: trend-volatility exposure plus fixed 10%, 20% and 30% drawdown caps.
5. `shrink_invvol_vol`: monthly 50% strategic-weight / 50% inverse-volatility shrinkage allocation, plus portfolio-volatility targeting.
6. `shrink_invvol_trend`: the shrinkage allocation plus the fixed trend breadth cap.

The shrinkage allocation is constrained to:

- SPY 25%-55%
- QQQ 25%-55%
- SOXX 10%-30%

## Actual product routes

### 2x route

- SPY exposure above 1x: SSO
- QQQ exposure above 1x: QLD
- SOXX exposure above 1x: USD

### 3x route

- SPY exposure above 1x: UPRO
- QQQ exposure above 1x: TQQQ
- SOXX exposure above 1x: SOXL

Adjusted product prices are used directly. No leveraged return series is synthesised by multiplying underlying returns.

## Candidate count and selection universe

- Six economic families.
- Two actual-product routes.
- Three target-volatility values.
- 36 total candidates.
- Only the twelve fixed-25%-target families enter CSCV/PBO and production selection.
- The 22% and 28% targets are neighbouring robustness diagnostics only.

## Benchmarks

Every candidate is compared with two separate benchmarks:

1. **Matched dynamic 1x benchmark**: same strategic or shrinkage allocation, same rebalance dates and same product universe, but fixed at 1.0x total exposure. This isolates exposure-management alpha from allocation/rebalancing effects.
2. **40/40/20 drift Buy & Hold**: initial 40% SPY / 40% QQQ / 20% SOXX without rebalancing.

## Transaction costs

Base one-way assumptions:

- SPY 4 bps
- QQQ 5 bps
- SOXX 9 bps
- BIL 2 bps
- SSO 8 bps
- QLD 9 bps
- USD 25 bps
- UPRO 12 bps
- TQQQ 10 bps
- SOXL 18 bps

Each candidate is evaluated at base, 2x and 3x transaction-cost stress.

## Promotion gate

The fixed 25% candidate must satisfy all of:

- CAGR at least 0.5 percentage point above its matched dynamic 1x benchmark.
- CAGR no lower than 40/40/20 drift Buy & Hold.
- Sharpe no lower than the matched benchmark.
- Maximum drawdown no more than 3 percentage points worse.
- Beta-adjusted alpha at least 0.5% annually.
- Positive excess CAGR in at least three of four contiguous blocks.
- Positive excess after 3x transaction-cost stress.
- Moving-block bootstrap P(excess > 0) at least 80%.
- Corrected deflated-Sharpe probability at least 80%.
- Twelve-family CSCV/PBO no more than 30%.

The selected family must additionally retain positive CAGR, positive beta-adjusted alpha, non-negative Sharpe improvement and positive 3x-cost excess at all three 22%, 25% and 28% target-volatility settings.

## Repeatability

Two independent full downloads and calculations must agree on:

- selected family and actual-product route
- classification and gate states
- fixed 25% production candidate
- current asset, leveraged-product and cash weights
- input date ranges and frozen base-engine source
- all numerical outputs within fixed tolerances

## Evidence basis

The economic premise follows the volatility-management literature: expected returns and volatility do not move proportionally, so reducing exposure in high-volatility states can improve risk-adjusted outcomes. The design also follows the diversification literature by using fixed strategic weights or constrained shrinkage toward simple weights rather than an unconstrained mean-variance optimizer.

This remains a pseudo-out-of-sample historical study. It is not a pristine untouched holdout and does not create an IBKR order instruction.
