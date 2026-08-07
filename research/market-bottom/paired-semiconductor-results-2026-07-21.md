# SMH as a Secondary SOXX Bottom Reference — 2026-07-21

> Classification: **PUBLIC REPRODUCIBILITY DIAGNOSTIC / AUDITED PROVISIONAL**  
> Production decision: **SMH is informational only; no SOXX trade rule is promoted.**

## Research question

Does an independently calculated SMH bottom state improve the SOXX bottom model enough to justify changing SOXX staged entries?

SOXX remains the sole traded semiconductor target. SMH is never assigned a tranche and cannot create a second semiconductor trade.

## Data

### IBKR audit

IBKR supplied five-year completed-RTH daily histories through 2026-07-21 for both products and identified the relevant splits:

- SMH: 2-for-1 on 2023-05-05;
- SOXX: 3-for-1 on 2024-03-07.

These histories establish product continuity and modern-market availability. They are not committed to the repository and therefore are not represented as an immutable workflow holdout.

### Public reproducibility diagnostic

GitHub Actions separately downloaded adjusted daily data through 2026-07-21:

| Symbol | Start | Rows | SHA256 |
|---|---:|---:|---|
| SMH | 2000-06-05 | 6,570 | `df285fb4e587a9c849cb1d02d9a62691d12814c1e8293f659755072f7fe8bf76` |
| SOXX | 2001-07-13 | 6,291 | `18983d219d78d89a9975eed488e9e8766f3f9f5ced26c081a4773c6df53e3d6e` |

Both files passed the adjusted-price continuity audit with zero malformed rows, unexplained split-like jumps or duplicate dates.

The public dataset is explicitly **not** labelled as the IBKR holdout.

## Causal design

- SMH and SOXX indicators are calculated independently.
- Only matching completed daily dates are aligned.
- Both signals use completed close `t`.
- SOXX entries execute at next open `t+1` plus configured costs.
- SMH never generates a trade row.
- Metrics evaluate bottom proximity, missed episodes, capital deployment and additional downside rather than CAGR.

## Variants

1. `SOXX_ONLY` — baseline.
2. `SMH_CONFIRMATION_VETO` — SMH deterioration can block SOXX State-4 confirmation only.
3. `SMH_CONFIRMATION_GATE` — SOXX State-4 confirmation additionally requires recent SMH confirmation.
4. `SMH_SOFT_CONFIRM` — SMH can lower the SOXX exhaustion/confirmation vote hurdle by one.
5. `SMH_VETO_ONLY` — SMH deterioration blocks both SOXX exhaustion and confirmation transitions.
6. `SMH_HARD_CONFIRM` — both SOXX exhaustion and confirmation require recent SMH corroboration.

## Full-history diagnostic

Sixteen completed SOXX drawdown episodes were available.

| Variant | Trades | Missed | Any tranche ≤5% from trough | ≤8% | Mean weighted distance | Mean worst additional downside | Mean deployment |
|---|---:|---:|---:|---:|---:|---:|---:|
| SOXX_ONLY | 57 | 0% | 68.75% | 81.25% | 13.448% | -11.164% | 27.188% |
| SMH_CONFIRMATION_VETO | 57 | 0% | 68.75% | 81.25% | 13.448% | -11.164% | 27.188% |
| SMH_CONFIRMATION_GATE | 57 | 0% | 68.75% | 81.25% | 13.448% | -11.164% | 27.188% |
| SMH_SOFT_CONFIRM | 55 | 0% | 62.50% | 81.25% | 13.597% | -11.869% | 25.173% |
| SMH_VETO_ONLY | 58 | 0% | 68.75% | 81.25% | 13.395% | -11.164% | 25.486% |
| SMH_HARD_CONFIRM | 58 | 0% | 68.75% | 81.25% | 13.395% | -11.164% | 25.486% |

Interpretation:

- Soft confirmation was worse: lower 5% hit rate, poorer weighted distance and worse adverse excursion.
- Broad veto/hard confirmation reduced average deployment and improved weighted distance by only about 0.054 percentage points.
- Confirmation-only variants were identical to SOXX-only; SMH did not alter a relevant State-4 transition in this sample.

## Post-2024 diagnostic

Five completed SOXX drawdown episodes were available.

| Variant | Trades | Missed | Any tranche ≤5% from trough | ≤8% | Mean weighted distance | Mean worst additional downside | Mean deployment |
|---|---:|---:|---:|---:|---:|---:|---:|
| SOXX_ONLY | 15 | 0% | 80% | 80% | 9.892% | -6.324% | 19.0% |
| SMH_CONFIRMATION_VETO | 15 | 0% | 80% | 80% | 9.892% | -6.324% | 19.0% |
| SMH_CONFIRMATION_GATE | 15 | 0% | 80% | 80% | 9.892% | -6.324% | 19.0% |
| SMH_SOFT_CONFIRM | 14 | 0% | 60% | 80% | 10.944% | -8.580% | 17.0% |
| SMH_VETO_ONLY | 14 | 0% | 80% | 80% | 10.317% | -6.324% | 16.0% |
| SMH_HARD_CONFIRM | 14 | 0% | 80% | 80% | 10.317% | -6.324% | 16.0% |

Interpretation:

- SOXX-only was at least as good as every paired variant in the recent sample.
- Broad SMH veto/hard confirmation conserved capital but worsened mean weighted distance by about 0.425 percentage points.
- Soft confirmation again performed materially worse.
- Confirmation-only rules produced no incremental signal.

## Decision

**No paired rule is promoted.**

SMH remains useful operationally as:

- a second displayed semiconductor drawdown/state number;
- a warning when SMH and SOXX sector structure diverges;
- qualitative corroboration for human review;
- a research feature for future non-overlapping outer-fold tests.

SMH does **not** currently:

- change the SOXX state;
- unlock or revoke a SOXX tranche;
- create a separate semiconductor allocation;
- act as a formal USD leverage veto.

## Why the decision is conservative

A full-history aggregate and five post-2024 episodes are insufficient for feature promotion. The apparent 0.054-point long-history gain from broad veto rules is economically small and fails to persist in the recent sample. Formal promotion still requires:

1. non-overlapping outer label windows;
2. long-cycle regime coverage;
3. one-standard-error selection;
4. worst-regime control;
5. identical-fold paired-feature ablation;
6. confirmation using immutable adjusted data.

## Production implication

The monitor should display:

- SOXX primary bottom state, levels, tranche and invalidation;
- SMH independent reference state and levels;
- pair label: `CONFIRMS`, `POSITIVE_DIVERGENCE`, `NEUTRAL`, `DIVERGES` or `VETO-LIKE DETERIORATION`;
- a clear note that the pair label is informational and currently does not alter SOXX sizing.
