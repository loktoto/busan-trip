# TA Performance Measurement Methodology

## 1. Signal population

Track every model decision classified as:

- BREAKOUT STARTER
- BREAKOUT CONFIRMED
- ADD ON RETEST
- RE-ENTRY CONFIRMED
- COUNTER-TREND STARTER
- FAILED BREAKOUT
- FAILED RE-ENTRY
- STOP HIT
- TP1 / TP2 / TP3 HIT
- SETUP REVISED or SETUP INVALID

WATCH and BREAKOUT PENDING observations are retained only when they later become actionable or are materially revised.

## 2. Timestamp and executable price

The decision timestamp is the time the monitor completed its analysis. Performance is measured from the first realistically executable price after the alert, not from an earlier intrabar wick.

- RTH: use the next available bid/ask midpoint or conservative side of spread.
- Overnight/premarket/after-hours: record the session and apply a liquidity flag.
- If quote or spread is unavailable, mark `UNEXECUTABLE` and exclude it from primary expectancy statistics.

## 3. Frozen levels

Entry zone, tactical stop, structural stop and TP1/TP2/TP3 are frozen at signal time. Later changes must be separate `SETUP REVISED` events; history is never overwritten.

## 4. Outcome metrics

For each actionable long signal calculate:

- 1, 5 and 10 completed-session returns
- maximum favorable excursion (MFE) in R
- maximum adverse excursion (MAE) in R
- time to TP1, TP2, TP3 or stop
- whether TP1/TP2/TP3 was reached before tactical stop
- realized model outcome using the frozen management rules

`R = executable entry price - tactical stop` for long signals.

## 5. Performance summaries

Report separately by:

- ticker
- sector group
- signal type
- score tier
- validated 7+ versus unvalidated
- weekly/daily alignment category
- RTH versus extended-hours signal
- event-adjusted versus ordinary setup

Primary statistics:

- number of signals
- win rate
- expectancy in R
- median and mean return
- profit factor
- average MFE and MAE
- TP1/TP2/TP3 hit rates
- stop rate
- maximum losing streak
- signal-level equity-curve drawdown

## 6. Anti-bias controls

- No deletion of losing signals.
- No retroactive change to entry, stop, targets or score.
- Model signals and actual user trades remain separate datasets.
- Duplicated alerts for the same unchanged setup are not new signals.
- Re-entry after a target or invalidation receives a new signal ID.
- Data-degraded runs cannot create a validated entry signal.

## 7. Review schedule

Evaluate only after sufficient sample size. Preliminary summaries may be shown after 20 actionable signals, but strategy-level conclusions require at least 50 signals and should include out-of-sample or walk-forward testing.
