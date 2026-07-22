# SPY + QQQ Fixed-Ensemble Challenger

## Objective

Reduce parameter-selection instability found in the expanded alpha search. SOXX is out of scope because PR #13 already validated its trend-vol signal and actual-product paths.

## Fixed candidates

1. Buy & Hold.
2. One raw exposure rule selected using data only through 2012-12-31 and then frozen.
3. Median exposure across the complete fixed volatility-target family.
4. 50% damped median volatility-target exposure.
5. Median exposure across the complete fixed trend-vol family.
6. 50% damped median trend-vol exposure.
7. Equal blend of the two damped median families.
8. The same blend capped at 0.5x in a high-volatility downtrend.
9. Fixed 1.25x low-vol uptrend / 0.75x high-vol downtrend rule.

No annual parameter reselection is used by the median or fixed-rule candidates.

## Evaluation

- Completed-close information and next regular-session-open execution.
- Evaluation starts 2013-01-01.
- Base, 2x and 3x transaction-cost stresses.
- Four contiguous regime blocks.
- Moving-block bootstrap.
- Corrected deflated-Sharpe probability with eight trials.
- CSCV/PBO across the nine fixed candidates.
- Beta-adjusted alpha versus Buy & Hold.
- Actual adjusted-price implementation using SSO/UPRO for SPY and QLD/TQQQ for QQQ.
- Two independent downloads and calculations must agree on winner, classification, product gate and current weights.

## Promotion

The same return-alpha and defensive-alpha gates used in PR #13 apply. A signal candidate is not promoted unless at least one actual-product path independently passes the product gate. RESEARCH_ONLY retains production exposure at 1.0x.

The 2013-2026 evaluation remains pseudo-OOS rather than untouched holdout because prior research has inspected the period.
