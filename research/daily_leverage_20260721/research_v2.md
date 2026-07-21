# Regime-aware daily leverage optimisation v2

Date: 2026-07-21  
Scope: SPY, SOXX and an 87.5% MAGS + 12.5% TSM basket  
Execution convention: signal on a completed regular-session daily close; change exposure at the following regular-session open.

## Research question

Can the daily pullback-and-reclaim framework be improved without using the final holdout to select parameters, and can those improvements survive the return path of the actual leveraged products rather than a frictionless multiple of the underlying?

The v1 result promoted SOXX/USD, rejected SPY/SSO and treated MAGS7+TSM as experimental. V2 does not assume those conclusions are correct. It retests the family with additional regime information and implementation choices.

## Hypotheses tested

1. **Volatility-managed leverage** — reduce effective leverage when 20-day realised volatility is high.
2. **Credit confirmation** — permit leverage only when HYG/LQD is above its 50-day mean or improving over 20 sessions.
3. **Breadth confirmation** — use RSP/SPY for SPY, XSD/SOXX for semiconductors and QQEW/QQQ for MAGS7+TSM.
4. **Volatility-regime confirmation** — test VIX below 30 and VIX below VIX3M as entry permissions.
5. **Implementation choice** — compare actual 2x products and equivalent leverage built with a 3x product blended with the native ETF. Product leverage and strategy leverage are modeled separately.
6. **Liquidity-aware costs** — use materially higher turnover costs for MAGX/TSMX than for SSO/SPUU or USD/SOXL.

## Actual implementations

| Native exposure | Implementation candidates | Strategy cap | Product leverage | Base switch cost |
|---|---|---:|---:|---:|
| SPY | SSO; SPUU | 2.0x | 2.0x | 8 bps |
| SOXX | USD; 50% SOXX + 50% SOXL when active | 2.0x | 2.0x / 3.0x | 25 / 18 bps |
| 87.5% MAGS + 12.5% TSM | 50% native + 50% of 87.5% MAGX + 12.5% TSMX | 1.5x | 2.0x | 80 bps |

Costs are charged in proportion to the change in effective leverage. Stress costs are the greater of twice the base cost or base cost plus 20 bps.

## Leakage controls

- The baseline daily signal family is ranked only on development folds.
- Stage 2 tests overlays, implementation and volatility targets only on a small, stable baseline shortlist.
- SPY and SOXX reserve 2025-01-01 onward as the final holdout.
- MAGS7+TSM reserves the available 2026 sample as holdout and remains experimental regardless of numerical pass.
- Holdout results do not change the development ranking; they only approve or reject the preselected winner.
- A moving-block bootstrap is applied to holdout daily excess returns.
- Promotion requires positive development, fold, cost-stress and holdout evidence plus at least 70% bootstrap probability of positive annualised mean excess. Experimental assets cannot receive production promotion.

## Daily baseline family

Entry requires price above a rising long moving average, a recent RSI(2) oversold event and a cross back above a short moving average. MAGS7+TSM also requires MAGS and TSM to remain above their own 100-day averages. Exit uses RSI(2) recovery and optionally a close below an exit moving average.

## Regime overlays

The stage-2 search compares no overlay; credit level or slope; breadth level or slope; 20-day realised volatility below 1.15 times 100-day realised volatility; VIX below 30; VIX below VIX3M; credit plus breadth; credit plus realised volatility; breadth plus realised volatility; and credit plus breadth plus VIX contango.

## Volatility targets

- SPY: fixed cap or 18%, 22%, 26% annualised target.
- SOXX: fixed cap or 35%, 45%, 55% target.
- MAGS7+TSM: fixed cap or 30%, 40% target.

Exposure remains at least 1x while a leverage state is active; the model never moves the native position to cash.

## Data and audit

GitHub Actions uses adjusted Yahoo Finance OHLCV to make the full run reproducible. Interactive Brokers is the independent contract, current-market and recent-history audit. The completed-close cutoff is 2026-07-20; July 21 snapshots are not inserted into daily backtests.

The IBKR audit records a 1,000-session SOXX daily history including the March 7, 2024 three-for-one split. It also shows a large liquidity gap between MAGS and MAGX, supporting the 80-bps MAGS7+TSM switch-cost assumption.

## Research basis

- ProShares states that SSO targets two times the **daily** S&P 500 return and that multi-day outcomes depend on volatility and holding path.
- ProShares states the same daily objective for USD against its semiconductor index.
- Direxion and Roundhill product materials describe daily objectives for SOXL, MAGX and TSMX rather than guaranteed multi-day multiples.
- Moreira and Muir's volatility-managed portfolio research supports reducing exposure when realised volatility rises; later adaptive-volatility-control research cautions that target-volatility rules can create turnover and parameter sensitivity.
- Recent leveraged-ETF research attributes multi-day gaps to compounding, volatility and implementation frictions; actual-product validation is therefore a promotion requirement.
- Cboe describes the VIX term structure as option-implied volatility expectations across maturities; VIX/VIX3M is used only as a regime permission, not as a price forecast.

## Promotion interpretation

`PROMOTE` means the strategy passed the specified historical gates. It does not imply guaranteed future outperformance. `REJECT` means the tested family did not justify replacing the native 1x position. `EXPERIMENTAL` means the numerical result may be interesting but the live product history is insufficient for production sizing.
