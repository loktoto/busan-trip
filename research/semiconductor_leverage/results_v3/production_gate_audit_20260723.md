# Production-gate audit — Semiconductor Leverage V3

**Audit date:** 2026-07-23  
**Candidate:** `SMH -> PB_RSI5_R10_H40 -> USD/SOXL`  
**Verdict:** `HIGH_PRIORITY_CHALLENGER_NOT_PRODUCTION`  
**Production decision:** retain the standalone SOXX annual-anchored trend-vol rule pinned by `main:production/leverage_signal.json`.

## Executive conclusion

The SMH RSI2 pullback-reclaim idea is economically interesting and produced very strong results in the latest semiconductor regime. It is not eligible for production because the published V3 ranking selected parameters on the full sample and then evaluated the same selected parameters in overlapping rolling windows. The result has no genuinely untouched chronological holdout, no formal SOXX Buy & Hold gate, no corrected DSR, no CSCV/PBO, and weak neighbouring-parameter stability.

This audit does **not** claim the signal is false. It classifies the signal as a high-priority challenger that needs a smaller pre-registered family, frozen historical selection and forward paper-live evidence.

## Code-level audit

The V3 engine:

1. builds hundreds of pullback, trend, volatility, MHT and hybrid variants;
2. ranks them using 3Y, 5Y, 10Y and MAX windows that all end at the latest sample date;
3. selects the top ten using those full-sample outcomes; and
4. computes rolling summaries only after that full-sample selection.

Consequences:

- the rolling windows are diagnostics, not out-of-sample evidence;
- all windows overlap heavily;
- the published ranking uses absolute strategy results without a formal same-period SOXX Buy & Hold promotion gate;
- the selected candidate has only a small number of independent trades in several subperiods;
- the trailing-stop implementation can turn a position back on during the same fixed holding window after a stop condition clears, so it is not a permanently latched trade exit;
- the workflow runs at the audited head returned `action_required` and no completed jobs, so the persisted local results are not independently reproduced CI evidence.

## Independent completed-close audit

Two checks were run:

- an IBKR exact-contract five-year recomputation through the completed 2026-07-22 RTH bar; and
- a full-history recomputation from the persisted adjusted SMH, SOXX, USD and SOXL input files in this branch.

Execution matches the V3 convention: completed-close signal, next-open position, actual adjusted leveraged-product prices, 10 bps per position change, and no synthetic daily-multiple series.

### Exact V3 candidate versus SOXX Buy & Hold

#### USD route

| Period | Candidate CAGR delta | Sharpe delta | MaxDD improvement | Interpretation |
|---|---:|---:|---:|---|
| 2013–2015 | **-16.65pp** | **-0.757** | **-9.54pp** | failed return, Sharpe and drawdown |
| 2016–2020 | **-13.05pp** | **-0.251** | +10.82pp | defensive but materially lagged return |
| 2024–2026-07-20 | +139.95pp | +1.674 | +23.00pp | exceptional recent-regime result |
| 2013–2026-07-20 | +11.60pp | +0.353 | +10.98pp | attractive aggregate, but selected with future knowledge |

The aggregate USD result used about 29.4% average product position and approximately 24.5 round trips. The edge is strongly concentrated after 2024.

#### SOXL route

| Period | Candidate CAGR delta | Sharpe delta | MaxDD improvement | Interpretation |
|---|---:|---:|---:|---|
| 2016–2020 | +5.93pp | **-0.078** | **-2.49pp** | failed Sharpe and drawdown guardrails |
| 2021–2023 | +21.08pp | +0.377 | +11.47pp | passed diagnostic comparison |
| 2024–2026-07-20 | +242.41pp | +1.313 | +15.67pp | exceptional recent-regime result |
| 2016–2026-07-20 | +46.02pp | +0.503 | +9.71pp | attractive aggregate, but selected with future knowledge |

The aggregate SOXL result used about 28.7% average product position and approximately 19 round trips.

## Frozen pre-period selection test

The same 80-member no-trailing-stop pullback neighbourhood was ranked using only information available before the stated development cutoff.

| Route | Development cutoff | Full-sample V3 winner rank using only development data | Frozen development winner |
|---|---|---:|---|
| USD | 2012-12-31 | 6 / 80 | `PB_RSI5_R5_H50` |
| SOXL | 2015-12-31 | 13 / 80 | `PB_RSI5_R10_H50` |

The exact V3 `H40` rule therefore was not the rule that would have been selected without later data.

The frozen winners also failed a complete production gate:

- USD frozen winner, 2013–2026: CAGR +7.51pp versus SOXX, but Sharpe -0.026 and MaxDD **8.06pp worse**.
- SOXL frozen winner, 2016–2026: CAGR +41.76pp and Sharpe +0.333, but MaxDD **10.78pp worse**.

## Neighbour stability

Across the 80 pre-specified RSI-low / reclaim-MA / hold-day neighbours over their route-specific OOS periods:

| Route | Positive CAGR | Positive CAGR + Sharpe | Positive CAGR + Sharpe + MaxDD | All-three rate |
|---|---:|---:|---:|---:|
| USD | 24 / 80 | 10 / 80 | **4 / 80** | **5.0%** |
| SOXL | 46 / 80 | 23 / 80 | **7 / 80** | **8.75%** |

That is insufficient local stability for promotion.

## Five-year IBKR diagnostic

The exact rule remained very strong in the recent IBKR window, including the later validation-like segments. This confirms the result is not a simple stale-price or split error. It does **not** create untouched evidence because the candidate was originally selected using those same recent years.

## Promotion decision

`REJECT_FOR_NOW`.

Reasons:

1. full-sample parameter selection leakage;
2. no untouched or legitimately frozen selection/holdout result for the exact H40 rule;
3. strong recent-regime concentration and poor 2013–2020 USD relative returns;
4. weak neighbouring-parameter pass rate;
5. sparse independent trades;
6. no corrected DSR or PBO gate;
7. workflow not independently completed at the audited head.

## Required next research

- reduce the pullback family before observing a new holdout;
- pre-register signal source, RSI threshold, reclaim length, hold/exit logic and product route;
- use a latched stateful stop rather than a reversible within-window stop mask;
- select only on a development period and freeze parameters before the next chronological validation period;
- compare every segment with SOXX Buy & Hold and the current production trend-vol rule;
- add actual-product base/2x/3x cost stress, moving-block bootstrap, corrected DSR and CSCV/PBO;
- require materially higher neighbouring-parameter stability;
- keep a forward paper-live ledger before any production replacement.

No order or order instruction was created.
