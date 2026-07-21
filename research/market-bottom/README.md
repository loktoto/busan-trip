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
- [`ibkr-validation-2026-07-21.md`](ibkr-validation-2026-07-21.md) — IBKR five-year windows, corporate actions, labelled capacity, volatility and actual-product mapping.
- [`feature-schema.md`](feature-schema.md) — point-in-time breadth, VRP and credit feature contract.
- [`feature_manifest.py`](feature_manifest.py) — feature provenance, availability-lag, revision-policy and immutable-hash audit.
- [`backtest.py`](backtest.py) — causal bottom-proximity backtest for adjusted daily OHLCV.
- [`validation.py`](validation.py) — signal-window isolation, full path-dependent context, evaluation-only forward tail and bootstrap diagnostics.
- [`robust_validation.py`](robust_validation.py) — preferred regime-aware walk-forward protocols, one-standard-error selection and complete candidate-fold matrices.
- [`selection.py`](selection.py) — episode utility, monotonic sizing checks, complexity control and feature-promotion gates.
- [`cscv.py`](cscv.py) — CSCV/PBO diagnostic on identical outer OOS candidate partitions.
- [`ablation.py`](ablation.py) — identical-fold price/breadth/VRP/credit feature ablation with manifest blockers.
- [`data_audit.py`](data_audit.py) — adjusted-price continuity and split-like discontinuity veto.
- [`leverage.py`](leverage.py) — tactical actual-product SSO/QLD/USD research, tracking-gap and path-dependency measurements.
- [`config.example.json`](config.example.json) — asset-specific research-candidate settings.
- [`grid.example.json`](grid.example.json) — bounded parameter-stability grid.
- [`tests/`](tests/) — causal, selection, label-isolation, feature-provenance, CSCV and actual-product tests.
- [`requirements.txt`](requirements.txt) — Python dependencies.

## Key conclusion

The strongest price-only candidate found so far is a **causal, back-loaded bottom-wave framework** combining:

1. drawdown from the unresolved cycle high;
2. volatility-normalized decline speed;
3. a nonlinear deployment curve that preserves most capital for deeper declines;
4. fresh-low, cooldown and previous-entry spacing rules;
5. an underwater-duration / long-bear throttle;
6. liquidation and volume-exhaustion evidence.

Price-only signals are useful for placing a **small probe** near later troughs, but they cannot reliably determine whether a 20% decline is the final low or the midpoint of a 40%–60% bear market. Breadth divergence, volatility/fear-premium information and credit/systemic filters therefore need to prove incremental out-of-sample value before larger additions.

## Optimisation governance

The optimiser no longer promotes the numerically highest training score automatically.

1. Audit adjusted prices for the underlying and leveraged product; reject split-like discontinuities.
2. Preserve all prior price history before each fold because unresolved cycle highs and underwater duration are path-dependent.
3. Restrict signals to the train/test interval and reserve a fixed 252-session evaluation-only forward tail.
4. Exclude the latest unlabelled live tail from completed historical accuracy claims.
5. Calculate episode-level utility across crash, ordinary-correction and long-bear regimes.
6. Apply the **one-standard-error rule** and choose the simplest/lower-capital candidate inside the statistically equivalent set.
7. Persist every candidate on every identical outer OOS partition.
8. Use CSCV/PBO only when at least eight usable partitions remain; otherwise classify it as underpowered.
9. Add breadth, VRP or credit only when the point-in-time manifest passes and identical-fold ablation shows positive median gain, bounded worst-fold damage and non-negative performance in at least 60% of comparable folds.
10. Test leverage separately with actual adjusted SSO, QLD and USD histories.

The original evaluator omitted drawdown episodes with no trade. Later audits also found invalid five-year zero-fold defaults, truncated future labels and a short warm-up that forgot earlier cycle highs. These issues are now explicitly tested.

No asset parameter is promoted solely because the engine was improved. SPY, QQQ, SMH and SOXX settings remain research candidates until immutable adjusted data is rerun through the full validation pipeline.

## Validation protocols

| Protocol | Train | Purge | Test | Step | Role on an approximately five-year daily window |
|---|---:|---:|---:|---:|---|
| `MODERN_5Y_PRIMARY` | 504 | 84 | 126 | 126 | Primary one-SE model selection; about three fully labelled folds after the 252-session tail. |
| `MODERN_5Y_DENSE_DIAGNOSTIC` | 315 | 84 | 63 | 63 | About nine shorter partitions for CSCV/PBO and instability diagnostics only. |
| `LONG_CYCLE` | 1,008 | 84 | 252 | 252 | Dot-com/GFC-scale external history; cannot run on the five-year IBKR window. |

Dense diagnostic partitions do not create additional independent crises. They cannot promote parameters without the primary and long-cycle gates.

## Data expectations

The price harness expects split- and distribution-adjusted daily OHLCV:

```text
Date,Open,High,Low,Close,Volume
```

Optional non-price inputs follow [`feature-schema.md`](feature-schema.md) and require a separate immutable manifest. Signals are calculated after the close and executed at the next session's open plus configured costs. Data is intentionally not bundled because source licences and corporate-action methodologies differ.

IBKR provides a five-year modern validation window for all four underlyings and resolves actual SSO, QLD and USD products. Longer external histories must be labelled separately as long-cycle stress tests rather than silently merged into the same holdout.

## Run

```bash
cd research/market-bottom
python -m pip install -r requirements.txt
pytest -q

python data_audit.py --csv data/SPY.csv --out audit/SPY

python backtest.py \
  --csv data/SPY.csv \
  --symbol SPY \
  --config config.example.json

python robust_validation.py \
  --csv data/SPY.csv \
  --symbol SPY \
  --config config.example.json \
  --grid grid.example.json \
  --protocol MODERN_5Y_PRIMARY

python robust_validation.py \
  --csv data/SPY.csv \
  --symbol SPY \
  --config config.example.json \
  --grid grid.example.json \
  --protocol MODERN_5Y_DENSE_DIAGNOSTIC

python cscv.py \
  --candidate-matrix robust-validation-output/SPY/MODERN_5Y_DENSE_DIAGNOSTIC/candidate_fold_matrix.csv \
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

- Raw licensed datasets and the original full signal ledger are not committed.
- Existing numerical snapshots remain **PROVISIONAL / NOT YET INDEPENDENTLY REPRODUCED**.
- Historical SMH/SOXX evidence is less mature than SPY/QQQ evidence.
- Formal CSCV/PBO requires the candidate matrices to be populated from immutable real datasets and remains underpowered if fewer than eight usable partitions survive.
- Five years of IBKR data do not include dot-com or GFC regimes; external long-cycle stress tests remain necessary.
- Genuine downside VRP requires model-free option-implied variance and intraday realised variance; simple underlying IV minus daily HV is only a proxy.
- No result is a guaranteed bottom, expected return, automatic order or optimal position size.
