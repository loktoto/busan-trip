# Daily leveraged-entry research — 2026-07-21

This directory contains the daily-signal rebuild for **SPY**, **SOXX**, and **MAGS7 + TSM**.

## Files

- `baseline_report.md` — audited baseline result produced from IBKR/local daily histories.
- `optimize_daily_leverage.py` — reproducible second-stage optimiser using adjusted OHLC data and actual leveraged ETFs where histories overlap.
- `research_outputs/daily_leverage_20260721/` — generated CSV and Markdown outputs when the optimiser runs.

## Execution model

- Signal is calculated only after the regular-session close.
- Position changes take effect at the following regular-session open.
- Returns are measured open-to-open after execution.
- The off-state remains invested in the native 1× asset.
- Product switching costs are deducted whenever the selected instrument changes.

## Validation policy

Parameters are selected using the training sample only. The later sample remains untouched out-of-sample validation. A candidate is not promoted only because it has the highest CAGR: it must also pass Sharpe, drawdown, cost-stress, rolling-window and parameter-neighbour tests.

## Limitations

- MAGS/MAGX/TSMX have short live histories, so MAGS7 + TSM has materially lower confidence than SPY.
- CI uses adjusted Yahoo OHLC for reproducibility; the baseline report uses IBKR/local datasets available during the original audit.
- Historical outperformance does not guarantee future outperformance.
