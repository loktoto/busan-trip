# Bottom-Zone Strategy Specification

## 1. Objective

The strategy answers two different questions:

1. **Ordinary 1× ETF:** Is price sufficiently close to a plausible local trough to justify a measured staged addition?
2. **Leveraged ETF:** Has the bottom zone been confirmed strongly enough to justify a temporary tactical rebound position?

The strategy does not attempt to identify the exact low. A small ordinary-ETF probe may be early if most reserved capital remains available. Leveraged false positives are penalised heavily because daily reset and path dependency can create substantial losses in volatile sideways markets.

## 2. Universe

| Role | Market | Instrument | Tactical leverage |
|---|---|---|---|
| Primary bottom target | S&P 500 | SPY | SSO |
| Primary bottom target | Nasdaq-100 | QQQ | QLD |
| Primary bottom target | Semiconductors | SOXX | USD |
| Secondary reference only | Semiconductors | SMH | None |

SMH is an independently calculated reference for the SOXX decision. It receives no capital allocation, tranche, position or leverage mapping. SOXX is the only traded semiconductor bottom target.

USD does not track exactly the same benchmark as SOXX. Any USD trade carries benchmark-basis risk in addition to daily-reset risk.

## 3. Signal hierarchy

Indicators are separated by economic role rather than mixed into an arbitrary score.

### Layer A — anticipatory bottom-zone evidence

Layer A is used for a small ordinary-ETF probe before a full recovery is visible.

#### A1. Unresolved-cycle drawdown

```text
cycle_drawdown = close / unresolved_cycle_high - 1
```

A mechanical rolling 52-week high is shown only as context. In a bear market lasting longer than one year, the old high can roll out and make the apparent drawdown shrink even though the economic loss has not recovered.

#### A2. Volatility-normalised decline

Compare raw drawdown and 1/3/5/10-day returns with:

- ATR(14) as a percentage of price;
- 20-day realised volatility;
- the asset's own volatility regime.

The objective is to distinguish an ordinary correction, a fast liquidity shock and a persistent valuation/earnings repricing.

#### A3. Back-loaded capital curve

```text
x = clip((abs(drawdown) - start_drawdown) /
         (max_drawdown - start_drawdown), 0, 1)

target_deployment = max_deployment × x^power
```

With `power > 1`, shallow declines receive only a micro-probe while most capital is retained for deeper drawdowns.

> Earlier tranches must never be re-normalised after observing how many later signals occurred. Unused future tranches remain cash.

#### A4. Fresh-low and entry-spacing discipline

A new tranche normally requires at least one of:

- fresh 10-session low;
- fresh 20-session low;
- price sufficiently below the previous actual entry;
- extreme volatility-normalised downside shock.

It also requires a minimum cooldown or meaningful price separation. This prevents repeated purchases at almost the same price during a slow decline.

#### A5. Liquidation evidence

Supporting observations include abnormal downside volume, weak close location, repeated downside gaps, high realised volatility and subsequent reduction in downside volume or decline speed. One high-volume down day is not sufficient.

#### A6. Breadth washout

Where point-in-time data is available, evaluate advance/decline breadth, up/down volume, new highs/lows, percentage above moving averages, cap-weighted versus equal-weight performance and historical semiconductor-constituent breadth.

A useful pattern is price making a new or marginal low while breadth, new lows or downside volume fails to make a new extreme.

#### A7. Fear premium and volatility structure

Use, in descending preference:

1. genuine model-free variance risk premium;
2. downside variance risk premium;
3. VIX/VIX9D/VIX3M/VVIX structure and divergence;
4. IBKR underlying IV minus historical volatility as a labelled low-weight proxy.

High VIX, high IV or high IV percentile alone cannot trigger a purchase.

#### A8. Credit and systemic filter

Use HY option-adjusted spreads and OFR stress impulse to distinguish sector liquidation from broad systemic stress. Stable credit can permit a small probe; accelerating credit/funding stress vetoes new tranches. Credit stability is not proof that sector price has stabilised.

### Layer B — exhaustion evidence

Layer B supports the second ordinary tranche. A full rebound is not required.

Typical evidence:

- price makes a new/marginal low but downside acceleration improves;
- retest volume contracts;
- breadth or new lows improve;
- volatility/correlation stress no longer worsens;
- HY spreads or systemic-stress impulse stops accelerating;
- RSI/MACD divergence is supporting evidence only.

### Layer C — confirmation evidence

Layer C supports larger ordinary additions and is normally required before tactical leverage.

Typical evidence:

- successful retest or higher closing low;
- false-breakdown reclaim;
- persistent breadth improvement;
- improving relative strength;
- falling ATR and realised volatility;
- stable/improving credit;
- recovery above short-term trend measures with improving slope.

## 4. SMH/SOXX paired semiconductor logic

### 4.1 Roles

- **SOXX:** primary state, bottom zone, tranche and invalidation.
- **SMH:** second independent semiconductor bottom coordinate.
- SMH cannot create a SOXX State 2 setup when SOXX itself has no drawdown setup.
- SMH never creates its own trade row or a second semiconductor allocation.

### 4.2 Causal alignment

- Calculate SOXX and SMH independently first.
- Inner-align same-date completed regular-session bars only.
- Never forward-fill a stale SMH close into a newer SOXX date.
- Signals use both completed closes at `t`; any SOXX execution occurs at SOXX next open `t+1`.

### 4.3 Pair classifications

| Pair status | Meaning | Provisional action effect |
|---|---|---|
| `CONFIRMS` | SMH independently corroborates SOXX exhaustion/confirmation within the recent causal window. | May increase confidence after paired validation. |
| `POSITIVE_DIVERGENCE` | SOXX retests while SMH decline speed, RV or selling pressure improves. | Supporting evidence only. |
| `NEUTRAL` | No material corroboration or contradiction. | Use SOXX-only state. |
| `DIVERGES` | Relative bottom structure or state materially disagrees. | Reduce confidence; do not increase size from pair evidence. |
| `VETO` | SMH fresh low plus worsening volatility/selling pressure signals renewed sector deterioration. | Defer/revoke SOXX exhaustion or confirmation tranche; micro-probe is not automatically liquidated. |

### 4.4 Backtest variants

1. `SOXX_ONLY` — baseline.
2. `SMH_SOFT_CONFIRM` — lowers the SOXX exhaustion/confirmation vote hurdle by one only when SOXX already has its own qualifying evidence.
3. `SMH_VETO_ONLY` — leaves the first SOXX probe unchanged but blocks larger transitions during an SMH veto.
4. `SMH_HARD_CONFIRM` — requires recent independent SMH corroboration for SOXX exhaustion/confirmation.

The paired rule is retained only if it improves out-of-sample bottom proximity without materially worsening missed bottoms, adverse excursion or capital deployment. Full-sample improvement alone cannot promote it.

## 5. Long-bear throttle

Classify `LONG_BEAR_RISK` when several of the following are present:

- price below a falling 200-day average;
- prolonged time below the unresolved cycle high;
- negative medium-term momentum;
- repeated failed rallies;
- credit or earnings conditions continue to deteriorate.

Under long-bear risk, restrict early cumulative deployment, preserve substantial capital for deeper levels and require stronger exhaustion evidence. This rule exists because price-only ladders deployed too early in dot-com, GFC and 2022-style repricing regimes.

## 6. State machine

| State | Name | Interpretation |
|---:|---|---|
| 0 | NO SETUP | Decline too shallow or evidence absent. |
| 1 | BOTTOM WATCH | Decline material but evidence incomplete. |
| 2 | CLOSE-TO-BOTTOM CANDIDATE | Multiple anticipatory families support a small ordinary probe. |
| 3 | EXHAUSTION ZONE | Selling pressure no longer accelerates; second ordinary tranche may be studied. |
| 4 | BOTTOM ZONE CONFIRMED | Retest, breadth and price evidence support a larger ordinary addition. |
| 5 | RECOVERY UNDERWAY | Trend/breadth improve persistently; leverage enters review. |
| 6 | FAILED SETUP | Downside acceleration, credit deterioration or structural invalidation negates the setup. |

Official state changes use completed regular-session bars. Premarket/intraday data is context unless explicitly labelled provisional.

## 7. Research-candidate sizing

All percentages refer to capital reserved for SPY, QQQ or SOXX, not total portfolio NAV.

| Stage | Increment | Cumulative | Evidence required |
|---|---:|---:|---|
| Early micro-probe | 1%–5% | 1%–5% | State 2; small enough to tolerate being early. |
| Exhaustion tranche | 5%–10% | 7.5%–15% | State 3; stress no longer accelerates. |
| Confirmed-bottom tranche | 10%–20% | 20%–35% | State 4; retest/breadth/price confirmation. |
| Recovery tranche | 10%–25% | 35%–60% | State 5; persistent recovery. |
| Reserved capital | remainder | — | Retained for deeper bear risk or later opportunities. |

These are governance ranges, not proven optimal sizes. SMH never receives a sizing row.

## 8. Tactical leverage

### Entry gate

Leverage is not permitted merely because drawdown is deep. Normally require State 4 or 5 plus breadth improvement, improving relative strength, falling ATR/RV, stable credit and a recovery structure persisting beyond one session. USD also requires no SMH/SOXX `VETO`.

### Position role

The leveraged ETF is a temporary tactical overlay intended to capture the first sustained rebound phase. It is not a permanent replacement for the ordinary ETF.

### Exit / reversion

Exit/revert when the confirmed retest low fails, breadth/relative strength rolls over, volatility reaccelerates, volatility/credit stress worsens, recovery structure breaks, target is reached, risk budget is exhausted or time stop expires.

Every tactical recommendation must include entry rationale, invalidation, target/reversion rule, volatility exit and time stop.

## 9. Asset-specific emphasis

### SPY

Prioritise broad breadth, VIX complex, HY credit/systemic stress and cap-weighted versus equal-weight divergence.

### QQQ

Prioritise Nasdaq breadth, valuation-repricing/long-bear throttle, QQQ/SPY relative strength and larger drawdown tolerance than SPY.

### SOXX

Prioritise SOXX-specific cycle drawdown, historical semiconductor breadth, SOXX/QQQ relative strength, sector liquidation volume, sector IV versus realised volatility and stress across major constituents. Add SMH only as an independently tested corroboration/veto input.

### SMH reference

Display its own drawdown, state, exhaustion and confirmation, but no tranche. Agreement is useful because index construction differs; it is not proof that both funds have identical bottoms.

## 10. Indicators explicitly demoted

The following cannot be standalone bottom triggers:

- absolute VIX threshold;
- VIX term structure alone;
- RSI or MACD alone;
- fixed 52-week drawdown alone;
- one high-volume down day;
- moving-average crossover alone;
- raw put/call ratio or call count;
- raw SKEW;
- public-OI dealer-gamma estimates;
- low-frequency positioning/flow series as daily timing signals;
- SMH agreement alone.

## 11. Live-monitor output requirements

Every complete report should show:

- SPY, QQQ and SOXX primary rows with source, completed-close date, cycle/52-week drawdowns, volatility-normalised decline, underwater duration, state, staged sizing, next trigger and invalidation;
- a separate SMH reference row with no capital or tranche;
- one SMH/SOXX pair status and its exact causal reason;
- leverage states `NOT READY`, `TACTICAL REVIEW` or `EXIT/REVERT`;
- observed facts, backtested evidence and provisional judgement separated visibly.
