# Bottom Zone Monitor — GitHub deterministic result

- Request: `bottom-20260722T005630Z-postclose`
- Input source: `IBKR_SNAPSHOT_PUBLIC_ADJUSTED_BOOTSTRAP`
- Input created: `2026-07-22T00:56:30Z`
- Model commit: `8cc8e61b47d91dea8cb0060a674416029cdaa4a0`
- Input SHA256: `acf17dbe9595f07dcb37f986767d8e25d60b76b321796e5735630d4b73b6c1ce`

| Asset | Close | Cycle DD | 52W DD | State | Candidate tranche | Cumulative |
|---|---:|---:|---:|---|---:|---:|
| SPY | 742.09 | -2.05% | -2.05% | 0 NO_SETUP | 0.00% | 0.00% |
| QQQ | 696.06 | -6.61% | -6.61% | 0 NO_SETUP | 0.00% | 7.50% |
| SOXX | 524.14 | -19.98% | -19.98% | 1 BOTTOM_WATCH | 0.00% | 22.50% |

## SMH reference
SMH close 558.83; cycle drawdown -16.46%; state 1 BOTTOM_WATCH. No tranche is assigned.

## Semiconductor pair
`NEUTRAL` — informational only; production weight remains zero.

## Material changes
- None

> Research signal only. No order is created or transmitted.

## Governance adjustments
- `{"new": 5, "old": 0, "symbol": "QQQ", "type": "ACTIVE_EPISODE_RECOVERY"}`
- `{"symbol": "SOXX", "type": "TARGET_FLOOR", "value": 0.22500000000000003}`
