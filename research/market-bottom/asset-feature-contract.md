# Asset-Specific Bottom Feature Contract

> Scope: **SPY, QQQ and SOXX only**. This document governs feature construction and prevents cross-asset threshold leakage.

## Common causal core

All three assets use completed daily bars and next-session-open execution. Common price families are unresolved-cycle drawdown, volatility-normalised decline, fresh-low/spacing controls, underwater duration, long-bear throttle, liquidation pressure and subsequent deceleration.

Common feature names do not imply common thresholds. Every candidate parameter must be estimated and validated separately for each underlying.

## SPY

### Preferred non-price evidence

- S&P 500 point-in-time breadth: advance/decline, up/down volume, new highs/lows and percentages above 20/50/200-day averages;
- cap-weighted versus equal-weight divergence, with methodology and rebalance history documented;
- Cboe VIX9D/VIX/VIX3M/VVIX term structure as non-directional volatility context;
- HY OAS and OFR FSI as publication-aligned systemic filters.

### Promotion rule

VIX level or inversion alone cannot promote a tranche. A larger ordinary addition requires price/liquidation deceleration plus breadth or recovery confirmation.

## QQQ

### Preferred non-price evidence

- Nasdaq-100 point-in-time constituent breadth;
- QQQ/SPY relative-strength level, slope and low-price divergence;
- equal-weight Nasdaq versus QQQ divergence;
- realized-volatility deceleration and failed-breakdown/retest quality;
- credit/systemic data as a veto rather than a technology-specific bottom signal.

### Promotion rule

QQQ thresholds must be independently fitted. SPY drawdown levels, VIX thresholds and adverse-excursion assumptions cannot be copied into QQQ.

## SOXX

### Benchmark identity

SOXX currently reports the **NYSE Semiconductor Index** as its benchmark, Bloomberg ticker `ICESEMIT`. Historical constituent breadth intended to explain SOXX must therefore use the point-in-time NYSE/ICE benchmark membership and weights where licensed data are available.

The Nasdaq PHLX Semiconductor Index (`SOX`) is a different modified market-capitalisation-weighted 30-company index. SOX constituent breadth, options or index returns may be useful secondary sector context, but must be labelled **BENCHMARK PROXY** and cannot be represented as exact SOXX breadth.

### Preferred non-price evidence

- NYSE Semiconductor Index point-in-time breadth and new-low participation;
- SOXX/QQQ relative-strength divergence and recovery;
- cross-sectional dispersion across benchmark constituents;
- separate stress measures for semiconductor manufacturers and semiconductor-equipment companies;
- sector liquidation volume and close-location deceleration;
- SOXX realized volatility versus implied volatility as context, never a standalone bottom vote;
- broad credit stress only as a systemic veto.

### Promotion rule

A SOXX price-only signal may remain a provisional watch or small-probe candidate. Exhaustion and confirmed-bottom promotion require either verified benchmark breadth/dispersion evidence or a separately validated price-only alternative that survives the long-cycle and worst-regime gates.

## Feature provenance

For every external feature store:

- source and series identifier;
- economic observation date;
- publication/availability timestamp and timezone;
- constituent and weighting methodology where relevant;
- revision policy;
- survivorship-bias classification;
- immutable file hash when archived.

Missing or proxy data must remain visibly missing/proxy. They must not be filled with zero or silently promoted to genuine point-in-time evidence.
