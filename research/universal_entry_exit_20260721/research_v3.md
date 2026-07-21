# Universal daily entry and exit research v3

Date: 2026-07-21  
Completed-close cutoff: 2026-07-20  
Scope: current IBKR ETF positions, strategic ETF watchlist, Mag 7 + TSM, and the user's active single-stock research universe.

## Objective

Find an independently selected daily entry and exit method for every instrument. The optimiser must not apply the SPY rule to semiconductors, crypto, metals, uranium, inverse volatility, international equities, or individual stocks merely because one rule worked elsewhere.

Two distinct decisions are evaluated:

1. **Swing timing** — move between cash proxy BIL and the traded instrument.
2. **Core add/reduce** — retain the 1x core and add or remove a 0.5x tranche. Financing on the extra tranche is represented by the BIL return.

Leveraged ETFs are evaluated only in swing mode. Their signal is generated from the unleveraged underlying where one exists, while realised returns, drawdowns and transaction costs use the actual leveraged product. SVIX receives dedicated VIX/VIX3M contango, VIX-cap, volatility-spike and SVIX-trend entry/exit families; generic equity RSI rules are not used for SVIX.

## Universe

The configuration includes broad equity, momentum/value, international, semiconductor, memory, photonics, metals/miners, uranium, crypto, Europe, inverse-volatility and regional ETFs. It also includes the Mag 7, TSM, AVGO, AMD, MU, ORCL, AAOI, NBIS, CRCL, MARA, PLTR, LITE, COHR, DELL, SMCI, SOFI, HOOD, HIMS, RBRK, MXL, RDW, ALAB, NU, DLO, ZETA, CSTM, KTOS and FN.

New funds such as DRAM and FOTO and every instrument with fewer than 1,000 common trading sessions are always marked experimental until a meaningful final holdout exists. The HSBC MSCI World holding is mapped to its Paris listing `WRD.PA`, not the unrelated U.S. ADR using ticker WRD. Taiwan 00935 and Japan 2644 are included with their local Yahoo symbols; calendar and FX differences remain explicit limitations.

## Stage 1: entry event study

Every asset receives its own search over four interpretable entry families:

- Pullback and short-moving-average reclaim inside a rising 100/200-day trend.
- Trend-conditioned mean reversion using RSI(2), a 20-day z-score and optional bullish close.
- 20/50/100-day breakout above a rising long-term trend.
- 63/126/252-day time-series momentum with a limited 20-day pullback.

Signals use a 1 basis-point hysteresis around moving averages and breakouts so tiny adjusted-price revisions cannot flip a rule. Entries execute at the following regular-session open. The event study evaluates 5, 10, 20 and 40-session forward returns and chronological development blocks. The final holdout does not rank entries.

## Stage 2: exit selection

Only a small development shortlist advances. Exit families are then tested independently:

- RSI(2) recovery combined with a 10/20/50-day moving-average failure.
- 10/20/50-day Donchian breakdown.
- 10/20/40-session maximum holding period.

This separation prevents a favourable exit from making an otherwise poor entry appear statistically useful.

## Stage 3: regime and risk management

Only the best development entry/exit pairs advance to:

- No overlay.
- Long-term regime trend.
- Asset-class breadth ratio.
- HYG/LQD credit confirmation.
- Realised-volatility contraction.
- 126-day relative strength versus the class regime proxy.

Trade management compares no hard stop, 8% and 12% hard stops, and 3/4 ATR trailing stops. Stop policies are not presumed helpful: they must improve the asset's own development evidence and survive holdout.

## Asset-specific signal mapping

- SOXL uses SOXX signals; UPRO uses SPY.
- BITX uses BTC-USD; AGQ uses SLV; GDXU uses GDX; URAA uses URA; EURL uses VGK.
- HODL uses BTC-USD and ETHA uses ETH-USD.
- Semiconductor stocks use SOXX/XSD context.
- Mega-cap and growth stocks use QQQ/QQEW context.
- Crypto equities use BTC and CRPT context.
- Metals, uranium, defence and international assets use their own sector or regional proxies.

## Selection and promotion gates

The workflow stores every adjusted OHLCV input and its SHA-256 fingerprint. Winner selection is development-only. A production alpha promotion requires:

- Positive development CAGR excess over buy-and-hold.
- Non-negative development Sharpe delta.
- No material development drawdown deterioration.
- Positive median chronological-block excess and a bounded worst block.
- Positive development excess after stressed transaction costs.
- Positive final-holdout CAGR excess, acceptable holdout Sharpe and drawdown.
- Positive full-sample stressed excess.
- At least 65% moving-block-bootstrap probability of positive annualised mean excess.
- Sufficient trades and a non-experimental history.

A swing rule that improves holdout Sharpe and drawdown but does not demonstrate alpha is labelled **risk-control only**, not promoted as an alpha strategy. All rejected or experimental diagnostic signals have `production_action=NO_ACTION`.

## Costs and execution

Base round-trip assumptions vary by liquidity and instrument type. Broad ETFs and mega-cap stocks use low single-digit basis points; thematic, leveraged, crypto and local-market products use progressively higher assumptions. Stress cost is the greater of twice base cost or base cost plus 20 basis points.

IBKR is used to identify the actual portfolio/trading universe, audit contracts, market state and representative liquidity. GitHub Actions uses adjusted public OHLCV for a reproducible full-history run and retains the exact inputs in the artifact.

## Research basis

The tested families reflect several evidence strands rather than one technical indicator:

- Time-series momentum documents trend persistence across liquid asset classes.
- Systematic technical pattern recognition can contain conditional return information, but requires objective definitions and statistical validation.
- Volatility-managed allocation may improve risk-adjusted returns, while related research warns that volatility scaling itself can explain apparent momentum alpha.
- Stop-loss rules can help in some trending regimes but are not universally value-adding.
- Fixed trading costs create no-trade regions, supporting hysteresis and liquidity-aware thresholds.

## Limitations

Historical earnings calendars are not sufficiently complete in the selected reproducible data source. The workflow therefore does not pretend to backtest an earnings blackout. Stock outputs record the latest overnight gap and the largest absolute gap in the prior 20 sessions. Any new stock `ENTER` or `ADD` promotion is labelled `EVENT_CHECK` until a verified corporate-event calendar is checked; reductions and exits are not blocked.

No historical promotion guarantees future outperformance. The purpose of the gates is to reject fragile rules, not to manufacture a signal for every ticker.
