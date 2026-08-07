# Bottom Monitor v4.0 Backtest and Optimisation

**Date:** 2026-07-23  
**Status:** AUDITED RESEARCH; production thresholds unchanged  
**Primary targets:** SPY, QQQ, SOXX  
**Secondary semiconductor reference:** SMH only  
**Objective:** find a sufficiently close, actionable bottom zone; not the exact lowest tick

## 1. Decision first

The current price-only staged-participation engine remains the production
baseline. No new indicator, parameter change, reserve overlay or leverage rule
passed the chronological holdout gate across the required assets.

That is not a claim that the existing model is optimal. It is a narrower
conclusion:

1. The existing ladder remains strong for **ordinary corrections and 63-session
   local bottoms**.
2. It remains weak at identifying the **final trough of a structural bear**,
   especially for QQQ and SOXX.
3. RSI/Bollinger washout, price reversal, volatility maturity, selling-pressure
   maturity, retest/higher-low and short-trend reclaim did not improve episode
   coverage versus the existing fresh-low ladder.
4. A deep-bear reserve overlay reduced some average entry distances, but the
   pre-2018-selected rule failed the 2018+ holdout gate because it sometimes
   withheld the later near-bottom tranche in fast corrections.
5. Therefore v4.0 adds reproducible shadow research and stricter reporting
   separation, but does **not** silently replace production rules.

The operational interpretation should be:

- **State 2:** bounded staged participation / local-bottom probe;
- **State 3:** exhaustion research evidence;
- **State 4:** local bottom confirmed strongly enough for a larger ordinary-ETF
  review;
- **State 5:** recovery underway;
- **cycle bottom:** never inferred from price-only evidence in a structural-bear
  regime;
- **leverage:** remains unpromoted.

## 2. Fresh IBKR validation

IBKR returned 1,254 daily bars per asset from 2021-07-26 through the live
2026-07-23 session. The unfinished 2026-07-23 bar was excluded. The latest
completed regular-session bar is 2026-07-22.

| Asset | IBKR contract | Completed five-year/public overlap | Daily-return correlation | Split audit |
|---|---:|---:|---:|---|
| SPY | 756733 | 1,252 bars | 0.999223 | none |
| QQQ | 320227571 | 1,252 bars | 0.999913 | none |
| SOXX | 12658194 | 1,252 bars | 0.999931 | 3:1 on 2024-03-07 |
| SMH | 229725622 | 1,252 bars | 0.999834 | 2:1 on 2023-05-05 |

The public files are split/distribution-adjusted while IBKR supplies explicit
corporate-action rows and a different historical price-level convention.
Return-path correlation, split continuity and exact recent closes were therefore
used as the cross-check. Raw licensed IBKR bars were not committed.

Latest completed RTH closes:

| Date | SPY | QQQ | SOXX | SMH |
|---|---:|---:|---:|---:|
| 2026-07-22 | 747.41 | 705.35 | 555.52 | 586.91 |

## 3. Validation design

### 3.1 Signal and execution causality

- completed close at `t`;
- execution at next open `t+1`;
- 1 bp transaction cost plus 2 bps slippage;
- no future trough, completion flag or forward return in a signal;
- all complete episodes retained, including misses;
- unfinished current-session bars removed;
- raw IBKR data not persisted in the public repository.

### 3.2 Selection and holdout

- candidate policies were selected only from episodes beginning before
  2018-01-01;
- episodes beginning on or after 2018-01-01 formed the chronological holdout;
- the modern five-year window begins 2021-07-26;
- the candidate family was restricted to 12 pre-declared policies;
- a one-standard-error rule preferred the simpler/lower-capital candidate;
- promotion additionally required positive holdout episode-score improvement,
  at least 60% non-negative holdout deltas and bounded worst-episode damage.

### 3.3 Two different bottom labels

The audit now states explicitly that these are different questions:

1. **Local bottom:** entry close to the minimum over the next 63 sessions.
2. **Cycle bottom:** entry close to the final trough of the complete drawdown
   episode.

The fixed 252-session label remains useful for leakage-safe model selection, but
it is not a complete final-cycle label for multi-year bears such as 2000-2002.
Full-cycle distance is retained as a descriptive stress test, not a signal input.

## 4. Existing baseline remains difficult to beat

### 4.1 Full-history baseline

| Asset | Complete episodes | Missed | Mean deployment | Weighted distance | Additional downside | Any trade within 5% |
|---|---:|---:|---:|---:|---:|---:|
| SPY | 37 | 0.00% | 26.41% | 6.31% | -5.90% | 89.19% |
| QQQ | 26 | 19.23% | 18.10% | 11.40% | -9.22% | 73.08% |
| SOXX | 16 | 0.00% | 27.19% | 13.45% | -11.16% | 68.75% |

### 4.2 Local 63-session bottom behaviour

| Asset | Signals | Episode hit within 8% | Signal precision within 8% | False start above 10% |
|---|---:|---:|---:|---:|
| SPY | 140 | 100.00% | 77.86% | 18.57% |
| QQQ | 78 | 73.08% | 62.82% | 34.62% |
| SOXX | 57 | 87.50% | 50.88% | 47.37% |

This explains why adding more conventional rebound indicators did not help:
the baseline already achieves high local-bottom episode coverage by permitting
multiple spaced fresh-low events. Its main weakness is false starts and capital
timing in long bears, not absence of a rebound oscillator.

## 5. Indicator-family ablation

The v4.1 ensemble tested six completed-bar families:

1. RSI14 / five-day z-score / Bollinger washout followed by momentum reversal;
2. positive intraday reversal and strong close location;
3. realised-volatility and ATR maturity;
4. declining short-window selling pressure;
5. retest/higher-low structure near the 20-day low;
6. SMA10 reclaim with positive slope and five-day return.

The score threshold was tested from two to six families. Representative results:

| Asset | Candidate | Episode hit within 8% / 63d | Signal precision within 8% / 63d | Missed episodes |
|---|---|---:|---:|---:|
| SPY | Existing baseline | 100.00% | 77.86% | 0.00% |
| SPY | score ≥3 | 64.86% | 71.54% | 35.14% |
| QQQ | Existing baseline | 73.08% | 62.82% | 19.23% |
| QQQ | score ≥4 | 46.15% | 65.50% | 53.85% |
| SOXX | Existing baseline | 87.50% | 50.88% | 0.00% |
| SOXX | score ≥4 | 43.75% | 53.88% | 56.25% |

Filtering the existing baseline by the same score gave only a small precision
gain for SPY and materially worsened episode coverage. It did not improve SOXX.

**Decision:** reject the ensemble as a trade gate. It may remain an explanatory
confidence panel, but its production weight is zero.

## 6. Deep-bear reserve overlay

The reserve overlay tested:

- early structural-bear votes: below SMA200, falling SMA200, SMA50 below SMA200,
  negative 63-day return and prolonged underwater duration;
- falling-knife votes: extreme five-day return, rising RV20, high selling
  pressure, weak close location and falling SMA10;
- bounded release evidence: deep drawdown, recent retest, improving momentum,
  contracting volatility and maturing selling pressure;
- persistent structural-risk latch so an intermediate bear rally cannot erase
  the reserve regime.

### 6.1 Apparent improvements

The balanced 10% reserve overlay improved full-history weighted distance from
6.31% to 5.78% for SPY and from 13.45% to 10.74% for SOXX. It did not improve
QQQ reliably. These full-sample gains are not sufficient for promotion.

### 6.2 Chronological selection result

| Asset | Pre-2018 one-SE selection | 2018+ holdout decision | Reason |
|---|---|---|---|
| SPY | `R10_BALANCED` | FAIL | mean episode-score delta -0.375; one fast-correction loss dominated |
| QQQ | `BASELINE` | RETAIN | no reserve candidate beat baseline in selection sample |
| SOXX | `BASELINE` | RETAIN | only three pre-2018 episodes; reserve alternatives underpowered |

The modern window can look attractive for selected reserve variants—for example
SPY `R10_DEEP30` had 4.76% weighted distance and SOXX `R10_DEEP50` had 12.52%,
versus 5.41% and 16.52% for their baselines. Those variants were not selected
without using modern outcomes, so promoting them would be post-hoc overfitting.

**Decision:** retain reserve logic as shadow diagnostics only. It may label
`DEEP_BEAR_CAPITAL_RESERVATION_WATCH`, but cannot alter the production tranche.

## 7. Core parameter grid

A separate 48-combination per-asset grid tested:

- deployment power: baseline ±0.2;
- spacing: baseline and 1.5× baseline;
- long-bear cap: 10% and 20%;
- exhaustion votes: 2 and 3;
- confirmation votes: 3 and 4.

Best pre-2018 differences were economically negligible and did not improve the
2018+ robust score:

| Asset | Baseline pre-2018 robust score | Apparent best | Baseline 2018+ | Apparent-best 2018+ |
|---|---:|---:|---:|---:|
| SPY | 1.7687 | 1.7694 | 1.7165 | 1.7168 |
| QQQ | -0.6013 | -0.5908 | 1.5412 | 1.5003 |
| SOXX | 0.8316 | 0.8504 | 1.4070 | 1.4055 |

**Decision:** no core parameter change.

## 8. Why VIX/OFR-type indicators remain context, not triggers

Cboe describes VIX as expected 30-day volatility, not market direction, and its
own historical discussion notes that backwardation can accompany risk but can
also reverse quickly. OFR describes its FSI as a multi-category measure of
systemic stress using credit, equity valuation, funding, safe-asset and
volatility inputs. These measures help distinguish systemic stress from an
ordinary correction; neither definition supplies a final-trough rule.

- Cboe:
  https://www.cboe.com/insights/posts/inside-volatility-trading-is-vix-backwardation-necessarily-a-sign-of-a-future-down-market
- OFR FSI:
  https://www.financialresearch.gov/financial-stress-index/
- OFR methodology:
  https://www.financialresearch.gov/working-papers/files/OFRwp-17-04_The-OFR-Financial-Stress-Index.pdf

The repo's earlier corrected tests reached the same empirical result: broad
stress normalisation can happen during an intermediate bear rally. It remains a
veto/context family, not a standalone bottom trigger.

## 9. Retained, updated, corrected and new

### Retained

- completed-close / next-open causality;
- SPY, QQQ and SOXX independent states;
- SMH reference-only role;
- multiple spaced ordinary-ETF probes;
- no price-only leverage rule;
- no automatic order authority.

### Updated

- fresh IBKR five-year bars and corporate-action audit through 2026-07-22;
- 12-policy reserve comparison;
- 48-combination core-parameter comparison;
- six-family local-bottom ensemble;
- 85 passing regression tests.

### Corrected

- a good 63-session local-bottom detector is not necessarily a cycle-bottom
  detector;
- a fixed 252-session label does not contain the final trough of every multi-year
  bear;
- lower average entry distance achieved by withholding capital is not by itself
  a better bottom monitor;
- modern-window improvement cannot promote a policy selected after observing
  modern bottoms.

### New

- persistent structural-bear reserve latch;
- separate local-bottom indicator score with zero production weight;
- explicit full-cycle descriptive stress metric;
- fresh IBKR/public return-path correlations;
- explicit rule: `LOCAL_BOTTOM_ONLY_STRUCTURAL_BEAR` can never be displayed as
  `CYCLE_BOTTOM_CONFIRMED`.

## 10. Production specification after v4.0

No threshold, tranche or leverage mapping changes.

The monitor should output three separate lines per primary asset:

1. **Staged participation:** existing production state and model tranche.
2. **Local bottom:** local 63-session evidence; clearly labelled price-only.
3. **Cycle bottom / deep bear:** unconfirmed unless independent point-in-time
   breadth, genuine option-based variance evidence and credit/fundamental
   evidence survive identical-fold validation.

Shadow-only fields:

- `local_bottom_score`;
- `local_bottom_classification`;
- `deep_bear_reserve_watch`;
- `reserve_cap_shadow`;
- `full_cycle_evidence_gap`.

These fields may explain risk but must not increase production size, authorise
leverage or be represented as a filled trade.

## 11. Next research gate

The next useful improvement is not another price oscillator. It is one of:

1. point-in-time historical constituent breadth for QQQ and SOXX;
2. authorised COR1M/COR3M/DSPX history;
3. genuine downside variance-risk premium from option strips plus intraday
   realised variance;
4. point-in-time semiconductor earnings, inventory, order and revision breadth;
5. immutable long-cycle data with non-overlapping crisis partitions.

Until one of those families passes identical-fold ablation, the honest best
monitor is the current staged-participation baseline with stricter local-versus-
cycle labels—not a more complicated but unvalidated formula.
