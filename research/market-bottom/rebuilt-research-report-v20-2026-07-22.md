# Rebuilt market-bottom monitor research report v2.0

**Date:** 2026-07-22  
**Primary assets:** SPY, QQQ, SOXX  
**Reference asset:** SMH, informational only  
**Tactical products reviewed:** SSO, QLD, USD  
**Validated research head:** `542188223ff24ff4ded8db38475ddf31b6665e6c`  
**Recent validation window:** 2021-07-26 through 2026-07-21  
**Evidence manifest:** `rebuild-audit-v20-2026-07-22.json`

## 1. Executive conclusion

This report was rebuilt from the underlying code, current GitHub Actions artifacts, a fresh Interactive Brokers boundary check, actual leveraged-product histories and official source documentation. The previous narrative was used only as a checklist of claims to re-examine.

The central conclusion is narrower and more defensible than the original objective:

> **The current engine is suitable as a bounded staged-drawdown participation model and a reporting framework for local recovery. It is not validated as a precise final-cycle-bottom detector for QQQ or SOXX.**

The production decision is therefore:

- retain the causal v1.1 price engine for small, bounded staged participation;
- retain the v1.5 separation between participation, local swing recovery and cycle-bottom evidence;
- do not promote a new QQQ or SOXX catch-up rule;
- do not promote any moving-average, breadth, financial-stress, funding, volatility, sector-internal or SMH-paired rule as a standalone bottom trigger;
- do not activate SSO, QLD or USD from the current research;
- continue to treat SMH as an informational semiconductor cross-check with production weight zero;
- treat SOXX→USD as a **cross-index tactical proxy**, not a same-benchmark leveraged mapping.

No order was created or transmitted.

---

## 2. What changed relative to the previous report

| Classification | Finding |
|---|---|
| **Retained** | Signals use completed close `t`; conceptual executions occur at next regular-session open `t+1` plus configured costs. Missed/no-trade episodes remain in the denominator. |
| **Retained** | SPY staging is materially closer to the eventual trough than QQQ or SOXX, but it is not exact-bottom timing. |
| **Retained** | QQQ and SOXX V-shaped catch-up rules remain rejected. |
| **Retained** | SMH remains reference-only; no independent tranche and no double-counting of semiconductor capital. |
| **Retained** | Participation, local swing recovery and cycle-bottom confirmation must remain separate questions. |
| **Updated** | Every major study was rerun on the current branch: recovery/catch-up v1.2, SMH/SOXX pairing, late-stage v1.4, orthogonal proxies v1.6, stress maturity v1.8, sector internals v1.9 and actual-product leverage mapping v2.0. |
| **Updated** | Interactive Brokers reconfirmed the 2026-07-21 completed RTH closes and the 2024-03-07 SOXX 3-for-1 split boundary. |
| **Updated** | Current delayed pre-market context shows realised volatility above implied volatility for QQQ, SOXX, SMH and USD, with very high IV percentiles in semiconductor assets. This is risk context, not bottom evidence. |
| **Corrected** | Positive 63- or 126-session returns after an early entry do not prove bottom precision. They show eventual recovery, which is a different objective. |
| **Corrected** | `cumulative_model_deployment` is simulated strategy state, not evidence that the user received or executed an earlier tranche. |
| **Corrected** | OFR FSI and preliminary repo histories can be revised. Publication lags and release vintages must be respected; a current revised history is not a point-in-time production dataset. |
| **Corrected** | Fixed current constituent panels and equal-weight ETFs are research proxies, not historical point-in-time breadth. |
| **Corrected** | SOXX tracks the NYSE Semiconductor Index while USD targets 2x the daily Dow Jones U.S. Semiconductors Index. A USD-minus-2x-SOXX gap is not USD tracking error. |
| **New** | Actual SSO, QLD and USD adjusted price histories were used to audit daily mapping and tactical trades. |
| **New** | The report introduces an explicit evidence-grade and production-authority matrix. |
| **New** | The highest-value remaining research is ranked by empirical value and data-governance difficulty rather than by ease of obtaining another public proxy. |

---

## 3. Source hierarchy and reproducibility

### 3.1 Source order

1. **Interactive Brokers:** completed-RTH boundary, current delayed snapshot context and corporate-action checks.
2. **Deterministic GitHub Actions:** current-branch code, tests, data audits, signal generation and numerical outputs.
3. **Official sources:** issuer benchmark definitions, daily leveraged objectives, OFR release policy and Cboe index-history availability.
4. **Audited public adjusted OHLCV:** reproducible long-history calculations in the public repository.
5. **Research proxies:** explicitly prevented from direct production promotion where historical membership, immutable vintages or authorised bulk histories are unavailable.

### 3.2 Current successful reruns

| Study | GitHub run | Artifact SHA-256 | Result |
|---|---:|---|---|
| Recovery/catch-up v1.2 and paired semiconductor | `29908981946` | `b2e3ec51...` / `47a82278...` | Success |
| Regime-aware late-stage v1.4 | `29908981897` | `1ea5c6ab...` | Success |
| Orthogonal proxies v1.6 | `29908981959` | `92bbc830...` | Success |
| Corrected stress maturity v1.8 | `29908981967` | `09e1ea79...` | Success |
| Sector internals v1.9 | `29908981896` | `4c1fe26b...` | Success |
| Actual-product leverage mapping v2.0 | `29908982024` | `7967e4db...` | Success |

The full artifact identifiers and hashes are preserved in `rebuild-audit-v20-2026-07-22.json`.

### 3.3 Causal controls retained

The core engine:

- uses completed information at close `t`;
- executes at open `t+1`;
- charges 1 bp transaction cost plus 2 bps slippage for staged underlying entries;
- does not use future prices to construct signals;
- evaluates episodes with no trade;
- caps individual tranches and cumulative deployment;
- applies exhaustion and confirmation bonuses only on transitions;
- retains a 252-session evaluation tail for bottom labels.

For model selection, the current walk-forward framework requires a purge at least as long as the 252-session label tail. Dense five-year rolling tests are explicitly dependent diagnostics, not independent PBO evidence. Formal CSCV/PBO remains blocked unless at least eight non-overlapping outer OOS partitions survive.

---

## 4. Current IBKR boundary and market context

### 4.1 Latest completed RTH bar used for official state

| Asset | Open | High | Low | Close | Corporate-action note |
|---|---:|---:|---:|---:|---|
| SPY | 746.29 | 749.04 | 744.18 | **748.28** | None in five-year audit window |
| QQQ | 706.59 | 710.05 | 702.80 | **708.97** | None in five-year audit window |
| SOXX | 549.10 | 555.16 | 540.15 | **552.69** | 3-for-1 split on 2024-03-07 |
| SMH | — | — | — | **584.08** | Reference-only |

The completed-bar date is **2026-07-21**. Public adjusted closes and IBKR closes matched well within the 20 bp audit tolerance.

### 4.2 Delayed 2026-07-22 pre-market context

| Asset | Delayed last | 30-day historical volatility | Underlying implied volatility | IV percentile |
|---|---:|---:|---:|---:|
| SPY | 746.79 | 16.89% | unavailable in snapshot | 46.61% |
| QQQ | 704.83 | 29.27% | 23.64% | 84.06% |
| SOXX | 542.30 | 74.94% | 63.12% | 96.41% |
| SMH | 572.75 | 63.34% | 55.38% | 92.43% |
| SSO | 67.15 | 31.95% | 26.40% | 43.82% |
| QLD | 87.86 | 58.54% | 45.91% | 80.48% |
| USD | 87.28 | 114.30% | 106.81% | 97.21% |

Interpretation:

- semiconductor and leveraged-semiconductor volatility remains extreme;
- realised volatility exceeding implied volatility does not establish exhaustion;
- a sharp rebound in this environment can still be an intermediate bear-market rally;
- these snapshots are context only and cannot overwrite the completed-close official state.

---

## 5. Baseline monitor: what it actually does well and poorly

### 5.1 Recent-window results

| Asset | Complete episodes | Missed rate | Mean first entry above eventual trough | Mean weighted entry distance | Mean worst additional downside | Mean sessions before trough | Mean 63-day return after first entry | Entry later suffered >10% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SPY | 7 | 0.00% | **6.58%** | **5.41%** | **-5.28%** | 30.29 | +7.74% | 28.57% |
| QQQ | 6 | 0.00% | **12.49%** | **9.48%** | **-9.48%** | 53.33 | +5.62% | 33.33% |
| SOXX | 6 | 0.00% | **18.96%** | **16.52%** | **-11.42%** | 61.67 | +24.58% | 33.33% |

### 5.2 Interpretation by asset

#### SPY — retained, with narrower language

SPY passed the asset-specific staging precision screen used in the v1.2 research. Its first entry was, on average, 6.58% above the eventual trough and the weighted entry was 5.41% above the trough.

This supports:

- small staged participation during qualifying drawdowns;
- explicit acknowledgement that entries often occur roughly a month before the final trough;
- no claim of exact-bottom identification;
- no automatic leverage activation.

The proposed 2% SPY post-threshold catch-up remains **research-only**, not a production tranche.

#### QQQ — too early for a close-to-bottom claim

QQQ participated in every recent complete episode, but the first entry was on average 12.49% above the eventual trough and approximately 53 sessions early. A one-third false-start rate above the 10% adverse threshold is material.

Therefore:

- small early staging can remain a participation tool;
- the model must not describe State 2 or simulated deployment as close-to-bottom confirmation;
- no V-shaped catch-up is authorised;
- later confirmation candidates remain research watch only.

#### SOXX — useful for staged exposure, not bottom precision

SOXX first entries averaged 18.96% above the eventual trough and about 62 sessions early. The high 63-day mean return reflects powerful eventual sector rebounds; it does **not** offset the poor bottom proximity or prove that the entry was close to the final low.

Therefore:

- the current price engine cannot be marketed as a final semiconductor-cycle-bottom detector;
- a rebound cannot create a catch-up tranche;
- a larger action requires independent evidence about the semiconductor cycle, not just a price recovery;
- USD remains blocked.

---

## 6. Recovery and catch-up reconstruction

| Asset | Rebuilt decision | Key evidence | Production authority |
|---|---|---|---|
| SPY | Research-only catch-up candidate | Full-history catch-up quality and missed-alert resilience passed the diagnostic gate | None |
| QQQ | Reject current post-threshold catch-up | Catch-up entry 11.25% above trough; mean 63-day return -5.14% | None |
| SOXX | Reject current post-threshold catch-up | Fewer than three full-history catch-ups; missed-alert catch-up 30.76% above trough with -17.84% additional downside | None |

A critical governance rule is retained:

> Model-simulated deployment must be shown separately from actual confirmed deployment and current action.

The model cannot assume that a user received or executed an earlier alert merely because the historical ledger contains a trade.

---

## 7. Late-stage price confirmation: v1.4 rerun

### 7.1 QQQ

| Candidate | Recent trades | Missed rate | Entry above trough | Additional downside | 63-day return | Decision |
|---|---:|---:|---:|---:|---:|---|
| Regime exhaustion reclaim | 2 | 66.67% | 22.38% | -15.88% | -7.39% | Reject |
| Regime retest confirm | 2 | 66.67% | 11.70% | -8.00% | +23.23% | Research watch only; sample inadequate |
| Regime strong confirm | 2 | 66.67% | 22.81% | -16.26% | -5.55% | Reject |
| Regime dual path | 4 | 33.33% | 18.47% | -9.52% | +6.13% | Reject |

The QQQ retest path is the least-bad late-stage candidate, but two recent trades and inadequate paired evidence are insufficient. It cannot create or enlarge a production tranche.

### 7.2 SOXX

| Candidate | Recent trades | Missed rate | Entry above trough | Additional downside | 63-day return | Decision |
|---|---:|---:|---:|---:|---:|---|
| Regime exhaustion reclaim | 2 | 66.67% | 41.72% | -15.26% | +0.22% | Reject |
| Regime retest confirm | 1 | 83.33% | 45.05% | -31.06% | -11.24% | Reject |
| Regime strong confirm | 3 | 50.00% | 32.94% | -20.16% | -8.07% | Reject |
| Regime dual path | 2 | 66.67% | 38.12% | -13.64% | +2.97% | Reject |

Conventional late-stage price confirmation still identified sector rallies far above a later trough. No v1.4 SOXX rule survives.

---

## 8. Orthogonal proxy families: v1.6 rerun

The following deliberately different families were tested:

- equal-weight versus cap-weight breadth: RSP/SPY, QQQE/QQQ and XSD/SOXX;
- credit appetite: HYG/IEF;
- broad volatility and term structure: VIX, VXN and VIX3M;
- relative strength: QQQ/SPY and SOXX/QQQ;
- combined multi-factor variants.

### Key results

| Candidate | Recent trades | Missed rate | Entry above trough | Additional downside | 63-day return | Decision |
|---|---:|---:|---:|---:|---:|---|
| QQQ breadth + credit | 1 | 83.33% | 7.11% | -6.64% | +8.11% | Interesting single observation; insufficient |
| SOXX equal-weight breadth reversal | 2 | 66.67% | 52.28% | -34.28% | -14.68% | Actively misleading |
| SOXX multi-factor proxy | 2 | 66.67% | 43.50% | -30.25% | -9.20% | Reject |

Conclusion:

- equal-weight breadth is useful for describing rebound participation;
- a broad semiconductor rebound can occur in the middle of a longer decline;
- ETF ratio proxies are not historical point-in-time constituent breadth;
- no v1.6 family is retained as a standalone entry trigger.

---

## 9. Financial, funding and volatility stress: v1.8 rerun

### 9.1 Data governance

The study used:

- OFR Financial Stress Index and its category components;
- SOFR average, 1st percentile and 99th percentile;
- BGCR;
- DVP repo rates and volume;
- primary-dealer fails to deliver;
- VIX, VIX3M, VIX9D, VVIX, VXN and MOVE.

Conservative availability lags were applied: one business day for SOFR/BGCR/DVP, and two business days for dealer fails and OFR FSI.

However:

- OFR states that preliminary repo series may be revised before a final quarterly release;
- the current public FSI history is not an immutable release-vintage archive;
- OFR published a 2026 correction to several FSI dates;
- therefore the current history is a high-quality official research source, but not a complete point-in-time production dataset.

### 9.2 Corrected stress-maturity results

| Asset / candidate | Recent trades | Missed rate | Entry above trough | Additional downside | 63-day return | Decision |
|---|---:|---:|---:|---:|---:|---|
| SPY mature FSI | 2 | 71.43% | 19.30% | -16.03% | -3.18% | Reject |
| QQQ mature FSI | 3 | 50.00% | 22.39% | -10.59% | -0.24% | Reject |
| QQQ mature funding/composite | 2 | 66.67% | 24.53% | -17.18% | -7.65% | Reject |
| SOXX mature FSI | 2 | 66.67% | 52.27% | -34.27% | -16.07% | Reject |
| SOXX mature funding/composite | 1 | 83.33% | 50.32% | -33.48% | -8.36% | Reject |

Broad financial stress can peak and normalise before the final QQQ or semiconductor trough. These series remain valuable for systemic-risk context and leverage vetoes, but not as standalone bottom triggers.

---

## 10. Cross-sectional sector internals: v1.9 rerun

### 10.1 Research panels

- SPY: nine long-running sector ETFs.
- QQQ: a fixed panel of current long-history mega-cap and technology leaders.
- SOXX: a fixed panel of long-history semiconductor companies.

The QQQ and SOXX panels are explicitly survivorship-biased discovery proxies. Production promotion would require historical membership known at each date.

### 10.2 Results

| Candidate | Recent trades | Missed rate | Entry above trough | Additional downside | 63-day return | Decision |
|---|---:|---:|---:|---:|---:|---|
| QQQ internal breadth thrust / dispersion | 1 | 83.33% | 9.33% | -5.60% | +4.62% | One acceptable path; insufficient |
| SOXX internal breadth thrust | 2 | 66.67% | 52.27% | -34.28% | -16.07% | Reject |
| SOXX dispersion normalisation | 1 | 83.33% | 47.99% | -32.43% | -8.11% | Reject |
| SOXX internal divergence | 0 | 100% | n/a | n/a | n/a | No usable signal |

The SOXX result is important: the failure is not merely cap-weight concentration. A broad set of semiconductor stocks can rebound together while the sector remains well above a later cycle low.

Internal breadth and dispersion can grade the quality of a local rebound. They do not establish final cycle-bottom completion.

---

## 11. SMH as a semiconductor cross-check

### 11.1 Full history: 16 complete SOXX episodes

| Variant | Trades | Within 5% | Within 8% | Weighted distance | Worst additional downside |
|---|---:|---:|---:|---:|---:|
| SOXX only | 57 | 68.75% | 81.25% | 13.448% | -11.164% |
| SMH confirmation veto/gate | 57 | 68.75% | 81.25% | 13.448% | -11.164% |
| SMH soft confirm | 55 | 62.50% | 81.25% | 13.597% | -11.869% |
| SMH veto-only / hard confirm | 58 | 68.75% | 81.25% | 13.395% | -11.164% |

The apparent full-history improvement from broad veto/hard confirmation was only approximately 0.054 percentage points.

### 11.2 Post-2024: five complete episodes

| Variant | Trades | Within 5% | Within 8% | Weighted distance | Worst additional downside |
|---|---:|---:|---:|---:|---:|
| SOXX only | 15 | 80.00% | 80.00% | 9.892% | -6.324% |
| SMH confirmation veto/gate | 15 | 80.00% | 80.00% | 9.892% | -6.324% |
| SMH soft confirm | 14 | 60.00% | 80.00% | 10.944% | -8.580% |
| SMH veto-only / hard confirm | 14 | 80.00% | 80.00% | 10.317% | -6.324% |

The small apparent full-history gain did not persist. The production decision remains:

- SMH is displayed as a second semiconductor coordinate;
- SMH may affect narrative confidence only;
- SMH cannot create, enlarge or revoke a SOXX tranche;
- SMH cannot independently authorise USD;
- production weight remains zero.

---

## 12. Actual leveraged-product audit: new v2.0 evidence

### 12.1 Official benchmark mapping

Official issuer documentation confirms:

- SSO seeks 2x the **daily** S&P 500 return;
- QLD seeks 2x the **daily** Nasdaq-100 return;
- USD seeks 2x the **daily** Dow Jones U.S. Semiconductors Index return;
- SOXX tracks the **NYSE Semiconductor Index**.

Therefore:

- SPY→SSO and QQQ→QLD are same-benchmark-family mappings;
- SOXX→USD is a cross-index tactical proxy;
- a theoretical 2x SOXX path is not USD's stated objective.

### 12.2 Daily mapping diagnostics

| Mapping | Relationship | Daily observations | Correlation | Daily beta | Gap RMSE versus 2x signal ETF |
|---|---|---:|---:|---:|---:|
| SPY→SSO | Same benchmark family | 5,050 | 0.9956 | 1.9592 | 0.231% |
| QQQ→QLD | Same benchmark family | 5,050 | 0.9960 | 1.9832 | 0.250% |
| SOXX→USD | **Cross-index proxy** | 4,896 | 0.9584 | 1.9120 | **1.148%** |

For SOXX→USD, the gap includes benchmark-composition differences, fund implementation, fees, financing, market-price noise and daily reset effects. It must not be described as product tracking error.

### 12.3 Tactical actual-product trades

| Mapping | Trades | Win rate | Mean return | Median return | Worst return | Mean MAE | Worst MAE | Mean holding days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SPY→SSO | 16 | 56.25% | +2.19% | +2.02% | -4.77% | -2.20% | -5.65% | 18.19 |
| QQQ→QLD | 17 | 58.82% | +3.44% | +0.31% | -5.16% | -3.19% | -8.60% | 11.53 |
| SOXX→USD | 31 | 48.39% | +1.38% | **-1.19%** | **-23.24%** | **-6.50%** | **-28.63%** | 10.84 |

Important limitations:

- these are full-history tactical diagnostics, not a formally selected OOS strategy;
- point-in-time breadth was unavailable in these product tests, so the optional breadth gate did not operate;
- all products have daily objectives and multi-day returns are path-dependent;
- no product mapping or leverage rule is promoted;
- the SOXX→USD tail loss is incompatible with using the current signal as a production leverage trigger.

---

## 13. Evidence-grade matrix

| Claim | Evidence grade | Production authority | Decision |
|---|---|---|---|
| Completed-close / next-open causal implementation | **A** | Yes, implementation only | Retain |
| IBKR recent boundary and corporate-action audit | **A-** | Data boundary only | Retain |
| SPY small staged participation | **B** | Existing bounded v1.1 logic only | Retain with narrower language |
| QQQ small staged participation | **B-** | Existing bounded v1.1 logic only | Retain; do not call close-to-bottom |
| SOXX small staged participation | **C+** | Existing bounded v1.1 logic only | Retain only as staged exposure |
| QQQ retest or breadth confirmation | **C** | None | Research watch |
| SOXX price confirmation | **D** | None | Reject |
| Equal-weight / ratio breadth | **C-** | None | Descriptive only |
| Fixed-panel sector breadth | **C-** | None | Descriptive only; survivorship-biased |
| OFR stress / funding normalisation | **C** | Veto/context only | No entry trigger |
| SMH paired rule | **C** | Narrative confidence only | No sizing or trade authority |
| SSO / QLD actual-product tactical mapping | **C** | None | Continue research |
| USD actual-product tactical mapping | **D+** | None | Block; cross-index and severe tail loss |
| Genuine model-free downside VRP | **Unbuilt** | None | High-priority future gate |
| PIT earnings-revision and semiconductor-cycle breadth | **Unbuilt** | None | High-priority future gate |

Grades describe the strength of evidence for this monitor, not the general validity of each financial indicator.

---

## 14. Final production specification

### 14.1 Universal rules

1. Official state uses completed RTH close data only.
2. Intraday, overnight and pre-market information is context only.
3. The v1.1 engine can produce bounded staged-participation candidates.
4. The v1.5 taxonomy remains reporting-only:
   - participation status;
   - local swing status;
   - cycle-bottom status.
5. Local swing recovery is not cycle-bottom confirmation.
6. Model-simulated deployment, actual confirmed deployment and current action must be displayed separately.
7. No alternative proxy can create or size a trade unless it passes point-in-time provenance and identical-fold validation.
8. No leverage product is activated by drawdown, high IV percentile, breadth reversal or a sharp rebound alone.

### 14.2 SPY

- retain small staged participation;
- retain 2% post-threshold catch-up as research-only when an earlier probe is confirmed not executed;
- do not describe the result as exact-bottom timing;
- SSO remains unavailable until a separate leverage rule survives formal OOS validation.

### 14.3 QQQ

- retain small early staging only;
- no V-shaped catch-up;
- QQQ retest/internal breadth can be displayed as a research watch, not a tranche;
- QLD remains unavailable.

### 14.4 SOXX

- retain only bounded staged exposure under the original price engine;
- no V-shaped catch-up;
- no late-stage price-only confirmation tranche;
- SMH remains informational;
- broad semiconductor breadth does not confirm the final sector trough;
- USD remains unavailable and must be labelled a cross-index proxy if discussed.

---

## 15. What the monitor should say instead of repeatedly saying “wait”

The monitor should give one of four explicit outputs:

1. **STAGED PARTICIPATION:** a bounded left-side tranche is available under the original drawdown engine.
2. **LOCAL RECOVERY WATCH:** price/internal/stress evidence is improving, but no new production tranche is authorised.
3. **LOCAL SWING RECOVERY:** the tradable rebound structure is stronger, but cycle-bottom evidence remains incomplete.
4. **CYCLE BOTTOM UNCONFIRMED:** independent evidence is missing, divergent, revised, survivorship-biased or statistically underpowered.

When earlier execution is unknown, the report must provide both paths:

- **If the earlier tranche was executed:** hold/manage according to the stored invalidation and next-stage rule.
- **If the earlier tranche was not executed:** state whether a validated catch-up exists. For QQQ and SOXX, the current answer is no.

This removes the circular logic of “wait if falling, wait if rising” without inventing an unvalidated catch-up.

---

## 16. Highest-value remaining research

Further free price proxies have low marginal value. The remaining research should prioritise data that addresses the specific failure modes found above.

### Priority 1 — historical point-in-time earnings and semiconductor cycle breadth

Required fields:

- EPS and revenue revision breadth;
- change in estimate dispersion;
- inventory days and inventory revision breadth;
- book-to-bill, order growth and cancellation indicators;
- lead times and utilisation where available;
- publication timestamps and historical constituent membership.

Why it matters: financial and funding stress can normalise before the semiconductor earnings/inventory cycle is complete.

### Priority 2 — genuine model-free downside variance risk premium

A valid VRP feature requires:

- a model-free option-strip implied variance measure;
- high-frequency intraday realised variance, preferably downside-specific;
- point-in-time option data and expiry/strike controls.

A simple underlying IV-minus-daily-HV proxy is not methodologically equivalent. The academic evidence itself depends critically on model-free implied variance and high-frequency realised variance.

### Priority 3 — authorised Cboe correlation and dispersion history

Potential features:

- COR1M / COR3M;
- DSPX / VIXEQ;
- correlation-stress peak and normalisation;
- dispersion collapse and recovery.

These may help distinguish market-wide liquidation from a cap-weighted or sector-specific rebound. Historical access must be authorised and reproducible.

### Priority 4 — authorised bulk options-flow history

Required:

- equity, index and ETP put/call ratios;
- net option premium imbalance;
- opening versus closing activity where available;
- date-stamped bulk history rather than day-by-day webpage scraping.

### Priority 5 — formal long-cycle validation

- immutable datasets;
- at least eight non-overlapping outer OOS partitions;
- same folds for price → breadth → VRP → credit → earnings ablations;
- one-standard-error selection;
- worst-regime and economic-significance gates;
- actual-product validation after the underlying signal survives.

---

## 17. Official-source register

- [OFR Financial Stress Index](https://www.financialresearch.gov/financial-stress-index/) — construction, categories, two-business-day lag and published corrections.
- [OFR U.S. Repo Markets Data Release](https://www.financialresearch.gov/short-term-funding-monitor/datasets/repo/) — preliminary/final status and release lags.
- [OFR STFM API](https://www.financialresearch.gov/short-term-funding-monitor/api/) — official machine-readable series access.
- [Cboe VIX and other volatility-index historical data](https://www.cboe.com/tradable-products/vix/vix-historical-data) — official VIX, VVIX and VIX9D history access.
- [SOXX official iShares page](https://www.ishares.com/us/products/239705/SOX) — NYSE Semiconductor Index benchmark.
- [SSO official ProShares page](https://www.proshares.com/our-etfs/leveraged-and-inverse/sso) — 2x daily S&P 500 objective and multi-day path warning.
- [QLD official ProShares page](https://www.proshares.com/our-etfs/leveraged-and-inverse/qld) — 2x daily Nasdaq-100 objective and multi-day path warning.
- [USD official ProShares page](https://www.proshares.com/our-etfs/leveraged-and-inverse/usd) — 2x daily Dow Jones U.S. Semiconductors Index objective.
- [Federal Reserve: Expected Stock Returns and Variance Risk Premia](https://www.federalreserve.gov/econres/feds/expected-stock-returns-and-variance-risk-premia.htm) — why a genuine VRP construction requires model-free implied variance and high-frequency realised variance.

---

## 18. Final retained, updated, corrected and new decisions

### Retained findings

- causal completed-close / next-open execution;
- bounded staged participation;
- SPY is the most defensible staging asset of the three;
- QQQ and SOXX catch-up rules remain rejected;
- SMH remains informational only;
- three-layer reporting taxonomy remains correct.

### Updated findings

- all numerical studies were rerun on the latest validated branch;
- latest completed RTH boundaries and SOXX split handling passed IBKR cross-checks;
- semiconductor and leveraged-semiconductor volatility remains extreme;
- no alternative family improved enough to change production.

### Corrected findings

- positive forward return is not bottom precision;
- simulated deployment is not actual execution;
- OFR current histories are not immutable vintage data;
- current-member breadth panels are not point-in-time breadth;
- SOXX→USD is not a same-index leverage mapping;
- USD gap versus theoretical 2x SOXX is not tracking error.

### Newly added insights

- actual-product leverage results show tolerable historical tails for the unpromoted SSO/QLD research, but materially worse USD tails;
- QQQ’s best late-stage and breadth observations remain underpowered rather than validated;
- SOXX’s failure persists even when a broad semiconductor panel participates in the rebound;
- the highest-value next inputs are earnings/inventory-cycle data, genuine downside VRP, and authorised correlation/dispersion histories.

## Final verdict

> **Keep the monitor active as a staged-participation and recovery-classification system. Do not call it a validated precise-bottom detector for QQQ or SOXX. Do not promote new thresholds, tranches, SMH gates or leverage rules. The next material improvement must come from point-in-time semiconductor-cycle, genuine option-variance and correlation/dispersion evidence—not another price proxy.**
