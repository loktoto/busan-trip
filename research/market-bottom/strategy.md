# Bottom-Zone Strategy Specification

## 1. Objective

The strategy is designed to answer two different questions:

1. **Ordinary 1× ETF:** Is price sufficiently close to a plausible local trough to justify a measured staged addition?
2. **Leveraged ETF:** Has the bottom zone been confirmed strongly enough to justify a temporary tactical rebound position?

The strategy does **not** attempt to identify the exact low. For the ordinary ETF, entering slightly early is acceptable if the initial tranche is small and most reserved capital remains available. For leveraged ETFs, false positives are penalised heavily because daily reset and path dependency can create substantial losses during volatile sideways markets.

## 2. Universe

| Underlying | Ordinary exposure | Tactical leverage mapping |
|---|---|---|
| S&P 500 | SPY | SSO |
| Nasdaq-100 | QQQ | QLD |
| Semiconductors | SMH / SOXX | USD |

SMH and SOXX are treated as **one semiconductor sleeve** unless capital is explicitly assigned separately. A single semiconductor signal must not trigger two full tranches.

USD does not track exactly the same benchmark as SMH or SOXX. Any USD trade therefore carries benchmark-basis risk in addition to daily-reset risk.

## 3. Signal hierarchy

Indicators are separated by economic role. They are not mixed into one arbitrary score.

### Layer A — anticipatory bottom-zone evidence

Layer A is used for a small ordinary-ETF probe before a full recovery is visible.

#### A1. Unresolved-cycle drawdown

Use the last unresolved all-time or cycle peak as the reference:

```text
cycle_drawdown = close / unresolved_cycle_high - 1
```

A mechanical rolling 52-week high is shown only as context. In a bear market lasting longer than one year, the prior peak can roll out of a 252-day window and make the apparent drawdown shrink even though the economic loss has not recovered.

#### A2. Volatility-normalized decline

Compare raw drawdown and 1/3/5/10-day returns with:

- ATR(14) as a percentage of price;
- 20-day realised volatility;
- the asset's own recent volatility regime.

The objective is to distinguish:

- an ordinary correction;
- a fast liquidity shock;
- a persistent valuation or earnings repricing.

#### A3. Back-loaded capital curve

Capital is deployed nonlinearly. A generic target-deployment function is:

```text
x = clip((abs(drawdown) - start_drawdown) /
         (max_drawdown - start_drawdown), 0, 1)

target_deployment = max_deployment × x^power
```

With `power > 1`, shallow declines receive only a micro-probe while most capital is preserved for deeper drawdowns.

Critical causal rule:

> Earlier tranches must never be re-normalised after observing how many later signals occurred. Unused future tranches remain cash.

#### A4. Fresh-low and entry-spacing discipline

A new tranche normally requires at least one of:

- a fresh 10-session low;
- a fresh 20-session low;
- price sufficiently below the previous actual candidate entry;
- an extreme volatility-normalized downside shock.

It also requires either:

- a minimum cooldown since the previous entry; or
- meaningful price separation from the previous entry.

This prevents repeated purchases at nearly the same price during a slow decline.

#### A5. Liquidation evidence

Supporting observations include:

- abnormal downside volume;
- weak close location within the daily range;
- repeated downside gaps;
- high realised volatility;
- a subsequent reduction in downside volume or decline speed.

A single high-volume down day is not sufficient.

#### A6. Breadth washout

Where point-in-time data is available, evaluate:

- advance/decline breadth;
- up-volume versus down-volume;
- new highs versus new lows;
- percentage of members above 20/50/200-day averages;
- cap-weighted versus equal-weight performance;
- semiconductor constituent breadth for SMH/SOXX.

A particularly useful pattern is:

> Price makes a new or marginal low while breadth, new lows or downside volume fails to make a new extreme.

#### A7. Fear premium and volatility structure

Use, in descending preference:

1. genuine model-free variance risk premium;
2. downside variance risk premium;
3. VIX/VIX9D/VIX3M/VVIX term structure and divergence;
4. IBKR underlying IV minus historical volatility as a clearly labelled low-weight proxy.

High VIX, high IV or a high IV percentile alone cannot trigger a purchase.

#### A8. Credit and systemic filter

Use HY option-adjusted spreads and the OFR Financial Stress Index impulse to distinguish sector liquidation from broad systemic stress.

- Stable credit can permit a small sector probe.
- Accelerating credit or funding stress vetoes new tranches.
- Credit stability is not proof that a sector price has stabilised.

### Layer B — exhaustion evidence

Layer B supports the second ordinary tranche. A full price rebound is not required.

Typical evidence:

- price makes a new or marginal low but realised downside acceleration improves;
- retest volume contracts;
- breadth or new lows improve;
- VIX/VVIX or implied correlation no longer worsens;
- HY spreads or systemic-stress impulse stops accelerating;
- RSI/MACD divergence is present as secondary evidence only.

### Layer C — confirmation evidence

Layer C supports larger ordinary additions and is normally required before tactical leverage.

Typical evidence:

- successful retest or higher closing low;
- false-breakdown reclaim;
- persistent breadth improvement rather than a one-day thrust;
- improving relative strength;
- falling ATR and realised volatility;
- stable or improving credit conditions;
- recovery above short-term trend measures with improving slope.

## 4. Long-bear throttle

Classify `LONG_BEAR_RISK` when several of the following are present:

- price below a falling 200-day moving average;
- prolonged time below the unresolved cycle high;
- negative medium-term momentum;
- repeated failed rallies;
- credit or earnings conditions continue to deteriorate.

Under long-bear risk:

- restrict early cumulative deployment;
- preserve substantial capital for deeper drawdown levels;
- require stronger exhaustion evidence before increasing tranche size.

This rule exists because price-only ladders tended to deploy too early during dot-com, GFC and 2022-style repricing regimes.

## 5. State machine

| State | Name | Interpretation |
|---:|---|---|
| 0 | NO SETUP | Decline is too shallow or evidence is absent. |
| 1 | BOTTOM WATCH | Decline is material but evidence is incomplete. |
| 2 | CLOSE-TO-BOTTOM CANDIDATE | Multiple anticipatory families support a small ordinary probe. |
| 3 | EXHAUSTION ZONE | Selling pressure is no longer accelerating; second ordinary tranche may be considered. |
| 4 | BOTTOM ZONE CONFIRMED | Retest, breadth and price evidence support a larger ordinary addition. |
| 5 | RECOVERY UNDERWAY | Trend and breadth improve persistently; planned ordinary deployment may be completed and leverage enters review. |
| 6 | FAILED SETUP | Downside acceleration, credit deterioration or structural invalidation negates the prior setup. |

Official state changes use completed regular-session bars. Premarket and intraday data are context unless explicitly labelled provisional.

## 6. Research-candidate sizing

All percentages refer to capital reserved for the relevant asset or sleeve, not total portfolio NAV.

A generic staged structure is:

| Stage | Increment | Cumulative | Evidence required |
|---|---:|---:|---|
| Early micro-probe | 1%–5% | 1%–5% | State 2; enough to avoid missing a V-shaped trough, small enough to tolerate being early. |
| Exhaustion tranche | 5%–10% | 7.5%–15% | State 3; stress no longer accelerates. |
| Confirmed-bottom tranche | 10%–20% | 20%–35% | State 4; retest/breadth/price confirmation. |
| Recovery tranche | 10%–25% | 35%–60% | State 5; persistent recovery. |
| Reserved capital | remainder | — | Retained for deeper bear-market risk or later opportunities. |

These ranges are governance examples, not proven optimal sizes. Asset-specific values must be selected using causal, out-of-sample validation.

## 7. Tactical leverage rules

### Entry gate

Leverage is not permitted because drawdown is deep. Normally require State 4 or 5 plus:

- breadth improvement;
- improving relative strength;
- falling ATR / realised volatility;
- stable or improving credit/stress;
- a recovery structure that persists beyond one session.

### Position role

The leveraged ETF is a temporary tactical overlay intended to capture the first sustained rebound phase. It is not a permanent replacement for the ordinary ETF.

### Exit / reversion

Exit or revert to the ordinary ETF when any of the following occurs:

- confirmed retest low fails;
- breadth or relative strength rolls over;
- ATR or realised volatility reaccelerates;
- VIX/VVIX/term structure or credit stress worsens materially;
- short-term recovery structure breaks;
- preset rebound target is reached;
- risk budget is exhausted;
- maximum holding-window time stop expires.

Every tactical leverage recommendation must include an entry rationale, invalidation level, target/reversion rule, volatility exit and time stop.

## 8. Asset-specific emphasis

### SPY

Prioritise:

- broad breadth;
- VIX complex;
- HY credit and systemic stress;
- cap-weighted versus equal-weight divergence.

### QQQ

Prioritise:

- Nasdaq breadth;
- valuation-repricing / long-bear throttle;
- QQQ relative strength and volatility regime;
- a larger drawdown tolerance than SPY.

### SMH / SOXX

Prioritise:

- semiconductor-specific cycle drawdown;
- sector constituent breadth;
- SMH/QQQ and SOXX/QQQ relative strength;
- sector liquidation volume;
- sector IV versus realised volatility;
- stress in major semiconductor constituents.

Do not require a broad-market VIX crisis for a semiconductor bottom. Broad credit data is a filter, not a substitute for sector breadth and price stability.

## 9. Indicators explicitly demoted

The following cannot be standalone bottom triggers:

- absolute VIX threshold;
- VIX term structure alone;
- RSI or MACD alone;
- fixed 52-week drawdown alone;
- one high-volume down day;
- moving-average crossover alone;
- raw put/call ratio or call count;
- raw SKEW;
- public-open-interest dealer-gamma estimates;
- low-frequency positioning or fund-flow series as daily timing signals.

## 10. Live-monitor output requirements

Every complete report should show for SPY, QQQ, SMH and SOXX:

- data source, quote status and timestamp;
- unresolved cycle high and cycle drawdown;
- rolling 52-week drawdown separately;
- ATR / realised-volatility-normalized decline;
- underwater duration and long-bear status;
- current state;
- Layer A, B and C evidence;
- current candidate tranche, cumulative deployment and remaining reserve;
- previous-entry spacing and cooldown;
- exact next trigger and invalidation;
- leverage status: `NOT READY`, `TACTICAL REVIEW` or `EXIT/REVERT`;
- observed facts separated from provisional model judgement.
