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

### Next research gate

1. archive continuous adjusted OHLCV for all four underlyings;
2. create immutable point-in-time breadth and credit manifests;
3. run base-price, volume, breadth, VRP and credit feature ablations;
4. keep a complete candidate-by-fold matrix for formal CSCV/PBO;
5. validate actual SSO, QLD and USD tactical entry/exit rules separately.
