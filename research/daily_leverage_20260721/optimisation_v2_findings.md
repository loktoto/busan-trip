# Daily leverage optimisation v2 — final findings

Validated by GitHub Actions run 17 on 2026-07-21. The code head tested was `8d025c95d93fe10716bb326911d589cafad8aeaf`.

## Executive conclusion

No daily leveraged-entry strategy in this v2 family qualifies for production promotion.

| Asset | Decision | Production exposure |
|---|---|---|
| SPY | Reject | 1x SPY |
| SOXX | Reject / downgrade prior promotion | 1x SOXX |
| MAGS7 + TSM | Experimental; reject for production | 87.5% MAGS + 12.5% TSM |

## Corrected findings

### SPY

The diagnostic SSO rule generated positive full-sample and holdout excess, but **zero** stage-2 candidates passed the complete development gate. The selected fallback failed both development and full-sample cost stress by about 1.8 percentage points annually. It is not promotable.

### SOXX

The development-only winner was effective 2x exposure made from 50% SOXX and 50% SOXL, filtered by 20-day realised volatility below 1.15 times 100-day realised volatility. Its development evidence was strong, but the preselected rule failed the untouched 2025-2026 holdout:

- holdout CAGR excess: -6.63 percentage points;
- holdout Sharpe delta: -0.202;
- block-bootstrap probability of positive mean excess: 37.4%.

A different candidate cannot be selected because it performed better in holdout; doing so would reuse the holdout as training data. The prior v1 SOXX/USD promotion is therefore downgraded pending genuinely new data or a separately specified research design.

### MAGS7 + TSM

No development candidate passed. The diagnostic fallback produced negative development, holdout and stress alpha, and the actual leveraged-product overlap remains only 448 sessions. Its calculated 1.06x current state is a model diagnostic only and must not be traded.

## Research corrections made during v2

1. Removed holdout metrics from winner ranking. The holdout now only approves or rejects the development-selected winner.
2. Restricted the cost-stress gate used in selection to the development sample; full-sample stress is reported separately.
3. Excluded SPUU after the IBKR execution audit showed materially weaker liquidity and displayed market quality than SSO.
4. Modeled product leverage separately from strategy leverage, including a 50% native + 50% SOXL construction for effective 2x and a 50% native + 50% MAGX/TSMX construction for effective 1.5x.
5. Applied higher switching costs to less-liquid MAGS leverage products.

## Operating rule

Until a new independently validated strategy passes:

- SPY remains 1x;
- SOXX remains 1x;
- MAGS7 + TSM remains the native 87.5% / 12.5% basket;
- no diagnostic `current_leverage` field is actionable when `strict_promotion` is false.

Historical rejection or promotion is not a forecast or guarantee. Any future challenger must be selected without reusing the 2025-2026 holdout as a parameter-selection set.
