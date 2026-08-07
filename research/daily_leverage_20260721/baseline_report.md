# Daily Leveraged-ETF Entry/Exit Backtest

**As of:** 2026-07-21  
**Universe:** SPY, SOXX, MAGS7 + TSM  
**Objective:** use daily signals to decide when to raise exposure above the native 1× asset. Each asset was searched independently.

## Common controls

- Signal uses completed regular-session close data only.
- SPY and SOXX changes execute at the next regular-session open.
- MAGS7 + TSM uses a one-session delay because live common history is short and early MAGS liquidity was thin.
- Off-state remains invested in the native 1× asset; this is not a cash-timing strategy.
- Base assumptions: 4% financing above 1×, about 0.95%–1.00% product drag and 10 bps per exposure change.
- Stress assumptions: 7% financing, 1.20%–1.50% product drag and 20–25 bps per exposure change.
- No same-close execution or future data.

---

## SPY daily model

### Rule

Raise to 2× when all conditions are met:

1. SPY closes above SMA200.
2. SMA200 is above its level 20 sessions earlier.
3. RSI(2) fell below 20 during the prior 10 sessions.
4. SPY subsequently crosses back above SMA10.
5. Switch at the next regular-session open.

Exit to 1× SPY when RSI(2) exceeds 90, at the next regular-session open.

**Implementation:** 100% SSO, or equivalent effective 2× exposure. UPRO should only be a smaller sleeve if total effective exposure remains 2× or below.

### Validation

- Price sample: 2016-07-07 to 2026-07-06.
- Train: 2017-05-01 to 2021-10-29.
- OOS: 2021-11-01 to 2026-07-06.
- 7,650 daily specifications screened.

| Period | SPY B&H CAGR | Strategy CAGR | SPY Sharpe | Strategy Sharpe | SPY MaxDD | Strategy MaxDD |
|---|---:|---:|---:|---:|---:|---:|
| Train | 15.73% | **22.27%** | 0.91 | **1.06** | -32.45% | -32.45% |
| OOS | 10.99% | **13.81%** | 0.68 | **0.71** | -27.13% | **-26.52%** |
| Full | 13.28% | **17.87%** | 0.79 | **0.88** | -32.45% | -32.45% |

- Stress-cost CAGR: **15.10%**, versus SPY 13.28%.
- Rolling 3-year CAGR beat rate: **100%**; worst annualised excess +0.77 percentage points.
- Rolling 5-year CAGR beat rate: **100%**; worst annualised excess +2.85 percentage points.
- Average effective exposure: 1.23×.

### State at 2026-07-20

- Close 742.09; SMA10 749.17; SMA200 697.08 and rising; RSI(2) 9.53.
- Existing 2× position remains active.
- No fresh add until a new close reclaims SMA10.

---

## SOXX daily model

### Rule

Raise to 2× when:

1. SOXX closes above SMA200.
2. SMA200 is above its level 10 sessions earlier.
3. RSI(2) fell below 10 during the prior three sessions.
4. SOXX crosses back above SMA20.
5. Switch at the next regular-session open.

Exit to 1× SOXX when RSI(2) exceeds 90 **or** SOXX closes below SMA50.

This is a semiconductor-specific oversold-reclaim rule and is not the SPY/QQQ rule.

### Validation

- IBKR sample: 1,000 sessions, 2022-07-25 to 2026-07-20.
- Train: 2023-07-26 to 2025-05-07.
- OOS: 2025-05-08 to 2026-07-20.
- 21,852 SOXX-specific specifications screened.

| Period | SOXX B&H CAGR | Strategy CAGR | SOXX Sharpe | Strategy Sharpe | SOXX MaxDD | Strategy MaxDD |
|---|---:|---:|---:|---:|---:|---:|
| Train | 6.91% | **17.30%** | 0.37 | **0.62** | -42.99% | -42.99% |
| OOS | 135.47% | **165.95%** | 2.34 | **2.43** | -22.18% | -22.18% |
| Full | 46.74% | **62.88%** | 1.21 | **1.42** | -42.99% | -42.99% |

- Stress-cost CAGR: **61.32%**, versus SOXX 46.74%.
- Rolling 6-month beat rate 68.3%; 1-year 86.2%; 2-year and 3-year 100% in the available sample.
- The four-year sample and unusually strong OOS semiconductor regime materially reduce confidence.

### State at 2026-07-20

- Close 524.14; SMA20 580.38; SMA50 566.72; SMA200 392.25 and rising.
- RSI(2) 20.82; prior-three-session minimum 7.81.
- State: **1× SOXX** because SMA20/SMA50 reclaim has not occurred.

---

## MAGS7 + TSM daily model

### Tradable native basket

- 87.5% MAGS
- 12.5% TSM

This approximates eight equal 12.5% sleeves: the seven MAGS constituents plus TSM, without back-casting current winners before MAGS existed.

### Rule

Raise to 1.5× when:

1. Native basket is above SMA200.
2. SMA200 is above its level 20 sessions earlier.
3. MAGS and TSM are each above their own SMA100.
4. Basket RSI(2) fell below 5 during the prior 10 sessions.
5. Basket subsequently crosses above SMA15.
6. Exposure rises one session later.

Exit to 1× when basket RSI(2) exceeds 95 or basket closes below SMA50.

A possible 1.5× implementation is 43.75% MAGS, 6.25% TSM, 43.75% MAGX and 6.25% TSMX.

### Validation

- Common IBKR sample: 2023-04-12 to 2026-07-20, 820 sessions.
- Train ends 2024-12-31; OOS begins 2025-01-02.

| Period | Native B&H CAGR | Strategy CAGR | Native Sharpe | Strategy Sharpe | Native MaxDD | Strategy MaxDD |
|---|---:|---:|---:|---:|---:|---:|
| Train | 64.36% | **70.64%** | 2.03 | **2.13** | -18.51% | -18.51% |
| OOS | 19.95% | **22.20%** | 0.78 | **0.84** | -29.43% | -29.43% |
| Full | 35.09% | **38.61%** | 1.23 | **1.31** | -30.28% | -30.28% |

- Stress-cost CAGR: **37.90%**, versus native 35.09%.
- Rolling 6-month beat rate 75.3%; 1-year 97.4%; 2-year 100% in this short sample.
- Average exposure only 1.02×; the qualifying entry is intentionally rare.

### State at 2026-07-20

- MAGS 66.93 above SMA100 64.66.
- TSM 402.30 above SMA100 393.69.
- Basket remains above a rising SMA200 but below SMA15 and SMA50.
- RSI(2) 25.41; prior-ten-session minimum 18.87.
- State: **1× native basket; no MAGX/TSMX leverage**.

---

## Operating table

| Asset | Raise leverage only when | Exit leverage when | 2026-07-20 state |
|---|---|---|---|
| SPY | Rising SMA200 + RSI(2)<20 in 10 days + reclaim SMA10 | RSI(2)>90 | Existing 2× may remain; no fresh add |
| SOXX | Rising SMA200 + RSI(2)<10 in 3 days + reclaim SMA20 | RSI(2)>90 or close<SMA50 | 1× SOXX |
| MAGS7+TSM | Rising SMA200 + both components>SMA100 + RSI(2)<5 in 10 days + reclaim SMA15 | RSI(2)>95 or basket<SMA50 | 1× native basket |

## Audit limitations

1. Historical outperformance is not a guarantee of future outperformance.
2. Baseline SPY/SOXX leverage results use cost-adjusted effective exposure rather than exact reconciliation to every daily SSO/USD NAV observation.
3. SOXX contains only about four years of daily IBKR data in this audit.
4. MAGS7 + TSM has only a little over three years of live common history.
5. Daily-reset products can diverge materially from a simple multiple because of compounding, volatility and financing paths.
