# Final Ground-Up Market-Bottom Monitor Research Report

**Date:** 2026-07-22  
**Status:** final rebuilt research report for the current evidence set  
**Scope:** SPY, QQQ and SOXX; SMH informational only; tactical mappings SPY→SSO, QQQ→QLD and SOXX→USD  
**Supersedes:** all earlier narrative reports, including the first `ground-up-market-bottom-report-2026-07-22.md` draft  
**Research branch:** `agent/market-bottom-strategy`

---

## 1. Final conclusion

The monitor should **not** be made more aggressive on the evidence currently available.

The validated interpretation is:

1. The existing price engine is a **staged drawdown-participation model**, not a reliably precise cycle-bottom detector.
2. It performs acceptably in shallow corrections but deteriorates sharply in deep bear markets.
3. The v1.1 recovery overlay does not improve bottom proximity. It adds trades without improving episode hit rates and slightly worsens weighted distance for SPY, QQQ and SOXX.
4. QQQ and especially SOXX can experience large, broad and technically convincing rebounds well before the final trough.
5. Equal-weight breadth, sector breadth, dispersion, financial stress, funding stress and volatility normalisation are useful context or veto variables, but none passed as a standalone bottom trigger.
6. SMH does not add stable incremental production value and remains informational with production weight zero.
7. Actual-product leveraged audits have now been completed. SSO and QLD map closely to their same-benchmark underlyings on daily returns, but no tactical rule is promoted. SOXX→USD is a cross-index proxy and displayed materially worse path risk.
8. The highest-value next test is a **deep-bear capital-reservation overlay**, not another rebound indicator.

### Production decision

- Retain bounded staged participation for ordinary corrections.
- Retain the v1.5 reporting taxonomy separating participation, local recovery and cycle-bottom evidence.
- Do not permit QQQ or SOXX v-shaped catch-up.
- Do not allow price recovery, breadth or stress normalisation alone to activate SSO, QLD or USD.
- Keep model-simulated deployment separate from actual confirmed execution.
- Create no order.

---

## 2. Retained, updated, corrected and new findings

### Retained findings

- Official signals use completed regular-session close `t`; conceptual execution is next regular-session open `t+1` plus configured costs.
- Complete drawdown episodes, including no-trade episodes, must be evaluated.
- Corporate actions, publication delays, unresolved episodes and point-in-time provenance controls remain mandatory.
- SPY, QQQ and SOXX are calculated independently.
- SMH is an informational semiconductor coordinate only and never receives a tranche.
- Simulated model deployment is not evidence that the user received or executed a trade.

### Updated findings

- The baseline engine is most useful as staged participation in ordinary corrections, not as a universal bottom-timing rule.
- Breadth, dispersion, funding stress and volatility structure may describe rebound quality or reduce confidence; they do not independently prove a final trough.
- Product-level leveraged paths are no longer untested: an actual adjusted-price mapping audit now exists, but all mappings remain blocked from production.

### Corrected findings

- The v1.1 recovery overlay does **not** improve bottom detection.
- Positive 42/63/84-session returns do not validate bottom proximity.
- The first v1.7 stress-normalisation output is invalid for promotion because breach age was reset repeatedly while price remained below the drawdown threshold. Only corrected v1.8 results are admissible.
- Fixed current-constituent stock panels are survivorship-biased discovery proxies.
- A local swing recovery is not equivalent to a cycle bottom.
- SOXX→USD is not a same-benchmark tracking relationship. USD targets a different semiconductor index.

### Newly added findings

- The principal model failure is concentrated in episodes whose final drawdown exceeds 25%.
- The model commits the most capital in the regime where its timing is least reliable.
- A common data-pipeline defect was identified and fixed: public providers may expose an unfinished current-session daily bar. The shared fetcher now removes the current exchange-local bar before a conservative 16:30 local cutoff.
- Actual-product audit results show materially different risk among SSO, QLD and USD; USD has the weakest mapping and the most adverse tactical path.
- The next research priority is deep-bear capital reservation followed by authorised point-in-time feature ablation.

---

## 3. Evidence hierarchy and causal controls

### Sources

1. IBKR for recent five-year boundaries, completed daily bars, corporate actions, fresh context and leveraged-product snapshots.
2. Immutable GitHub Actions artifacts for strategy calculations, trades, episodes, data audits and tests.
3. Official institutional and sponsor sources: OFR, Cboe, SIA/WSTS, index/ETF sponsors and ProShares.
4. Primary academic research for future feature hypotheses such as variance-risk premia—not as proof that a current proxy already works.

### Admissible backtest rules

- completed-close features only;
- next-open execution;
- transaction costs and slippage;
- no ex-post tranche normalisation;
- future prices used only for evaluation;
- publication-delayed series shifted to first strategy-available session;
- point-in-time membership/vintage gaps explicitly block production promotion;
- unfinished current-session daily bars excluded.

### Primary performance metrics

1. entry distance above eventual trough;
2. additional downside after entry;
3. missed-episode rate;
4. sessions before/after trough;
5. capital deployed near trough;
6. stability across regimes and independent episodes;
7. forward return as a secondary outcome only.

---

## 4. Baseline and v1.1 recovery overlay

### Full history

| Asset | History | Complete episodes | Baseline missed | Baseline weighted distance | Baseline additional downside | Within 5% | v1.1 weighted distance | v1.1 additional downside | Decision |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| SPY | 1993-01-29–2026-07-21 | 37 | 0.00% | 6.31% | -5.90% | 89.19% | 6.32% | -5.90% | No improvement |
| QQQ | 1999-03-10–2026-07-21 | 26 | 19.23% | 11.40% | -9.22% | 73.08% | 11.44% | -9.23% | Slightly worse |
| SOXX | 2001-07-13–2026-07-21 | 16 | 0.00% | 13.45% | -11.16% | 68.75% | 13.88% | -11.23% | Worse |

Trade counts increased without improving episode hit rates:

- SPY: 140→151;
- QQQ: 78→86;
- SOXX: 57→63.

**Decision:** do not describe v1.1 as an enhanced bottom detector.

### Recent five-year baseline: 2021-07-26–2026-07-21

| Asset | Complete episodes | Missed | First entry above trough | Additional downside | Mean timing | 63-session return |
|---|---:|---:|---:|---:|---:|---:|
| SPY | 7 | 0.00% | 6.58% | -5.22% | 30.3 sessions early | +7.74% |
| QQQ | 6 | 0.00% | 12.49% | -9.36% | 53.3 sessions early | +5.62% |
| SOXX | 6 | 0.00% | 18.96% | -11.30% | 61.7 sessions early | +24.58% |

Positive forward returns do not negate the materially early QQQ/SOXX entries.

---

## 5. Structural regime failure

### v1.1 results by eventual episode depth

| Asset | Final drawdown | Episodes | Mean deployment | Weighted distance | Additional downside | Any trade within 5% |
|---|---|---:|---:|---:|---:|---:|
| SPY | <15% | 30 | 19.17% | 2.05% | -1.91% | 100.00% |
| SPY | 15–25% | 4 | 56.50% | 13.28% | -16.15% | 50.00% |
| SPY | ≥25% | 3 | 60.00% | **39.77%** | **-32.12%** | 33.33% |
| QQQ | <15% | 19 | 8.82% | 2.60% | -2.06% | 73.68% |
| QQQ | 15–25% | 4 | 40.81% | 8.45% | -12.32% | 100.00% |
| QQQ | ≥25% | 3 | 48.33% | **56.71%** | **-38.57%** | 33.33% |
| SOXX | <15% | 6 | 6.67% | 2.30% | +0.22% | 83.33% |
| SOXX | 15–25% | 5 | 23.50% | 4.98% | -5.88% | 100.00% |
| SOXX | ≥25% | 5 | 57.50% | **36.67%** | **-30.34%** | 20.00% |

### Interpretation

- Shallow-correction participation is the strongest retained use case.
- A single deployment curve is not robust across structural bears.
- The current long-bear cap arrives too late to reverse capital already committed earlier in the episode.

### Next hypothesis—not production

`DEEP_BEAR_CAPITAL_RESERVATION` should test:

- small ordinary-correction probe retained;
- incremental deployment frozen after falling-200DMA/deep-regime evidence;
- a fixed reserve held back;
- reserve released only after independent point-in-time evidence improves;
- evaluation on identical episodes and actual SSO/QLD/USD paths.

---

## 6. Later price confirmation

### QQQ

| Candidate | Missed | Distance | Additional downside | 63-session return | Decision |
|---|---:|---:|---:|---:|---|
| Regime exhaustion reclaim | 66.67% | 22.38% | -15.88% | -7.39% | Reject |
| Regime retest confirmation | 66.67% | 11.70% | -8.00% | +23.23% | Research watch; only two recent episodes |
| Regime strong confirmation | 66.67% | 22.81% | -16.26% | -5.55% | Reject |
| Regime dual path | 33.33% | 18.47% | -9.52% | +6.13% | Reject |

### SOXX

| Candidate | Missed | Distance | Additional downside | 63-session return | Decision |
|---|---:|---:|---:|---:|---|
| Regime exhaustion reclaim | 66.67% | 41.72% | -15.26% | +0.22% | Reject |
| Regime retest confirmation | 83.33% | 45.05% | -31.06% | -11.24% | Reject |
| Regime strong confirmation | 50.00% | 32.94% | -20.16% | -8.07% | Reject |
| Regime dual path | 66.67% | 38.12% | -13.64% | +2.97% | Reject |

SOXX moving-average or rebound confirmation remains unsafe.

---

## 7. Independent indicator families

### Equal-weight breadth and credit appetite

Verified proxies:

- RSP/SPY;
- QQQE/QQQ;
- XSD/SOXX;
- HYG/IEF.

They measure concentration and broad participation, not historical point-in-time constituent breadth.

| Candidate | Recent signals | Distance | Additional downside | 63-session return | Decision |
|---|---:|---:|---:|---:|---|
| QQQ breadth + credit | 1/6 episodes | 7.11% | -6.64% | +8.11% | Too sparse |
| SOXX equal-weight breadth | 2/6 episodes | 52.28% | -34.28% | -14.68% | Reject |
| SOXX multi-factor proxy | 2/6 episodes | 43.50% | -30.25% | -9.20% | Reject |

### Financial, funding and volatility stress

Corrected v1.8 results:

| Asset/candidate | Missed | Distance | Additional downside | 63-session return | Decision |
|---|---:|---:|---:|---:|---|
| SPY mature FSI | 71.43% | 19.30% | -16.03% | -3.18% | Reject |
| QQQ mature FSI | 50.00% | 22.39% | -10.59% | -0.24% | Reject |
| QQQ funding/composite | 66.67% | 24.53% | -17.18% | -7.65% | Reject |
| SOXX mature FSI | 66.67% | 52.27% | -34.27% | -16.07% | Reject |
| SOXX funding/composite | 83.33% | 50.32% | -33.48% | -8.36% | Reject |

Systemic stress may peak before the final equity or semiconductor trough.

### Cross-sectional internals

| Asset/candidate | Missed | Distance | Additional downside | 63-session return | Decision |
|---|---:|---:|---:|---:|---|
| QQQ breadth/dispersion | 83.33% | 9.33% | -5.60% | +4.62% | One recent episode; insufficient |
| SOXX breadth thrust | 66.67% | 52.27% | -34.27% | -16.07% | Reject |
| SOXX dispersion normalisation | 83.33% | 47.99% | -32.43% | -8.11% | Reject |

A broad semiconductor rebound can occur during the middle of a longer sector decline.

---

## 8. SMH/SOXX paired evidence

- SOXX remained the only executable semiconductor target.
- State-4 confirmation-only rules were effectively identical to SOXX-only.
- Soft confirmation worsened results.
- A negligible full-history improvement from broad veto/hard-confirm rules did not persist post-2024.

**Decision:** SMH remains a displayed informational coordinate and divergence warning only.

---

## 9. Options, correlation and fundamental-cycle gaps

### Available context

- VIX-family term structure, VVIX and SKEW;
- OFR FSI and funding series with conservative publication delays;
- public SIA/WSTS release summaries;
- ETF/equal-weight proxies.

### Not production-ready

- authorised long-history COR1M/COR3M and DSPX/VIXEQ data;
- bulk reproducible put/call history;
- model-free downside implied variance paired with intraday realised downside variance;
- historical point-in-time semiconductor membership;
- point-in-time revenue/EPS revision breadth;
- detailed WSTS category shipments, inventory, lead-time and order-cycle histories aligned to release dates.

An `IV minus daily HV` calculation is not an equivalent substitute for genuine downside variance-risk premium.

---

## 10. Actual-product leveraged audit v2.0

All tactical P&L calculations use actual adjusted leveraged-product prices. A theoretical 2x path is diagnostic only.

| Mapping | Benchmark relationship | Daily correlation | Daily beta | Gap RMSE | Trades | Win rate | Mean return | Median return | Worst trade | Worst MAE | Promotion |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| SPY→SSO | Same benchmark family | 0.9956 | 1.9592 | 0.23% | 16 | 56.25% | +2.19% | +2.02% | -4.77% | -5.65% | Blocked |
| QQQ→QLD | Same benchmark family | 0.9960 | 1.9832 | 0.25% | 17 | 58.82% | +3.44% | +0.31% | -5.16% | -8.60% | Blocked |
| SOXX→USD | **Cross-index proxy** | 0.9584 | 1.9120 | **1.15%** | 31 | 48.39% | +1.38% | **-1.19%** | **-23.24%** | **-28.63%** | Blocked |

### Critical interpretation

- SSO and QLD are same-benchmark-family products, but fees, financing, daily reset and tracking still matter.
- USD targets the Dow Jones U.S. Semiconductors Index while SOXX tracks the NYSE Semiconductor Index.
- The SOXX/USD gap is a combination of benchmark mismatch and product path; it is not valid to label the entire gap as USD tracking error.
- All products have daily objectives and multi-day path dependency.
- The tested tactical rule itself has not passed formal promotion gates.

### Leveraged decision

All mappings remain blocked by an unpromoted tactical rule and daily-reset path dependency. USD has the additional benchmark-mismatch blocker.

---

## 11. Current IBKR context

Snapshot around **2026-07-22 23:16–23:17 HKT / 11:16–11:17 ET**. Entitlement may make fields live or delayed; the latest completed RTH daily bar was 2026-07-21.

| Asset | Last | 52-week-high drawdown | Historical vol | Underlying IV | 52-week IV percentile |
|---|---:|---:|---:|---:|---:|
| SPY | 748.87 | -1.52% | 16.89% | 13.38% | 39.84% |
| QQQ | 708.87 | -5.31% | 29.27% | 23.75% | 84.06% |
| SOXX | 559.52 | -14.70% | 74.94% | 62.96% | 96.02% |
| SMH | 590.52 | -12.10% | 63.34% | 55.15% | 92.43% |
| SSO | 67.52 | -3.71% | 31.95% | 25.54% | 33.47% |
| QLD | 89.20 | -11.85% | 58.54% | 47.05% | 85.26% |
| USD | 93.51 | -19.73% | 114.30% | 106.68% | 97.21% |

This is context, not a causal entry signal. High IV percentile alone is not exhaustion.

---

## 12. Production specification

### Retain

- completed-RTH-close official state;
- small staged participation;
- independent SPY, QQQ and SOXX calculations;
- SMH informational only;
- participation/local-swing/cycle-bottom taxonomy;
- separate model deployment, actual execution and current action;
- leverage veto until independently promoted.

### Do not promote

- v1.1 overlay as a bottom improvement;
- QQQ/SOXX v-shaped catch-up;
- simple MA reclaim;
- equal-weight breadth reversal;
- semiconductor breadth thrust;
- FSI/repo normalisation;
- high IV percentile;
- one put/call extreme;
- current-survivor panels;
- any present leveraged mapping.

### Report as context only

- breadth and concentration;
- sector-internal breadth/dispersion;
- volatility-stack normalisation;
- financial/funding stress;
- SMH/SOXX divergence;
- ordinary correction versus transition versus structural bear.

---

## 13. Prioritised roadmap

1. **Deep-bear capital reservation** on identical episodes and actual products.
2. Historical point-in-time semiconductor membership and breadth.
3. Authorised Cboe correlation/dispersion histories.
4. Genuine model-free downside variance-risk premium.
5. Point-in-time semiconductor revenue/EPS revisions.
6. Authorised bulk options-flow history.
7. WSTS/SIA category shipments, inventory and order-cycle data.
8. Revalidate SSO/QLD/USD only after the underlying entry rule survives.

---

## 14. Confidence

| Finding | Confidence |
|---|---|
| v1.1 does not improve aggregate bottom proximity | High |
| Baseline is staged participation, not precise bottom detection | High |
| Deep drawdowns are the principal failure regime | High |
| Breadth and stress normalisation are not standalone trough triggers | High |
| SMH has no stable incremental production value | Medium-high |
| QQQ retest may contain useful information | Low-medium; too few episodes |
| Actual SSO/QLD/USD mappings are currently promotable | No |
| Deep-bear capital reservation will improve results | Research hypothesis |

---

## 15. Reproducible evidence register

- `market-bottom-recovery-v11-validation-29904424650`
- `market-bottom-late-stage-v14-29892427629`
- `market-bottom-orthogonal-v16-29901410362`
- `market-bottom-stress-maturity-v18-29903164618`
- `market-bottom-sector-internal-v19-29904163231`
- `market-bottom-leverage-mapping-v20-29933935491`
- IBKR five-year RTH histories, corporate actions and 2026-07-22 snapshots
- repository modules and tests under `research/market-bottom/`

Official methodologies and data definitions were checked against OFR, Cboe, Invesco, Direxion, State Street, iShares, ProShares, SEC, SIA and WSTS primary sources.

---

## Final decision

The rebuilt evidence supports a more honest and regime-aware monitor, not a more aggressive one:

- ordinary correction → bounded staged participation;
- local recovery → describe it, do not call it a cycle bottom;
- structural bear → reserve capital and demand independent evidence;
- leverage → blocked until both the underlying rule and actual product path pass.

No order is created or transmitted.
