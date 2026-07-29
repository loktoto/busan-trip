# Evidence-Based TA Redesign — 2026-07-29

## Production conclusion

The monitor should not search for a single magical indicator. The most defensible architecture is:

1. trend/regime filter;
2. cross-sectional and time-series relative strength;
3. volatility-aware setup quality and entry location;
4. completed 1H setup with completed 15m execution trigger;
5. liquidity, event and executable R/R controls;
6. mandatory second-pass validation for high-score signals.

RSI and MACD remain secondary. They may refine location or confirmation, but neither is allowed to create a signal independently.

## Research retained

### Trend following / time-series momentum

- Moskowitz, Ooi and Pedersen document positive predictive power from an instrument's own past return across a broad set of liquid futures and forwards. The effect is robust across lookbacks and holding periods and persists for roughly a year before partial longer-horizon reversal.
- Hurst, Ooi and Pedersen extend trend-following evidence back to 1880 across many market regimes.

Production implication: weekly/daily trend and relative-strength evidence should carry more weight than short-horizon oscillator readings.

Sources:
- https://www.aqr.com/insights/research/journal-article/time-series-momentum
- https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing

### Cross-sectional momentum and information diffusion

- Momentum evidence supports ranking securities by relative performance rather than examining each chart in isolation.
- Hong, Lim and Stein find momentum profitability varies with size and analyst coverage, consistent with gradual information diffusion.

Production implication: a Dynamic Discovery Board should compare candidates with SPY and sector peers and should scan across sectors rather than rely on a correlated fixed theme universe.

Source:
- https://www.nber.org/papers/w6553

### Moving-average / technical timing evidence

- Research on moving-average rules suggests they can capture return dependence and may improve risk-adjusted outcomes in some samples, especially in volatile portfolios.
- This does not justify mechanical moving-average crossovers in isolation; results vary by market, frequency and specification.

Production implication: moving averages define regime and dynamic support, not standalone entries. Completed price structure, relative strength, execution quality and R/R remain necessary.

Sources:
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4172147
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1656460
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1926376

### Momentum crash risk

- Long-run momentum evidence also documents large, partly predictable crashes.

Production implication: do not chase extended leaders; use ATR extension penalties, event controls, staged entries, structural invalidation and sector breadth checks.

Source:
- https://www.nber.org/papers/w20660

## Design corrections adopted

1. Preserve the original 21-name board but add a sector-diversified Dynamic Discovery Board.
2. Split entry into ANTICIPATORY STARTER, CONFIRMED STARTER and CONFIRMED ADD.
3. Calculate market-now, preferred-zone and confirmation-entry R/R separately.
4. PASS 2 can preserve a conditional setup instead of converting every non-chase situation into failure.
5. Use 15m as the primary execution trigger once the 1H setup is valid.
6. Cache completed weekly/daily data and refresh lower-timeframe trigger data each run.
7. Degrade data failures per ticker rather than invalidating the full board.
8. Record explicit rejection reason codes so zero-entry periods can be diagnosed.

## Validation plan

Before declaring this redesign superior, run walk-forward and out-of-sample tests with:

- fixed 21-name universe and broad discovery universe reported separately;
- survivorship-bias-aware historical membership where available;
- realistic spread/slippage and event gaps;
- signal timestamp using only data available at that time;
- 1D, 5D, 10D outcomes, MFE, MAE, hit rate, expectancy, profit factor and maximum drawdown;
- ablation tests removing relative strength, regime, 15m trigger, ATR extension and PASS 2 one at a time;
- comparison against fixed-board-only production and simple SPY/QQQ benchmarks.

No parameter should be promoted solely because it maximises in-sample return. Prefer stable plateaus across neighbouring parameters, multiple regimes and multiple sectors.