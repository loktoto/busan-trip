# Point-in-Time Feature Schema

Optional `--features-csv` input is merged by `Date` and forward-filled. Every row must represent the value actually available on that date; publication-delayed series must be shifted before export.

Recommended columns:

| Column | Direction | Notes |
|---|---|---|
| `breadth_score` | higher = healthier breadth | Composite of advance/decline, up/down volume, new lows and percentage above moving averages. Build separately for SPY, QQQ and semiconductor constituents. |
| `downside_vrp` | higher = richer downside fear premium | Must be model-free and point-in-time to receive full weight. A simple underlying IV minus historical volatility is only a proxy. |
| `hy_oas` | higher = worse credit stress | Use the publication date available to the strategy, not the economic observation date alone. |
| `ofr_fsi` | higher = worse systemic stress | OFR publishes with a two-business-day data lag. Shift accordingly. |
| `relative_strength` | higher = improving relative strength | For semiconductors use SMH/QQQ or SOXX/QQQ; for QQQ use QQQ/SPY where appropriate. |

The backtest creates causal trailing z-scores named `<column>_z`. The current engine consumes `breadth_score_z`, `downside_vrp_z`, `hy_oas_z` and `ofr_fsi_z` when present. Missing features remain missing; they are never fabricated or replaced by zero.

## Point-in-time rules

1. Corporate actions and index membership must be known as of each historical date.
2. Never backfill revised values into earlier dates.
3. Shift daily publications by their actual availability delay.
4. Store source, observation date, publication timestamp, timezone and revision policy in the dataset manifest.
5. Semiconductor breadth must use historical constituents or an explicitly documented survivorship-biased proxy.
