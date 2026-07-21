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

### Next research gate

1. export or archive continuous adjusted IBKR OHLCV for all four underlyings and all three leveraged products;
2. create immutable point-in-time breadth, VRP and credit manifests;
3. populate the candidate-by-fold matrix for SPY, QQQ, SMH and SOXX;
4. compare price-only versus each incremental feature family on identical folds;
5. test actual SSO, QLD and USD tactical entries independently;
6. run longer dot-com/GFC stress histories separately from the modern five-year IBKR validation window;
7. promote only parameters that survive the one-SE, worst-regime and feature-ablation gates.
