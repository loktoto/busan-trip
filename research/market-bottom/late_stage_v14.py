#!/usr/bin/env python3
"""Regime-aware late-stage bottom candidates for QQQ and SOXX.

V1.3 showed that a completed-close rebound can still be an early bear-market rally.
V1.4 therefore separates ordinary corrections from falling-200DMA bear regimes.
In a bear regime, a candidate must be mature: sufficiently deep, underwater for at
least 60 sessions, supported by multiple washouts, and accompanied by a flattening
200DMA decline.  Signals remain close-t and execute next-open t+1.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any

import numpy as np
import pandas as pd

from backtest import Config, episode_catalog, episode_ids
from late_stage_v13 import SPECS, LateStageSpec, add_late_stage_features


@dataclass(frozen=True)
class RegimeParams:
    deep_bear_drawdown: float
    min_underwater_days: int = 60
    washout_count_window: int = 126
    min_prior_washouts: int = 2
    flattening_lookback: int = 20


REGIME_PARAMS = {
    "QQQ": RegimeParams(deep_bear_drawdown=0.15),
    "SOXX": RegimeParams(deep_bear_drawdown=0.25),
}


def _regime_specs(symbol: str) -> tuple[LateStageSpec, ...]:
    return tuple(
        replace(spec, name=spec.name.replace(symbol + "_", symbol + "_REGIME_"))
        for spec in SPECS[symbol]
    )


REGIME_SPECS = {symbol: _regime_specs(symbol) for symbol in ("QQQ", "SOXX")}


def add_regime_features(
    x: pd.DataFrame,
    spec: LateStageSpec,
    params: RegimeParams,
) -> pd.DataFrame:
    """Apply v1.3 signal quality inside an explicit market-regime gate."""
    original_long_bear = x.long_bear.astype(bool).copy()
    base_input = x.copy()
    # V1.3 prohibited every long-bear row. V1.4 evaluates them only through the
    # stricter mature-bear path below; credit veto remains active.
    base_input["long_bear"] = False
    y = add_late_stage_features(base_input, spec)
    y["long_bear"] = original_long_bear

    y["regime_washout_count"] = (
        y.late_washout.shift(1)
        .rolling(params.washout_count_window, min_periods=1)
        .sum()
        .fillna(0)
    )
    y["regime_sma50_slope10"] = y.sma50 / y.sma50.shift(10) - 1.0
    y["regime_sma200_flattening"] = y.sma200_slope > y.sma200_slope.shift(
        params.flattening_lookback
    )
    y["ordinary_correction_regime"] = (
        (y.Close >= y.sma200) | (y.sma200_slope >= 0)
    ).fillna(False)
    y["falling_200dma_regime"] = (
        (y.Close < y.sma200) & (y.sma200_slope < 0)
    ).fillna(False)
    y["mature_bear_regime"] = (
        y.falling_200dma_regime
        & (y.underwater >= params.min_underwater_days)
        & (y.regime_washout_count >= params.min_prior_washouts)
        & (y.cycle_dd <= -params.deep_bear_drawdown)
        & y.regime_sma200_flattening
        & (y.Close > y.sma10)
        & (y.sma10_slope > 0)
        & y.late_higher_low_5
        & (y.late_rv_ratio <= spec.max_rv_ratio)
        & (~y.credit_veto.astype(bool))
    ).fillna(False)
    y["regime_gate"] = (
        y.ordinary_correction_regime | y.mature_bear_regime
    ).fillna(False)
    y["regime_late_stage_signal"] = (
        y.late_stage_signal & y.regime_gate
    ).fillna(False)
    return y


def _reason(r: pd.Series, spec: LateStageSpec) -> str:
    if bool(r.mature_bear_regime):
        prefix = "MATURE_BEAR"
    else:
        prefix = "ORDINARY_CORRECTION"
    if spec.family == "DUAL_PATH":
        if bool(r.late_retest_confirm):
            return f"{prefix}_RETEST_CONFIRM"
        if bool(r.late_exhaustion_reclaim):
            return f"{prefix}_EXHAUSTION_RECLAIM"
    return f"{prefix}_{spec.family}"


def run_regime_late_stage(
    x: pd.DataFrame,
    cfg: Config,
    spec: LateStageSpec,
    params: RegimeParams | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if cfg.symbol != spec.symbol:
        raise ValueError(f"Config/spec mismatch: {cfg.symbol} != {spec.symbol}")
    if not (cfg.min_tranche <= spec.tranche <= cfg.max_tranche):
        raise ValueError("Late-stage tranche breaches configured tranche bounds")
    params = params or REGIME_PARAMS[cfg.symbol]
    y = add_regime_features(x, spec, params)
    y["episode"] = episode_ids(y, cfg)
    catalog = episode_catalog(y, cfg)
    taken: set[int] = set()
    rows: list[dict[str, Any]] = []

    for i in range(200, len(y) - 1):
        r = y.iloc[i]
        eid = int(r.episode)
        if eid == 0 or eid in taken or not bool(r.regime_late_stage_signal):
            continue
        if bool(r.credit_veto):
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
                "reason": _reason(r, spec),
                "cycle_dd": float(r.cycle_dd),
                "dd_52w": float(r.dd_52w),
                "atrp": float(r.atrp),
                "rv20": float(r.rv20),
                "volume_ratio": float(r.vol_ratio),
                "underwater": int(r.underwater),
                "long_bear": bool(r.long_bear),
                "ordinary_correction_regime": bool(r.ordinary_correction_regime),
                "mature_bear_regime": bool(r.mature_bear_regime),
                "regime_washout_count": float(r.regime_washout_count),
                "regime_sma200_flattening": bool(r.regime_sma200_flattening),
                "late_sessions_since_washout": float(r.late_sessions_since_washout),
                "late_rv_ratio": float(r.late_rv_ratio),
                "late_exhaustion_reclaim": bool(r.late_exhaustion_reclaim),
                "late_retest_confirm": bool(r.late_retest_confirm),
                "late_strong_confirm": bool(r.late_strong_confirm),
                "spec": spec.name,
            }
        )
        taken.add(eid)
    return pd.DataFrame(rows), catalog


def regime_spec_dict(spec: LateStageSpec, params: RegimeParams) -> dict[str, Any]:
    return {"late_stage": asdict(spec), "regime": asdict(params)}
