# SPY + QQQ + SOXX Meta Risk Strategy

## Hypothesis

The earlier research treated each index or full-portfolio rotation as the unit of alpha. This challenger instead preserves diversified core exposure while applying the already validated SOXX trend-vol signal inside a fixed satellite sleeve, then scales the whole portfolio to a fixed risk budget.

## Pre-specified production candidate

- 20% SPY capital sleeve
- 20% QQQ capital sleeve
- 60% SOXX capital sleeve
- SPY and QQQ normally target 1.0x sleeve exposure
- SOXX uses the annual anchored trend-vol choices already validated in PR #13
- whole-portfolio target volatility: 30%
- 40-session realised-volatility estimator, EWM span 5
- portfolio scale constrained to 0.75x-1.35x
- total effective gross exposure capped at 1.50x

The 30% target is risk-matched to the long-run volatility of SOXX rather than selected to maximise terminal wealth.

## Actual implementation

Each capital sleeve is internally implemented with cash, its 1x ETF and its 2x ETF:

- SPY / SSO
- QQQ / QLD
- SOXX / USD

For a sleeve target below 1.0x, the unused capital remains in the 3-month Treasury cash series. Above 1.0x, the sleeve blends the 1x and 2x ETFs to reproduce the target exposure. The three sleeve capital budgets always sum to 100%.

## Robustness variants

The production weights are fixed before the run. Three neighbouring variants test whether the result depends on one strategic allocation:

- 30/30/40
- 25/25/50
- 20/20/60 — production
- 15/15/70

Promotion requires the production candidate to pass and at least three of four variants to pass the same return-alpha gate.

## Benchmarks

Primary benchmark: literal initial-weight Buy & Hold. At the first pseudo-OOS open, the benchmark invests the same SPY/QQQ/SOXX strategic capital weights once and then allows the weights to drift without rebalancing.

Additional dominance comparison: SOXX Buy & Hold over the exact common period. Production classification additionally requires higher CAGR, higher Sharpe and a smaller maximum drawdown than SOXX Buy & Hold.

The earlier daily constant-mix benchmark was withdrawn because it was not literal Buy & Hold. The strategy was rerun from source against the stricter benchmark before promotion.

## Gate

- CAGR at least 0.5 percentage point above the literal initial-weight Buy & Hold benchmark
- Sharpe no lower
- maximum drawdown no more than 3 percentage points worse
- beta-adjusted alpha at least 0.5% annually
- positive excess CAGR in at least 3 of 4 contiguous blocks
- positive excess after 3x transaction costs
- moving-block bootstrap P(excess > 0) at least 80%
- corrected DSR at least 80%, with an eight-trial floor reflecting prior strategy search
- CSCV/PBO no greater than 30%
- two independent downloads must agree on classification, current product weights and all inherited annual SOXX rule identities
- IBKR parity is required against the completed 2026-07-22 closes

## Reporting integrity

Returns use signal-day close information with next-RTH-open execution. Current target weights preserve the latest completed-close signal date rather than truncating to the last realised open-to-open return date. The canonical workflow hard-requires a 2026-07-22 current signal date.

The 2013-2026 evaluation is pseudo-OOS and is not described as untouched holdout evidence. PBO of zero is not interpreted as literal proof of no overfitting risk. No order instruction is created.
