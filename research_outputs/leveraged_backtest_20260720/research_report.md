# Leveraged ETF Entry/Exit Backtest — Full Rebuild

Generated with data through 2026-07-17.

## Method

- Longest available adjusted daily history from Yahoo Finance; failed tickers are disclosed in `data_manifest.csv`.
- Signals use the unleveraged underlying. Trades are delayed to the next open; open-to-open returns are used.
- Long-history synthetic 2x/3x returns include conservative annual drag calibrated against actual ETFs where possible, never below 5% for 2x or 9% for 3x.
- Base transaction cost: 10 bps per side. Stress: 30 bps plus 8.2%/15.2% annual drag for 2x/3x.
- Strategy selection is evaluated with first-60%/last-40% pseudo-OOS, rolling 3Y/5Y windows, actual ETF validation and leave-one-asset-out tests.
- Gap/volume rules are price-event proxies, not true point-in-time earnings-surprise backtests.

## Index universe — 2x: top robust exact strategies

| strategy        | family                   |   final_score |   asset_count | median_cagr   | median_late_cagr   | median_stress_cagr   | worst_maxdd   |   median_sharpe |   median_trades |
|:----------------|:-------------------------|--------------:|--------------:|:--------------|:-------------------|:---------------------|:--------------|----------------:|----------------:|
| MA_50_200       | ma_crossover             |         0.938 |             3 | 14.7%         | 23.0%              | 11.8%                | -66.0%        |           0.599 |              16 |
| TSMOM_E4_X0     | time_series_momentum     |         0.926 |             3 | 14.2%         | 21.1%              | 11.3%                | -69.5%        |           0.584 |              28 |
| PRICE_SMA200_H1 | price_hysteresis         |         0.889 |             3 | 11.6%         | 22.1%              | 8.3%                 | -80.5%        |           0.574 |              47 |
| PRICE_SMA200_H2 | price_hysteresis         |         0.885 |             3 | 13.4%         | 19.1%              | 10.4%                | -78.6%        |           0.608 |              32 |
| MHT_E6_X1       | multi_horizon_trend      |         0.884 |             3 | 11.5%         | 23.1%              | 8.8%                 | -73.4%        |           0.536 |              28 |
| PRICE_SMA200_H3 | price_hysteresis         |         0.883 |             3 | 13.5%         | 19.9%              | 10.6%                | -75.0%        |           0.573 |              24 |
| TSMOM_E3_X0     | time_series_momentum     |         0.873 |             3 | 14.3%         | 23.2%              | 10.9%                | -81.2%        |           0.55  |              38 |
| MHT_VOL_E4_VR80 | volatility_managed_trend |         0.864 |             3 | 9.4%          | 17.1%              | 6.7%                 | -65.4%        |           0.469 |              53 |
| MHT_VOL_E5_VR80 | volatility_managed_trend |         0.853 |             3 | 8.0%          | 16.4%              | 5.2%                 | -72.2%        |           0.479 |              49 |
| MHT_E5_X1       | multi_horizon_trend      |         0.849 |             3 | 14.3%         | 27.9%              | 11.1%                | -85.2%        |           0.555 |              39 |
| PRICE_SMA200_H0 | price_hysteresis         |         0.834 |             3 | 10.2%         | 18.6%              | 6.2%                 | -82.4%        |           0.524 |              95 |
| MHT_E4_X1       | multi_horizon_trend      |         0.825 |             3 | 10.7%         | 28.0%              | 7.2%                 | -87.0%        |           0.529 |              55 |

### Index universe — 2x: family ranking

| family                   |   best_final_score |   median_final_score | median_cagr   | median_late_cagr   | median_stress_cagr   | worst_maxdd   |
|:-------------------------|-------------------:|---------------------:|:--------------|:-------------------|:---------------------|:--------------|
| ma_crossover             |              0.938 |                0.621 | 6.7%          | 19.9%              | 2.7%                 | -95.8%        |
| time_series_momentum     |              0.926 |                0.81  | 9.5%          | 15.4%              | 6.2%                 | -83.1%        |
| price_hysteresis         |              0.889 |                0.71  | 8.4%          | 17.9%              | 4.7%                 | -96.6%        |
| multi_horizon_trend      |              0.884 |                0.8   | 9.5%          | 16.2%              | 5.9%                 | -87.0%        |
| volatility_managed_trend |              0.864 |                0.76  | 8.3%          | 15.4%              | 5.1%                 | -80.4%        |
| pullback_reclaim         |              0.782 |                0.391 | 1.4%          | 0.1%               | -1.6%                | -87.3%        |
| breakout                 |              0.74  |                0.505 | 2.9%          | 7.9%               | -0.1%                | -91.9%        |
| drawdown_reclaim         |              0.58  |                0.475 | 1.9%          | 0.4%               | -1.3%                | -45.9%        |

## Index universe — 3x: top robust exact strategies

| strategy              | family                   |   final_score |   asset_count | median_cagr   | median_late_cagr   | median_stress_cagr   | worst_maxdd   |   median_sharpe |   median_trades |
|:----------------------|:-------------------------|--------------:|--------------:|:--------------|:-------------------|:---------------------|:--------------|----------------:|----------------:|
| MA_50_200             | ma_crossover             |         0.925 |             3 | 16.0%         | 27.2%              | 10.5%                | -84.3%        |           0.573 |              16 |
| TSMOM_E4_X0           | time_series_momentum     |         0.924 |             3 | 16.8%         | 26.6%              | 11.2%                | -87.1%        |           0.571 |              28 |
| PRICE_SMA200_H1       | price_hysteresis         |         0.89  |             3 | 14.1%         | 27.5%              | 8.3%                 | -93.3%        |           0.547 |              47 |
| MHT_E6_X1             | multi_horizon_trend      |         0.888 |             3 | 12.4%         | 30.1%              | 7.5%                 | -88.7%        |           0.51  |              28 |
| PRICE_SMA200_H2       | price_hysteresis         |         0.879 |             3 | 16.8%         | 22.9%              | 11.1%                | -92.4%        |           0.595 |              32 |
| PRICE_SMA200_H3       | price_hysteresis         |         0.876 |             3 | 16.1%         | 24.1%              | 10.9%                | -91.4%        |           0.559 |              24 |
| TSMOM_E3_X0           | time_series_momentum     |         0.862 |             3 | 14.6%         | 29.1%              | 8.7%                 | -95.2%        |           0.537 |              38 |
| MHT_VOL_E4_VR80       | volatility_managed_trend |         0.862 |             3 | 10.5%         | 21.8%              | 5.9%                 | -83.9%        |           0.451 |              53 |
| MHT_VOL_E5_VR80       | volatility_managed_trend |         0.851 |             3 | 9.6%          | 21.0%              | 4.8%                 | -88.5%        |           0.456 |              49 |
| MHT_E5_X1             | multi_horizon_trend      |         0.84  |             3 | 14.8%         | 37.4%              | 9.4%                 | -95.6%        |           0.543 |              39 |
| PRICE_SMA200_H0       | price_hysteresis         |         0.829 |             3 | 12.3%         | 22.2%              | 5.7%                 | -94.2%        |           0.502 |              95 |
| RSI2_15_REC3_XR70_T20 | pullback_reclaim         |         0.826 |             3 | 8.8%          | 6.1%               | 3.5%                 | -63.1%        |           0.605 |             279 |

### Index universe — 3x: family ranking

| family                   |   best_final_score |   median_final_score | median_cagr   | median_late_cagr   | median_stress_cagr   | worst_maxdd   |
|:-------------------------|-------------------:|---------------------:|:--------------|:-------------------|:---------------------|:--------------|
| ma_crossover             |              0.925 |                0.494 | 4.4%          | 26.6%              | -0.7%                | -99.6%        |
| time_series_momentum     |              0.924 |                0.806 | 11.2%         | 19.4%              | 5.5%                 | -95.2%        |
| price_hysteresis         |              0.89  |                0.689 | 6.9%          | 22.0%              | 1.3%                 | -99.8%        |
| multi_horizon_trend      |              0.888 |                0.798 | 10.1%         | 19.9%              | 4.2%                 | -95.9%        |
| volatility_managed_trend |              0.862 |                0.727 | 8.3%          | 19.1%              | 2.9%                 | -93.4%        |
| pullback_reclaim         |              0.826 |                0.415 | 1.5%          | -0.5%              | -1.2%                | -96.4%        |
| breakout                 |              0.729 |                0.474 | 1.9%          | 10.1%              | -1.9%                | -98.8%        |
| drawdown_reclaim         |              0.674 |                0.559 | 2.8%          | 0.2%               | -0.7%                | -59.4%        |

## Single-stock universe — 2x: top robust exact strategies

| strategy         | family                   |   final_score |   asset_count | median_cagr   | median_late_cagr   | median_stress_cagr   | worst_maxdd   |   median_sharpe |   median_trades |
|:-----------------|:-------------------------|--------------:|--------------:|:--------------|:-------------------|:---------------------|:--------------|----------------:|----------------:|
| MHT_E4_X1        | multi_horizon_trend      |         0.871 |             9 | 16.7%         | 25.2%              | 17.1%                | -99.6%        |           0.573 |              63 |
| TSMOM_E3_X1      | time_series_momentum     |         0.852 |             9 | 17.6%         | 21.7%              | 17.9%                | -99.7%        |           0.602 |              98 |
| TSMOM_E3_X0      | time_series_momentum     |         0.849 |             9 | 18.5%         | 22.1%              | 20.3%                | -100.0%       |           0.615 |              44 |
| PRICE_SMA200_H1  | price_hysteresis         |         0.846 |             9 | 16.3%         | 22.4%              | 17.2%                | -99.9%        |           0.554 |              66 |
| MHT_VOL_E5_VR100 | volatility_managed_trend |         0.845 |             9 | 17.5%         | 18.8%              | 18.6%                | -99.0%        |           0.588 |              73 |
| TSMOM_E4_X0      | time_series_momentum     |         0.842 |             9 | 17.6%         | 23.5%              | 19.0%                | -99.9%        |           0.572 |              30 |
| MHT_VOL_E5_VR125 | volatility_managed_trend |         0.833 |             9 | 16.7%         | 18.8%              | 17.2%                | -99.6%        |           0.576 |              85 |
| MHT_VOL_E5_VR80  | volatility_managed_trend |         0.825 |             9 | 17.6%         | 21.9%              | 18.5%                | -98.1%        |           0.574 |              51 |
| MA_10_30         | ma_crossover             |         0.812 |             9 | 20.4%         | 19.4%              | 20.2%                | -100.0%       |           0.632 |             130 |
| MHT_VOL_E4_VR80  | volatility_managed_trend |         0.805 |             9 | 18.8%         | 21.6%              | 19.8%                | -97.8%        |           0.594 |              62 |
| MHT_E5_X1        | multi_horizon_trend      |         0.8   |             9 | 14.6%         | 19.9%              | 16.2%                | -99.8%        |           0.573 |              50 |
| MHT_E5_X2        | multi_horizon_trend      |         0.8   |             9 | 14.8%         | 23.3%              | 14.8%                | -99.4%        |           0.53  |              86 |

### Single-stock universe — 2x: family ranking

| family                   |   best_final_score |   median_final_score | median_cagr   | median_late_cagr   | median_stress_cagr   | worst_maxdd   |
|:-------------------------|-------------------:|---------------------:|:--------------|:-------------------|:---------------------|:--------------|
| multi_horizon_trend      |              0.871 |                0.722 | 14.6%         | 20.1%              | 14.8%                | -99.8%        |
| time_series_momentum     |              0.852 |                0.812 | 16.6%         | 19.4%              | 17.2%                | -100.0%       |
| price_hysteresis         |              0.846 |                0.698 | 15.3%         | 20.0%              | 15.1%                | -100.0%       |
| volatility_managed_trend |              0.845 |                0.815 | 17.1%         | 19.5%              | 17.8%                | -99.6%        |
| ma_crossover             |              0.812 |                0.666 | 13.7%         | 19.4%              | 13.9%                | -100.0%       |
| breakout                 |              0.763 |                0.673 | 10.7%         | 16.9%              | 10.3%                | -99.9%        |
| relative_strength        |              0.703 |                0.646 | 8.4%          | 18.5%              | 5.9%                 | -98.3%        |
| gap_momentum_proxy       |              0.616 |                0.464 | 1.2%          | 5.6%               | 0.9%                 | -98.2%        |
| drawdown_reclaim         |              0.552 |                0.254 | -0.8%         | -0.2%              | -3.9%                | -95.2%        |
| pullback_reclaim         |              0.5   |                0.275 | -0.8%         | 0.6%               | -2.6%                | -100.0%       |

## SPY / QQQ / SOXX — best strategy constrained to pooled top 15

| asset   |   leverage | strategy              | family              | cagr   | late_cagr   | stress_cagr   |   sharpe | maxdd   |   calmar |   trades |   exposure |
|:--------|-----------:|:----------------------|:--------------------|:-------|:------------|:--------------|---------:|:--------|---------:|---------:|-----------:|
| QQQ     |          2 | MA_50_200             | ma_crossover        | 14.7%  | 23.0%       | 11.8%         |    0.555 | -64.3%  |    0.228 |       17 |      0.715 |
| SOXX    |          2 | MHT_E6_X1             | multi_horizon_trend | 20.3%  | 38.8%       | 17.5%         |    0.653 | -61.6%  |    0.329 |       28 |      0.599 |
| SPY     |          2 | PRICE_SMA200_H2       | price_hysteresis    | 13.4%  | 14.7%       | 10.4%         |    0.635 | -39.4%  |    0.34  |       25 |      0.749 |
| QQQ     |          3 | RSI2_15_REC3_XR70_T20 | pullback_reclaim    | 13.2%  | 8.5%        | 8.0%          |    0.654 | -45.0%  |    0.294 |      279 |      0.112 |
| SOXX    |          3 | MHT_E6_X1             | multi_horizon_trend | 22.5%  | 46.6%       | 17.5%         |    0.641 | -77.7%  |    0.289 |       28 |      0.599 |
| SPY     |          3 | RSI2_15_REC3_XR70_T20 | pullback_reclaim    | 8.8%   | 6.1%        | 3.5%          |    0.605 | -28.1%  |    0.313 |      358 |      0.12  |

## Pseudo-OOS: strategy selected on first 60%, tested on final 40%

| universe   |   leverage | asset   | selected_strategy     | family               |   early_cagr | late_cagr   |   late_sharpe |   late_maxdd |   late_calmar |
|:-----------|-----------:|:--------|:----------------------|:---------------------|-------------:|:------------|--------------:|-------------:|--------------:|
| index      |          2 | QQQ     | RSI2_15_REC3_XR70_T10 | pullback_reclaim     |        0.108 | 5.8%        |         0.416 |       -0.313 |         0.187 |
| index      |          2 | SOXX    | RSI2_10_REC5_XR70_T20 | pullback_reclaim     |        0.048 | 1.1%        |         0.15  |       -0.336 |         0.034 |
| index      |          2 | SPY     | RSI2_15_REC3_XR70_T20 | pullback_reclaim     |        0.067 | 3.6%        |         0.38  |       -0.164 |         0.222 |
| index      |          3 | QQQ     | RSI2_15_REC3_XR70_T10 | pullback_reclaim     |        0.167 | 8.6%        |         0.45  |       -0.45  |         0.19  |
| index      |          3 | SOXX    | RSI2_10_REC5_XR70_T20 | pullback_reclaim     |        0.072 | 1.5%        |         0.176 |       -0.466 |         0.031 |
| index      |          3 | SPY     | RSI2_15_REC3_XR70_T20 | pullback_reclaim     |        0.107 | 6.1%        |         0.439 |       -0.231 |         0.263 |
| stock      |          2 | AAPL    | BRK50_F200_XMA50      | breakout             |        0.237 | 19.5%       |         0.686 |       -0.539 |         0.362 |
| stock      |          2 | AMD     | PRICE_SMA50_H1        | price_hysteresis     |        0.161 | 15.6%       |         0.588 |       -0.957 |         0.163 |
| stock      |          2 | AMZN    | TSMOM_E4_X1           | time_series_momentum |        0.234 | 5.0%        |         0.339 |       -0.864 |         0.058 |
| stock      |          2 | GOOGL   | MA_10_20              | ma_crossover         |        0.315 | 7.4%        |         0.383 |       -0.675 |         0.109 |
| stock      |          2 | META    | TSMOM_E3_X0           | time_series_momentum |        0.423 | 31.0%       |         0.742 |       -0.742 |         0.418 |
| stock      |          2 | MSFT    | MA_10_20              | ma_crossover         |        0.263 | 6.0%        |         0.344 |       -0.641 |         0.094 |
| stock      |          2 | MU      | RSI2_15_REC5_XR70_T20 | pullback_reclaim     |        0.105 | 2.8%        |         0.246 |       -0.702 |         0.039 |
| stock      |          2 | NVDA    | DD50_5_REC5_T10       | drawdown_reclaim     |        0.285 | 5.0%        |         0.317 |       -0.586 |         0.086 |
| stock      |          2 | TSLA    | BRK20_F100_XMA10      | breakout             |        0.384 | 59.3%       |         1.009 |       -0.521 |         1.138 |

## Leave-one-asset-out

| universe   |   leverage | heldout_asset   | selected_strategy     | family                   |   heldout_cagr |   heldout_late_cagr |   heldout_sharpe |   heldout_maxdd |   heldout_calmar |
|:-----------|-----------:|:----------------|:----------------------|:-------------------------|---------------:|--------------------:|-----------------:|----------------:|-----------------:|
| index      |          2 | QQQ             | PRICE_SMA200_H2       | price_hysteresis         |          0.095 |               0.191 |            0.437 |          -0.786 |            0.121 |
| index      |          2 | SOXX            | RSI2_15_REC3_XR70_T20 | pullback_reclaim         |          0.036 |               0.031 |            0.28  |          -0.463 |            0.079 |
| index      |          2 | SPY             | MA_50_200             | ma_crossover             |          0.133 |               0.13  |            0.599 |          -0.559 |            0.237 |
| index      |          3 | QQQ             | PRICE_SMA200_H1       | price_hysteresis         |          0.088 |               0.275 |            0.426 |          -0.933 |            0.095 |
| index      |          3 | SOXX            | RSI2_15_REC3_XR70_T20 | pullback_reclaim         |          0.047 |               0.031 |            0.305 |          -0.631 |            0.075 |
| index      |          3 | SPY             | MA_50_200             | ma_crossover             |          0.16  |               0.151 |            0.573 |          -0.726 |            0.22  |
| stock      |          2 | AAPL            | MA_10_30              | ma_crossover             |          0.168 |               0.21  |            0.557 |          -0.921 |            0.183 |
| stock      |          2 | AMD             | MHT_VOL_E5_VR80       | volatility_managed_trend |          0.095 |               0.295 |            0.477 |          -0.981 |            0.097 |
| stock      |          2 | AMZN            | MA_10_30              | ma_crossover             |          0.068 |               0.194 |            0.494 |          -1     |            0.068 |
| stock      |          2 | GOOGL           | MHT_VOL_E5_VR80       | volatility_managed_trend |          0.086 |               0.116 |            0.407 |          -0.765 |            0.113 |
| stock      |          2 | META            | BRK126_F200_XMA50     | breakout                 |          0.001 |               0.203 |            0.204 |          -0.889 |            0.001 |
| stock      |          2 | MSFT            | BRK126_F200_XMA50     | breakout                 |          0.093 |               0.045 |            0.432 |          -0.858 |            0.109 |
| stock      |          2 | MU              | MA_10_30              | ma_crossover             |          0.026 |               0.068 |            0.455 |          -1     |            0.026 |
| stock      |          2 | NVDA            | MA_10_30              | ma_crossover             |          0.263 |               0.671 |            0.691 |          -0.959 |            0.274 |
| stock      |          2 | TSLA            | MHT_VOL_E5_VR80       | volatility_managed_trend |          0.211 |               0.219 |            0.622 |          -0.894 |            0.236 |

## Current signals for constrained winners

| asset   | universe   |   leverage | strategy              | family                   | signal_date   |   target_position | last_entry_signal   | last_exit_signal   |
|:--------|:-----------|-----------:|:----------------------|:-------------------------|:--------------|------------------:|:--------------------|:-------------------|
| QQQ     | index      |          2 | MA_50_200             | ma_crossover             | 2026-07-17    |                 1 | 2025-06-23          | 2025-04-14         |
| SOXX    | index      |          2 | MHT_E6_X1             | multi_horizon_trend      | 2026-07-17    |                 1 | 2025-06-03          | 2025-02-25         |
| SPY     | index      |          2 | PRICE_SMA200_H2       | price_hysteresis         | 2026-07-17    |                 1 | 2026-04-08          | 2026-03-27         |
| QQQ     | index      |          3 | RSI2_15_REC3_XR70_T20 | pullback_reclaim         | 2026-07-17    |                 0 | 2026-06-25          | 2026-06-29         |
| SOXX    | index      |          3 | MHT_E6_X1             | multi_horizon_trend      | 2026-07-17    |                 1 | 2025-06-03          | 2025-02-25         |
| SPY     | index      |          3 | RSI2_15_REC3_XR70_T20 | pullback_reclaim         | 2026-07-17    |                 0 | 2026-06-25          | 2026-06-29         |
| AAPL    | stock      |          2 | MHT_VOL_E5_VR80       | volatility_managed_trend | 2026-07-17    |                 1 | 2026-05-27          | 2026-01-20         |
| AMD     | stock      |          2 | MA_10_30              | ma_crossover             | 2026-07-17    |                 1 | 2026-03-26          | 2026-02-10         |
| AMZN    | stock      |          2 | TSMOM_E4_X0           | time_series_momentum     | 2026-07-17    |                 1 | 2026-04-14          | 2026-02-06         |
| GOOGL   | stock      |          2 | TSMOM_E3_X1           | time_series_momentum     | 2026-07-17    |                 1 | 2026-04-08          | 2026-03-23         |
| META    | stock      |          2 | MHT_VOL_E4_VR80       | volatility_managed_trend | 2026-07-17    |                 0 | 2026-04-29          | 2026-04-30         |
| MSFT    | stock      |          2 | MA_10_30              | ma_crossover             | 2026-07-17    |                 1 | 2026-07-16          | 2026-06-12         |
| MU      | stock      |          2 | MHT_VOL_E4_VR100      | volatility_managed_trend | 2026-07-17    |                 1 | 2025-05-27          | 2025-05-23         |
| NVDA    | stock      |          2 | MHT_VOL_E5_VR100      | volatility_managed_trend | 2026-07-17    |                 1 | 2026-04-13          | 2026-02-03         |
| TSLA    | stock      |          2 | MA_10_30              | ma_crossover             | 2026-07-17    |                 0 | 2026-07-10          | 2026-07-16         |

## Data failures / exclusions

None.

## Interpretation guardrails

- A high in-sample CAGR is not enough. Prefer strategies that remain near the top across assets, later samples, stress costs and actual ETF prices.
- Single-stock leveraged ETFs have short actual histories and some changed target leverage; synthetic history is therefore the primary long-cycle test and actual products are validation only.
- SOXX-to-SOXL/USD validation contains index-methodology and tracking differences; treat it as semiconductor-sector validation, not a perfect same-index replication.
- No strategy should be deployed at full size without paper trading and live fill/slippage validation.