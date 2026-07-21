# Backtest Results and Research Audit

> Classification: **PROVISIONAL / NOT YET INDEPENDENTLY REPRODUCED**  
> Primary objective: bottom proximity and additional-downside control, not CAGR maximisation.

## 1. What was tested

The research compared variants of:

- fixed drawdown ladders;
- cycle drawdown from an unresolved peak;
- volatility-normalized drawdown;
- nonlinear back-loaded deployment curves;
- fresh 10/20-session lows;
- cooldown and previous-entry price spacing;
- RSI as a throttle;
- downside-volume shock and deceleration;
- crash overrides;
- 200-day trend / long-bear throttles;
- underwater duration;
- early micro-probes for V-shaped recoveries;
- confirmation overlays for tactical leverage.

Signals were intended to be calculated after the close and executed at the next session's open. Drawdown episodes were clustered so repeated daily signals inside one correction were not treated as independent successes.

A research run reported approximately **34,516 model/period evaluations**. The full parameter grid and raw output were not persisted into this repository, so the count and the summary tables below should be treated as an audit trail of the research process, not as a reproducible final certification.

## 2. Evaluation metrics

The strategy was evaluated primarily on:

- distance from entry to the minimum adjusted close over the following 42, 63 and 84 sessions;
- whether at least one tranche was within 3%, 5% or 8% of the later trough;
- capital-weighted average entry distance from the trough;
- maximum additional downside after entry;
- days from entry to trough;
- missed-bottom rate;
- false-bottom frequency;
- repeated signals per drawdown episode;
- cumulative reserved capital deployed near the trough;
- unused capital preserved during long bear markets.

## 3. SPY / QQQ price-layer snapshot

### Reported holdout composition

The final research summary described a holdout containing:

- 5 completed SPY drawdown episodes;
- 6 completed QQQ drawdown episodes;
- 11 total episodes.

The exact train/holdout date split was described inconsistently during the iterative research. Consequently, the following numbers are preserved as **reported holdout snapshots**, not as a fully reproducible untouched holdout claim.

### Reported results — meaningful-deployment version

| Metric | Reported result |
|---|---:|
| At least one tranche within 8% of later trough | 11 / 11 (100%) |
| At least one tranche within 5% of later trough | 8 / 11 (72.7%) |
| Capital-weighted average entry within 8% | 9 / 11 (81.8%) |
| Capital-weighted average entry within 5% | 7 / 11 (63.6%) |

Approximate Wilson 95% confidence intervals reported during the research:

| Observation | Approximate interval |
|---|---:|
| 11 / 11 at least one tranche within 8% | 74%–100% |
| 9 / 11 weighted average within 8% | 52%–95% |
| 7 / 11 weighted average within 5% | 35%–85% |

### Interpretation

- The price layer appeared effective at placing **at least one small tranche** reasonably near a later trough.
- It was less reliable at placing a **substantial capital-weighted average cost** within 5% of the trough.
- Sample size was small and the confidence intervals were wide.
- The 2022-style slow repricing bear market remained the largest failure mode.

## 4. Early micro-probe version

A conservative seed version reportedly placed at least one tranche within 3%/5%/8% in every holdout episode, but average deployed capital was only around 2%–3% of the reserved sleeve.

This was not considered a complete solution because it mostly proved that a tiny probe can be placed near many troughs. It did not solve the harder problem of deploying meaningful capital near the low.

## 5. Long-bear stress tests

### Initial fixed-ladder weakness

Simple four-level drawdown ladders performed acceptably in ordinary corrections but deployed too early in dot-com and GFC-type declines. The initial long-bear stress test reported capital-weighted average costs approximately **43%–48% above the eventual trough**.

### Back-loaded improvement

Moving most reserved capital toward deeper drawdown bands reportedly reduced the long-bear tail error to approximately **24%–28% above the eventual trough**.

This was an improvement but still demonstrated a fundamental limitation:

> Price-only signals cannot reliably determine whether a 20% decline is close to the final low or is merely the midpoint of a 40%–60% bear market.

The result motivated the long-bear throttle and the requirement for breadth, volatility and credit divergence before larger additions.

## 6. SMH / SOXX independent research snapshot

SPY/QQQ thresholds and results were not assumed to apply automatically to semiconductors.

### Recent one-year daily test — reported five episodes per ETF

| ETF | At least one tranche within 5% | Within 8% | Reported capital-weighted distance |
|---|---:|---:|---:|
| SMH | 60% | 60% | 2.9% |
| SOXX | 40% | 40% | 3.2% |

### Five-year weekly stress test — reported five episodes per ETF

| ETF | At least one tranche within 5% | Within 8% | Reported capital-weighted distance |
|---|---:|---:|---:|
| SMH | 20% | 20% | 17.2% |
| SOXX | 0% | 20% | 25.7% |

### Interpretation

- Weekly data was too coarse for precise bottom capture; rapid sell-offs often rebounded before the next weekly execution point.
- SOXX tended to pass multiple drawdown thresholds in a single volatile move. A rule allowing only one new tranche per session was therefore necessary.
- The semiconductor sample was small and the long daily history was not fully archived.
- These numbers are insufficient to claim a validated semiconductor champion.

## 7. Leverage research evidence

A separate QLD volatility-management study from a fixed third-party dataset reportedly found approximately:

| Strategy | Reported result |
|---|---:|
| QQQ buy-and-hold CAGR | ~19% |
| QQQ Sharpe | ~0.75 |
| Fast-volatility-managed QLD CAGR | ~30% |
| Fast-volatility-managed QLD Sharpe | ~0.9–1.0 |
| Fast-volatility-managed QLD maximum drawdown | ~-42% |

This evidence supports using realised-volatility control for leveraged exposure, but it does **not** demonstrate that fast volatility identifies the exact market bottom. The test was also exposed to crisis-period parameter selection and was not treated as an untouched holdout.

Operational conclusion:

- ordinary ETF: anticipatory small probe may be permitted;
- leveraged ETF: wait for bottom confirmation, improving breadth and falling volatility;
- leveraged position: temporary tactical trade with an explicit exit and time stop.

## 8. Rejected or demoted approaches

### Fixed VIX threshold

Rejected as a primary bottom trigger because:

- VIX measures expected SPX volatility, not price direction;
- important bottoms can occur without VIX reaching an arbitrary level such as 40;
- SPX VIX is not a semiconductor-specific panic measure.

### VIX term structure alone

Useful as a regime and leverage-risk filter, but prone to false alarms and early risk-off signals.

### RSI alone

Oversold readings can persist through long bear markets. Retained only as a throttle or divergence input.

### One high-volume down day

Could represent capitulation or the beginning of a new breakdown. Retained only when followed by deceleration or a weaker-volume retest.

### Moving-average confirmation for first ordinary tranche

Reduced false positives but entered too late in V-shaped recoveries. Retained for larger ordinary additions and tactical leverage.

### Rolling 52-week drawdown

Demoted because the old peak can roll out during multi-year bear markets. The unresolved cycle high is the primary reference.

## 9. Look-ahead issue discovered and removed

One early model normalised tranche weights using the eventual number of signals in the episode:

```text
weight_i = i^1.5 / sum(j^1.5 for j in 1..n)
```

At signal time, `n` was unknown. This introduced future information and made the result appear better than a tradable strategy.

Corrected rule:

- every tranche amount is fixed or calculated causally at the time of the signal;
- unused future tranches remain cash;
- no ex-post redistribution to earlier entries.

All look-ahead-affected figures were withdrawn from the strategy decision.

## 10. Current research ranking

| Component | Current assessment |
|---|---|
| Unresolved-cycle drawdown | Retain — better than rolling 52-week drawdown. |
| Volatility-normalized decline | Retain — improves cross-regime comparability. |
| Back-loaded deployment | Retain — reduces early capital exhaustion. |
| Fresh-low + previous-entry spacing | Retain — controls repeated entries. |
| Underwater-duration / long-bear throttle | Retain — addresses slow repricing regimes. |
| Volume/liquidation exhaustion | Promising — requires point-in-time validation. |
| Breadth divergence | High-priority addition — incomplete dataset. |
| Genuine downside VRP | High-priority addition — data-intensive and incomplete. |
| HY OAS / OFR filter | Retain as veto/regime filter, not direct timing trigger. |
| RSI/MACD/VIX absolute level | Supporting only. |
| Tactical leverage confirmation | Promising, not fully validated for SSO/QLD/USD. |

## 11. What is still required for a formal validation claim

- commit the raw signal ledger;
- archive exact data-vendor and corporate-action methodology;
- define one immutable development/validation/holdout split;
- use next-session execution and realistic costs;
- perform rolling-origin and purged validation;
- cluster overlapping drawdown episodes;
- test parameter stability;
- run block bootstrap confidence intervals;
- calculate Deflated Sharpe Ratio and Probability of Backtest Overfitting where return optimisation is used;
- independently validate SMH, SOXX and actual USD history;
- test breadth, downside VRP and credit features incrementally;
- delete features that do not improve out-of-sample bottom proximity or false-bottom control.

## 12. Bottom line

The research supports a **small anticipatory ordinary-ETF probe plus back-loaded staged deployment**. It does not support claiming that the current model identifies the exact bottom or that the reported sizing is optimal.

The strongest unresolved problem is deciding when to deploy a meaningful tranche during a prolonged bear market. The next research priority is a causal ensemble of:

```text
price/volatility-normalized liquidation
+ breadth divergence
+ fear-premium divergence
+ credit/systemic veto
```
