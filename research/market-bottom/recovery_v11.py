#!/usr/bin/env python3
"""Market-bottom v1.1 recovery overlay.

This module fixes three production inconsistencies without changing the audited
price indicators:

1. deployment targets can never fall below already deployed capital;
2. an active episode can remain RECOVERY_UNDERWAY after price rebounds above the
   watch threshold but before near-full recovery;
3. one small, volatility-normalised recovery probe may be added after a strong
   first rebound from a recent trough.

Signals use completed close t and execute at next open t+1 plus configured costs.
The recovery probe is allowed at most once per episode, is disabled in a long-bear
regime, and never applies to SMH in production.
"""
from __future__ import annotations

import math
from typing import Any

import pandas as pd

from backtest import Config, episode_catalog, episode_ids, target_deployment

RECOVERY_LOOKBACK = 5
RECOVERY_WASHOUT_LOOKBACK = 3
RECOVERY_MIN_BOUNCE = 0.015
RECOVERY_ATR_MULTIPLE = 0.75
RECOVERY_MIN_CLOSE_LOCATION = 0.75
RECOVERY_MIN_VOLUME_RATIO = 0.90


def add_recovery_features(x: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Add causal recovery-probe diagnostics to an indicator frame."""
    y = x.copy()
    recent_close_low = y.Close.rolling(RECOVERY_LOOKBACK, min_periods=2).min()
    y["recovery_bounce"] = y.Close / recent_close_low - 1.0
    y["recovery_threshold"] = pd.concat(
        [
            pd.Series(RECOVERY_MIN_BOUNCE, index=y.index, dtype=float),
            RECOVERY_ATR_MULTIPLE * y.atrp,
        ],
        axis=1,
    ).max(axis=1)

    prior_washout = (
        y[["newlow10", "newlow20", "crash", "exhaustion"]]
        .astype(bool)
        .any(axis=1)
        .shift(1)
        .rolling(RECOVERY_WASHOUT_LOOKBACK, min_periods=1)
        .max()
        .fillna(0)
        .astype(bool)
    )
    y["recent_washout"] = prior_washout

    prior_high = y.High.shift(1)
    y["recovery_probe"] = (
        (y.cycle_dd <= -cfg.start_dd)
        & y.recent_washout
        & (y.recovery_bounce >= y.recovery_threshold)
        & (y.r1 > 0)
        & (y.close_loc >= RECOVERY_MIN_CLOSE_LOCATION)
        & (y.vol_ratio >= RECOVERY_MIN_VOLUME_RATIO)
        & (y.Close > prior_high)
        & (~y.long_bear.astype(bool))
        & (~y.credit_veto.astype(bool))
        & (~y.newlow10.astype(bool))
        & (~y.newlow20.astype(bool))
    ).fillna(False)
    return y


def _bounded_target(raw_target: float, used: float, cfg: Config) -> tuple[float, bool]:
    """Apply long-only deployment monotonicity and the hard model cap."""
    bounded = min(max(float(raw_target), float(used)), cfg.max_deploy)
    return bounded, bounded > float(raw_target) + 1e-12


def run_v11(x: pd.DataFrame, cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reconstruct all trades using baseline rules plus the v1.1 recovery overlay."""
    y = add_recovery_features(x, cfg)
    y["episode"] = episode_ids(y, cfg)
    catalog = episode_catalog(y, cfg)

    rows: list[dict[str, Any]] = []
    deployed: dict[int, float] = {}
    last_i: dict[int, int] = {}
    last_px: dict[int, float] = {}
    last_exhaustion: dict[int, bool] = {}
    last_confirmation: dict[int, bool] = {}
    last_recovery_probe: dict[int, bool] = {}
    recovery_probe_taken: set[int] = set()

    for i in range(200, len(y) - 1):
        r = y.iloc[i]
        eid = int(r.episode)
        if eid == 0 or float(r.cycle_dd) > -cfg.start_dd or bool(r.credit_veto):
            continue

        used = deployed.get(eid, 0.0)
        raw_want = target_deployment(float(r.cycle_dd), cfg)
        if bool(r.long_bear) and not bool(r.exhaustion) and not bool(r.confirmation):
            raw_want = min(raw_want, cfg.long_bear_cap)
        want, floor_applied = _bounded_target(raw_want, used, cfg)

        exhaustion_transition = bool(r.exhaustion) and not last_exhaustion.get(eid, False)
        confirmation_transition = bool(r.confirmation) and not last_confirmation.get(eid, False)
        recovery_transition = (
            bool(r.recovery_probe)
            and not last_recovery_probe.get(eid, False)
            and eid not in recovery_probe_taken
        )

        if exhaustion_transition:
            want = max(want, used + cfg.exhaustion_bonus)
        if confirmation_transition:
            want = max(want, used + cfg.confirmation_bonus)
        if recovery_transition:
            # One small micro-probe only.  It cannot exceed the normal tranche cap.
            want = max(want, used + min(cfg.micro_probe, cfg.max_tranche))
        want = min(max(want, used), cfg.max_deploy)

        fresh = bool(r.newlow10 or r.newlow20)
        crash = bool(r.crash)
        cooldown_ok = eid not in last_i or i - last_i[eid] >= cfg.cooldown
        spacing_ok = eid not in last_px or float(r.Close) <= last_px[eid] * (1 - cfg.spacing)
        event = fresh or crash or exhaustion_transition or confirmation_transition or recovery_transition
        eligible = event and (
            cooldown_ok or spacing_ok or confirmation_transition or recovery_transition
        )

        last_exhaustion[eid] = bool(r.exhaustion)
        last_confirmation[eid] = bool(r.confirmation)
        last_recovery_probe[eid] = bool(r.recovery_probe)
        if not eligible:
            continue

        if used == 0:
            want = max(want, cfg.micro_probe)
        tranche = min(max(0.0, want - used), cfg.max_tranche, cfg.max_deploy - used)
        if tranche < cfg.min_tranche:
            continue

        nxt = y.iloc[i + 1]
        raw_px = float(nxt.Open)
        px = raw_px * (1 + cfg.all_in_cost_bps / 10_000)
        if recovery_transition:
            state = 5
        elif confirmation_transition:
            state = 4
        elif exhaustion_transition:
            state = 3
        else:
            state = 2

        used += tranche
        deployed[eid] = used
        last_i[eid] = i + 1
        last_px[eid] = px
        if recovery_transition:
            recovery_probe_taken.add(eid)

        rows.append(
            {
                "symbol": cfg.symbol,
                "episode": eid,
                "signal_index": i,
                "execution_index": i + 1,
                "signal_date": r.Date.date(),
                "execution_date": nxt.Date.date(),
                "raw_open": raw_px,
                "execution_price": px,
                "cost_bps": cfg.all_in_cost_bps,
                "tranche": tranche,
                "cumulative": used,
                "state": state,
                "cycle_dd": float(r.cycle_dd),
                "dd_52w": float(r.dd_52w),
                "atrp": float(r.atrp),
                "rv20": float(r.rv20),
                "volume_ratio": float(r.vol_ratio),
                "underwater": int(r.underwater),
                "long_bear": bool(r.long_bear),
                "fresh_low": fresh,
                "crash": crash,
                "exhaustion_transition": exhaustion_transition,
                "confirmation_transition": confirmation_transition,
                "recovery_probe_transition": recovery_transition,
                "recent_washout": bool(r.recent_washout),
                "recovery_bounce": float(r.recovery_bounce),
                "recovery_threshold": float(r.recovery_threshold),
                "deployment_floor_applied": floor_applied,
            }
        )

    return pd.DataFrame(rows), catalog


def state_v11(latest: pd.Series, prior: pd.Series, cfg: Config, used: float) -> int:
    """Return a coherent state for an active episode and its deployed capital."""
    dd = float(latest.cycle_dd)
    active_episode = int(latest.get("episode", 0)) > 0

    if bool(latest.credit_veto) and dd <= -cfg.watch_dd:
        return 6

    # Do not collapse an already deployed active episode to NO_SETUP merely because
    # price rebounded above the watch threshold.  It remains in recovery until the
    # episode reaches the near-full-recovery boundary.
    if dd > -cfg.watch_dd:
        if active_episode and used > 0 and dd < -cfg.recovery_dd:
            return 5
        return 0

    if dd > -cfg.start_dd:
        return 1
    if bool(latest.get("recovery_probe", False)):
        return 5
    if bool(latest.confirmation):
        recovery = (
            math.isfinite(float(latest.get("r5", float("nan"))))
            and float(latest.r5) > 0
            and math.isfinite(float(latest.get("sma10", float("nan"))))
            and float(latest.Close) > float(latest.sma10)
        )
        return 5 if recovery else 4
    if bool(latest.exhaustion):
        return 3
    if bool(latest.newlow10 or latest.newlow20 or latest.crash):
        return 2
    return 1


def candidate_v11(x: pd.DataFrame, trades: pd.DataFrame, cfg: Config) -> dict[str, Any]:
    """Calculate the next-open candidate with monotonic deployment and recovery probe."""
    y = add_recovery_features(x, cfg)
    if "episode" not in y:
        y["episode"] = episode_ids(y, cfg)
    i = len(y) - 1
    latest = y.iloc[i]
    prior = y.iloc[i - 1]
    eid = int(latest.episode)
    episode_trades = (
        trades.loc[trades.episode == eid].sort_values("execution_index")
        if eid and not trades.empty
        else pd.DataFrame()
    )
    used = float(episode_trades.tranche.sum()) if not episode_trades.empty else 0.0
    recovery_already_used = bool(
        not episode_trades.empty
        and "recovery_probe_transition" in episode_trades
        and episode_trades.recovery_probe_transition.fillna(False).any()
    )

    result: dict[str, Any] = {
        "current_episode": eid,
        "cumulative_model_deployment": used,
        "candidate_tranche": 0.0,
        "candidate_target_cumulative": used,
        "candidate_reason": "NONE",
        "eligible_at_next_open": False,
        "recovery_probe": bool(latest.recovery_probe),
        "recent_washout": bool(latest.recent_washout),
        "recovery_bounce": float(latest.recovery_bounce),
        "recovery_threshold": float(latest.recovery_threshold),
        "recovery_probe_already_used": recovery_already_used,
        "deployment_floor_applied": False,
    }
    if eid == 0 or float(latest.cycle_dd) > -cfg.start_dd or bool(latest.credit_veto):
        return result

    raw_want = target_deployment(float(latest.cycle_dd), cfg)
    if bool(latest.long_bear) and not bool(latest.exhaustion) and not bool(latest.confirmation):
        raw_want = min(raw_want, cfg.long_bear_cap)
    want, floor_applied = _bounded_target(raw_want, used, cfg)
    result["deployment_floor_applied"] = floor_applied

    exhaustion_transition = bool(latest.exhaustion) and not bool(prior.exhaustion)
    confirmation_transition = bool(latest.confirmation) and not bool(prior.confirmation)
    recovery_transition = (
        bool(latest.recovery_probe)
        and not bool(prior.recovery_probe)
        and not recovery_already_used
    )
    if exhaustion_transition:
        want = max(want, used + cfg.exhaustion_bonus)
    if confirmation_transition:
        want = max(want, used + cfg.confirmation_bonus)
    if recovery_transition:
        want = max(want, used + min(cfg.micro_probe, cfg.max_tranche))
    want = min(max(want, used), cfg.max_deploy)

    fresh = bool(latest.newlow10 or latest.newlow20)
    crash = bool(latest.crash)
    if episode_trades.empty:
        cooldown_ok = spacing_ok = True
    else:
        last = episode_trades.iloc[-1]
        cooldown_ok = i - int(last.execution_index) >= cfg.cooldown
        spacing_ok = float(latest.Close) <= float(last.execution_price) * (1 - cfg.spacing)
    event = fresh or crash or exhaustion_transition or confirmation_transition or recovery_transition
    eligible = event and (
        cooldown_ok or spacing_ok or confirmation_transition or recovery_transition
    )
    if not eligible:
        result["candidate_target_cumulative"] = float(want)
        result["candidate_reason"] = "WAIT_COOLDOWN_OR_PRICE_SPACING" if event else "NO_NEW_EVENT"
        return result

    if used == 0:
        want = max(want, cfg.micro_probe)
    tranche = min(max(0.0, want - used), cfg.max_tranche, cfg.max_deploy - used)
    if tranche < cfg.min_tranche:
        result["candidate_target_cumulative"] = float(want)
        result["candidate_reason"] = "BELOW_MINIMUM_TRANCHE"
        return result

    reasons: list[str] = []
    if fresh:
        reasons.append("FRESH_LOW")
    if crash:
        reasons.append("CRASH_OVERRIDE")
    if exhaustion_transition:
        reasons.append("EXHAUSTION_TRANSITION")
    if confirmation_transition:
        reasons.append("CONFIRMATION_TRANSITION")
    if recovery_transition:
        reasons.append("RECOVERY_PROBE_TRANSITION")
    result.update(
        {
            "candidate_tranche": float(tranche),
            "candidate_target_cumulative": float(used + tranche),
            "candidate_reason": "+".join(reasons),
            "eligible_at_next_open": True,
        }
    )
    return result
