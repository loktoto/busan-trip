# Bottom Zone Monitor — GitHub deterministic result

- Request: `bottom-20260722T010300Z-rthclose`
- Input source: `IBKR_SNAPSHOT_PUBLIC_ADJUSTED_BOOTSTRAP`
- Input created: `2026-07-22T01:03:00Z`
- Model commit: `956f88871b2049f0877e058e0eb169062e52f5af`
- Input SHA256: `c2e90352be29f2aa1a188f6af637c7d5909775c739a0da5869baad79464ffc6a`

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
