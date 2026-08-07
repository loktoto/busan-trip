#!/usr/bin/env python3
"""Asset-specific late-stage bottom candidates for QQQ and SOXX.

This module is deliberately separate from the production monitor.  It tests
whether waiting for completed-close exhaustion, retest and confirmation evidence
improves bottom proximity without replacing one early error with a late chase.

Causality:
- every feature uses information available by completed close t;
- every candidate executes at next regular-session open t+1 plus stored costs;
- at most one late-stage tranche is emitted per drawdown episode;
- SMH never creates or sizes a SOXX trade.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

from backtest import Config, episode_catalog, episode_ids


@dataclass(frozen=True)
class LateStageSpec:
    name: str
    symbol: str
    family: str
    washout_lookback: int
    min_exhaustion_score: int
    min_current_drawdown: float
    reclaim_ma: int
    min_confirmation_score: int
    max_rv_ratio: float
    min_volume_ratio: float
    min_close_location: float
    retest_atr_distance: float
    max_retest_break_atr: float
    tranche: float


SPECS: dict[str, tuple[LateStageSpec, ...]] = {
    "QQQ": (
        LateStageSpec(
            "QQQ_EXHAUSTION_RECLAIM", "QQQ", "EXHAUSTION_RECLAIM",
            12, 3, 0.040, 10, 3, 1.05, 0.75, 0.65, 1.10, 0.50, 0.05,
        ),
        LateStageSpec(
            "QQQ_RETEST_CONFIRM", "QQQ", "RETEST_CONFIRM",
            25, 2, 0.035, 10, 2, 1.10, 0.70, 0.68, 1.25, 0.50, 0.05,
        ),
        LateStageSpec(
            "QQQ_STRONG_CONFIRM", "QQQ", "STRONG_CONFIRM",
            20, 2, 0.030, 20, 4, 1.00, 0.75, 0.65, 1.10, 0.50, 0.05,
        ),
        LateStageSpec(
            "QQQ_DUAL_PATH", "QQQ", "DUAL_PATH",
            25, 2, 0.035, 10, 3, 1.05, 0.75, 0.68, 1.25, 0.50, 0.05,
        ),
    ),
    "SOXX": (
        LateStageSpec(
            "SOXX_EXHAUSTION_RECLAIM", "SOXX", "EXHAUSTION_RECLAIM",
            15, 3, 0.100, 20, 4, 0.98, 0.85, 0.70, 1.50, 0.75, 0.05,
        ),
        LateStageSpec(
            "SOXX_RETEST_CONFIRM", "SOXX", "RETEST_CONFIRM",
            30, 3, 0.080, 10, 3, 1.00, 0.80, 0.70, 1.50, 0.75, 0.05,
        ),
        LateStageSpec(
            "SOXX_STRONG_CONFIRM", "SOXX", "STRONG_CONFIRM",
            25, 3, 0.070, 20, 4, 0.95, 0.80, 0.68, 1.40, 0.75, 0.05,
        ),
        LateStageSpec(
            "SOXX_DUAL_PATH", "SOXX", "DUAL_PATH",
            30, 3, 0.080, 10, 3, 1.00, 0.80, 0.70, 1.50, 0.75, 0.05,
        ),
    ),
}


def _sessions_since(event: pd.Series) -> pd.Series:
    out: list[float] = []
    last: int | None = None
    for i, value in enumerate(event.fillna(False).astype(bool)):
        if value:
            last = i
        out.append(np.nan if last is None else float(i - last))
    return pd.Series(out, index=event.index, dtype=float)


def add_late_stage_features(x: pd.DataFrame, spec: LateStageSpec) -> pd.DataFrame:
    """Add causal late-stage diagnostics for one declared candidate."""
    y = x.copy()
    exhaustion_score = y.exhaustion_score.fillna(0).astype(float)
    washout = (
        (y.newlow20.astype(bool) & (exhaustion_score >= spec.min_exhaustion_score))
        | (y.crash.astype(bool) & y.newlow10.astype(bool))
    ).fillna(False)
    y["late_washout"] = washout
    y["late_sessions_since_washout"] = _sessions_since(washout)
    y["late_recent_washout"] = (
        washout.shift(1)
        .rolling(spec.washout_lookback, min_periods=1)
        .max()
        .fillna(0)
        .astype(bool)
    )
    y["late_washout_low"] = y.Low.where(washout).ffill(limit=spec.washout_lookback)
    y["late_rv_ratio"] = y.rv20 / y.rv20.shift(5).replace(0, np.nan)
    y["late_higher_low_5"] = (
        y.Low.rolling(5, min_periods=3).min()
        > y.Low.shift(5).rolling(5, min_periods=3).min()
    ).fillna(False)

    ma_name = f"sma{spec.reclaim_ma}"
    if ma_name not in y:
        raise ValueError(f"Missing required indicator: {ma_name}")
    reclaim_ma = y[ma_name]

    drawdown_ok = y.cycle_dd <= -spec.min_current_drawdown
    no_veto = (~y.long_bear.astype(bool)) & (~y.credit_veto.astype(bool))
    quality = (
        y.late_recent_washout
        & drawdown_ok
        & (y.close_loc >= spec.min_close_location)
        & (y.vol_ratio >= spec.min_volume_ratio)
        & (y.late_rv_ratio <= spec.max_rv_ratio)
        & no_veto
    ).fillna(False)

    y["late_exhaustion_reclaim"] = (
        quality
        & (y.Close > reclaim_ma)
        & (y.sma10_slope > 0)
        & (y.r5 > 0)
        & y.late_higher_low_5
        & (y.confirmation_score >= spec.min_confirmation_score)
    ).fillna(False)

    atr = y.atr14.replace(0, np.nan)
    y["late_retest_atr_distance"] = (y.Low - y.late_washout_low) / atr
    y["late_retest_touch"] = (
        y.late_recent_washout
        & drawdown_ok
        & y.late_washout_low.notna()
        & (y.late_retest_atr_distance <= spec.retest_atr_distance)
        & (y.late_retest_atr_distance >= -spec.max_retest_break_atr)
        & (~y.newlow20.astype(bool))
        & no_veto
    ).fillna(False)
    prior_retest = (
        y.late_retest_touch.shift(1)
        .rolling(3, min_periods=1)
        .max()
        .fillna(0)
        .astype(bool)
    )
    y["late_retest_confirm"] = (
        prior_retest
        & drawdown_ok
        & (y.Close > y.High.shift(1))
        & (y.Close > reclaim_ma)
        & (y.r1 > 0)
        & (y.sma10_slope > 0)
        & (y.close_loc >= spec.min_close_location)
        & (y.vol_ratio >= spec.min_volume_ratio)
        & (y.late_rv_ratio <= spec.max_rv_ratio)
        & no_veto
    ).fillna(False)

    y["late_strong_confirm"] = (
        y.late_recent_washout
        & drawdown_ok
        & (y.Close > y.sma20)
        & (y.sma10 > y.sma20)
        & (y.sma10_slope > 0)
        & (y.r10 > 0)
        & y.late_higher_low_5
        & (y.confirmation_score >= spec.min_confirmation_score)
        & (y.late_rv_ratio <= spec.max_rv_ratio)
        & (y.vol_ratio >= spec.min_volume_ratio)
        & no_veto
    ).fillna(False)

    if spec.family == "EXHAUSTION_RECLAIM":
        signal = y.late_exhaustion_reclaim
    elif spec.family == "RETEST_CONFIRM":
        signal = y.late_retest_confirm
    elif spec.family == "STRONG_CONFIRM":
        signal = y.late_strong_confirm
    elif spec.family == "DUAL_PATH":
        signal = y.late_exhaustion_reclaim | y.late_retest_confirm
    else:
        raise ValueError(f"Unknown family: {spec.family}")
    y["late_stage_signal"] = signal.fillna(False)
    return y


def _signal_reason(r: pd.Series, spec: LateStageSpec) -> str:
    if spec.family == "DUAL_PATH":
        if bool(r.late_retest_confirm):
            return "RETEST_CONFIRM"
        if bool(r.late_exhaustion_reclaim):
            return "EXHAUSTION_RECLAIM"
    return spec.family


def run_late_stage(
    x: pd.DataFrame,
    cfg: Config,
    spec: LateStageSpec,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Emit at most one fixed, bounded late-stage tranche per episode."""
    if cfg.symbol != spec.symbol:
        raise ValueError(f"Config/spec mismatch: {cfg.symbol} != {spec.symbol}")
    if not (cfg.min_tranche <= spec.tranche <= cfg.max_tranche):
        raise ValueError("Late-stage tranche breaches configured tranche bounds")

    y = add_late_stage_features(x, spec)
    y["episode"] = episode_ids(y, cfg)
    catalog = episode_catalog(y, cfg)
    taken: set[int] = set()
    rows: list[dict[str, Any]] = []

    for i in range(200, len(y) - 1):
        r = y.iloc[i]
        eid = int(r.episode)
        if eid == 0 or eid in taken or not bool(r.late_stage_signal):
            continue
        if bool(r.long_bear) or bool(r.credit_veto):
            continue

        nxt = y.iloc[i + 1]
        raw_px = float(nxt.Open)
        px = raw_px * (1 + cfg.all_in_cost_bps / 10_000)
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
                "tranche": float(spec.tranche),
                "cumulative": float(spec.tranche),
                "state": 4,
                "reason": _signal_reason(r, spec),
                "cycle_dd": float(r.cycle_dd),
                "dd_52w": float(r.dd_52w),
                "atrp": float(r.atrp),
                "rv20": float(r.rv20),
                "volume_ratio": float(r.vol_ratio),
                "underwater": int(r.underwater),
                "long_bear": bool(r.long_bear),
                "late_sessions_since_washout": float(r.late_sessions_since_washout),
                "late_rv_ratio": float(r.late_rv_ratio),
                "late_retest_atr_distance": (
                    float(r.late_retest_atr_distance)
                    if np.isfinite(float(r.late_retest_atr_distance))
                    else np.nan
                ),
                "late_exhaustion_reclaim": bool(r.late_exhaustion_reclaim),
                "late_retest_confirm": bool(r.late_retest_confirm),
                "late_strong_confirm": bool(r.late_strong_confirm),
                "spec": spec.name,
            }
        )
        taken.add(eid)

    return pd.DataFrame(rows), catalog


def spec_dict(spec: LateStageSpec) -> dict[str, Any]:
    return asdict(spec)
