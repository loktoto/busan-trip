# Ground-Up Market-Bottom Monitor Research Report

**Date:** 2026-07-22  
**Scope:** SPY, QQQ and SOXX; SMH as an informational semiconductor cross-check; tactical leveraged mappings SSO, QLD and USD  
**Supersedes:** prior market-bottom, recovery-overlay, alternative-indicator and sector-internal narrative reports  
**Research branch:** `agent/market-bottom-strategy`  
**Decision standard:** completed-close signal at session `t`; conceptual execution at next regular-session open `t+1`, including configured costs

---

## 1. Executive conclusion

The previous research contained useful engineering and governance work, but its investment interpretation was too optimistic in several places.

The rebuilt conclusion is:

1. **The existing price engine is a staged drawdown-participation model, not a reliably precise cycle-bottom detector.**
2. **Its aggregate performance is dominated by acceptable results in shallow corrections. Its performance deteriorates sharply in deep bear markets.**
3. **The v1.1 recovery overlay does not improve bottom proximity.** It adds trades and capital, while weighted distance to the eventual trough is unchanged or slightly worse for SPY, QQQ and SOXX.
4. **QQQ and especially SOXX require a separate deep-bear regime.** A large rebound, moving-average reclaim, broad sector participation, stress normalisation or high implied-volatility percentile can all occur well before the final trough.
5. **SMH remains informational only.** The paired SMH/SOXX research did not show persistent incremental value sufficient to change SOXX state, tranche sizing, invalidation or USD eligibility.
6. **No new entry threshold, tranche size or leveraged-entry rule is promoted.**
7. **The highest-value next experiment is not another rebound indicator.** It is a causal deep-bear capital-preservation rule that reserves capital after a drawdown becomes structurally severe, followed by point-in-time breadth, downside variance-risk-premium, credit and earnings-revision ablations.
8. **SSO, QLD and USD remain blocked.** Their objectives are daily 2x targets; multi-day outcomes depend on volatility and compounding. Product-level path backtests are still required.

### Production decision

- Retain the current monitor for **small, bounded staged participation**.
- Retain the v1.5 reporting taxonomy separating:
  - participation,
  - local-swing recovery,
  - cycle-bottom evidence.
- Do **not** call a QQQ or SOXX local rebound a confirmed cycle bottom.
- Do **not** allow v-shaped catch-up for QQQ or SOXX.
- Do **not** activate SSO, QLD or USD from price recovery, breadth or stress normalisation alone.
- Treat model-simulated deployment and actual user execution as separate fields.

---

## 2. Disposition of prior findings

| Classification | Rebuilt finding |
|---|---|
| **RETAINED** | Completed-close signals, next-open execution, explicit costs, complete episode catalogues, corporate-action audits, publication-lag controls, unresolved-episode handling and separation of model deployment from actual execution remain valid. |
| **RETAINED** | SPY, QQQ and SOXX should be calculated independently. SMH remains an informational semiconductor coordinate with production weight zero. |
| **UPDATED** | The baseline model is useful primarily for staged participation in ordinary corrections. Its value is materially weaker in deep drawdowns. |
| **UPDATED** | Breadth, dispersion, funding stress and volatility structure are useful as rebound-quality, confidence or veto variables—not as independent proof of a final trough. |
| **CORRECTED** | The v1.1 recovery overlay does not enhance bottom detection on the validated aggregate metrics. |
| **CORRECTED** | Positive 42/63/84-day forward returns do not establish bottom-timing accuracy. Bottom proximity and adverse excursion are the primary metrics. |
| **CORRECTED** | The first v1.7 stress-normalisation result is invalid for promotion because breach age was reset repeatedly while price remained below the threshold. Only the corrected v1.8 results are admissible. |
| **CORRECTED** | Fixed current-constituent stock panels are survivorship-biased discovery proxies and cannot support production promotion. |
| **NEW** | The most serious model risk is regime concentration: shallow corrections look good, while final drawdowns above 25% produce very early and materially adverse deployment. |
| **NEW** | The next candidate should test capital reservation or deployment freezing in structural bear regimes before adding further confirmation features. |
| **NEW** | Current authorised or high-quality data gaps—not a shortage of price indicators—are now the principal bottleneck. |

---

## 3. Evidence hierarchy and validation controls

### 3.1 Source hierarchy

1. **IBKR:** recent five-year boundary, current completed bar, corporate actions, current market context and leveraged-product snapshots.
2. **GitHub immutable workflow artifacts:** exact strategy outputs, episode tables, trades, audits and test logs.
3. **Official institutions and product sponsors:**
   - OFR for financial and funding stress;
   - Cboe for VIX-family, dispersion and correlation methodologies;
   - Nasdaq, S&P DJI and ETF sponsors for equal-weight/index definitions;
   - ProShares and SEC filings for daily-leverage objectives and compounding risk;
   - SIA/WSTS for semiconductor market data definitions and release availability.
4. **Peer-reviewed or primary research:** variance-risk-premium and analyst-expectation research used to justify future feature families, not to claim that the present implementation has already passed.

### 3.2 Causality controls

The admissible backtests use:

- data known by completed regular-session close `t`;
- next-session open `t+1` execution;
- configured transaction costs and slippage;
- no ex-post re-normalisation of tranche sizes;
- complete drawdown episodes, including no-trade episodes;
- future prices only for evaluation labels;
- publication-delay shifts for OFR and funding series;
- explicit blocking when point-in-time constituent membership or historical vintages are unavailable.

### 3.3 Primary metrics

The rebuilt report ranks metrics in this order:

1. mean and median entry distance above the eventual episode trough;
2. additional downside after entry;
3. missed-episode rate;
4. sessions before or after the eventual trough;
5. capital deployed near the trough;
6. stability across drawdown regimes and independent episodes;
7. forward return as a secondary economic outcome only.

A strategy can have positive forward returns simply because risky assets eventually recover. That does not prove close-to-bottom timing.

---

## 4. Recomputed baseline and v1.1 recovery overlay

### 4.1 Full-history results

| Asset | History | Complete episodes | Baseline missed | Baseline weighted distance | Baseline additional downside | Baseline within 5% | v1.1 weighted distance | v1.1 additional downside | Decision |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| SPY | 1993-01-29 to 2026-07-21 | 37 | 0.00% | 6.31% | -5.90% | 89.19% | 6.32% | -5.90% | Overlay adds no meaningful value |
| QQQ | 1999-03-10 to 2026-07-21 | 26 | 19.23% | 11.40% | -9.22% | 73.08% | 11.44% | -9.23% | Slightly worse |
| SOXX | 2001-07-13 to 2026-07-21 | 16 | 0.00% | 13.45% | -11.16% | 68.75% | 13.88% | -11.23% | Clearly worse |

The overlay increased trade counts:

- SPY: 140 to 151;
- QQQ: 78 to 86;
- SOXX: 57 to 63.

It did not improve the episode hit rates. Therefore the recovery overlay must not be described as an improved bottom detector.

### 4.2 Recent five-year baseline

Validation window: **2021-07-26 to 2026-07-21**.

| Asset | Complete episodes | Missed | First entry above trough | Additional downside | Mean timing vs trough | 63-day forward return |
|---|---:|---:|---:|---:|---:|---:|
| SPY | 7 | 0.00% | 6.58% | -5.22% | 30.3 sessions early | +7.74% |
| QQQ | 6 | 0.00% | 12.49% | -9.36% | 53.3 sessions early | +5.62% |
| SOXX | 6 | 0.00% | 18.96% | -11.30% | 61.7 sessions early | +24.58% |

The forward-return column is not a bottom-precision score. QQQ and SOXX entered materially before the eventual trough despite positive eventual returns.

---

## 5. Newly identified regime failure

The aggregate averages conceal a large regime dependency.

### 5.1 v1.1 performance by final episode depth

| Asset | Final drawdown bucket | Complete episodes | Mean deployment | Weighted distance above trough | Additional downside | Any trade within 5% |
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

### 5.2 Interpretation

**RETAINED:** Small, staged participation can work in ordinary corrections.

**CORRECTED:** The same deployment curve cannot be assumed to work in structural bear markets.

**NEW:** The model commits the most capital in the regime where its timing is least reliable. A long-bear cap applied only after the regime becomes obvious cannot undo capital already deployed earlier in the episode.

This is the highest-priority research defect.

### 5.3 Proposed—but not promoted—next candidate

Test a `DEEP_BEAR_CAPITAL_RESERVATION` overlay:

- normal shallow-correction probe remains available;
- once price is below a falling 200DMA or the episode exceeds a regime-specific drawdown/maturity threshold:
  - freeze incremental deployment,
  - reserve a fixed proportion of capital,
  - release reserved capital only after independent point-in-time evidence improves;
- compare against v1.1 on the same episodes and product paths.

This is a research hypothesis, not a current production change.

---

## 6. Late-stage price confirmation

Four causal families were tested independently: exhaustion reclaim, retest confirmation, strong confirmation and a dual path.

### QQQ

| Candidate | Recent missed | Distance above trough | Additional downside | 63-day return | Decision |
|---|---:|---:|---:|---:|---|
| Regime exhaustion reclaim | 66.67% | 22.38% | -15.88% | -7.39% | Reject |
| Regime retest confirmation | 66.67% | 11.70% | -8.00% | +23.23% | Research watch only; two recent episodes |
| Regime strong confirmation | 66.67% | 22.81% | -16.26% | -5.55% | Reject |
| Regime dual path | 33.33% | 18.47% | -9.52% | +6.13% | Reject |

The QQQ retest path is worth preserving as a research watch, but the sample is insufficient for promotion.

### SOXX

| Candidate | Recent missed | Distance above trough | Additional downside | 63-day return | Decision |
|---|---:|---:|---:|---:|---|
| Regime exhaustion reclaim | 66.67% | 41.72% | -15.26% | +0.22% | Reject |
| Regime retest confirmation | 83.33% | 45.05% | -31.06% | -11.24% | Reject |
| Regime strong confirmation | 50.00% | 32.94% | -20.16% | -8.07% | Reject |
| Regime dual path | 66.67% | 38.12% | -13.64% | +2.97% | Reject |

A common moving-average or rebound confirmation is especially unsafe for SOXX.

---

## 7. Orthogonal indicators rebuilt

### 7.1 Equal-weight breadth and credit appetite

Verified proxies:

- RSP/SPY for S&P 500 equal-weight participation;
- QQQE/QQQ for Nasdaq-100 equal-weight participation;
- XSD/SOXX for modified-equal-weight semiconductor participation;
- HYG/IEF for a public credit-risk-appetite proxy.

Official product methodology confirms:

- RSP equally weights S&P 500 constituents and rebalances quarterly;
- QQQE tracks the Nasdaq-100 Equal Weighted Index;
- XSD tracks a modified equal-weight semiconductor index across large-, mid- and small-cap stocks.

These ratios are breadth/concentration proxies, not true historical constituent breadth.

| Candidate | Recent observations | Distance above trough | Additional downside | 63-day return | Decision |
|---|---:|---:|---:|---:|---|
| QQQ breadth + credit | 1 of 6 episodes | 7.11% | -6.64% | +8.11% | Too sparse |
| SOXX equal-weight breadth | 2 of 6 episodes | 52.28% | -34.28% | -14.68% | Reject |
| SOXX multi-factor proxy | 2 of 6 episodes | 43.50% | -30.25% | -9.20% | Reject |

**Updated conclusion:** Equal-weight breadth measures whether participation is broad. It does not prove that the earnings or inventory cycle has finished declining.

### 7.2 Financial, funding and volatility stress

Official-source families included:

- OFR FSI and its categories;
- SOFR average and transaction percentiles;
- BGCR;
- DVP repo rate and volume;
- primary-dealer fails;
- VIX, VIX9D, VIX3M, VVIX, VXN and MOVE.

Conservative availability lags were applied. The OFR FSI public file is current revised history, not a vintage archive; it is therefore a research proxy unless vintage provenance is added.

The first v1.7 implementation is invalidated because breach age reset on every day below the threshold. The corrected v1.8 result is:

| Asset/candidate | Recent missed | Distance above trough | Additional downside | 63-day return | Decision |
|---|---:|---:|---:|---:|---|
| SPY mature FSI | 71.43% | 19.30% | -16.03% | -3.18% | Reject |
| QQQ mature FSI | 50.00% | 22.39% | -10.59% | -0.24% | Reject |
| QQQ funding/composite | 66.67% | 24.53% | -17.18% | -7.65% | Reject |
| SOXX mature FSI | 66.67% | 52.27% | -34.27% | -16.07% | Reject |
| SOXX funding/composite | 83.33% | 50.32% | -33.48% | -8.36% | Reject |

**Updated conclusion:** Systemic stress can peak before the final sector trough. Use these families as systemic-risk context or leverage vetoes, not standalone equity-bottom triggers.

### 7.3 Cross-sectional sector internals

Research panels measured:

- percentage above 20DMA and 50DMA;
- positive five-session return breadth;
- fresh-low breadth;
- median return;
- cross-sectional dispersion;
- breadth thrust, dispersion normalisation and divergence.

The QQQ and SOXX panels used current long-running survivors. They are explicitly survivorship-biased.

| Asset/candidate | Recent missed | Distance above trough | Additional downside | 63-day return | Decision |
|---|---:|---:|---:|---:|---|
| QQQ breadth/dispersion | 83.33% | 9.33% | -5.60% | +4.62% | One recent episode; insufficient |
| SOXX breadth thrust | 66.67% | 52.27% | -34.27% | -16.07% | Reject |
| SOXX dispersion normalisation | 83.33% | 47.99% | -32.43% | -8.11% | Reject |

**Newly strengthened conclusion:** SOXX's problem is not merely cap-weight concentration. A broad semiconductor rebound can occur during the middle of a longer sector decline.

---

## 8. SMH/SOXX paired evidence

The paired study kept SOXX as the only executable semiconductor target and gave SMH zero production weight.

Findings:

- state-4 confirmation-only rules were effectively identical to SOXX-only;
- soft confirmation worsened hit rates or adverse excursion;
- broad veto/hard-confirm variants showed only a negligible full-history improvement and failed to persist in the post-2024 sample.

**Retained decision:** SMH may provide a second semiconductor coordinate and divergence warning. It does not currently change SOXX state, tranche, invalidation or USD eligibility.

---

## 9. Options, correlation and variance-risk evidence

### 9.1 What public data can support now

Usable public daily histories exist for VIX-family indices, VVIX and SKEW. Cboe defines VIX as 30-day expected SPX volatility from option prices and publishes a term structure including VIX9D, VIX, VIX3M and longer maturities.

Cboe's DSPX methodology measures 30-day forward implied dispersion using SPX and single-stock options. This is conceptually closer to the correlation/dispersion question than an ETF ratio.

### 9.2 What is not yet production-ready

- authorised long-history COR1M/COR3M or DSPX/VIXEQ datasets;
- bulk, reproducible Cboe put/call histories;
- model-free downside implied variance matched with intraday realised downside variance;
- immutable option-strip inputs and settlement rules.

Academic evidence supports the variance risk premium as a potentially informative return predictor. It does not validate an `IV minus daily HV` shortcut as an equivalent downside-VRP measure.

---

## 10. Semiconductor fundamental-cycle evidence

SIA states that WSTS compiles industry-wide monthly semiconductor shipment data, including value, units and average selling prices. Public SIA releases generally report a three-month moving average, while comprehensive historical data and detailed forecasts require the WSTS data package.

This creates two important controls:

1. public press-release growth rates are smoothed and cannot be treated as instantaneous inventory-cycle turns;
2. any book-to-bill, shipment, inventory or forecast-revision feature must be aligned to its actual publication date.

The present monitor has not yet tested point-in-time:

- WSTS product-category shipment momentum;
- semiconductor inventory days and lead times;
- order or book-to-bill breadth;
- revenue/EPS revision breadth and estimate dispersion.

These remain high-value candidates, especially for SOXX.

---

## 11. Leveraged products

Official objectives:

- SSO targets 2x the **daily** S&P 500 return;
- QLD targets 2x the **daily** Nasdaq-100 return;
- USD targets 2x the **daily** Dow Jones U.S. Semiconductors Index return.

The sponsors and SEC filings both warn that multi-day returns can differ significantly from two times the underlying holding-period return; the divergence becomes more pronounced with higher volatility and longer holding periods.

### Current IBKR context

IBKR snapshot around **2026-07-22 23:16–23:17 HKT / 11:16–11:17 ET**. The snapshot may be live or delayed according to account entitlement; the latest fully completed daily bar at that time was 2026-07-21.

| Asset | Last | Drawdown from 52-week high | Historical vol | Underlying IV | 52-week IV percentile |
|---|---:|---:|---:|---:|---:|
| SPY | 748.87 | -1.52% | 16.89% | 13.38% | 39.84% |
| QQQ | 708.87 | -5.31% | 29.27% | 23.75% | 84.06% |
| SOXX | 559.52 | -14.70% | 74.94% | 62.96% | 96.02% |
| SMH | 590.52 | -12.10% | 63.34% | 55.15% | 92.43% |
| SSO | 67.52 | -3.71% | 31.95% | 25.54% | 33.47% |
| QLD | 89.20 | -11.85% | 58.54% | 47.05% | 85.26% |
| USD | 93.51 | -19.73% | 114.30% | 106.68% | 97.21% |

This is market context, not a causal signal. In particular, SOXX and USD remain extremely volatile. High IV percentile alone is not exhaustion or bottom confirmation.

### Leveraged decision

No leveraged rule is promoted because:

- the underlying bottom detector is not sufficiently precise in deep regimes;
- product-level entry/exit path tests are incomplete;
- USD uses a different benchmark from SOXX and has strong daily-reset path dependency;
- current volatility materially raises compounding risk.

---

## 12. Production specification after rebuild

### Retain

- hourly calculation, with completed RTH close as the official signal;
- small staged participation;
- separate SPY, QQQ and SOXX states;
- SMH informational only;
- v1.5 taxonomy:
  - `participation_status`,
  - `local_swing_status`,
  - `cycle_bottom_status`,
  - evidence gaps;
- explicit separation of:
  - model-simulated deployment,
  - actual confirmed position/execution,
  - current action;
- leverage veto until separately validated.

### Do not promote

- v1.1 recovery overlay as a bottom improvement;
- QQQ or SOXX v-shaped catch-up;
- a simple moving-average reclaim;
- equal-weight breadth reversal;
- semiconductor-panel breadth thrust;
- FSI or repo stress normalisation;
- high IV percentile;
- a single put/call extreme;
- present-day constituent panels;
- simulated deployment as evidence that the user executed a trade.

### Add to reporting—not sizing

The monitor may report:

- broad versus narrow participation;
- volatility-stack normalisation;
- financial/funding stress;
- SMH/SOXX divergence;
- sector-internal breadth and dispersion;
- whether the episode is an ordinary correction, transition regime or structural bear.

These fields should not create a tranche until they pass identical-fold point-in-time ablation.

---

## 13. Prioritised research roadmap

### Priority 1 — deep-bear capital reservation

Test whether reserving capital after structural-bear evidence improves:

- weighted distance;
- adverse excursion;
- capital near the trough;
- worst-regime outcomes;
- actual SSO/QLD/USD product paths.

This directly addresses the newly verified failure mode.

### Priority 2 — authorised point-in-time evidence

1. historical semiconductor constituent membership and true breadth;
2. Cboe correlation/dispersion histories;
3. model-free downside variance-risk premium;
4. point-in-time semiconductor revenue/EPS revisions;
5. authorised bulk options-flow history;
6. WSTS/SIA category shipments plus inventory/order-cycle data.

### Priority 3 — product-level leverage backtest

For each mapping independently:

- SPY→SSO;
- QQQ→QLD;
- SOXX→USD.

Use actual adjusted product prices, daily reset, fees, financing/tracking gap, entry at next open, exit and end-of-data treatment. Do not infer product returns by multiplying the underlying return.

---

## 14. Confidence assessment

| Finding | Confidence |
|---|---|
| v1.1 recovery overlay does not improve aggregate bottom proximity | High |
| Baseline is better described as staged participation than precise bottom detection | High |
| Deep drawdowns are the principal current failure regime | High |
| Equal-weight breadth and fixed-panel breadth are not standalone cycle-bottom triggers | High |
| OFR/funding normalisation is context, not a standalone SOXX bottom trigger | High |
| SMH does not currently add stable production value | Medium-high |
| QQQ retest confirmation may contain useful information | Low-medium; sample too small |
| Genuine downside VRP, PIT revisions and correlation/dispersion may improve the model | Research hypothesis |
| Any current leveraged entry is justified by the rebuilt evidence | No |

---

## 15. Source register

### Internal reproducible evidence

- GitHub workflow artifact: `market-bottom-recovery-v11-validation-29904424650`
- GitHub workflow artifact: `market-bottom-late-stage-v14-29892427629`
- GitHub workflow artifact: `market-bottom-orthogonal-v16-29901410362`
- GitHub workflow artifact: `market-bottom-stress-maturity-v18-29903164618`
- GitHub workflow artifact: `market-bottom-sector-internal-v19-29904163231`
- IBKR five-year daily RTH histories, snapshots and corporate actions
- Repository modules under `research/market-bottom/`

### Official and primary external sources

- OFR Financial Stress Index: https://www.financialresearch.gov/financial-stress-index/
- OFR Short-term Funding Monitor API/documentation: https://www.financialresearch.gov/short-term-funding-monitor/
- Cboe VIX methodology and historical data: https://www.cboe.com/tradable_products/vix/
- Cboe implied dispersion (DSPX): https://www.cboe.com/us/indices/dashboard/DSPX/
- Direxion QQQE: https://www.direxion.com/product/nasdaq-100-equal-weighted-index-etf
- Invesco RSP: https://www.invesco.com/us/financial-products/etfs/product-detail?productId=RSP
- State Street XSD: https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-semiconductor-etf-xsd
- iShares SOXX: https://www.ishares.com/us/products/239705/SOXX
- ProShares SSO: https://www.proshares.com/our-etfs/leveraged-and-inverse/sso
- ProShares QLD: https://www.proshares.com/our-etfs/leveraged-and-inverse/qld
- ProShares USD: https://www.proshares.com/our-etfs/leveraged-and-inverse/usd
- SIA semiconductor market data: https://www.semiconductors.org/data-resources/market-data/
- WSTS: https://www.wsts.org/
- Bekaert and Hoerova, *The VIX, the Variance Premium and Stock Market Volatility*: https://www.nber.org/papers/w18995
- Bollerslev, Todorov and Xu, *Tail Risk Premia and Return Predictability*: https://doi.org/10.1016/j.jfineco.2015.02.010

---

## Final decision

The rebuilt evidence does **not** support making the monitor more aggressive today.

It supports making the monitor more honest and more regime-aware:

- ordinary correction → bounded staged participation;
- local recovery → describe it, do not call it a cycle bottom;
- structural bear → reserve capital and demand independent evidence;
- leverage → blocked until both the underlying and the actual product pass.

No order is created or transmitted.
