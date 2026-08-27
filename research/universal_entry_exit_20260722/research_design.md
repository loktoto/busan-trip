# Universal ETF and stock entry/exit research design

Date: 2026-07-22

## Objective

Find robust daily entry and exit methods for the user's current ETF holdings and recently tracked individual stocks. The goal is not to maximize one in-sample backtest. The goal is to identify rules that remain useful across related assets, chronological development folds, a final untouched holdout, realistic costs, and repeated data-provider runs.

## Universe

- Current IBKR ETF positions: QQQM, SPMO, VT, VTV, IDMO, FLKR, FMTM, SOXX, DRAM, FOTO, 00935.TW, 2644.T, 7709.HK and 7747.HK.
- Thematic comparison ETF: COPX.
- Recently tracked stocks: NVDA, MU, AMD, TSM, DELL, SMCI, META, MSFT, GOOGL, TSLA, CRCL, RKLB, AAOI, NBIS, SOFI, HOOD, HIMS, RBRK, MXL, MARA, RDW, EQT, GM, EIX, PLAB, ALAB, NU, KTOS, DLO, ZETA, INCY, GRAB, ERIC, CSTM and LITE.

## Asset-specific implementation

### Core ETFs

Core ETFs are not treated as all-in/all-out trades. The model compares a permanent 1.0x holding with a 1.0x/1.5x add-and-trim overlay. A rule must improve the holdout result versus native buy-and-hold before it can be promoted.

### Thematic ETFs and stocks

Thematic ETFs and individual stocks are treated as tactical sleeves switching between cash and 1.0x exposure. The promotion gate focuses on positive holdout CAGR, Sharpe, Calmar, sufficient trades and drawdown control. It does not reward an isolated high CAGR with poor risk-adjusted results.

### Leveraged and structured ETFs

7709.HK and 7747.HK are excluded from generic product-price optimisation. Their entries require underlying trend confirmation plus official NAV/premium and realised tracking-gap controls. Their exits combine underlying trend failure, premium expansion and tracking deterioration.

## Rule families tested

1. Trend pullback and short-average reclaim inside a rising 100/150/200-day regime.
2. Relative-strength pullback versus the relevant benchmark.
3. 20/50/100-day breakout with rolling ATR/price-channel exit.
4. 3/6/12-month time-series momentum with daily moving-average exits.
5. Short-horizon reversal only inside a positive long-term trend.
6. Stock gap-volume drift, designed to capture earnings/news-style information shocks without claiming that every gap is an earnings event.

## Why exits are not one fixed percentage stop

Kaminski and Lo show that stop-loss value depends on the return process and that stops can help in momentum regimes. Lo and Remorov show that tight stops on individual stocks often underperform after transaction costs. The search therefore compares regime exits, moving-average failures, volatility-scaled exits and time stops rather than imposing one universal 5% or 10% stop.

## Research controls

- Completed daily close signal; next regular-session open execution.
- Cluster-level development ranking before asset-level selection.
- Each asset can select only from the ten development winners of its cluster.
- Final holdout cannot rank candidates; it only promotes, watches or rejects the preselected rule.
- 1 bp hysteresis around moving averages and breakouts to prevent tiny provider revisions from flipping signals.
- Sequential single-ticker downloads, compressed input snapshots and SHA-256 fingerprints.
- Canonical output precision and deterministic tie-breaks.
- Costs differ by core ETF, thematic ETF, large stock and high-beta stock.

## Research basis

- Moreira and Muir, *Volatility-Managed Portfolios*: lower exposure when realised volatility is high can improve factor Sharpe ratios.
- Daniel and Moskowitz, *Momentum Crashes*: momentum can crash in high-volatility panic/rebound states, supporting regime-aware sizing and exits.
- Kaminski and Lo, *When Do Stop-Loss Rules Stop Losses?*: stops add value only under particular return dynamics.
- Lo and Remorov, *Stop-Loss Strategies with Serial Correlation, Regime Switching, and Transaction Costs*: tight stock stops often lose value through turnover.
- Medhat and Schmeling, *Short-term Momentum*: turnover/liquidity conditions help distinguish short-term momentum from reversal.
- Recent RFS evidence on short-term reversals and longer-term momentum supports testing both horizons rather than treating them as contradictory.
- PEAD literature supports testing post-information-shock drift; this workflow uses a price/volume gap proxy unless verified earnings-surprise data are available.

## Promotion interpretation

`PROMOTE_OVERLAY` means the core ETF's tactical add/trim overlay passed development and holdout gates. `PROMOTE_TACTICAL` means a cash-to-position rule passed the tactical gates. `WATCH` means the family remains promising but the holdout evidence is not strong enough. `REJECT` means the tested rules do not justify replacing simple holding or discretionary sizing. `SPECIALIST_ONLY` means generic price-only optimisation is invalid for that product.
