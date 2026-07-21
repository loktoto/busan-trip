# Market Bottom Zone Research

> Status: **AUDITED PROVISIONAL**  
> Scope: SPY, QQQ, SMH, SOXX; tactical leverage mappings SPY→SSO, QQQ→QLD, SMH/SOXX→USD.

This directory documents the market-bottom research used by the `Bottom Zone Monitor`.

The objective is **not** to predict the exact lowest tick. The objective is to identify a sufficiently close bottom zone where measured additions to ordinary 1× exposure have an acceptable additional-downside risk. Leveraged ETFs are treated separately and are considered only after bottom confirmation for a temporary rebound trade.

## Files

- [`strategy.md`](strategy.md) — signal hierarchy, states, staged sizing and leverage rules.
- [`backtest-results.md`](backtest-results.md) — results reported from the research runs, limitations and rejected approaches.
- [`backtest.py`](backtest.py) — causal backtest harness for adjusted daily OHLCV data.
- [`config.example.json`](config.example.json) — example asset-specific parameters.
- [`requirements.txt`](requirements.txt) — minimal Python dependencies.

## Key conclusion

The strongest price-only candidate found so far is a **causal, back-loaded bottom-wave framework** combining:

1. drawdown from the unresolved cycle high;
2. volatility-normalized decline speed;
3. a nonlinear deployment curve that preserves most capital for deeper declines;
4. fresh-low, cooldown and previous-entry spacing rules;
5. an underwater-duration / long-bear throttle;
6. liquidation and volume-exhaustion evidence.

Price-only signals are useful for placing a **small probe** near later troughs, but they cannot reliably determine whether a 20% decline is the final low or the midpoint of a 40%–60% bear market. Breadth divergence, volatility/fear-premium information and credit/systemic filters are therefore required before larger additions.

## Important limitations

- The backtest snapshots in this directory were produced during iterative research and are not a fully archived institutional research package.
- The raw point-in-time signal ledger, licensed market datasets and every intermediate parameter run are not committed here.
- Reported figures are therefore labelled **PROVISIONAL / NOT YET INDEPENDENTLY REPRODUCED**.
- Historical SMH/SOXX tests are less mature than SPY/QQQ tests.
- No result should be interpreted as a guaranteed bottom, expected return, automatic order or optimal position size.

## Data expectations

The backtest harness expects split- and distribution-adjusted daily OHLCV data with these columns:

```text
Date,Open,High,Low,Close,Volume
```

Signals are calculated after the close and executed at the next session's open. Data is intentionally not bundled in the repository because source licences and corporate-action methodologies differ.
