#!/usr/bin/env python3
"""Market-bottom v1.2 dual-path recovery overlay.

This research candidate addresses a specific failure mode in v1.1: a market can
briefly enter the drawdown watch zone and then rebound above that threshold before
the conservative engine produces a trade.  V1.1 still returns WAIT in that case.

V1.2 preserves the audited left-side, exhaustion and confirmation rules, and adds
one tightly bounded post-threshold catch-up tranche per drawdown episode.

Causal constraints
------------------
- signal uses completed close t only;
- execution is next open t+1 plus configured costs;
- the qualifying threshold breach must have occurred before the signal close;
- no future trough, forward return or episode completion information is used;
- SMH remains reference-only and is not supported by this production candidate.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from backtest import Config, episode_catalog, episode_ids, target_deployment
from recovery_v11 import add_recovery_features, _bounded_target

PRIMARY = ("SPY", "QQQ", "SOXX")

# Deliberately simple, pre-declared policy values.  They are research candidates,
# not fitted optima.  Size is a fraction of capital reserved for that asset.
CATCHUP_WINDOW = {"SPY": 10, "QQQ": 10, "SOXX": 7}
CATCHUP_SIZE = {"SPY": 0.02, "QQQ": 0.03, "SOXX": 0.05}
CATCHUP_MAX_RECOVERED_DD = {"SPY": 0.025, "QQQ": 0.035, "SOXX": 0.060}
CATCHUP_MAX_ATR_ABOVE_THRESHOLD = 1.25
CATCHUP_MIN_CLOSE_LOCATION = 0.55
CATCHUP_MIN_VOTES = 3
CATCHUP_RV_MULTIPLE = 1.08


def _policy(symbol: str) -> tuple[int, float, float]:
    if symbol not in PRIMARY:
        raise ValueError(f"v1.2 catch-up supports only {PRIMARY}; got {symbol}")
    return (
        CATCHUP_WINDOW[symbol],
        CATCHUP_SIZE[symbol],
        CATCHUP_MAX_RECOVERED_DD[symbol],
    )


def add_catchup_features(x: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Add causal post-threshold catch-up diagnostics.

    The qualifying breach is shifted by one session, so the current bar cannot
    create and consume its own threshold event.  A catch-up is therefore possible
    only after a completed prior close entered the watch zone and a later completed
    close rebounded above it.
    """
    window, _, max_recovered_dd = _policy(cfg.symbol)
    y = add_recovery_features(x, cfg)

    prior_breach = (y.cycle_dd <= -cfg.watch_dd).shift(1).fillna(False)
    y["catchup_recent_breach"] = (
        prior_breach.rolling(window, min_periods=1).max().fillna(0).astype(bool)
    )
    y["catchup_sessions_since_breach"] = np.nan
    last_breach: int | None = None
    for i in range(len(y)):
        if bool(prior_breach.iloc[i]):
            last_breach = i - 1
        if last_breach is not None:
            y.at[y.index[i], "catchup_sessions_since_breach"] = i - last_breach

    threshold_price = y.cycle_high * (1.0 - cfg.watch_dd)
    y["catchup_threshold_price"] = threshold_price
    y["catchup_atr_above_threshold"] = (
        (y.Close - threshold_price) / y.atr14.replace(0, np.nan)
    )
    current_depth = (-y.cycle_dd).clip(lower=0.0)
    y["catchup_recovered_dd"] = (cfg.watch_dd - current_depth).clip(lower=0.0)

    rv_reference = y.rv20.shift(5)
    vote_parts = pd.concat(
        [
            y.r5 > 0,
            y.Close >= y.sma10,
            y.sma10_slope > 0,
            y.rv20 <= rv_reference * CATCHUP_RV_MULTIPLE,
            y.recovery_bounce >= y.recovery_threshold,
        ],
        axis=1,
    ).fillna(False)
    y["catchup_votes"] = vote_parts.sum(axis=1)

    above_watch = y.cycle_dd > -cfg.watch_dd
    still_underwater = y.cycle_dd < -cfg.recovery_dd
    within_dd_band = y.catchup_recovered_dd <= max_recovered_dd + 1e-12
    within_atr_band = (
        y.catchup_atr_above_threshold <= CATCHUP_MAX_ATR_ABOVE_THRESHOLD
    )
    positive_atr_distance = y.catchup_atr_above_threshold >= 0

    y["catchup_probe"] = (
        above_watch
        & still_underwater
        & y.catchup_recent_breach
        & within_dd_band
        & within_atr_band
        & positive_atr_distance
        & (y.r1 > 0)
        & (y.close_loc >= CATCHUP_MIN_CLOSE_LOCATION)
        & (y.catchup_votes >= CATCHUP_MIN_VOTES)
        & (~y.newlow10.astype(bool))
        & (~y.newlow20.astype(bool))
        & (~y.long_bear.astype(bool))
        & (~y.credit_veto.astype(bool))
    ).fillna(False)
    return y


def run_v12(x: pd.DataFrame, cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run baseline + v1.1 recovery + one bounded post-threshold catch-up."""
    y = add_catchup_features(x, cfg)
    y["episode"] = episode_ids(y, cfg)
    catalog = episode_catalog(y, cfg)

    rows: list[dict[str, Any]] = []
    deployed: dict[int, float] = {}
    last_i: dict[int, int] = {}
    last_px: dict[int, float] = {}
    last_exhaustion: dict[int, bool] = {}
    last_confirmation: dict[int, bool] = {}
    last_recovery_probe: dict[int, bool] = {}
    last_catchup_probe: dict[int, bool] = {}
    recovery_probe_taken: set[int] = set()
    catchup_probe_taken: set[int] = set()

    for i in range(200, len(y) - 1):
        r = y.iloc[i]
        eid = int(r.episode)
        if eid == 0 or bool(r.credit_veto):
            continue

        inside_start_zone = float(r.cycle_dd) <= -cfg.start_dd
        catchup_signal = bool(r.catchup_probe)
        # Outside the start zone, only the explicitly bounded catch-up path is legal.
        if not inside_start_zone and not catchup_signal:
            continue

        used = deployed.get(eid, 0.0)
        raw_want = target_deployment(float(r.cycle_dd), cfg)
        if bool(r.long_bear) and not bool(r.exhaustion) and not bool(r.confirmation):
            raw_want = min(raw_want, cfg.long_bear_cap)
        want, floor_applied = _bounded_target(raw_want, used, cfg)

        exhaustion_transition = (
            inside_start_zone
            and bool(r.exhaustion)
            and not last_exhaustion.get(eid, False)
        )
        confirmation_transition = (
            inside_start_zone
            and bool(r.confirmation)
            and not last_confirmation.get(eid, False)
        )
        recovery_transition = (
            inside_start_zone
            and bool(r.recovery_probe)
            and not last_recovery_probe.get(eid, False)
            and eid not in recovery_probe_taken
        )
        catchup_transition = (
            catchup_signal
            and not last_catchup_probe.get(eid, False)
            and eid not in catchup_probe_taken
            and used < min(CATCHUP_SIZE[cfg.symbol], cfg.max_deploy) - 1e-12
        )

        if exhaustion_transition:
            want = max(want, used + cfg.exhaustion_bonus)
        if confirmation_transition:
            want = max(want, used + cfg.confirmation_bonus)
        if recovery_transition:
            want = max(want, used + min(cfg.micro_probe, cfg.max_tranche))
        if catchup_transition:
            # Catch up only to the small declared participation cap; never add a
            # full confirmation tranche merely because price bounced.
            want = max(
                want,
                min(CATCHUP_SIZE[cfg.symbol], cfg.max_deploy, used + cfg.max_tranche),
            )
        want = min(max(want, used), cfg.max_deploy)

        fresh = inside_start_zone and bool(r.newlow10 or r.newlow20)
        crash = inside_start_zone and bool(r.crash)
        cooldown_ok = eid not in last_i or i - last_i[eid] >= cfg.cooldown
        spacing_ok = eid not in last_px or float(r.Close) <= last_px[eid] * (1 - cfg.spacing)
        event = (
            fresh
            or crash
            or exhaustion_transition
            or confirmation_transition
            or recovery_transition
            or catchup_transition
        )
        eligible = event and (
            cooldown_ok
            or spacing_ok
            or confirmation_transition
            or recovery_transition
            or catchup_transition
        )

        last_exhaustion[eid] = bool(r.exhaustion)
        last_confirmation[eid] = bool(r.confirmation)
        last_recovery_probe[eid] = bool(r.recovery_probe)
        last_catchup_probe[eid] = bool(r.catchup_probe)
        if not eligible:
            continue

        if used == 0 and inside_start_zone:
            want = max(want, cfg.micro_probe)
        tranche = min(max(0.0, want - used), cfg.max_tranche, cfg.max_deploy - used)
        if tranche < cfg.min_tranche:
            continue

        nxt = y.iloc[i + 1]
        raw_px = float(nxt.Open)
        px = raw_px * (1 + cfg.all_in_cost_bps / 10_000)
        if catchup_transition:
            state, reason = 5, "POST_THRESHOLD_CATCHUP"
        elif recovery_transition:
            state, reason = 5, "INSIDE_ZONE_RECOVERY"
        elif confirmation_transition:
            state, reason = 4, "CONFIRMATION"
        elif exhaustion_transition:
            state, reason = 3, "EXHAUSTION"
        else:
            state, reason = 2, "LEFT_SIDE_EVENT"

        used += tranche
        deployed[eid] = used
        last_i[eid] = i + 1
        last_px[eid] = px
        if recovery_transition:
            recovery_probe_taken.add(eid)
        if catchup_transition:
            catchup_probe_taken.add(eid)

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
                "reason": reason,
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
                "catchup_probe_transition": catchup_transition,
                "catchup_recent_breach": bool(r.catchup_recent_breach),
                "catchup_sessions_since_breach": (
                    None
                    if pd.isna(r.catchup_sessions_since_breach)
                    else int(r.catchup_sessions_since_breach)
                ),
                "catchup_recovered_dd": float(r.catchup_recovered_dd),
                "catchup_atr_above_threshold": float(r.catchup_atr_above_threshold),
                "catchup_votes": int(r.catchup_votes),
                "recovery_bounce": float(r.recovery_bounce),
                "deployment_floor_applied": floor_applied,
            }
        )

    return pd.DataFrame(rows), catalog
