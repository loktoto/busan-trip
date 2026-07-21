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
- [`ibkr-validation-2026-07-21.md`](ibkr-validation-2026-07-21.md) — IBKR five-year windows, corporate actions, volatility and actual-product mapping.
- [`feature-schema.md`](feature-schema.md) — point-in-time breadth, VRP and credit feature contract.
- [`backtest.py`](backtest.py) — causal bottom-proximity backtest for adjusted daily OHLCV.
- [`validation.py`](validation.py) — baseline purged walk-forward selection and bootstrap diagnostics.
- [`robust_validation.py`](robust_validation.py) — preferred regime-aware outer walk-forward with one-standard-error selection and a complete candidate-fold matrix.
- [`selection.py`](selection.py) — episode utility, monotonic sizing checks, complexity control and feature-promotion gates.
- [`ablation.py`](ablation.py) — identical-fold price/breadth/VRP/credit feature ablation.
- [`data_audit.py`](data_audit.py) — adjusted-price continuity and split-like discontinuity veto.
- [`leverage.py`](leverage.py) — tactical actual-product SSO/QLD/USD research using unleveraged-underlying signals.
- [`config.example.json`](config.example.json) — asset-specific research-candidate settings.
- [`grid.example.json`](grid.example.json) — bounded parameter-stability grid.
- [`tests/`](tests/) — causal, selection, data-integrity and actual-product execution tests.
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

1. Audit adjusted prices and reject split-like discontinuities.
2. Preserve an outer test fold with an 84-session purge.
3. Calculate episode-level utility across crash, ordinary-correction and long-bear regimes.
4. Apply the **one-standard-error rule** and choose the simplest/lower-capital candidate inside the statistically equivalent set.
5. Persist every candidate-by-fold result rather than only the winner.
6. Add breadth, VRP or credit only when identical-fold ablation shows a positive median gain, bounded worst-fold damage and improvement in at least 60% of comparable folds.
7. Test leverage separately with actual SSO, QLD and USD histories.

The original evaluator omitted drawdown episodes with no trade. The revised engine creates the complete episode catalogue before evaluating trades, so missed bottoms are included in headline metrics. It also applies transaction costs, prevents repeated state bonuses and supports publication-aligned point-in-time features.

No asset parameter is promoted solely because the engine was improved. SPY, QQQ, SMH and SOXX settings remain research candidates until the same archived data is rerun through the revised validation pipeline.

## Data expectations

The price harness expects split- and distribution-adjusted daily OHLCV:

```text
Date,Open,High,Low,Close,Volume
```

Optional non-price inputs follow [`feature-schema.md`](feature-schema.md). Signals are calculated after the close and executed at the next session's open plus configured costs. Data is intentionally not bundled because source licences and corporate-action methodologies differ.

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
  --train-days 1008 \
  --test-days 252 \
  --purge-days 84

python ablation.py \
  --csv data/SPY.csv \
  --features-csv data/SPY-point-in-time-features.csv \
  --symbol SPY \
  --config config.example.json \
  --grid grid.example.json

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
- Formal CSCV/PBO requires the newly persisted candidate-by-fold matrix to be populated with the immutable real datasets.
- Five years of IBKR data do not include dot-com or GFC regimes; external long-cycle stress tests remain necessary.
- No result is a guaranteed bottom, expected return, automatic order or optimal position size.
