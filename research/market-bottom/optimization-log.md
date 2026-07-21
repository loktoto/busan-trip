# Optimisation Log

## 2026-07-21 — Validation and causal-engine pass

### Corrected biases and bugs

1. **Missed episodes were excluded from the old evaluator.**
   - Old behaviour: headline rates were calculated only from episodes containing at least one trade.
   - Fix: build the complete episode catalogue first and retain no-trade episodes with `missed=true`.

2. **Asset configuration did not inherit `default`.**
   - Fix: merge common defaults first, then overlay the symbol block.

3. **Exhaustion and confirmation bonuses could repeat.**
   - Fix: bonuses apply only on a false→true transition.

4. **Current-bar rolling low was used as its own comparison.**
   - Fix: shift prior 10/20-session lows by one bar.

### Added controls

- transaction costs and slippage;
- completed and incomplete episode separation;
- worst post-entry adverse excursion;
- optional point-in-time breadth, downside-VRP, HY OAS and OFR FSI;
- credit/systemic veto;
- purged walk-forward selection;
- bounded parameter grids;
- episode bootstrap intervals;
- regression tests for causal execution, missed episodes, inheritance, missingness and tranche limits.

### Decision

No parameter was promoted.

## 2026-07-21 — IBKR product audit and robust-selection pass

### IBKR findings

- Five-year daily RTH histories are available for SPY, QQQ, SMH and SOXX.
- SMH contains a 2-for-1 split dated 2023-05-05.
- SOXX contains a 3-for-1 split dated 2024-03-07.
- Actual tactical products resolve as SPY→SSO, QQQ→QLD and semiconductor sleeve→USD.
- Semiconductor realised volatility remained above implied volatility despite extreme IV percentiles; panic intensity cannot be treated as exhaustion.

### Added controls

1. **Corporate-action continuity audit** for both underlying and leveraged-product histories.
2. **One-standard-error selection** that prefers the simpler/lower-capital candidate when results are statistically close.
3. **Complete candidate-by-fold storage**, not winner-only storage.
4. **Feature promotion gates** using identical folds, median improvement, worst-fold damage and at least 60% non-negative comparable folds.
5. **Actual-product leverage testing** using SSO, QLD and USD rather than synthetic 2× returns.

### Decision

No live threshold, tranche or leveraged-entry rule was promoted.

## 2026-07-21 — Labelled-fold, CSCV and feature-provenance pass

### Further biases found and corrected

1. **The old five-year defaults generated zero folds.**
   - The original `1008 train + 84 purge + 252 test` design did not fit a five-year daily sample once future labels were reserved.

2. **Test-window boundaries truncated future bottom labels.**
   - Fix: signals stay inside the fold; an evaluation-only forward tail supplies later trough labels; tail trades are excluded.

3. **A 260-session warm-up forgot path-dependent state.**
   - Fix: preserve all available earlier history for unresolved cycle highs and underwater duration.

4. **The latest year was treated as historically labelled.**
   - Fix: reserve the latest 252 sessions as an unlabelled live tail.

5. **Only the selected OOS candidate was persisted.**
   - Fix: store all candidates as `TEST_ALL` on each identical OOS signal block.

6. **Feature names were accepted as proof of methodology.**
   - Fix: require a point-in-time manifest, revision policy, availability lag and optional immutable SHA256.
   - IV minus daily HV remains a proxy, not genuine downside VRP.
   - Current-constituent breadth remains survivorship-biased and non-promotable.

7. **Leveraged-product boundary and benchmark bias.**
   - Fix: retain an `END_OF_DATA` exit, require recent bottom stress and falling realised volatility, and compare actual product returns with theoretical daily-reset 2× and linear 2× paths.

8. **Training-label leakage into the test period.**
   - Old design used a 252-session forward label tail for training episodes but only an 84-session purge before test signals.
   - Consequence: candidate selection could observe prices inside the future test period.
   - Fix: require `purge_days >= evaluation_tail_days`; the current 252-session label design therefore requires a 252-session purge.

9. **Rolling OOS partitions reused the same future label path.**
   - Consequence: a dense five-year fold matrix could appear to have many observations while repeatedly scoring candidates against overlapping future market periods.
   - Fix: candidate matrices record test and label boundaries. `cscv.py` blocks PBO unless label windows are declared and verified non-overlapping.

### Additional IBKR corporate actions

- SSO: 2-for-1 splits on 2022-01-13 and 2025-11-20.
- QLD: 2-for-1 split on 2025-11-20.
- USD: 2-for-1 splits on 2024-11-07 and 2025-11-20.

### Corrected statistical interpretation

- `MODERN_5Y_PRIMARY` provides about **one clean recent holdout**, not three independent folds.
- `MODERN_5Y_DENSE_DIAGNOSTIC` provides about six rolling sensitivity observations, but their forward labels overlap; formal CSCV/PBO is blocked.
- `LONG_CYCLE` uses a 252-session purge and 504-session step so test blocks plus forward labels do not overlap. Roughly 20+ years of history are needed to approach eight partitions.
- Fewer than eight independent usable partitions remains underpowered even when label independence is satisfied.
- No PBO cutoff overrides regime coverage, economic significance, adverse excursion or feature provenance.

### Decision

**No parameter promoted.** Results generated with zero-fold defaults, truncated labels, short path history, training-label leakage, overlapping PBO labels or unmanifested features are invalid for promotion.

### Next gate

1. archive immutable adjusted daily OHLCV for SPY, QQQ, SMH, SOXX, SSO, QLD and USD;
2. populate one clean modern IBKR holdout per underlying;
3. build long-cycle non-overlapping candidate matrices for formal CSCV/PBO;
4. run point-in-time price/breadth/true downside-VRP/credit ablations;
5. test actual SSO, QLD and USD entries, tracking gaps and path dependence;
6. promote only candidates surviving one-SE, worst-regime, provenance, ablation, independent-PBO and actual-product gates.
