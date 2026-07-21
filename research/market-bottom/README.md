# Market Bottom Zone Research

> Status: **AUDITED PROVISIONAL**  
> Scope: SPY, QQQ, SMH, SOXX; tactical leverage mappings SPY→SSO, QQQ→QLD, SMH/SOXX→USD.

This directory documents the market-bottom research used by the `Bottom Zone Monitor`.

The objective is **not** to predict the exact lowest tick. The objective is to identify a sufficiently close bottom zone where measured additions to ordinary 1× exposure have an acceptable additional-downside risk. Leveraged ETFs are treated separately and are considered only after bottom confirmation for a temporary rebound trade.

## Files

- [`strategy.md`](strategy.md) — signal hierarchy, states, staged sizing and leverage rules.
- [`backtest-results.md`](backtest-results.md) — historical research snapshots, limitations and rejected approaches.
- [`optimization-log.md`](optimization-log.md) — causal-engine corrections and current optimisation gate.
- [`research-evidence.md`](research-evidence.md) — primary-source evidence mapped to model design.
- [`ibkr-validation-2026-07-21.md`](ibkr-validation-2026-07-21.md) — IBKR windows, corporate actions, labelled capacity, volatility and product mapping.
- [`feature-schema.md`](feature-schema.md) — point-in-time breadth, VRP and credit feature contract.
- [`feature_manifest.py`](feature_manifest.py) — provenance, availability-lag, revision-policy and immutable-hash audit.
- [`backtest.py`](backtest.py) — causal bottom-proximity backtest for adjusted daily OHLCV.
- [`validation.py`](validation.py) — signal-window isolation, full path context and evaluation-only forward labels.
- [`robust_validation.py`](robust_validation.py) — leakage-safe protocols, one-standard-error selection and candidate-fold matrices.
- [`selection.py`](selection.py) — episode utility, monotonic sizing, complexity control and feature gates.
- [`cscv.py`](cscv.py) — CSCV/PBO diagnostic that rejects overlapping or unverified label windows.
- [`ablation.py`](ablation.py) — identical-fold feature ablation with manifest blockers.
- [`data_audit.py`](data_audit.py) — adjusted-price continuity and split-like discontinuity veto.
- [`leverage.py`](leverage.py) — actual-product SSO/QLD/USD research, tracking gaps and path dependence.
- [`tests/`](tests/) — causal, label-isolation, provenance, CSCV and actual-product regression tests.

## Key conclusion

The strongest price-only research candidate remains a **causal, back-loaded bottom-wave framework** combining unresolved-cycle drawdown, volatility-normalised decline, nonlinear deployment, fresh-low spacing, long-bear throttling and liquidation/exhaustion evidence.

Price-only signals may justify a small research probe, but cannot reliably distinguish the final low from the midpoint of a deeper bear market. Breadth, genuine downside VRP and credit/systemic features must prove incremental point-in-time out-of-sample value before receiving promotion weight.

## Optimisation governance

1. Audit adjusted prices for the underlying and leveraged product.
2. Preserve all earlier price history because cycle highs and underwater duration are path-dependent.
3. Restrict signals to the train/test interval and retain a 252-session evaluation-only label tail.
4. Require a purge of at least 252 sessions between training signals and test signals; shorter purges leak test-period prices into model selection.
5. Exclude the latest unlabelled live tail from historical accuracy claims.
6. Score crash, ordinary-correction and long-bear episodes separately.
7. Apply the one-standard-error rule and prefer the simpler/lower-capital candidate.
8. Persist every candidate on every identical outer OOS signal block.
9. Calculate CSCV/PBO only when at least eight OOS partitions have verified non-overlapping future-label windows.
10. Promote breadth, VRP or credit only after manifest and identical-fold ablation gates.
11. Test leverage separately with actual adjusted SSO, QLD and USD histories.

The audits found omitted missed episodes, repeated bonuses, invalid rolling-low comparisons, zero-fold defaults, truncated labels, short path history and training-label leakage. Results generated before those corrections are not promotion evidence.

**No asset parameter is currently promoted.**

## Validation protocols

| Protocol | Train | Purge | Test | Step | Approximate capacity on 5Y daily data | Role |
|---|---:|---:|---:|---:|---:|---|
| `MODERN_5Y_PRIMARY` | 504 | 252 | 126 | 126 | about 1 fully labelled holdout | Recent-regime holdout only. |
| `MODERN_5Y_DENSE_DIAGNOSTIC` | 315 | 252 | 63 | 63 | about 6 rolling observations | Dependent sensitivity diagnostic; CSCV blocked because future labels overlap. |
| `LONG_CYCLE` | 1,008 | 252 | 252 | 504 | needs roughly 20+ years for ≥8 partitions | Candidate protocol for formal CSCV/PBO and long-cycle stress testing. |

Five years of IBKR history are valuable for recent product validation, but cannot provide many independent crisis episodes. Rolling windows do not create independent evidence when they reuse the same future path.

## Data expectations

The price harness expects split- and distribution-adjusted daily OHLCV:

```text
Date,Open,High,Low,Close,Volume
```

Optional non-price inputs require both a CSV and a point-in-time manifest. Signals are calculated after the close and executed at the next session's open plus configured costs. Raw licensed data is intentionally not bundled.

## Run

```bash
cd research/market-bottom
python -m pip install -r requirements.txt
pytest -q

python data_audit.py --csv data/SPY.csv --out audit/SPY

python robust_validation.py \
  --csv data/SPY.csv \
  --symbol SPY \
  --config config.example.json \
  --grid grid.example.json \
  --protocol MODERN_5Y_PRIMARY

python robust_validation.py \
  --csv data/SPY-long-history.csv \
  --symbol SPY \
  --config config.example.json \
  --grid grid.example.json \
  --protocol LONG_CYCLE

python cscv.py \
  --candidate-matrix robust-validation-output/SPY/LONG_CYCLE/candidate_fold_matrix.csv \
  --out cscv-output/SPY

python ablation.py \
  --csv data/SPY.csv \
  --features-csv data/SPY-point-in-time-features.csv \
  --feature-manifest data/SPY-point-in-time-features.manifest.json \
  --symbol SPY \
  --config config.example.json \
  --grid grid.example.json \
  --protocol MODERN_5Y_PRIMARY

python leverage.py \
  --underlying-csv data/QQQ.csv \
  --leveraged-csv data/QLD.csv \
  --symbol QQQ \
  --leveraged-symbol QLD \
  --config config.example.json
```

## Limitations

- Immutable licensed daily datasets have not yet been archived in the workflow.
- Existing numerical snapshots remain **PROVISIONAL / NOT YET INDEPENDENTLY REPRODUCED**.
- A five-year window supports recent holdout validation, not a formal multi-crisis PBO claim.
- Historical SMH/SOXX evidence remains less mature than SPY/QQQ evidence.
- Genuine downside VRP requires model-free option-implied variance and intraday realised variance; simple IV minus daily HV is only a proxy.
- Dot-com/GFC long-cycle histories must remain separate from the modern IBKR holdout.
- No result is a guaranteed bottom, expected return, automatic order or optimal position size.
