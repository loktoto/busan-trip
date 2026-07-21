# Regime-aware daily leverage optimisation v2

Date: 2026-07-21  
Scope: SPY, SOXX and an 87.5% MAGS + 12.5% TSM basket  
Execution convention: signal on a completed regular-session daily close; change exposure at the following regular-session open.

## Research question

Can the daily pullback-and-reclaim framework be improved without using the final holdout to select parameters, and can those improvements survive the return path of actual leveraged products rather than a frictionless multiple of the underlying?

The v1 result promoted SOXX/USD, rejected SPY/SSO and treated MAGS7+TSM as experimental. V2 retests those findings with regime information, volatility sizing and implementation-aware costs.

## Hypotheses tested

1. **Volatility-managed leverage** — reduce effective leverage when 20-day realised volatility is high.
2. **Credit confirmation** — permit leverage only when HYG/LQD is above its 50-day mean or improving over 20 sessions.
3. **Breadth confirmation** — use RSP/SPY for SPY, XSD/SOXX for semiconductors and QQEW/QQQ for MAGS7+TSM.
4. **Volatility-regime confirmation** — test VIX below 30 and VIX below VIX3M as entry permissions.
5. **Implementation choice** — compare an actual 2x product with effective 2x exposure built from a liquid 3x product plus the native ETF. Product leverage and strategy leverage are modeled separately.
6. **Liquidity-aware eligibility and costs** — reject products whose IBKR execution audit does not support production use and apply materially higher costs to MAGX/TSMX.

## Actual implementations

| Native exposure | Production candidates | Strategy cap | Product leverage | Base switch cost |
|---|---|---:|---:|---:|
| SPY | SSO | 2.0x | 2.0x | 8 bps |
| SOXX | USD; 50% SOXX + 50% SOXL when active | 2.0x | 2.0x / 3.0x | 25 / 18 bps |
| 87.5% MAGS + 12.5% TSM | 50% native + 50% of 87.5% MAGX + 12.5% TSMX | 1.5x | 2.0x | 80 bps |

SPUU was researched but excluded before final optimisation. IBKR showed roughly US$4.57 million of 90-day average dollar volume and a materially poorer displayed market than SSO, so treating both products as an 8-bps implementation choice would be unrealistic.

Costs are charged in proportion to the change in effective leverage. Stress costs are the greater of twice the base cost or base cost plus 20 bps.

## Leakage controls

- The baseline daily signal family is ranked only on development folds.
- Stage 2 tests overlays, implementation and volatility targets only on a small, stable baseline shortlist.
- SPY and SOXX reserve 2025-01-01 onward as the final holdout.
- MAGS7+TSM reserves the available 2026 sample as holdout and remains experimental regardless of numerical pass.
- The winner is selected **only** by development score. Holdout metrics are not included in ranking and can only approve or reject the preselected winner.
- Cost stress used in development selection is calculated only through the development cutoff. Full-sample stress is a separate final validation.
- A moving-block bootstrap is applied to the winner's holdout daily excess returns.
- Promotion requires positive development, fold, development-stress, full-stress and holdout evidence plus at least 70% bootstrap probability of positive annualised mean excess. Experimental assets cannot receive production promotion.

## Daily baseline family

Entry requires price above a rising long moving average, a recent RSI(2) oversold event and a cross back above a short moving average. MAGS7+TSM also requires MAGS and TSM above their own 100-day averages. Exit uses RSI(2) recovery and optionally a close below an exit moving average.

## Regime overlays

The stage-2 search compares no overlay; credit level or slope; breadth level or slope; 20-day realised volatility below 1.15 times 100-day realised volatility; VIX below 30; VIX below VIX3M; credit plus breadth; credit plus realised volatility; breadth plus realised volatility; and credit plus breadth plus VIX contango.

## Volatility targets

- SPY: fixed cap or 18%, 22%, 26% annualised target.
- SOXX: fixed cap or 35%, 45%, 55% target.
- MAGS7+TSM: fixed cap or 30%, 40% target.

The native 1x position remains invested whenever leverage is inactive; the model never moves the underlying allocation to cash.

## Data and audit

GitHub Actions uses adjusted Yahoo Finance OHLCV for a reproducible full-history run. Interactive Brokers is the independent contract, market-state, liquidity and recent-history audit. The completed-close cutoff is 2026-07-20; July 21 snapshots are not inserted into daily backtests.

The IBKR audit records 1,000 SOXX daily sessions including the March 7, 2024 three-for-one split. It also supports using SOXL as a liquid implementation component, excluding SPUU, and applying a large liquidity penalty to MAGX/TSMX.

## Research basis

- Official fund materials define SSO, USD, SOXL, MAGX and TSMX objectives on a **daily** basis; multi-day outcomes depend on path, volatility and implementation frictions.
- Moreira and Muir's volatility-managed portfolio research supports reducing exposure when realised volatility rises, while adaptive target-volatility research warns about turnover and parameter sensitivity.
- Leveraged-ETF research attributes multi-day gaps to compounding, volatility and tracking frictions, making actual-product validation necessary.
- Cboe describes the VIX term structure as option-implied volatility expectations across maturities; VIX/VIX3M is used only as a regime permission, not as a directional forecast.

## Promotion interpretation

`PROMOTE` means the strategy passed the specified historical gates. It does not imply guaranteed future outperformance. `REJECT` means the tested family did not justify replacing the native 1x position. `EXPERIMENTAL` means the product history or implementation quality is insufficient for production sizing.
