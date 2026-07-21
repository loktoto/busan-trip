# Optimisation Log

## 2026-07-21 — Validation and causal-engine pass

### Corrected biases and bugs

1. **Missed episodes were excluded from the old evaluator.**
   - Old behaviour: headline rates were calculated only from episodes containing at least one trade.
   - Consequence: missed-bottom rate was structurally understated.
   - Fix: build a complete episode catalogue first, then left-join trades; episodes with no trades are retained with `missed=true`.

2. **Asset configuration did not inherit `default`.**
   - Old behaviour: symbol blocks replaced rather than extended default configuration.
   - Consequence: new global assumptions such as transaction costs could silently fall back to dataclass defaults.
   - Fix: merge `default` first, then overlay the symbol block.

3. **Exhaustion and confirmation bonuses could repeat.**
   - Old behaviour: a persistent state could add the bonus again after cooldown/spacing.
   - Fix: bonuses apply only on a false→true state transition.

4. **Current-bar rolling low was used as its own comparison.**
   - Fix: prior 10/20-session lows are shifted by one bar before the new-low comparison.

### Added controls

- transaction-cost and slippage assumptions;
- completed-episode and incomplete-episode separation;
- worst post-entry adverse excursion per episode;
- optional point-in-time breadth, downside-VRP, HY OAS and OFR FSI features;
- credit/systemic veto;
- purged walk-forward selection;
- bounded parameter-stability grid;
- episode bootstrap confidence intervals;
- PBO-inspired selection-instability diagnostic, explicitly not labelled formal CSCV PBO;
- regression tests for causal execution, missed episodes, config inheritance, feature missingness and tranche limits.

### Optimisation decision

No new asset parameter is promoted merely because the revised engine exists. SPY, QQQ, SMH and SOXX parameters remain research candidates until the same point-in-time dataset is run through the new validation pipeline.

## 2026-07-21 — IBKR product audit and robust-selection pass

### IBKR findings

- Five-year daily RTH histories are available for SPY, QQQ, SMH and SOXX.
- SMH contains a 2-for-1 split dated 2023-05-05.
- SOXX contains a 3-for-1 split dated 2024-03-07.
- Actual tactical products resolve as SPY→SSO, QQQ→QLD and semiconductor sleeve→USD.
- Current semiconductor realised volatility remains above implied volatility despite extreme IV percentiles. Panic intensity therefore cannot be treated as exhaustion.

### Added controls

1. **Corporate-action continuity audit**
   - Reject split-like discontinuities before calculating drawdown, ATR, new lows or volatility.
   - Separate adjusted-price integrity from signal logic.

2. **One-standard-error selection**
   - Preserve an outer purged test fold.
   - Calculate utility at episode level.
   - Penalise regime concentration.
   - Select the simpler, lower-capital candidate when several candidates are statistically indistinguishable from the apparent winner.

3. **Complete candidate-by-fold matrix**
   - Persist every candidate result, not only the selected model.
   - This is required before formal CSCV/PBO can be calculated honestly.

4. **Feature promotion gate**
   - Run price/volume, breadth, downside-VRP, credit and full-ensemble variants on identical folds.
   - Require a positive median fold improvement.
   - Limit worst-fold damage.
   - Require at least 60% of comparable folds to be non-negative before retaining a feature family.

5. **Actual-product tactical leverage**
   - Generate entries from the unleveraged underlying.
   - Calculate P&L and path risk from actual SSO, QLD or USD adjusted prices.
   - Exit on underlying-bottom failure, volatility reacceleration, recovery-structure break, target or time stop.
   - Do not approximate leveraged returns by multiplying the underlying return.

### Optimisation decision

No new live parameter or tranche size is promoted in this pass. The changes improve falsifiability and reduce selection bias; they do not manufacture a better historical result. Asset-specific promotion requires immutable IBKR/point-in-time datasets to pass the new robust validator and ablation gates.

## 2026-07-21 — Labelled-fold, CSCV and feature-provenance pass

### Further biases found and corrected

1. **The old five-year defaults generated zero folds.**
   - `1008 train + 84 purge + 252 test` already exceeds the useful five-year IBKR daily sample once a forward label horizon is reserved.
   - Fix: introduce explicit `MODERN_5Y_PRIMARY`, `MODERN_5Y_DENSE_DIAGNOSTIC` and `LONG_CYCLE` protocols with preflight fold-count checks.

2. **Test-window boundaries truncated future bottom labels.**
   - Old behaviour: an episode that started in a test fold but recovered after the fold boundary was treated as incomplete or ignored.
   - Fix: restrict signals to the fold, retain a fixed evaluation-only forward tail, and exclude all trades generated in that tail.

3. **A 260-session warm-up forgot path-dependent state.**
   - Old behaviour: unresolved cycle highs and underwater duration could be reset inside a long bear market.
   - Fix: preserve all available history before the signal interval; only the allowed signal dates are restricted.

4. **The latest year was implicitly treated as historically labelled.**
   - Fix: reserve the final 252 sessions as an unlabelled live tail. They may produce monitor states but cannot enter completed historical accuracy claims.

5. **Only the selected OOS candidate was persisted.**
   - Fix: record every candidate as `TEST_ALL` on every identical non-overlapping OOS partition, enabling a genuine CSCV/PBO diagnostic.

6. **Feature names were accepted as proof of methodology.**
   - Fix: require a point-in-time manifest, revision policy, availability lags and optional immutable SHA256. A simple IV-minus-HV series cannot be promoted as genuine downside VRP; current-constituent breadth remains a survivorship-biased proxy.

7. **Leveraged-product boundary and benchmark bias.**
   - Open positions at the dataset end were silently omitted.
   - Fix: retain an auditable `END_OF_DATA` exit, require recent bottom stress and falling realised volatility for entry, and compare actual product returns with theoretical daily-reset 2× and linear 2× paths.

### Additional IBKR corporate-action findings

- SSO: 2-for-1 splits on 2022-01-13 and 2025-11-20.
- QLD: 2-for-1 split on 2025-11-20.
- USD: 2-for-1 splits on 2024-11-07 and 2025-11-20.
- Corporate-action continuity therefore applies independently to both underlying and leveraged-product files.

### Statistical interpretation

- `MODERN_5Y_PRIMARY` is the model-selection protocol but yields only about three fully labelled folds in a five-year daily sample after the forward tail is reserved.
- `MODERN_5Y_DENSE_DIAGNOSTIC` can provide about nine shorter partitions for CSCV/PBO diagnostics; it is explicitly prohibited from promoting live parameters by itself.
- Formal PBO is classified as underpowered when fewer than eight usable partitions remain after no-event folds are removed.
- No fixed PBO threshold overrides regime coverage, economic significance, adverse excursion or feature provenance.

### Optimisation decision

**No parameter promoted.** This pass invalidates any result generated with zero-fold defaults, truncated labels, short path history or unmanifested features. Numerical candidate matrices and leverage results must be regenerated from immutable adjusted daily datasets before any live threshold or tranche can be upgraded.

### Next research gate

1. export or archive continuous adjusted IBKR OHLCV for SPY, QQQ, SMH, SOXX, SSO, QLD and USD with immutable manifests;
2. populate primary and dense candidate-by-fold matrices for all four underlyings;
3. run CSCV/PBO only on complete identical OOS candidate partitions;
4. run price-only versus breadth, true downside-VRP and credit ablations with point-in-time manifests;
5. test actual SSO, QLD and USD tactical entries, tracking gaps and path dependency independently;
6. run longer dot-com/GFC stress histories separately from the modern five-year IBKR validation window;
7. promote only parameters that survive one-SE, worst-regime, feature-provenance, ablation and actual-product gates.
