# IBKR Recent Daily Grid Audit — Leverage Monitor

**Audit date:** 2026-07-23  
**Completed-close cutoff:** 2026-07-22  
**Connector:** Interactive Brokers exact US contracts, regular-session daily OHLCV  
**Scope:** SPY/SSO, QQQ/QLD, SOXX/USD; 3-month Treasury return set to 0% in this conservative connector-side audit  
**Decision:** `NO_PARAMETER_REPLACEMENT`

## Executive finding

An independent 5-year IBKR challenge tested 5,184 neighbouring trend/volatility parameter combinations around the fixed PR #19 meta strategy. None beat the same-weight literal Buy & Hold benchmark in both the development segment and the following validation segment while also respecting the drawdown and Sharpe guardrails. The attractive 20-session variants were rejected because their apparent full-period improvement did not survive the next validation segment and they also lagged the final one-year test.

The validated PR #19 production identity therefore remains unchanged. This audit does not promote a new rule, create an order, merge the draft PR, or give SMH a trade sleeve.

## Data integrity

- Exact IBKR US contract matches: SPY, SSO, QQQ, QLD, SOXX and USD.
- IBKR returned 1,253 common completed daily bars from 2021-07-26 through 2026-07-22.
- The unfinished 2026-07-23 bar was excluded.
- Reporting correction: the cutoff-day unavailable next-open return is ignored by EWM, matching pandas and the canonical engine; this affects only the displayed current scale, not historical returns.
- Completed 2026-07-22 closes matched the canonical workflow exactly: SPY 747.41, QQQ 705.35, SOXX 555.52, SSO 67.27, QLD 88.28 and USD 92.55.
- The first request exceeded IBKR's 1,000-bar `step_count` limit; the required single retry used the supported `FIVE_YEARS` period and succeeded for every contract.

## Challenger grid

| Dimension | Values |
|---|---|
| SOXX trend gate | SMA50>SMA200; close>SMA200; 252-session time-series momentum |
| SOXX realised-volatility lookback | 20, 40, 63 sessions |
| SOXX volatility target | 30%, 35%, 40%, 45% |
| SOXX exposure cap | 1.25x, 1.50x |
| SOXX risk-off exposure | 0x, 0.5x |
| Whole-portfolio volatility target | 25%, 30%, 35% |
| Portfolio realised-volatility lookback | 20, 40, 63 sessions |
| Portfolio exposure floor | 0.50x, 0.75x |
| Portfolio exposure cap | 1.20x, 1.35x |

Signals used completed closes and next-RTH-open execution. Actual 2x product paths were used, with one-way trading-cost assumptions of 4/8 bps for SPY/SSO, 5/10 bps for QQQ/QLD and 9/25 bps for SOXX/USD.

## Frozen PR #19 rule — recent IBKR challenge

| Segment | Meta CAGR | Literal B&H CAGR | CAGR delta | Meta Sharpe | Sharpe delta | Meta MaxDD | B&H MaxDD | DD change |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Development: 2022-05-02 to 2024-06-28 | 52.18% | 27.14% | +25.04pp | 1.465 | +0.460 | -24.02% | -26.92% | +2.91pp |
| Validation: 2024-07-01 to 2025-06-30 | -10.13% | 3.14% | -13.27pp | -0.213 | -0.470 | -36.92% | -32.41% | -4.51pp |
| Final test: 2025-07-01 to 2026-07-21 | 74.06% | 80.78% | -6.72pp | 1.979 | -0.011 | -13.62% | -17.89% | +4.27pp |
| Common recent period: 2022-05-02 to 2026-07-21 | 38.97% | 32.21% | +6.76pp | 1.213 | +0.147 | -36.92% | -34.07% | -2.85pp |

The recent common-period result is attractive, but the frozen rule failed the deliberately separate validation year on both return and drawdown. That does not invalidate the longer 2013-2026 pseudo-OOS evidence in the canonical report; it prevents this short connector window from being used as a fresh independent promotion claim.

## Best-looking challenger and rejection reason

The highest recent-grid score used SMA50>SMA200, SOXX RV20, 45% target, 1.50x cap, 0x risk-off, portfolio RV20, 30% portfolio target, 0.75x floor and 1.35x cap.

| Segment | Challenger CAGR delta vs B&H | MaxDD improvement | Sharpe delta |
|---|---:|---:|---:|
| Development | +26.34pp | +9.09pp | +0.634 |
| Validation | -1.74pp | +6.33pp | -0.082 |
| Final test | -9.89pp | +4.54pp | -0.039 |
| Common recent period | +10.75pp | +7.99pp | +0.364 |

Despite the strong full-period numbers, the next validation segment and final test both had negative return alpha. It is a classic recent-window overfit and is not allowed to replace the annual anchored 40-day rule.

## Entry and exit logic retained for the monitor

1. SPY/QQQ 2x entry is allowed only when the smoothed whole-portfolio exposure scale rises above 1.0x. Operationally this requires the EWM-smoothed 30% target divided by 40-session portfolio realised volatility to exceed 1.0, subject to the 0.75x-1.35x scale band and the 1.50x gross cap.
2. SOXX 2x entry additionally requires SMA50>SMA200 and `portfolio_scale × EWM5(clip(40% / SOXX_RV40, 0.5x, 1.5x)) > 1.0x`.
3. Signals are read only after the completed RTH close and executed, if manually approved, at the next RTH open.
4. The 2x weight inside a sleeve is `sleeve_budget × (target_exposure - 1)` when target exposure is above 1.0x. Below 1.0x, the leveraged product weight is zero and unused capital stays in Treasury cash.
5. Exit the 2x product when target exposure returns to 1.0x or below. SOXX immediately falls to the 0.5x risk-off state when SMA50 is no longer above SMA200; rising realised volatility can also de-lever before the trend gate breaks.
6. RSI2/B50 may remain a separate QQQ shadow diagnostic, but it is not combined with or allowed to override this portfolio-level production identity.

## Current completed-close state

The canonical adjusted-price engine remains authoritative for target weights: portfolio scale 0.8778x, SOXX alpha exposure about 0.5647x, effective gross exposure about 0.6485x, and 0% in SSO, QLD and USD. The connector-only raw-price audit independently estimated a 0.8781x scale and the same approximately 0.565x SOXX alpha exposure; both methods agree that no leveraged ETF entry is active. The 0.8781x figure uses pandas-compatible EWM handling that carries the prior smoothed value across the cutoff day's unavailable next-open return.

## Limitations

- IBKR's connector exposes at most five years in one daily-history request. The 1/3/5/10/MAX evidence remains the actual adjusted-product pseudo-OOS workflow persisted in this PR.
- IBKR OHLCV here is a price-path audit, not a dividend-adjusted total-return reconstruction. Setting the Treasury sleeve to 0% is conservative and prevents an unverified cash-yield assumption.
- The 2013-2026 history is pseudo-OOS, not untouched prospective evidence. Forward paper-live monitoring remains required.
- No automatic order authority is introduced.