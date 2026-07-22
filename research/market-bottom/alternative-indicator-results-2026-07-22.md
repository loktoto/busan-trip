# Alternative bottom-indicator research — 2026-07-22

## Executive decision

The research tested materially different indicator families rather than adding more moving-average variants.  **No new SPY, QQQ or SOXX entry rule is promoted.**

The negative result is informative:

- equal-weight breadth can improve during an intermediate bear-market rally;
- broad financial, funding and volatility stress can peak and normalise well before the final equity trough;
- a fixed semiconductor-stock panel can rebound broadly while SOXX remains far above a later cycle low;
- public put/call history is not available in a verified bulk format suitable for the production pipeline;
- SKEW, VIX9D and VVIX have usable public histories, but they remain sentiment/stress context rather than validated bottom triggers.

The existing production architecture remains correct:

1. small staged drawdown participation;
2. separate local-swing recovery classification;
3. cycle-bottom confirmation withheld until independent, point-in-time feature families pass identical-fold validation.

No automation threshold, tranche size or leverage rule changed as a result of this research.

## Data and causality

- Primary targets: SPY, QQQ and SOXX.
- SMH: informational semiconductor reference only, production weight zero.
- Signal time: completed regular-session close `t`.
- Conceptual execution: next regular-session open `t+1` plus stored transaction costs and slippage.
- Recent validation window: 2021-07-26 through 2026-07-21.
- Recent boundary, completed closes and SOXX corporate-action continuity were independently checked with IBKR.
- Public adjusted histories were used for reproducibility; raw licensed IBKR history was not committed to the public repository.
- Every public proxy family is blocked from direct production promotion when point-in-time provenance, historical membership or release vintages are unavailable.

## V1.6 — breadth, credit appetite and broad volatility

### Indicator families

- SPY breadth proxy: RSP/SPY.
- QQQ breadth proxy: QQQE/QQQ.
- SOXX breadth proxy: XSD/SOXX.
- Credit appetite: HYG/IEF.
- Volatility normalisation: VIX or VXN and term-structure context.
- Relative strength: QQQ/SPY or SOXX/QQQ.

### Result

No family passed the research-retention gate.

The only superficially interesting recent result was `QQQ_BREADTH_CREDIT`:

- one recent trade;
- entry about 7.11% above the eventual trough;
- additional downside about -6.64%;
- 63-session return about +8.11%;
- missed five of six recent complete QQQ episodes.

The sample was too sparse for paired bootstrap evidence or promotion.

For SOXX, the equal-weight semiconductor proxy was actively misleading:

- `SOXX_BREADTH_REVERSAL` entered about 52.28% above the eventual trough;
- additional downside was about -34.28%;
- 63-session return was about -14.68%.

**Decision:** equal-weight breadth is retained as a descriptive measure of rebound participation, not as a bottom-completion trigger.

## V1.7 — official financial, funding and volatility stress

### Official/public sources discovered

#### OFR Financial Stress Index

The direct OFR CSV contains:

- total OFR FSI;
- Credit;
- Equity valuation;
- Safe assets;
- Funding;
- Volatility;
- United States;
- Other advanced economies;
- Emerging markets.

The series begins in 2000 and is shifted by two business sessions before strategy use.  The public file is current revised history, not an immutable release-vintage archive.

#### OFR Short-term Funding Monitor

Official API series included:

- SOFR average: `FNYR-SOFR-A`;
- SOFR first percentile: `FNYR-SOFR_1Pctl-A`;
- SOFR 99th percentile: `FNYR-SOFR_99Pctl-A`;
- BGCR: `FNYR-BGCR-A`;
- DVP overnight/open repo rate: `REPO-DVP_AR_OO-P`;
- DVP overnight/open repo volume: `REPO-DVP_OV_OO-P`;
- primary-dealer total fails to deliver: `NYPD-PD_AFtD_TOT-A`;
- corporate fails to deliver: `NYPD-PD_AFtD_CORS-A`.

Conservative strategy-availability lags were applied:

- one business session for SOFR, BGCR and DVP repo data;
- two business sessions for dealer fails;
- two business sessions for OFR FSI.

#### Volatility stack

Usable public histories were confirmed for:

- VIX;
- VIX3M;
- VIX9D;
- VVIX;
- VXN;
- MOVE;
- SKEW.

### V1.7 candidate construction

- FSI peak normalisation;
- volatility-stack peak normalisation using VIX9D/VIX, VIX/VIX3M, VVIX/VIX, VXN/VIX and MOVE;
- funding-stress peak normalisation using SOFR transaction dispersion, repo-rate bases, repo-volume shock and dealer fails;
- composite requiring at least two independent families.

### V1.7 defect

The first implementation measured `sessions_since_breach` from the latest day that price remained below the watch threshold, so the counter reset to zero repeatedly inside a long drawdown.  It did not measure time since the initial threshold transition.

V1.7 is therefore explicitly **invalidated for promotion**, despite its hard tests and data downloads succeeding.

## V1.8 — corrected breach age and bear-cycle maturity

V1.8 corrected breach-age accounting:

- breach age starts only when price transitions through the drawdown threshold;
- same-day threshold breach and confirmation is prohibited;
- ambiguous transition regimes are blocked;
- falling-200DMA bear regimes require a deeper drawdown, at least 90 sessions underwater, at least two prior independent stress-normalisation events, two currently supportive stress families and a flattening 200DMA decline.

### SPY v1.8

| Candidate | Recent missed rate | Mean entry above trough | Additional downside | 63-session return | Decision |
|---|---:|---:|---:|---:|---|
| Mature FSI | 71.43% | 19.30% | -16.03% | -3.18% | Reject |
| Mature funding/composite | Higher/similarly sparse | Worse than baseline | Materially adverse | Non-positive | Reject |

### QQQ v1.8

| Candidate | Recent missed rate | Mean entry above trough | Additional downside | 63-session return | Decision |
|---|---:|---:|---:|---:|---|
| Mature FSI | 50.00% | 22.39% | -10.59% | -0.24% | Reject |
| Mature funding/composite | 66.67% | 24.53% | -17.18% | -7.65% | Reject |
| Mature volatility | No recent trades | n/a | n/a | n/a | Reject / insufficient |

### SOXX v1.8

| Candidate | Recent missed rate | Mean entry above trough | Additional downside | 63-session return | Decision |
|---|---:|---:|---:|---:|---|
| Mature FSI | 66.67% | 52.27% | -34.27% | -16.07% | Reject |
| Mature funding/composite | 83.33% | 50.32% | -33.48% | -8.36% | Reject |
| Mature volatility | No trades | n/a | n/a | n/a | Reject / insufficient |

**Decision:** broad financial and funding stress normalisation can identify an intermediate bear-market rally.  These families may be used as veto/confidence context, but not as standalone bottom triggers.

## V1.9 — cross-sectional sector and semiconductor internals

### Fixed research panels

#### SPY

Nine long-running sector ETFs:

`XLB, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY`

#### QQQ

Fixed current-leader panel:

`AAPL, MSFT, AMZN, NVDA, GOOGL, META, AVGO, COST, NFLX, TSLA, AMD, QCOM`

#### SOXX

Fixed long-history semiconductor panel:

`AMD, INTC, NVDA, TXN, QCOM, AMAT, LRCX, KLAC, MU, ADI, MCHP, MRVL, ON`

The QQQ and SOXX panels have explicit survivorship bias.  They are discovery tools only.

### Internal features

- percentage above 20DMA;
- percentage above 50DMA;
- percentage with positive five-session return;
- percentage making a fresh 20-session low;
- median five-session return;
- cross-sectional five-session return dispersion and causal z-score;
- breadth thrust after an internal washout;
- dispersion normalisation after a dispersion spike;
- positive breadth divergence near the ETF low;
- multi-family confirmation.

The ordinary-correction path required price above the 200DMA **and** a non-negative 200DMA slope.  Ambiguous transition regimes were blocked.  Bear-regime candidates required a deep drawdown, at least 90 sessions underwater, a flattening 200DMA decline and at least two internal repair families.

### SPY v1.9

All internal candidates were too sparse and materially late/unsafe.  The diagnostic dispersion candidate still had:

- recent missed rate about 71.43%;
- entry about 20.94% above the eventual trough;
- additional downside about -10.17%;
- 63-session return about -2.12%.

### QQQ v1.9

The breadth-thrust and dispersion candidates produced the same single recent trade:

- recent missed rate: 83.33%;
- entry about 9.33% above the eventual trough;
- additional downside about -5.60%;
- 63-session return about +4.62%;
- trade occurred eight sessions after the trough.

The path quality was acceptable, but one trade cannot establish a feature family.  Full-history missed rates were 70%–80%, and paired bootstrap evidence was unavailable.

### SOXX v1.9

| Candidate | Recent missed rate | Mean entry above trough | Additional downside | 63-session return | Decision |
|---|---:|---:|---:|---:|---|
| Internal breadth thrust | 66.67% | 52.27% | -34.27% | -16.07% | Reject |
| Internal dispersion normalisation | 83.33% | 47.99% | -32.43% | -8.11% | Reject |
| Internal divergence | 100% | n/a | n/a | n/a | No usable signals |
| Internal multi-family | 83.33% | 47.99% | -32.43% | -8.11% | Reject |

**Key conclusion:** the SOXX problem is not only cap-weight concentration.  A broad set of semiconductor stocks can rebound together during the middle of a longer sector decline.  Internal breadth and dispersion describe rebound quality but still do not establish final cycle-bottom completion.

## Options-sentiment source discovery

### Verified

The official Cboe daily statistics page can return historical daily values by date for:

- total put/call ratio;
- index put/call ratio;
- exchange-traded-products put/call ratio;
- equity put/call ratio;
- VIX put/call ratio.

Sample historical dates from 2019, 2020, 2022, 2024 and 2025 were parsed successfully.

### Not verified for bulk research use

- No bulk CSV/download link was present on the historical daily pages.
- Yahoo symbols `^CPC`, `^CPCE` and `^CPCI` were unavailable.
- Date-by-date scraping is not accepted as a production data pipeline.

Therefore put/call ratios remain an event-study candidate unless an authorised bulk historical dataset is obtained.

Public daily histories were confirmed for:

- `^SKEW`;
- `^VIX9D`;
- `^VVIX`.

SKEW can be tested as a tail-hedging context feature, but it should not be assumed to be monotonic fear: extreme SKEW can occur in otherwise calm markets and may collapse during immediate panic.

## What the evidence now supports

### Retain as descriptive or veto features

- equal-weight/cap-weight breadth;
- cross-sectional internal breadth;
- dispersion level and normalisation;
- OFR FSI and category stress;
- funding-market stress;
- volatility term structure;
- SMH/SOXX divergence;
- SKEW and options-sentiment context when reliable data is available.

These can lower confidence, flag a local swing recovery or veto leverage.  They have not passed as standalone trade triggers.

### Do not use as standalone bottom triggers

- V-shaped rebound;
- simple moving-average reclaim;
- equal-weight breadth reversal;
- semiconductor-panel breadth thrust;
- broad FSI peak and decline;
- repo/funding stress decline;
- high IV percentile;
- a single put/call extreme;
- one isolated QQQ breadth/retest observation.

## Highest-value remaining empirical gates

The remaining promising sources are not safely replaceable with casual public proxies:

1. **Historical point-in-time semiconductor membership and constituent breadth** — removes current-survivor bias.
2. **Cboe correlation and dispersion histories** — COR1M/COR3M and DSPX/VIXEQ, obtained through an authorised historical dataset rather than scraping a streaming feed.
3. **Genuine model-free downside variance risk premium** — option-strip implied downside variance versus high-frequency realised downside variance.
4. **Historical point-in-time earnings-revision breadth** — especially semiconductor revenue/EPS revisions and estimate dispersion.
5. **Authorised bulk options-flow history** — equity/index/ETP put-call ratios and net option-premium imbalance.
6. **Semiconductor inventory/order-cycle data** — book-to-bill, inventories, lead times and revision breadth, aligned to publication dates.

These features should be evaluated as identical-fold ablations on top of the existing price engine.  They should not be substituted with present-day holdings or unreproducible screenshots.

## Governance status

- V1.6 orthogonal-proxy CI: passed.
- V1.7 official-source discovery and payload inspection: passed.
- V1.7 preliminary stress results: invalidated for promotion by breach-age accounting defect.
- V1.8 corrected stress-maturity tests and validation: passed; no family retained.
- V1.9 sector-internal tests, data retrieval and validation: passed; no family retained.
- IBKR recent boundary and corporate-action audit: passed.
- Production threshold changes: none.
- Production tranche changes: none.
- Leverage changes: none.
- Orders created or transmitted: none.
