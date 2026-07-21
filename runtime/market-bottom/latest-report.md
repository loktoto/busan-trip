# Bottom Zone Monitor — GitHub deterministic result

- Request: `bottom-20260721T155800Z-bootstrap1`
- Input source: `IBKR_SNAPSHOT_PUBLIC_ADJUSTED_BOOTSTRAP`
- Input created: `2026-07-21T15:58:00Z`
- Model commit: `9cf32b7b1245743bfa7a9ea0fe375596dcdc8286`
- Input SHA256: `db0297cf2d0046cdc9755a3017ba453ba188f92af682959df4cc975edd19daf4`

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
- `{"new": 0, "old": 5, "symbol": "QQQ", "type": "STATE"}`

> Research signal only. No order is created or transmitted.

## Governance adjustments
- `{"new": 5, "old": 0, "symbol": "QQQ", "type": "ACTIVE_EPISODE_RECOVERY"}`
- `{"symbol": "SOXX", "type": "TARGET_FLOOR", "value": 0.22500000000000003}`
