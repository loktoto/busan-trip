# Rebuilt Market-Bottom Monitor Research Report v3.0

**Report date:** 2026-07-23  
**Research evidence cut-off:** 2026-07-23  
**Latest completed U.S. regular-session boundary:** 2026-07-22  
**Primary assets:** SPY, QQQ, SOXX  
**Reference asset:** SMH, informational only  
**Tactical products audited:** SSO, QLD, USD  
**Evidence branch:** `agent/market-bottom-strategy`  
**Validated evidence head before this report:** `493d0d6526c0fbc5c4de8def7fb1a931c36d4e24`  
**Repository visibility at audit time:** public  
**Companion audit:** `rebuild-audit-v30-2026-07-23.json`

---

## 1. Executive conclusion

This report was rebuilt from the current code, current successful GitHub Actions runs, fresh Interactive Brokers market boundaries, actual leveraged-product histories and current official source documentation. Earlier reports were used only as a claim inventory; no earlier number or conclusion was retained without rechecking its origin and interpretation.

The most defensible conclusion is:

> **The current monitor is a bounded staged-drawdown participation system with a useful recovery taxonomy. It is not a validated precise final-cycle-bottom detector for QQQ or SOXX.**

The production decision remains conservative, but the reason is now more specific:

1. The engine works best in ordinary corrections with final drawdowns below 15%.
2. Its principal failure occurs in structural bear episodes with final drawdowns of at least 25%.
3. In those deep episodes, the current deployment curve commits the most capital while bottom timing is least reliable.
4. The v1.1 recovery overlay adds trades but does not improve episode hit rates or bottom proximity.
5. Price recovery, moving-average reclaim, equal-weight breadth, fixed-panel breadth, dispersion normalisation, financial stress, funding stress and volatility normalisation can all occur during an intermediate bear-market rally.
6. No tested QQQ or SOXX catch-up or late-stage confirmation rule passed production gates.
7. SMH did not add persistent incremental value to SOXX and remains informational with production weight zero.
8. SSO and QLD are same-benchmark-family 2x daily products, but the tactical entry rule remains unpromoted. USD is additionally a cross-index proxy for SOXX and exhibited materially worse tactical tail risk.
9. The next high-value improvement is not another rebound indicator. It is a **deep-bear capital-reservation overlay**, followed by point-in-time semiconductor-cycle, genuine variance-risk-premium and authorised correlation/dispersion evidence.

### Production action

- Retain small, bounded v1.1 staged participation.
- Retain v1.5 reporting separation among participation, local recovery and cycle-bottom evidence.
- Do not add a new QQQ or SOXX catch-up tranche.
- Do not add a late-stage SOXX confirmation tranche.
- Do not activate SSO, QLD or USD from the present research.
- Keep simulated deployment, actual confirmed execution and current action separate.
- Do not treat the stale runtime result dated 2026-07-21 as the latest official state.
- Create or transmit no order.

---

## 2. Retained, updated, corrected and newly added findings

### 2.1 Retained findings

- Signals use completed regular-session information at close `t`; conceptual execution is next regular-session open `t+1` plus stored costs.
- Every complete drawdown episode, including missed and no-trade episodes, remains in the evaluation denominator.
- SPY, QQQ and SOXX are calculated independently.
- SMH is an informational semiconductor coordinate only and never receives a tranche.
- Positive forward return is secondary to bottom proximity, additional downside and missed-episode rate.
- Participation, local swing recovery and cycle-bottom confirmation remain separate questions.
- Model-simulated deployment is not evidence that the user received or executed a tranche.
- Point-in-time constituent membership, publication lag and revision provenance are mandatory for production feature promotion.

### 2.2 Updated findings

- All major research workflows at evidence head `493d0d...` completed successfully, including baseline/recovery, late-stage, orthogonal proxies, stress maturity, sector internals and actual-product leverage mapping.
- The latest completed IBKR RTH boundary advanced from 2026-07-21 to **2026-07-22**.
- On 2026-07-22, SOXX and SMH extended their rebound, while QQQ closed below its 2026-07-21 close. Semiconductor rebound and broad technology confirmation therefore remained non-identical observations.
- Current delayed 2026-07-23 context continued to show historical volatility above underlying implied volatility for SPY, QQQ, SOXX, SMH, SSO, QLD and USD.
- Official 2026 semiconductor data show exceptionally strong aggregate sales and equipment investment, but those series are smoothed, lagged and heterogeneous. They do not provide a daily final-trough signal.

### 2.3 Corrected findings

- **The monitor is not a close-to-bottom detector in all regimes.** It is primarily a staged participation engine.
- **The v1.1 recovery overlay is not an enhancement to bottom detection.** It increases trade count while weighted distance is flat to worse.
- **Deep-bear episodes are the principal failure regime.** Aggregate averages previously concealed the concentration of error in final drawdowns of at least 25%.
- **The current long-bear cap arrives too late.** Substantial capital may already have been committed before the cap becomes active.
- **The latest provider daily row cannot automatically be treated as complete.** Public providers can expose an unfinished exchange-local current-session bar.
- **The current runtime JSON is stale.** It remains dated 2026-07-21 and is not an official 2026-07-22 calculation.
- **The repository remains public.** Raw licensed IBKR history, account data, positions, credentials or personally identifiable information must not be committed.
- **OFR current histories are not immutable vintage histories.** The OFR FSI publishes with a two-business-day lag and has documented corrections; preliminary repo data can also be revised.
- **Current-member stock panels are not historical point-in-time breadth.** QQQ and SOXX panels remain survivorship-biased discovery proxies.
- **SOXX→USD is not a same-index tracking relationship.** SOXX tracks the NYSE Semiconductor Index; USD targets 2x the daily Dow Jones U.S. Semiconductors Index.
- **A theoretical 2x SOXX path minus USD is not pure product tracking error.** It combines benchmark mismatch, implementation, financing, fees, market-price effects and daily-reset path.
- **Monthly North American semiconductor equipment book-to-bill is not a currently published public series.** SEMI discontinued the monthly book-to-bill report in 2017; current research should use authorised billings, WWSEMS, company orders/backlogs and point-in-time revisions instead.
- **Underlying IV minus daily historical volatility is not a genuine variance-risk premium.** A defensible VRP feature requires model-free option-strip implied variance and high-frequency realised variance.

### 2.4 Newly added insights

- The model commits approximately 48%–60% in the deepest historical regimes while weighted entry distance reaches approximately 37%–57% above the final trough. Capital reservation is therefore more important than adding another recovery vote.
- Current official semiconductor fundamentals are strong enough that broad financial-stress normalisation is even less likely to identify the final SOXX trough. Aggregate industry strength can coexist with violent ETF drawdowns and subsector dispersion.
- May 2026 global semiconductor sales were reported at $120.6 billion, a three-month moving average, and Q1 2026 global equipment billings reached $36.55 billion. These are valuable cycle context but are too lagged and smoothed for daily entry timing.
- WSTS's Spring 2026 forecast is heavily driven by memory and AI infrastructure. A sector-level aggregate therefore risks masking differences among memory, logic, analogue, equipment and communications names.
- Cboe VIX, VVIX and VIX9D histories are publicly reproducible; COR1M/COR3M and DSPX are methodologically relevant, but robust historical access and redistribution require an authorised data path.
- The current PR has become a large research branch rather than a narrow production patch. Mergeability was unresolved at the latest check and must be reviewed separately from research validity.

---

## 3. Evidence hierarchy and validation controls

### 3.1 Source hierarchy

1. **Interactive Brokers:** latest completed RTH bars, current delayed context and corporate-action boundaries.
2. **Deterministic GitHub Actions:** code, tests, data audits, episode tables, trades and numerical summaries.
3. **Official primary sources:** ETF sponsors, OFR, Cboe, Federal Reserve research, SIA, WSTS and SEMI.
4. **Audited public adjusted OHLCV:** long-history reproducibility in the public repository.
5. **Research proxies:** explicitly blocked from production where point-in-time membership, immutable vintages, authorised bulk history or correct methodology is missing.

### 3.2 Successful current-branch workflows

At evidence head `493d0d...`, the following were successful:

| Workflow | Run ID | Status |
|---|---:|---|
| Core Market Bottom Research | `29934777840` | Success |
| Recovery v1.1 / catch-up research | `29934779140` | Success |
| Regime-aware Late Stage v1.4 | `29934779079` | Success |
| Orthogonal Proxies v1.6 | `29934777691` | Success |
| Stress Normalisation v1.7 | `29934777808` | Success; preliminary output remains invalid for promotion |
| Corrected Stress Maturity v1.8 | `29934778038` | Success |
| Sector Internals v1.9 | `29934777958` | Success |
| Actual-Product Leverage Mapping v2.0 | `29934779433` | Success |
| OFR source/payload and options-sentiment discovery | multiple | Success |

A green workflow validates execution and declared invariants. It does not imply that a candidate passed economic promotion gates.

### 3.3 Causal controls

- completed-close features only;
- next-open execution;
- 1 bp transaction cost plus 2 bps slippage for staged underlying entries;
- no future data in signal construction;
- no ex-post tranche renormalisation;
- missed/no-trade episodes included;
- transition-only exhaustion and confirmation bonuses;
- 252-session evaluation tail for bottom labels;
- purge at least as long as the label tail before OOS tests;
- dense overlapping rolling windows treated as dependent diagnostics, not independent evidence;
- formal CSCV/PBO blocked unless at least eight non-overlapping outer OOS partitions survive;
- publication-delayed series shifted to first strategy-available session;
- point-in-time data and immutable hashes required for production feature ablation;
- current unfinished exchange-local provider rows removed before use.

### 3.4 Primary performance metrics

1. first and weighted entry distance above eventual trough;
2. worst additional downside after entry;
3. missed complete episodes;
4. timing before or after trough;
5. deployment near trough;
6. false starts exceeding 10% additional downside;
7. stability across shallow, medium and deep regimes;
8. forward return as a secondary economic outcome;
9. actual leveraged-product path after the underlying signal survives.

---

## 4. Fresh IBKR boundary and current context

### 4.1 Latest completed RTH bar: 2026-07-22

| Asset | Open | High | Low | Close | Change versus 2026-07-21 close |
|---|---:|---:|---:|---:|---:|
| SPY | 746.62 | 750.01 | 746.37 | **747.41** | -0.12% |
| QQQ | 703.56 | 709.64 | 703.56 | **705.35** | -0.51% |
| SOXX | 539.55 | 561.07 | 539.55 | **555.52** | +0.51% |
| SMH | 572.86 | 592.00 | 572.80 | **586.91** | +0.48% |

Interpretation:

- the semiconductor rebound continued on the completed close;
- QQQ did not confirm with a higher close;
- this cross-asset divergence is context, not a new production trigger;
- the runtime result in the repository still uses 2026-07-21 and must not be represented as current.

### 4.2 Delayed 2026-07-23 pre-market context

Approximate snapshot time: 12:06–12:09 HKT / 00:06–00:09 ET, with one SMH/USD field sampled earlier.

| Asset | Last | Drawdown from IBKR 52-week high | 30-day historical vol | Underlying IV | 52-week IV percentile |
|---|---:|---:|---:|---:|---:|
| SPY | 746.04 | -1.89% | 16.89% | 13.42% | 42.63% |
| QQQ | 703.10 | -6.08% | 29.27% | 23.74% | 84.06% |
| SOXX | 554.22 | -15.51% | 74.94% | 62.74% | 95.22% |
| SMH | 584.99 | -12.93% | 63.34% | 56.15% | 93.63% |
| SSO | 67.00 | -4.45% | 31.95% | 26.03% | 40.24% |
| QLD | 87.81 | -13.22% | 58.54% | 47.19% | 85.26% |
| USD | 92.52 | -20.58% | 114.30% | 106.02% | 96.81% |

Historical volatility exceeded implied volatility for all seven snapshots. This is evidence of recent realised turbulence, not proof that selling pressure is exhausted. SOXX, SMH and USD remained in extremely high-volatility regimes.

---

## 5. Baseline engine rebuilt from current evidence

### 5.1 Full-history baseline versus v1.1 recovery overlay

| Asset | History | Complete episodes | Baseline missed | Baseline weighted distance | Baseline additional downside | Any trade within 5% | v1.1 weighted distance | v1.1 additional downside | Trades baseline→v1.1 | Decision |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| SPY | 1993-01-29–2026-07-21 | 37 | 0.00% | 6.31% | -5.90% | 89.19% | 6.32% | -5.90% | 140→151 | No improvement |
| QQQ | 1999-03-10–2026-07-21 | 26 | 19.23% | 11.40% | -9.22% | 73.08% | 11.44% | -9.23% | 78→86 | Slightly worse |
| SOXX | 2001-07-13–2026-07-21 | 16 | 0.00% | 13.45% | -11.16% | 68.75% | 13.88% | -11.23% | 57→63 | Worse |

The v1.1 overlay increases trade count without improving episode coverage. It must not be described as an improved bottom detector.

### 5.2 Recent five-year baseline: 2021-07-26–2026-07-21

The machine-readable audit is the source of truth for exact downside values; earlier narrative tables rounded the values inconsistently.

| Asset | Complete episodes | Missed | First entry above trough | Weighted entry above trough | Worst additional downside | Mean timing | 63-session return | Later suffered >10% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SPY | 7 | 0.00% | 6.58% | 5.41% | **-5.28%** | 30.3 sessions early | +7.74% | 28.57% |
| QQQ | 6 | 0.00% | 12.49% | 9.48% | **-9.48%** | 53.3 sessions early | +5.62% | 33.33% |
| SOXX | 6 | 0.00% | 18.96% | 16.52% | **-11.42%** | 61.7 sessions early | +24.58% | 33.33% |

Interpretation:

- SPY is the most defensible staging asset, but it is not exact-bottom timing.
- QQQ enters materially early for a close-to-bottom claim.
- SOXX participates in eventual rebounds, but proximity is poor and timing is very early.
- SOXX's strong 63-day average is recovery economics, not evidence of precise bottom identification.

---

## 6. Structural regime failure: the central new diagnosis

### 6.1 v1.1 results by final episode depth

| Asset | Final drawdown | Episodes | Mean deployment | Weighted distance | Additional downside | Any trade within 5% |
|---|---|---:|---:|---:|---:|---:|
| SPY | <15% | 30 | 19.17% | 2.05% | -1.91% | 100.00% |
| SPY | 15–25% | 4 | 56.50% | 13.28% | -16.15% | 50.00% |
| SPY | ≥25% | 3 | **60.00%** | **39.77%** | **-32.12%** | 33.33% |
| QQQ | <15% | 19 | 8.82% | 2.60% | -2.06% | 73.68% |
| QQQ | 15–25% | 4 | 40.81% | 8.45% | -12.32% | 100.00% |
| QQQ | ≥25% | 3 | **48.33%** | **56.71%** | **-38.57%** | 33.33% |
| SOXX | <15% | 6 | 6.67% | 2.30% | +0.22% | 83.33% |
| SOXX | 15–25% | 5 | 23.50% | 4.98% | -5.88% | 100.00% |
| SOXX | ≥25% | 5 | **57.50%** | **36.67%** | **-30.34%** | 20.00% |

### 6.2 Interpretation

The model is not uniformly weak. It is specifically misallocated across regimes:

- ordinary corrections are the strongest use case;
- medium drawdowns are mixed but manageable with bounded staging;
- structural bears are the failure regime;
- the model commits its highest capital fraction in the failure regime;
- the existing long-bear cap becomes active after material capital can already be deployed.

### 6.3 Highest-value next hypothesis

`DEEP_BEAR_CAPITAL_RESERVATION` should be tested before another bottom indicator:

1. preserve a small initial ordinary-correction probe;
2. detect a transition into falling-200DMA/deep-bear conditions;
3. freeze incremental deployment before the current curve reaches high utilisation;
4. reserve a fixed fraction of capital;
5. release the reserve only after independent point-in-time evidence improves;
6. compare identical episodes, identical costs and actual SSO/QLD/USD product paths;
7. require improvement in deep-regime distance and adverse excursion without unacceptable missed ordinary corrections.

No reserve percentage is promoted in this report.

---

## 7. Recovery, catch-up and later price confirmation

### 7.1 Post-threshold catch-up

| Asset | Result | Key evidence | Production authority |
|---|---|---|---|
| SPY | Diagnostic candidate only | Full-history catch-up quality and missed-alert resilience passed internal screen | None; 2% remains research-only |
| QQQ | Reject | Catch-up 11.25% above trough; mean 63-day return -5.14% | None |
| SOXX | Reject | Fewer than three full-history catch-ups; missed-alert path 30.76% above trough and -17.84% additional downside | None |

### 7.2 QQQ regime-aware late-stage v1.4

| Candidate | Recent trades | Missed | Entry above trough | Additional downside | 63-day return | Decision |
|---|---:|---:|---:|---:|---:|---|
| Exhaustion reclaim | 2 | 66.67% | 22.38% | -15.88% | -7.39% | Reject |
| Retest confirmation | 2 | 66.67% | 11.70% | -8.00% | +23.23% | Research watch; underpowered |
| Strong confirmation | 2 | 66.67% | 22.81% | -16.26% | -5.55% | Reject |
| Dual path | 4 | 33.33% | 18.47% | -9.52% | +6.13% | Reject |

The QQQ retest path is the least-bad later confirmation, but two observations and inadequate paired evidence cannot support a tranche.

### 7.3 SOXX regime-aware late-stage v1.4

| Candidate | Recent trades | Missed | Entry above trough | Additional downside | 63-day return | Decision |
|---|---:|---:|---:|---:|---:|---|
| Exhaustion reclaim | 2 | 66.67% | 41.72% | -15.26% | +0.22% | Reject |
| Retest confirmation | 1 | 83.33% | 45.05% | -31.06% | -11.24% | Reject |
| Strong confirmation | 3 | 50.00% | 32.94% | -20.16% | -8.07% | Reject |
| Dual path | 2 | 66.67% | 38.12% | -13.64% | +2.97% | Reject |

Conventional price recovery remains unable to distinguish a final semiconductor trough from an intermediate sector rally.

---

## 8. Independent indicator families

### 8.1 Equal-weight breadth, credit appetite and relative strength

Tested proxies:

- RSP/SPY;
- QQQE/QQQ;
- XSD/SOXX;
- HYG/IEF;
- QQQ/SPY;
- SOXX/QQQ;
- VIX/VXN/VIX3M context.

| Candidate | Recent trades | Missed | Entry above trough | Additional downside | 63-day return | Decision |
|---|---:|---:|---:|---:|---:|---|
| QQQ breadth + credit | 1 | 83.33% | 7.11% | -6.64% | +8.11% | Interesting single path; insufficient |
| SOXX equal-weight breadth | 2 | 66.67% | 52.28% | -34.28% | -14.68% | Actively misleading |
| SOXX multi-factor proxy | 2 | 66.67% | 43.50% | -30.25% | -9.20% | Reject |

Equal-weight breadth measures participation and concentration. It is not historical point-in-time constituent breadth and did not establish bottom completion.

### 8.2 Financial, funding and volatility stress

Corrected v1.8 used:

- OFR FSI and category components;
- SOFR average, 1st and 99th percentiles;
- BGCR;
- DVP repo rate and volume;
- primary-dealer fails to deliver;
- VIX, VIX3M, VIX9D, VVIX, VXN and MOVE.

Conservative availability lags:

- one business session for SOFR, BGCR and DVP data;
- two business sessions for dealer fails and OFR FSI.

| Asset / candidate | Recent trades | Missed | Entry above trough | Additional downside | 63-day return | Decision |
|---|---:|---:|---:|---:|---:|---|
| SPY mature FSI | 2 | 71.43% | 19.30% | -16.03% | -3.18% | Reject |
| QQQ mature FSI | 3 | 50.00% | 22.39% | -10.59% | -0.24% | Reject |
| QQQ funding/composite | 2 | 66.67% | 24.53% | -17.18% | -7.65% | Reject |
| SOXX mature FSI | 2 | 66.67% | 52.27% | -34.27% | -16.07% | Reject |
| SOXX funding/composite | 1 | 83.33% | 50.32% | -33.48% | -8.36% | Reject |

Broad stress can peak before the final equity or semiconductor trough. Retain it as systemic-risk context and a possible leverage veto, not as a standalone entry trigger.

### 8.3 Cross-sectional sector internals

Research panels:

- SPY: nine long-running sector ETFs;
- QQQ: fixed current long-history mega-cap/technology panel;
- SOXX: fixed long-history semiconductor panel.

The QQQ and SOXX panels are current-survivor proxies and cannot be promoted without historical membership.

| Candidate | Recent trades | Missed | Entry above trough | Additional downside | 63-day return | Decision |
|---|---:|---:|---:|---:|---:|---|
| QQQ breadth/dispersion | 1 | 83.33% | 9.33% | -5.60% | +4.62% | One acceptable path; insufficient |
| SOXX breadth thrust | 2 | 66.67% | 52.27% | -34.28% | -16.07% | Reject |
| SOXX dispersion normalisation | 1 | 83.33% | 47.99% | -32.43% | -8.11% | Reject |
| SOXX positive divergence | 0 | 100% | n/a | n/a | n/a | No usable signal |

The SOXX failure is not merely cap-weight concentration. A broad semiconductor panel can rebound together during the middle of a longer decline.

### 8.4 Options and correlation evidence

Available and reproducible public context:

- VIX daily history;
- VVIX daily history;
- VIX9D daily history;
- selected Cboe historical put/call files and daily-statistics pages.

Methodologically relevant but requiring authorised/reproducible history:

- COR1M/COR3M implied correlation;
- DSPX/VIXEQ implied dispersion;
- bulk options-flow and opening/closing classifications.

Cboe defines DSPX as forward 30-day implied dispersion derived from SPX and selected constituent options using a modified VIX methodology. Implied correlation measures expected diversification/herding conditions. These are promising because they directly address index-versus-component structure, but they remain unbuilt production features.

### 8.5 Genuine variance-risk premium

A valid feature requires:

- model-free implied variance from an option strip;
- high-frequency intraday realised variance, preferably downside-specific;
- point-in-time strikes, expiries, timestamps and methodology;
- identical-fold ablation above the existing price engine.

Underlying IV minus daily historical volatility is only a rough context proxy and must not be labelled a validated VRP.

---

## 9. Semiconductor-cycle evidence: current official context and limitations

### 9.1 Current official industry data

- SIA reported May 2026 global semiconductor sales of **$120.6 billion**, up 9.2% from April and 104.1% year over year. The monthly figure is a three-month moving average.
- SEMI reported Q1 2026 global semiconductor equipment billings of **$36.55 billion**, up 14% year over year and 1% quarter over quarter, driven by leading-edge logic, DRAM and advanced packaging investment.
- WSTS's Spring 2026 forecast projected 2026 global semiconductor sales of approximately **$1.51 trillion**, with extraordinary memory growth and substantial logic growth.

### 9.2 Interpretation

These data do not invalidate a SOXX drawdown. They show that the sector is unusually strong and heterogeneous:

- memory and AI infrastructure can grow much faster than analogue, discrete, sensor or mature-node categories;
- equipment, design, foundry, packaging and memory stocks can be at different points in their earnings cycles;
- aggregate monthly sales are smoothed and publication-lagged;
- aggregate equipment billings can stay strong while valuation, positioning or subsector expectations correct sharply;
- final ETF trough timing therefore requires point-in-time revisions, inventory/order dispersion and market risk data rather than aggregate growth alone.

### 9.3 Corrected fundamental roadmap

Do not assume a current public monthly book-to-bill series exists. SEMI stopped publishing the North American monthly book-to-bill report in 2017.

Future authorised features should instead include:

- EPS and revenue revision breadth;
- estimate dispersion and revision acceleration;
- inventory days and inventory revision breadth;
- company order/backlog and cancellation indicators;
- authorised SEMI billings, WWSEMS and fab forecast data;
- capacity utilisation, lead times and advanced-packaging/HBM indicators;
- historical point-in-time SOXX/semiconductor membership;
- exact publication timestamps and vintage policy.

---

## 10. SMH/SOXX paired evidence

### 10.1 Full history: 16 complete SOXX episodes

| Variant | Trades | Within 5% | Within 8% | Weighted distance | Worst additional downside |
|---|---:|---:|---:|---:|---:|
| SOXX only | 57 | 68.75% | 81.25% | 13.448% | -11.164% |
| SMH confirmation veto/gate | 57 | 68.75% | 81.25% | 13.448% | -11.164% |
| SMH soft confirm | 55 | 62.50% | 81.25% | 13.597% | -11.869% |
| SMH veto-only/hard confirm | 58 | 68.75% | 81.25% | 13.395% | -11.164% |

The apparent gain was approximately 0.054 percentage points.

### 10.2 Post-2024: five complete episodes

| Variant | Trades | Within 5% | Within 8% | Weighted distance | Worst additional downside |
|---|---:|---:|---:|---:|---:|
| SOXX only | 15 | 80.00% | 80.00% | 9.892% | -6.324% |
| SMH confirmation veto/gate | 15 | 80.00% | 80.00% | 9.892% | -6.324% |
| SMH soft confirm | 14 | 60.00% | 80.00% | 10.944% | -8.580% |
| SMH veto-only/hard confirm | 14 | 80.00% | 80.00% | 10.317% | -6.324% |

The tiny full-history improvement did not persist. SMH remains:

- a second displayed semiconductor coordinate;
- a narrative divergence/confidence warning;
- production weight zero;
- unable to create, enlarge, revoke or duplicate a SOXX tranche;
- unable to authorise USD.

---

## 11. Actual leveraged-product audit

### 11.1 Official benchmark mapping

- SSO targets 2x the **daily S&P 500** return.
- QLD targets 2x the **daily Nasdaq-100** return.
- USD targets 2x the **daily Dow Jones U.S. Semiconductors Index** return.
- SOXX tracks the **NYSE Semiconductor Index**.

Thus:

- SPY→SSO and QQQ→QLD are same-benchmark-family mappings;
- SOXX→USD is a cross-index tactical proxy;
- all products have daily objectives and multi-day path dependency.

### 11.2 Daily mapping diagnostics

| Mapping | Relationship | Observations | Correlation | Daily beta | Gap RMSE versus 2x signal ETF |
|---|---|---:|---:|---:|---:|
| SPY→SSO | Same benchmark family | 5,050 | 0.9956 | 1.9592 | 0.231% |
| QQQ→QLD | Same benchmark family | 5,050 | 0.9960 | 1.9832 | 0.250% |
| SOXX→USD | Cross-index proxy | 4,896 | 0.9584 | 1.9120 | 1.148% |

For SOXX→USD, the gap is not pure tracking error.

### 11.3 Actual-product tactical trades

| Mapping | Trades | Win rate | Mean return | Median return | Worst trade | Mean MAE | Worst MAE | Mean holding days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SPY→SSO | 16 | 56.25% | +2.19% | +2.02% | -4.77% | -2.20% | -5.65% | 18.19 |
| QQQ→QLD | 17 | 58.82% | +3.44% | +0.31% | -5.16% | -3.19% | -8.60% | 11.53 |
| SOXX→USD | 31 | 48.39% | +1.38% | **-1.19%** | **-23.24%** | **-6.50%** | **-28.63%** | 10.84 |

All mappings remain blocked because:

- the underlying tactical entry rule is not formally promoted;
- daily-reset path dependency remains material;
- USD also has benchmark mismatch and severe audited tail loss.

---

## 12. Evidence-grade and production-authority matrix

| Claim | Evidence grade | Authority | Decision |
|---|---|---|---|
| Completed-close/next-open implementation | A | Implementation only | Retain |
| Latest IBKR boundary/corporate-action control | A- | Data boundary | Retain |
| Ordinary-correction staged participation | B | Existing bounded v1.1 logic | Retain |
| SPY close-to-bottom precision | B- | None beyond bounded staging | Narrow language |
| QQQ close-to-bottom precision | C | None | Reject claim |
| SOXX close-to-bottom precision | D+ | None | Reject claim |
| Deep-bear capital reservation | Unbuilt high-priority | None | Build next |
| QQQ retest/breadth observation | C- | None | Research watch only |
| SOXX price/breadth confirmation | D | None | Reject |
| Equal-weight ratio breadth | C- | Context only | Descriptive |
| Fixed-panel internals | C- | Context only | Survivorship-biased |
| OFR/funding normalisation | C | Veto/context only | No entry trigger |
| VIX/VVIX/VIX9D stack | C | Context only | No standalone trigger |
| SMH paired rule | C | Narrative confidence only | Weight zero |
| SSO/QLD mapping | C | None | Continue after underlying validation |
| USD mapping | D+ | None | Block |
| Genuine downside VRP | Unbuilt | None | High-priority data gate |
| PIT revisions/inventory/order breadth | Unbuilt | None | High-priority data gate |
| COR1M/COR3M and DSPX history | Unbuilt/authorisation required | None | High-priority data gate |

---

## 13. Final production specification

### 13.1 Universal

1. Official signal state uses the latest fully completed RTH close.
2. Intraday, pre-market and after-hours data are context only.
3. Runtime output must match the latest request ID, completed-bar date, model commit and input hash.
4. A stale runtime result must be labelled stale, not current.
5. The v1.1 engine may create only bounded staged-participation candidates.
6. v1.5 taxonomy remains reporting-only:
   - participation status;
   - local swing status;
   - cycle-bottom status.
7. Local recovery is not cycle-bottom confirmation.
8. Simulated deployment, actual confirmed execution and current action must be separate fields.
9. No research proxy may create or size a trade without PIT provenance and identical-fold validation.
10. No leverage product is activated by drawdown, high IV percentile, breadth reversal, a stress decline or a sharp rebound alone.
11. The public repository must not contain raw licensed IBKR history, account data, positions, executions or credentials.

### 13.2 SPY

- retain small ordinary-correction staging;
- retain a 2% post-threshold catch-up as research-only when an earlier probe is confirmed not executed;
- do not call it exact-bottom timing;
- SSO remains unavailable pending formal underlying and actual-product OOS validation.

### 13.3 QQQ

- retain small early staging only;
- no V-shaped catch-up;
- retest/internal breadth can be displayed as research watch, not a tranche;
- QLD remains unavailable.

### 13.4 SOXX

- retain only bounded staged exposure under the original price engine;
- no V-shaped catch-up;
- no late-stage price-only confirmation tranche;
- SMH remains informational;
- broad semiconductor breadth does not confirm the final sector trough;
- USD remains unavailable and must always be labelled a cross-index proxy.

### 13.5 Required report language

Use one of four explicit outputs instead of circular waiting language:

1. **STAGED PARTICIPATION:** a bounded left-side tranche is available under the production price engine.
2. **LOCAL RECOVERY WATCH:** evidence is improving, but no new production tranche is authorised.
3. **LOCAL SWING RECOVERY:** tradable rebound structure is stronger, but cycle-bottom evidence remains incomplete.
4. **CYCLE BOTTOM UNCONFIRMED:** independent evidence is missing, divergent, revised, biased or underpowered.

When earlier execution is unknown:

- **If earlier tranche executed:** hold/manage using stored invalidation and next-stage logic.
- **If earlier tranche not executed:** state whether a validated catch-up exists. Current answer: no for QQQ and SOXX.

---

## 14. Prioritised research roadmap

### Priority 1 — deep-bear capital reservation

- run identical episodes using a reserve overlay;
- freeze incremental deployment upon structural-bear transition;
- optimise nothing on the latest episode alone;
- evaluate shallow-correction participation loss versus deep-bear distance/MAE improvement;
- validate actual SSO/QLD/USD only after underlying survival.

### Priority 2 — point-in-time semiconductor earnings and cycle breadth

- revenue/EPS revision breadth;
- estimate dispersion;
- inventory days and revisions;
- order/backlog/cancellation indicators;
- utilisation and lead times;
- historical constituent membership;
- exact release timestamps and vintages.

### Priority 3 — authorised correlation and dispersion history

- COR1M/COR3M;
- DSPX/VIXEQ;
- correlation-stress peak/normalisation;
- dispersion collapse/recovery;
- licensed historical files and reproducible hashes.

### Priority 4 — genuine downside variance-risk premium

- model-free option-strip implied downside variance;
- high-frequency realised downside variance;
- strike/expiry/liquidity controls;
- PIT construction and identical-fold ablation.

### Priority 5 — authorised bulk options-flow history

- equity/index/ETP put-call ratios;
- net option-premium imbalance;
- opening versus closing activity;
- reproducible bulk history rather than webpage-by-webpage scraping.

### Priority 6 — licensed semiconductor equipment/fab data

- SEMI billings and WWSEMS;
- fab forecast and capacity ramps;
- advanced packaging/HBM equipment indicators;
- company-level orders and backlogs;
- no assumption that a current monthly public book-to-bill series exists.

### Priority 7 — formal long-cycle validation

- immutable datasets;
- at least eight non-overlapping outer OOS partitions;
- same folds for price → breadth → VRP → credit → earnings ablations;
- one-standard-error selection;
- worst-regime and economic-significance gates;
- actual-product audit only after underlying promotion.

---

## 15. Official and primary-source register

- OFR Financial Stress Index: https://www.financialresearch.gov/financial-stress-index/
- Cboe VIX and other volatility-index history: https://www.cboe.com/tradable-products/vix/vix-historical-data
- Cboe implied correlation: https://www.cboe.com/us/indices/implied/
- Cboe S&P 500 Dispersion Index: https://www.cboe.com/us/indices/dispersion/
- Cboe index historical-data access: https://www.cboe.com/us/indices/accessing-index-data
- Federal Reserve, Expected Stock Returns and Variance Risk Premia: https://www.federalreserve.gov/econres/feds/expected-stock-returns-and-variance-risk-premia.htm
- iShares SOXX official page: https://www.ishares.com/us/products/239705/ishares-semiconductor-etf
- ProShares SSO: https://www.proshares.com/our-etfs/leveraged-and-inverse/sso
- ProShares QLD: https://www.proshares.com/our-etfs/leveraged-and-inverse/qld
- ProShares USD: https://www.proshares.com/our-etfs/leveraged-and-inverse/usd
- SIA May 2026 sales release: https://www.semiconductors.org/global-semiconductor-sales-increase-9-2-month-to-month-in-may/
- WSTS Spring 2026 forecast: https://www.wsts.org/76/Recent-News-Release
- SEMI Q1 2026 equipment billings: https://www.semi.org/en/semi-press-release/semi-reports-global-semiconductor-equipment-billings-increased-14-percent-year-over-year-in-q1-2026
- SEMI Billings Report and book-to-bill notice: https://www.semi.org/en/products-services/market-data/equipment/billings-report

---

## 16. Final verdict

> **Retain the monitor as a bounded ordinary-correction participation and recovery-classification system. Do not call it a validated precise-bottom detector for QQQ or SOXX. Do not promote new thresholds, tranches, SMH gates or leverage rules. The immediate engineering priority is to stop over-deploying in deep structural bears; the next data priority is point-in-time semiconductor-cycle, genuine downside-VRP and authorised correlation/dispersion evidence.**

No threshold, tranche, leverage rule or order was changed by this report.
