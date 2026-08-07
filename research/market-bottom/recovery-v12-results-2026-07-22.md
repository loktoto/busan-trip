# Latest bottom monitor backtest decision — 2026-07-22

## Decision

The current monitor is **not sufficiently precise to be described as a close-to-bottom detector for QQQ or SOXX**. It is better described as a staged drawdown-participation model.

No production threshold, tranche size or catch-up rule is promoted by this test.

The most important production defect is governance rather than arithmetic: a model-simulated deployment ledger is not evidence that the user received or executed the earlier tranche. Production reporting must separate:

1. model-simulated deployment;
2. actual confirmed deployment or position;
3. the action to take when an earlier alert was missed or not executed.

## Data and causality

- Signals: completed close `t` only.
- Execution: next open `t+1` plus configured transaction costs and slippage.
- Full-history numerical tests: audited public adjusted daily histories for reproducibility.
- Recent validation boundary: `2021-07-26` through `2026-07-21`, independently checked against IBKR five-year RTH histories.
- Raw licensed IBKR history was not committed to the public repository.
- Latest completed closes matched IBKR within 20 bps for SPY, QQQ and SOXX; observed gaps were effectively zero.
- SOXX's 3-for-1 split on `2024-03-07` was included in the corporate-action audit.
- GitHub Actions run: `29890223903`.
- Research commit: `463c8af5b37e2b019514a7d264886a5b8c7ba6e7`.

## Current baseline — recent five-year complete episodes

| Asset | Complete episodes | Missed rate | Mean first entry above eventual trough | Mean weighted entry above trough | Mean sessions first entry preceded trough | First entry followed by >10% decline | Mean forward return 21d | 63d | 126d |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SPY | 7 | 0.0% | 6.58% | 5.41% | 30.3 | 28.6% | 3.22% | 7.74% | 9.76% |
| QQQ | 6 | 0.0% | 12.49% | 9.48% | 53.3 | 33.3% | 2.74% | 5.62% | 9.02% |
| SOXX | 6 | 0.0% | 18.96% | 16.52% | 61.7 | 33.3% | 7.66% | 24.58% | 24.57% |

### Interpretation

- The baseline participated in every complete recent episode, so it was not generally missing corrections.
- However, it normally entered well before the final trough.
- Positive 63-day and 126-day returns do not establish bottom precision; they show that staged buying during long-run equity drawdowns can eventually recover.
- SPY's precision is acceptable only for a small staged probe, not an exact-bottom claim.
- QQQ and SOXX entries were too early for the stated close-to-bottom objective.

## V1.1 inside-zone recovery overlay

V1.1 did not materially improve first-entry timing, false-start rate or recent weighted distance. It still required price to remain inside the original watch zone, so a rebound above the threshold continued to produce `WAIT`.

## V1.2 true post-threshold catch-up

### Normal strategy path

In the recent five-year sample, V1.2 generated **zero post-threshold catch-up trades for SPY, QQQ and SOXX**. The model ledger had already recorded earlier trades in every relevant recent episode.

This proves that adding a catch-up condition alone does not solve the user's operational problem while the monitor treats simulated trades as if they were actually executed.

### Full-history catch-up trades

| Asset | Catch-up trades | Mean distance above episode trough | Mean additional downside | Mean forward return 63d | Decision |
|---|---:|---:|---:|---:|---|
| SPY | 5 | 3.64% | -3.02% | 3.26% | Research-only candidate |
| QQQ | 4 | 11.25% | -5.18% | -5.14% | Reject current rule |
| SOXX | 0 | n/a | n/a | n/a | Insufficient evidence |

## Missed-first-alert stress test — recent five years

The first baseline entry in each episode was deliberately treated as missed. The test then asked whether a later causal V1.2 catch-up opportunity appeared.

| Asset | Earlier-entry opportunities | Episodes with second chance | Second-chance rate | Catch-up price above eventual trough | Additional downside after catch-up |
|---|---:|---:|---:|---:|---:|
| SPY | 7 | 6 | 85.7% | 9.38% | -3.57% |
| QQQ | 6 | 4 | 66.7% | 10.50% | -3.60% |
| SOXX | 6 | 4 | 66.7% | 30.76% | -17.84% |

### Asset decisions

- **SPY:** a 2% post-threshold catch-up may be useful when an earlier probe was genuinely not executed, but remains research-only pending causal out-of-sample validation and an actual execution ledger.
- **QQQ:** reject the current catch-up rule. Full-history catch-ups were too far from the eventual trough and had a negative mean 63-day return.
- **SOXX:** reject post-threshold V-shaped catch-up. The missed-alert stress result was materially unsafe: entries remained about 30.8% above the eventual trough and subsequently fell another 17.8% on average.

## Required production changes

1. Never suppress a current action solely because `cumulative_model_deployment` is non-zero.
2. Store and display model-simulated deployment and actual confirmed deployment separately.
3. When actual deployment is unknown, issue two explicit paths:
   - `IF EARLIER TRANCHE EXECUTED`;
   - `IF EARLIER TRANCHE NOT EXECUTED`.
4. Keep SPY catch-up informational and capped at 2% of SPY-reserved capital until formal promotion.
5. Do not enable QQQ or SOXX V-shaped catch-up from this rule.
6. Rebuild QQQ and SOXX bottom thresholds around later exhaustion/confirmation evidence; do not label the current early probes as close-to-bottom entries.
7. Continue to show SMH only as an informational SOXX cross-check with zero production weight.

## Governance

- Hard invariants: passed.
- Data continuity audits: passed.
- IBKR latest-bar boundary checks: passed.
- Regression tests: passed.
- Overall catch-up promotion: `BLOCKED_ASSET_SPECIFIC_ONLY`.
- Production orders: none created or transmitted.
