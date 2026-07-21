# Point-in-Time Feature Schema

Optional `--features-csv` input is merged by `Date` and forward-filled. Every row must represent the value actually available to the strategy on that session; publication-delayed series must be shifted before export.

A feature CSV used for ablation must have a separate JSON manifest and pass `feature_manifest.py`. A descriptive column name is not evidence that the underlying construction is valid.

## Recommended columns

| Column | Direction | Promotion requirement |
|---|---|---|
| `breadth_score` | higher = healthier breadth | Composite of advance/decline, up/down volume, new lows and percentage above moving averages. Build separately for SPY, QQQ and semiconductor constituents. Full promotion requires historical point-in-time constituents. |
| `downside_vrp` | higher = richer downside fear premium | Full promotion requires model-free option-strip implied variance and intraday realised variance. Underlying IV minus daily historical volatility is only a proxy. |
| `hy_oas` | higher = worse credit stress | Use the publication timestamp available to the strategy and document the publication-to-session alignment rule. |
| `ofr_fsi` | higher = worse systemic stress | Shift by at least the documented two-business-day availability lag and retain vintage/revision provenance. |
| `relative_strength` | higher = improving relative strength | For semiconductors use SMH/QQQ or SOXX/QQQ; for QQQ use QQQ/SPY where appropriate. |

The backtest creates causal trailing z-scores named `<column>_z`. The current engine consumes `breadth_score_z`, `downside_vrp_z`, `hy_oas_z` and `ofr_fsi_z` when present. Missing features remain missing; they are never fabricated or replaced by zero.

## CSV date semantics

`Date` must mean `STRATEGY_AVAILABLE_SESSION`: the first trading session on which the observation could have been used. It must not simply be the economic observation date.

Examples:

- a release published after the close is assigned to the next trading session;
- a two-business-day delayed systemic series is shifted by its actual availability;
- revised historical observations are stored as new vintages rather than backfilled into earlier strategy dates.

## Required manifest fields

```json
{
  "schema_version": 1,
  "dataset_id": "immutable-dataset-identifier",
  "created_at_utc": "2026-07-21T00:00:00Z",
  "date_semantics": "STRATEGY_AVAILABLE_SESSION",
  "revision_policy": "APPEND_ONLY_VINTAGES",
  "csv_sha256": "optional-but-recommended-immutable-hash",
  "features": {
    "breadth_score": {
      "source": "source and licence description",
      "point_in_time": true,
      "availability_lag_business_days": 0,
      "historical_constituents": true
    },
    "downside_vrp": {
      "source": "option strip and realised variance inputs",
      "point_in_time": true,
      "availability_lag_business_days": 1,
      "method": "model_free_option_strip",
      "realized_variance_frequency": "5min"
    }
  }
}
```

## Point-in-time rules

1. Corporate actions and index membership must be known as of each historical date.
2. Never backfill latest revised values into earlier dates.
3. Shift publications by their actual strategy availability delay.
4. Store source, observation date, publication timestamp, timezone, revision policy and dataset hash.
5. Semiconductor breadth must use historical constituents or be explicitly blocked as a survivorship-biased proxy.
6. A proxy can be researched and reported, but `ablation.py` forces `promote=false` when the manifest does not meet the full methodology gate.
