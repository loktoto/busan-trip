# Regime-aware daily leverage optimisation v2

Signals use completed daily closes and execute at the next regular-session open.
Winner selection is development-only; the final holdout can only approve or reject that preselected winner.

## SPY

- Decision: **REJECT**
- Actual-product sample: 2010-01-04 to 2026-07-20 (4,160 sessions)
- Search: 5,184 baseline and 1,200 stage-2 candidates; 0 passed development gates
- Diagnostic implementation: SSO; overlay: credit_slope; fixed 2x when active
- Entry: close>SMA150, SMA rising over 10 sessions, RSI(2)<25 within 10 sessions, reclaim SMA10
- Exit: RSI(2)>85
- Full CAGR excess: 1.97%; Sharpe delta: 0.042; MaxDD delta: 0.00%
- Holdout CAGR excess: 2.31%; holdout Sharpe delta: 0.044
- Stress-cost excess: development -1.83%; full sample -1.82%
- Holdout block-bootstrap probability of positive annualised mean excess: 80.5%
- Current effective leverage: 1.00x

## SOXX

- Decision: **REJECT**
- Actual-product sample: 2010-03-11 to 2026-07-20 (4,114 sessions)
- Search: 15,360 baseline and 2,400 stage-2 candidates; 1,910 passed development gates
- Diagnostic implementation: 50% SOXX + 50% SOXL when active; overlay: rv_ratio; fixed effective 2x
- Entry: close>SMA100, SMA rising over 20 sessions, RSI(2)<20 within 2 sessions, reclaim SMA10
- Exit: RSI(2)>95
- Full CAGR excess: 7.54%; Sharpe delta: 0.109; MaxDD delta: 0.00%
- Holdout CAGR excess: -6.63%; holdout Sharpe delta: -0.202
- Stress-cost excess: development 7.26%; full sample 6.22%
- Holdout block-bootstrap probability of positive annualised mean excess: 37.4%
- Current effective leverage: 1.00x

## MAGS7_TSM

- Decision: **EXPERIMENTAL / REJECT FOR PRODUCTION**
- Actual-product sample: 2024-10-03 to 2026-07-20 (448 sessions)
- Search: 3,888 baseline and 900 stage-2 candidates; 0 passed development gates
- Diagnostic implementation: MAGX_TSMX; overlay: breadth_rv; 30% target volatility, capped at 1.5x
- Entry: close>SMA150, SMA rising over 5 sessions, RSI(2)<20 within 10 sessions, reclaim SMA5
- Exit: RSI(2)>90 or close<SMA20
- Full CAGR excess: -7.24%; Sharpe delta: -0.200; MaxDD delta: -0.37%
- Holdout CAGR excess: -13.62%; holdout Sharpe delta: -0.529
- Stress-cost excess: development -8.35%; full sample -13.14%
- Holdout block-bootstrap probability of positive annualised mean excess: 0.0%
- Diagnostic current effective leverage: 1.06x, **not actionable**
