# Market Bottom Zone Research

> Status: **AUDITED PROVISIONAL**  
> Primary bottom targets: **SPY, QQQ, SOXX**.  
> Secondary semiconductor reference: **SMH**, used only to corroborate or contradict SOXX.  
> Tactical mappings: SPY→SSO, QQQ→QLD, SOXX→USD.

This directory documents the research used by the `Bottom Zone Monitor`.

The objective is not to predict the exact lowest tick. It is to identify a sufficiently close bottom zone where measured additions to ordinary 1× exposure have acceptable additional-downside risk. Leveraged ETFs are researched separately and only after bottom confirmation.

## Universe governance

- SPY, QQQ and SOXX each have an independent state, capital reserve and staged-deployment record.
- SMH is calculated independently but has **no capital reserve, tranche or trade row**.
- SMH supplies a second semiconductor bottom coordinate for SOXX through a causal pair classification: `CONFIRMS`, `POSITIVE_DIVERGENCE`, `NEUTRAL`, `DIVERGES` or `VETO`.
- SMH evidence cannot manufacture a SOXX setup and cannot double semiconductor capital.
- Until paired rules pass leakage-safe outer validation, their effect on SOXX sizing remains provisional.

## Files

- [`strategy.md`](strategy.md) — signal hierarchy, states, staged sizing, SMH/SOXX pair governance and leverage rules.
- [`backtest-results.md`](backtest-results.md) — historical research snapshots, limitations and rejected approaches.
- [`optimization-log.md`](optimization-log.md) — causal-engine corrections and current optimisation gate.
- [`bottom-monitor-optimisation-v40-2026-07-23.md`](bottom-monitor-optimisation-v40-2026-07-23.md) — fresh IBKR audit, chronological holdout, local-bottom ensemble and deep-bear reserve decision.
- [`research-evidence.md`](research-evidence.md) — primary-source evidence mapped to model design.
- [`ibkr-validation-2026-07-21.md`](ibkr-validation-2026-07-21.md) — IBKR windows, corporate actions, labelled capacity, volatility and product mapping.
- [`feature-schema.md`](feature-schema.md) — point-in-time breadth, VRP and credit feature contract.
- [`feature_manifest.py`](feature_manifest.py) — provenance, availability-lag, revision-policy and immutable-hash audit.
- [`backtest.py`](backtest.py) — causal bottom-proximity backtest for adjusted daily OHLCV.
- [`paired_semiconductor.py`](paired_semiconductor.py) — SOXX-only versus SMH-confirmed/vetoed paired diagnostics; SOXX remains the sole traded asset.
- [`fetch_public_prices.py`](fetch_public_prices.py) — public adjusted-price fetcher for CI reproducibility diagnostics, never labelled as an IBKR holdout.
- [`validation.py`](validation.py) — signal-window isolation, full path context and evaluation-only forward labels.
- [`robust_validation.py`](robust_validation.py) — leakage-safe protocols, one-standard-error selection and candidate-fold matrices.
- [`selection.py`](selection.py) — episode utility, monotonic sizing, complexity control and feature gates.
- [`cscv.py`](cscv.py) — CSCV/PBO diagnostic that rejects overlapping or unverified label windows.
- [`ablation.py`](ablation.py) — identical-fold feature ablation with manifest blockers.
- [`data_audit.py`](data_audit.py) — adjusted-price continuity and split-like discontinuity veto.
- [`leverage.py`](leverage.py) — actual-product SSO/QLD/USD research, tracking gaps and path dependence.
- [`deep_bear_reserve_v40.py`](deep_bear_reserve_v40.py) — shadow-only structural-bear capital-reservation candidate.
- [`optimize_reserve_v40.py`](optimize_reserve_v40.py) — pre-2018 selection and 2018+ holdout comparison for 12 reserve policies.
- [`local_bottom_ensemble_v41.py`](local_bottom_ensemble_v41.py) — six-family 63-session local-bottom research score; zero production weight.
- [`tests/`](tests/) — causal, label-isolation, provenance, paired-semiconductor, CSCV and actual-product regression tests.

## Key conclusion

The strongest price-only research candidate remains a causal, back-loaded bottom-wave framework combining unresolved-cycle drawdown, volatility-normalised decline, nonlinear deployment, fresh-low spacing, long-bear throttling and liquidation/exhaustion evidence.

Price-only signals may justify a small probe but cannot reliably distinguish a final low from the midpoint of a deeper bear market. Breadth, genuine downside VRP, credit/systemic information and the SMH cross-check must each prove incremental point-in-time out-of-sample value before receiving promotion weight.

For semiconductors, the current research question is explicit:

> Does independently observed SMH exhaustion or deterioration improve SOXX bottom proximity, missed-bottom control and additional-downside risk versus the same SOXX model without SMH?

The paired engine compares:

1. `SOXX_ONLY`;
2. `SMH_SOFT_CONFIRM`;
3. `SMH_VETO_ONLY`;
4. `SMH_HARD_CONFIRM`.

A higher CAGR alone does not pass the gate. The paired rule must improve bottom proximity without materially worsening missed episodes, worst additional downside or capital deployment, and must survive non-overlapping outer validation.

## Optimisation governance

1. Audit adjusted prices for both SOXX and SMH independently.
2. Preserve all prior history because cycle highs and underwater duration are path-dependent.
3. Align only same-date completed bars; never forward-fill a stale SMH reference.
4. Restrict signals to the train/test interval and retain a 252-session evaluation-only label tail.
5. Require a purge of at least 252 sessions between training signals and test signals.
6. Exclude the latest unlabelled live tail from historical accuracy claims.
7. Score crash, ordinary-correction and long-bear episodes separately.
8. Apply the one-standard-error rule and prefer the simpler/lower-capital candidate.
9. Persist every candidate on identical outer OOS signal blocks.
10. Calculate CSCV/PBO only with at least eight verified non-overlapping future-label partitions.
11. Promote breadth, VRP, credit or the SMH pair feature only after provenance and identical-fold ablation gates.
12. Test leverage separately with actual adjusted SSO, QLD and USD histories.

The audits found omitted missed episodes, repeated bonuses, invalid rolling-low comparisons, zero-fold defaults, truncated labels, short path history and training-label leakage. Results generated before those corrections are not promotion evidence.

The v4.0 chronological holdout also rejected the new reserve policy as a
production replacement and rejected the six-family local-bottom score as a trade
gate. **No asset parameter, reserve overlay, indicator gate or SMH paired rule is
currently promoted.**

## Validation protocols

| Protocol | Train | Purge | Test | Step | Approximate capacity on 5Y daily data | Role |
|---|---:|---:|---:|---:|---:|---|
| `MODERN_5Y_PRIMARY` | 504 | 252 | 126 | 126 | about 1 fully labelled holdout | Recent-regime holdout only. |
| `MODERN_5Y_DENSE_DIAGNOSTIC` | 315 | 252 | 63 | 63 | about 6 rolling observations | Dependent sensitivity diagnostic; CSCV blocked. |
| `LONG_CYCLE` | 1,008 | 252 | 252 | 504 | needs roughly 20+ years for ≥8 partitions | Candidate protocol for formal CSCV/PBO and long-cycle stress testing. |

Five years of IBKR history are valuable for recent product validation but cannot provide many independent crisis episodes. Rolling windows do not create independent evidence when they reuse the same future path.

## Data expectations

The price harness expects split- and distribution-adjusted daily OHLCV:

```text
Date,Open,High,Low,Close,Volume
```

Optional non-price inputs require both a CSV and a point-in-time manifest. Signals are calculated after the close and executed at the next session open plus configured costs. Raw licensed data is not bundled.

The CI paired diagnostic downloads a separate public long-history dataset and archives its manifest. It is labelled **PUBLIC REPRODUCIBILITY DIAGNOSTIC — NOT IBKR HOLDOUT**. IBKR remains the audit source for modern product history, current volatility context and corporate actions.

## Run

```bash
cd research/market-bottom
python -m pip install -r requirements.txt
pytest -q

python paired_semiconductor.py \
  --soxx-csv data/SOXX.csv \
  --smh-csv data/SMH.csv \
  --config config.example.json \
  --out paired-output/full

python paired_semiconductor.py \
  --soxx-csv data/SOXX.csv \
  --smh-csv data/SMH.csv \
  --config config.example.json \
  --signal-start 2024-01-01 \
  --out paired-output/modern
```

## Limitations

- Immutable licensed daily datasets have not yet been archived in the workflow.
- Existing numerical snapshots remain **PROVISIONAL / NOT YET INDEPENDENTLY REPRODUCED**.
- A five-year window supports recent holdout validation, not a formal multi-crisis PBO claim.
- SMH and SOXX have different indexes and constituent weights; agreement is corroboration, not identity.
- Genuine downside VRP requires model-free option-implied variance and intraday realised variance; simple IV minus daily HV is only a proxy.
- Dot-com/GFC long-cycle histories must remain separate from the modern IBKR holdout.
- No result is a guaranteed bottom, expected return, automatic order or optimal position size.
