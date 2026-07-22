# Bottom monitor enhancement decision — v1.3 to v1.5

Date: 2026-07-22

## Executive decision

The monitor has been enhanced, but **no new QQQ or SOXX entry rule is promoted**.

The research establishes that one price-only rule cannot safely answer both:

1. whether to begin small staged participation during a drawdown; and
2. whether the final cycle bottom is likely complete.

The production architecture is therefore split into three independent reporting layers:

- `participation_status`: early, bounded drawdown participation;
- `local_swing_status`: completed-close evidence of a tradable local recovery;
- `cycle_bottom_status`: independent-evidence assessment of the broader cycle bottom.

The v1.1 trading engine and tranche calculations remain unchanged.  The v1.5 taxonomy has no trade authority and cannot authorise leverage.

## Data and validation boundary

- Signal time: completed regular-session close `t`.
- Execution assumption: next regular-session open `t+1` plus stored costs.
- Full history: audited public adjusted daily OHLCV for reproducibility.
- Recent boundary: 2021-07-26 through 2026-07-21.
- Recent boundary, latest completed close and SOXX split continuity were independently checked with IBKR.
- Raw licensed IBKR history was not committed to the public repository.

## Baseline problem

Recent complete episodes showed that the existing staged engine participated reliably but usually entered too early for a close-to-bottom claim:

| Asset | Complete episodes | Missed rate | Mean first entry above eventual trough | Mean additional downside after first entry | Mean 63-day forward return |
|---|---:|---:|---:|---:|---:|
| QQQ | 6 | 0.0% | 12.49% | -9.36% | 5.62% |
| SOXX | 6 | 0.0% | 18.96% | -11.30% | 24.58% |

Positive forward returns do not prove bottom precision.  They show that small staged purchases can benefit from eventual recovery.

## V1.3 — asset-specific exhaustion, retest and confirmation

Four causal candidates were tested independently for each asset:

1. exhaustion reclaim;
2. retest confirmation;
3. strong confirmation;
4. dual path.

### QQQ v1.3

| Candidate | Recent missed rate | Mean entry above eventual trough | Mean additional downside | Mean 63-day return | Promotion |
|---|---:|---:|---:|---:|---|
| Exhaustion reclaim | 66.67% | 22.38% | -15.88% | -7.39% | Rejected |
| Retest confirm | 66.67% | 11.70% | -8.00% | 23.23% | Rejected — only two recent trades and one paired episode |
| Strong confirm | 50.00% | 21.02% | -10.89% | 2.20% | Rejected |
| Dual path | 33.33% | 17.23% | -9.55% | 7.04% | Rejected |

The apparent QQQ retest result is interesting but statistically inadequate.  It cannot be promoted from two recent trades and one paired baseline comparison.

### SOXX v1.3

| Candidate | Recent missed rate | Mean entry above eventual trough | Mean additional downside | Mean 63-day return | Promotion |
|---|---:|---:|---:|---:|---|
| Exhaustion reclaim | 66.67% | 41.72% | -15.26% | 0.22% | Rejected |
| Retest confirm | 83.33% | 45.05% | -31.06% | -11.24% | Rejected |
| Strong confirm | 50.00% | 31.82% | -13.05% | 0.78% | Rejected |
| Dual path | 66.67% | 38.12% | -13.64% | 2.97% | Rejected |

SOXX price-only late confirmation was materially unsafe.  It often identified a rebound inside a longer semiconductor decline rather than the final cycle trough.

## V1.4 — regime-aware late-stage confirmation

V1.4 added an explicit distinction between ordinary corrections and falling-200DMA bear regimes.

A falling-200DMA bear candidate required:

- at least 60 sessions underwater;
- at least two prior washouts in 126 sessions;
- drawdown of at least 15% for QQQ or 25% for SOXX;
- flattening deterioration in the 200DMA slope;
- close above the 10DMA with positive 10DMA slope;
- a five-day higher low;
- realised-volatility contraction;
- no credit veto.

The filter successfully formalised bear-market maturity, but the resulting candidates still failed the asset-level promotion gate.

### QQQ v1.4

| Candidate | Recent missed rate | Mean entry above eventual trough | Mean additional downside | Mean 63-day return | P(distance improves) | Promotion |
|---|---:|---:|---:|---:|---:|---|
| Regime exhaustion reclaim | 66.67% | 22.38% | -15.88% | -7.39% | n/a | Rejected |
| Regime retest confirm | 66.67% | 11.70% | -8.00% | 23.23% | inadequate paired sample | Rejected |
| Regime strong confirm | 66.67% | 22.81% | -16.26% | -5.55% | n/a | Rejected |
| Regime dual path | 33.33% | 18.47% | -9.52% | 6.13% | 51.28% | Rejected |

### SOXX v1.4

| Candidate | Recent missed rate | Mean entry above eventual trough | Mean additional downside | Mean 63-day return | Promotion |
|---|---:|---:|---:|---:|---|
| Regime exhaustion reclaim | 66.67% | 41.72% | -15.26% | 0.22% | Rejected |
| Regime retest confirm | 83.33% | 45.05% | -31.06% | -11.24% | Rejected |
| Regime strong confirm | 50.00% | 32.94% | -20.16% | -8.07% | Rejected |
| Regime dual path | 66.67% | 38.12% | -13.64% | 2.97% | Rejected |

## Why the candidates failed

The failure is not merely a strict promotion threshold.

- QQQ price confirmation repeatedly treated bear-market rallies as cycle-bottom completion.
- SOXX rebounds were too violent and path-dependent; waiting for common moving-average confirmation frequently produced entries far above a later trough while substantial downside remained.
- Adding more price parameters reduced interpretability without producing persistent bottom-proximity improvement.
- SMH cross-confirmation had already failed to provide stable incremental value in identical-fold paired research.

## V1.5 production enhancement

V1.5 changes reporting architecture, not trading exposure.

Every official asset result now includes:

- `participation_status`;
- `local_swing_status`;
- `local_swing_votes` and component checks;
- `cycle_bottom_status`;
- independent breadth, downside-VRP and credit availability/support status;
- point-in-time provenance status;
- explicit evidence gaps;
- `trade_authority=NONE` and `leverage_authority=NONE_FROM_TAXONOMY`.

### Interpretation rules

- `STAGED_PARTICIPATION`: the drawdown engine may justify a small bounded probe.  This is not a bottom claim.
- `LOCAL_SWING_RECOVERY_WATCH`: some completed-close recovery evidence exists, but the swing is incomplete.
- `LOCAL_SWING_RECOVERY`: price structure, higher-low behaviour and realised-volatility contraction support a tradable local rebound.  This still is not a cycle-bottom claim.
- `CYCLE_BOTTOM_UNCONFIRMED_*`: price or independent evidence is incomplete or divergent.
- `CYCLE_BOTTOM_RESEARCH_CONFIRMATION_ONLY`: price plus independent evidence may be supportive, but point-in-time ablation and formal promotion remain incomplete.

The taxonomy cannot create, enlarge, revoke or validate a tranche.  It cannot activate SSO, QLD or USD.

## Production decisions by asset

### SPY

- Retain small staged participation.
- Retain the previously identified 2% post-threshold catch-up as research-only when an earlier probe was genuinely not executed.
- Do not describe it as exact-bottom timing.

### QQQ

- Keep the existing staged drawdown model for small probes only.
- Display retest confirmation as a research watch because its recent path metrics were acceptable but its sample was inadequate.
- Do not create a new tranche from v1.3 or v1.4.
- Do not permit V-shaped catch-up.
- Do not label a local recovery as a confirmed cycle bottom.

### SOXX

- No v1.3 or v1.4 candidate is retained for trade creation.
- Do not permit V-shaped catch-up.
- Require independent breadth, credit and genuine downside-VRP evidence before upgrading cycle-bottom confidence.
- SMH remains informational with production weight zero.

## Current volatility context from IBKR

At the enhancement review, QQQ and SOXX still showed realised volatility above implied volatility:

- QQQ: historical volatility about 29.5% versus underlying implied volatility about 23.7%;
- SOXX: historical volatility about 75.0% versus underlying implied volatility about 63.0%;
- SOXX 52-week IV percentile was about 96%; SMH about 98%.

This supports the decision to require realised-volatility contraction and independent evidence rather than treating a sharp rebound or high IV percentile as bottom confirmation.

## Governance status

- V1.3 hard invariants: passed.
- V1.4 regime tests and hard invariants: passed.
- Public adjusted-data audits: passed.
- IBKR recent boundary checks: passed.
- QQQ promoted late-stage rule: none.
- SOXX promoted late-stage rule: none.
- V1.5 taxonomy trade authority: none.
- Leveraged-product authority from this enhancement: none.
- Orders created or transmitted: none.

## Next empirical gate

A genuine QQQ/SOXX cycle-bottom upgrade now requires immutable point-in-time datasets and identical-fold ablation for:

1. broad-market and sector breadth;
2. genuine model-free downside variance risk premium;
3. high-yield credit and systemic stress;
4. earnings-revision breadth;
5. price recovery structure.

Until those gates pass, the monitor should report what it knows accurately: staged participation and local swing recovery, not a guaranteed or fully confirmed cycle bottom.
