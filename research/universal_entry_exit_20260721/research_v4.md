# Universal entry and exit research v4

Date: 2026-07-22  
Completed-close cutoff: 2026-07-21

## Corrections retained from v3

- Completed daily-close signals; next regular-session-open execution.
- Development-only parameter selection; holdout can only approve or reject.
- Actual traded-product returns for leveraged ETFs.
- Liquidity-aware costs, stressed costs, block bootstrap and input fingerprints.
- Stock entry promotions require a current corporate-event check.

## V4 methodological correction

V3's first-stage event study ranked entry events by positive absolute forward returns. In a persistent equity bull market, that can select dates that are profitable but not superior to a random or unconditional date. V4 subtracts the unconditional forward-return median at each horizon and requires positive timing excess in chronological development blocks.

For assets with long histories, the final holdout begins in 2022 where possible. This deliberately includes the 2022 equity bear market, the 2023-2025 recovery and the 2026 sample instead of relying mainly on the recent bull regime.

## New entry families

- Volatility-compression breakout: rising 100/200-day trend, realised-volatility contraction and 20/50-day breakout, optionally volume-confirmed.
- EMA pullback/reclaim: long trend, EMA20 above EMA50, controlled touch of EMA10/20 and close reclaim.
- Drawdown reclaim: 5/10/15% pullback from a 63-day high followed by SMA10/20 recovery inside a long trend.
- Relative-strength breakout: price breakout while the asset/regime ratio remains above its 63/126-day mean.

## New exits and overlays

- Realised-volatility spike plus SMA20/50 failure.
- Relative-strength failure plus SMA20/50 failure.
- Combined regime-trend and breadth permission.
- Combined credit and realised-volatility permission.
- Relative-strength-level permission.

## Added universe

- Hong Kong products: 7709.HK (CSOP SK hynix Daily 2x), 7747.HK (CSOP Samsung Daily 2x), 3191.HK (Global X China Semiconductor ETF).
- Korean stocks: 000660.KS (SK hynix), 005930.KS (Samsung Electronics).
- U.S. stocks: S (SentinelOne), GRAB (Grab Holdings).

7709/7747 are always experimental because of short product history, daily leverage reset, swap/options implementation and secondary-market premium/discount risk. Their signal is generated from the Korean underlying, while returns and costs use the Hong Kong product.

## DRAM and FOTO

Yahoo Finance did not return valid histories in v3. V4 supports committed static OHLC files sourced from IBKR. Because the observed live history is very short, any output remains experimental and cannot receive production promotion.

## Promotion interpretation

The optimiser is allowed to reject every rule for an asset. The objective is not to manufacture an entry signal; it is to identify only timing rules that survive development blocks, a multi-regime holdout, transaction-cost stress, drawdown/Sharpe gates and bootstrap evidence.
