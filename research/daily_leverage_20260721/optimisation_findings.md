# Optimisation findings and promotion decision

**Successful CI run:** Daily leverage optimisation, run 4  
**Market-data end date:** 2026-07-20  
**Execution:** completed close signal, next regular-session open  
**Product validation:** actual SSO, USD, MAGX and TSMX histories over their common live overlaps

## Decision summary

| Asset | Strict train gate | OOS promotion gate | Decision | Current implementation |
|---|---:|---:|---|---|
| SPY | 0 / 1,944 | Fail | Reject the daily 2× rule | 1× SPY |
| SOXX | 1,790 / 11,520 | Pass | Promote the new SOXX/USD rule | 1× SOXX pending trigger |
| MAGS7 + TSM | 24 / 1,296 | Pass | Experimental only | 87.5% MAGS + 12.5% TSM |

## 1. SPY — prior daily leverage conclusion is not confirmed

The best diagnostic fallback was:

- SPY above SMA200, with SMA200 rising over 10 sessions.
- RSI(2) below 15 during the prior five sessions.
- Entry after a reclaim of SMA20.
- Exit when RSI(2) exceeds 90.

It increased full-sample CAGR from 14.14% to 15.58%, but it failed the risk and cost controls:

- Full Sharpe fell from 0.885 to 0.809.
- Full MaxDD worsened from -32.05% to -32.45%.
- Train Sharpe delta was -0.151.
- Stress-cost excess CAGR was -0.35 percentage points.
- Rolling three-year CAGR beat rate was 70.4%, but Sharpe beat rate was only 35.8% and drawdown beat rate only 31.5%.
- No candidate passed all strict training requirements.

**Promotion decision:** fail. The diagnostic model's internal state happened to be levered on the last observation, but this is not actionable. The formal state is 1× SPY.

## 2. SOXX — promoted actual USD rule

### Rule

At the completed SOXX close:

1. SOXX is above SMA150.
2. SMA150 is above its level five sessions earlier.
3. RSI(2) was below 15 during either of the prior two sessions.
4. SOXX crosses back above SMA10.
5. At the following regular-session open, switch from SOXX to USD, the actual 2× semiconductor ETF.
6. Switch back to SOXX at the following open after RSI(2) exceeds 95.

No moving-average exit was retained by the winner.

### Validation

- Actual-product overlap: 2010-01-04 to 2026-07-20, 4,160 sessions.
- Train/OOS split: 2018-01-01.
- Parameter combinations: 11,520.
- Strict train passes: 1,790.
- Exposure changes: 68.
- Average effective exposure: 1.124×.

| Metric | Native SOXX | Strategy | Delta |
|---|---:|---:|---:|
| Full CAGR | 24.65% | 34.55% | +9.90 pp |
| Full Sharpe | 0.890 | 1.017 | +0.127 |
| Full MaxDD | -47.37% | -47.37% | neutral |
| OOS CAGR | 31.22% | 45.23% | +14.01 pp |
| Stress-cost full CAGR excess | — | +9.07 pp | positive |

Robustness evidence:

- 15 immediate parameter neighbours.
- Worst neighbouring train excess CAGR: +0.34 percentage points.
- Median neighbouring train excess CAGR: +4.20 percentage points.
- Rolling two-year CAGR beat rate: 98.85%; worst two-year alpha -0.71 percentage points.
- Rolling three-year CAGR beat rate: 100%; worst three-year alpha +1.85 percentage points.

**Promotion decision:** pass. The last state is native, so no USD position is indicated until a fresh trigger completes.

## 3. MAGS7 + TSM — passes numerically, remains experimental

### Tradable construction

- Native state: 87.5% MAGS + 12.5% TSM.
- 1.5× state: 50% native basket plus 50% of 87.5% MAGX + 12.5% TSMX.

### Rule

1. The native basket is above SMA150.
2. Basket SMA150 is above its level 10 sessions earlier.
3. MAGS and TSM are each above their own SMA100.
4. Basket RSI(2) was below 15 during the prior five sessions.
5. Basket crosses back above SMA5.
6. Raise exposure to 1.5× at the following regular-session open.
7. Return to the native basket after basket RSI(2) exceeds 90.

### Validation

- Actual-product overlap: 2024-10-03 to 2026-07-20, only 448 sessions.
- Train/OOS split: 2025-07-01.
- Parameter combinations: 1,296.
- Strict train passes: 24.
- Exposure changes: 20.
- Average effective exposure: 1.078×.

| Metric | Native basket | Strategy | Delta |
|---|---:|---:|---:|
| Full CAGR | 29.95% | 34.02% | +4.07 pp |
| Full Sharpe | 1.038 | 1.088 | +0.050 |
| Full MaxDD | -32.04% | -32.04% | neutral |
| OOS CAGR | 30.71% | 36.23% | +5.52 pp |
| Stress-cost full CAGR excess | — | +1.84 pp | positive |

The model passed the formal gate, but only nine rolling one-year windows were available. It has not experienced enough independent market regimes to justify production confidence.

**Promotion decision:** experimental only. Current state remains the native basket.

## Audit policy

- A higher CAGR alone is insufficient for promotion.
- A diagnostic fallback cannot be traded merely because its latest state says `levered`.
- Full parameter grids remain in the successful GitHub Actions artifact; the repository stores the reproducible optimiser and the promoted conclusions.
- Historical results do not guarantee future returns.
