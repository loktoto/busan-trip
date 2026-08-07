# Daily leverage optimisation — actual-product validation

Signals are calculated at the close and applied at the following regular-session open.
A diagnostic fallback is reported when no candidate passes the strict training gate; fallback rules are not promoted.

## SPY

- Actual-product overlap: 2010-01-04 to 2026-07-20 (4,160 sessions)
- Search: 1,944 candidates; 0 passed the strict training gate
- Selection mode: **diagnostic_fallback**
- Diagnostic entry: rising SMA200 over 10 sessions; RSI(2)<15 within 5 sessions; reclaim SMA20
- Diagnostic exit: RSI(2)>90
- Full CAGR: 15.58% vs native 14.14%
- Full Sharpe: 0.81 vs native 0.88
- Full MaxDD: -32.45% vs native -32.05%
- OOS excess: +1.81%; stress-cost excess: -0.35%
- Promotion gate: **FAIL**
- Official implementation state: **native 1× SPY**. The optimiser's internal `levered` state is diagnostic only and is not actionable.

## SOXX

- Actual-product overlap: 2010-01-04 to 2026-07-20 (4,160 sessions)
- Search: 11,520 candidates; 1,790 passed the strict training gate
- Selection mode: **strict**
- Entry: rising SMA150 over 5 sessions; RSI(2)<15 within 2 sessions; reclaim SMA10
- Exit: RSI(2)>95
- Full CAGR: 34.55% vs native 24.65%
- Full Sharpe: 1.02 vs native 0.89
- Full MaxDD: -47.37% vs native -47.37%
- OOS excess: +14.01%; stress-cost excess: +9.07%
- Promotion gate: **PASS**
- Current state: **native 1× SOXX**

## MAGS7 + TSM

- Actual-product overlap: 2024-10-03 to 2026-07-20 (448 sessions)
- Search: 1,296 candidates; 24 passed the strict training gate
- Selection mode: **strict**
- Entry: rising basket SMA150 over 10 sessions; MAGS and TSM each above SMA100; basket RSI(2)<15 within 5 sessions; reclaim basket SMA5
- Exit: basket RSI(2)>90
- Full CAGR: 34.02% vs native 29.95%
- Full Sharpe: 1.09 vs native 1.04
- Full MaxDD: -32.04% vs native -32.04%
- OOS excess: +5.52%; stress-cost excess: +1.84%
- Promotion gate: **PASS, experimental only** because the actual MAGX/TSMX overlap is only 448 sessions
- Current state: **native basket — 87.5% MAGS + 12.5% TSM**
