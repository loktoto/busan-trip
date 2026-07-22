# Bottom Zone Monitor — GitHub deterministic result

- Request: `bottom-20260722T010300Z-rthclose`
- Input source: `IBKR_SNAPSHOT_PUBLIC_ADJUSTED_BOOTSTRAP`
- Input created: `2026-07-22T01:03:00Z`
- Model commit: `a27a8e4dd780df907d029cc46d3a7f5df9c63fa1`
- Input SHA256: `c9f8fd552025e9db94b70027ef6321bbc283c3a9fdbcfe75a8fcd5c6cf36022e`

| Asset | Close | Cycle DD | 52W DD | State | Candidate tranche | Cumulative |
|---|---:|---:|---:|---|---:|---:|
| SPY | 748.28 | -1.23% | -1.23% | 0 NO_SETUP | 0.00% | 0.00% |
| QQQ | 708.97 | -4.88% | -4.88% | 0 NO_SETUP | 0.00% | 7.50% |
| SOXX | 552.69 | -15.62% | -15.62% | 1 BOTTOM_WATCH | 0.00% | 22.50% |

## SMH reference
SMH close 584.08; cycle drawdown -12.68%; state 1 BOTTOM_WATCH. No tranche is assigned.

## Semiconductor pair
`NEUTRAL` — informational only; production weight remains zero.

## Material changes
- `{"new": 0, "old": 5, "symbol": "QQQ", "type": "STATE"}`

> Research signal only. No order is created or transmitted.

## Governance adjustments
- `{"new": 5, "old": 0, "symbol": "QQQ", "type": "ACTIVE_EPISODE_RECOVERY"}`
- `{"symbol": "SOXX", "type": "TARGET_FLOOR", "value": 0.22500000000000003}`
