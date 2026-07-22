#!/usr/bin/env python3
"""Regime-mature stress normalisation candidates v1.8.

V1.7 demonstrated that a first decline in systemic/funding stress can still occur
inside a bear-market rally.  V1.8 corrects breach-age accounting and separates:

- ordinary corrections with a stable/rising 200DMA; and
- falling-200DMA bear regimes, which require deep drawdown, prolonged underwater
  duration, multiple independent stress-normalisation events and a flattening
  200DMA decline.

The engine remains research-only because OFR FSI and funding histories are current
or preliminary revisions rather than immutable point-in-time vintages.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

from backtest import Config, episode_catalog, episode_ids
from stress_normalization_v17 import StressSpec, add_stress_features


@dataclass(frozen=True)
class MaturityParams:
    deep_bear_drawdown: float
    min_underwater_days: int
    min_prior_stress_events: int
    stress_event_window: int
    sma200_flattening_lookback: int


PARAMS = {
    "SPY": MaturityParams(0.15, 90, 2, 126, 20),
    "QQQ": MaturityParams(0.20, 90, 2, 126, 20),
    "SOXX": MaturityParams(0.30, 90, 2, 126, 20),
}


SPECS: dict[str, tuple[StressSpec, ...]] = {
    "SPY": (
        StressSpec("SPY_MATURE_FSI", "SPY", "FSI", 0.035, 63, 63, 1.05, 0.03),
        StressSpec("SPY_MATURE_VOL", "SPY", "VOL", 0.035, 63, 63, 1.05, 0.03),
        StressSpec("SPY_MATURE_FUNDING", "SPY", "FUNDING", 0.035, 63, 63, 1.05, 0.03),
        StressSpec("SPY_MATURE_COMPOSITE", "SPY", "COMPOSITE", 0.035, 63, 63, 1.05, 0.03),
    ),
    "QQQ": (
        StressSpec("QQQ_MATURE_FSI", "QQQ", "FSI", 0.050, 63, 63, 1.05, 0.04),
        StressSpec("QQQ_MATURE_VOL", "QQQ", "VOL", 0.050, 63, 63, 1.05, 0.04),
        StressSpec("QQQ_MATURE_FUNDING", "QQQ", "FUNDING", 0.050, 63, 63, 1.05, 0.04),
        StressSpec("QQQ_MATURE_COMPOSITE", "QQQ", "COMPOSITE", 0.050, 63, 63, 1.05, 0.04),
    ),
    "SOXX": (
        StressSpec("SOXX_MATURE_FSI", "SOXX", "FSI", 0.090, 84, 84, 1.00, 0.05),
        StressSpec("SOXX_MATURE_VOL", "SOXX", "VOL", 0.090, 84, 84, 1.00, 0.05),
        StressSpec("SOXX_MATURE_FUNDING", "SOXX", "FUNDING", 0.090, 84, 84, 1.00, 0.05),
        StressSpec("SOXX_MATURE_COMPOSITE", "SOXX", "COMPOSITE", 0.090, 84, 84, 1.00, 0.05),
    ),
}


def _sessions_since_transition(event: pd.Series) -> pd.Series:
    result: list[float] = []
    last: int | None = None
    for i, value in enumerate(event.fillna(False).astype(bool)):
        if value:
            last = i
        result.append(np.nan if last is None else float(i - last))
    return pd.Series(result, index=event.index, dtype=float)


def add_maturity_features(
    x: pd.DataFrame,
    external: dict[str, pd.DataFrame],
    lags: dict[str, int],
    cfg: Config,
    params: MaturityParams | None = None,
) -> pd.DataFrame:
    params = params or PARAMS[cfg.symbol]
    y = add_stress_features(x, external, lags, cfg)

    breach = (y.cycle_dd <= -cfg.watch_dd).fillna(False)
    breach_transition = breach & (~breach.shift(1).fillna(False).astype(bool))
    y["maturity_breach_transition"] = breach_transition
    y["maturity_sessions_since_breach"] = _sessions_since_transition(breach_transition)
    y["maturity_recent_breach_63"] = (
        breach_transition.shift(1).rolling(63, min_periods=1).max().fillna(0).astype(bool)
    )
    y["maturity_recent_breach_84"] = (
        breach_transition.shift(1).rolling(84, min_periods=1).max().fillna(0).astype(bool)
    )

    family_columns = [
        "stress_fsi_normalizing",
        "stress_vol_normalizing",
        "stress_funding_normalizing",
    ]
    family_events = []
    for column in family_columns:
        event = y[column].astype(bool) & (~y[column].shift(1).fillna(False).astype(bool))
        y[f"{column}_event"] = event
        family_events.append(event.astype(int))
    any_event = pd.concat(family_events, axis=1).sum(axis=1) > 0
    y["maturity_stress_event"] = any_event
    y["maturity_prior_stress_event_count"] = (
        any_event.shift(1)
        .rolling(params.stress_event_window, min_periods=1)
        .sum()
        .fillna(0)
    )

    y["maturity_ordinary_regime"] = (
        (y.Close >= y.sma200) | (y.sma200_slope >= 0)
    ).fillna(False)
    y["maturity_falling_200dma"] = (
        (y.Close < y.sma200) & (y.sma200_slope < 0)
    ).fillna(False)
    y["maturity_sma200_flattening"] = (
        y.sma200_slope > y.sma200_slope.shift(params.sma200_flattening_lookback)
    ).fillna(False)
    y["maturity_bear_regime"] = (
        y.maturity_falling_200dma
        & (y.cycle_dd <= -params.deep_bear_drawdown)
        & (y.underwater >= params.min_underwater_days)
        & (y.maturity_prior_stress_event_count >= params.min_prior_stress_events)
        & y.maturity_sma200_flattening
        & (y.stress_family_votes >= 2)
        & (~y.credit_veto.astype(bool))
    ).fillna(False)
    y["maturity_regime_gate"] = (
        y.maturity_ordinary_regime | y.maturity_bear_regime
    ).fillna(False)
    return y


def _family_evidence(y: pd.DataFrame, family: str) -> pd.Series:
    if family == "FSI":
        return y.stress_fsi_normalizing
    if family == "VOL":
        return y.stress_vol_normalizing
    if family == "FUNDING":
        return y.stress_funding_normalizing
    if family == "COMPOSITE":
        return y.stress_family_votes >= 2
    raise ValueError(f"Unknown family {family}")


def _signal(y: pd.DataFrame, spec: StressSpec) -> pd.Series:
    recent = y.maturity_recent_breach_84 if spec.recent_breach_window > 63 else y.maturity_recent_breach_63
    common = (
        y.stress_price_quality
        & recent
        & (y.maturity_sessions_since_breach >= 1)
        & (y.maturity_sessions_since_breach <= spec.max_sessions_after_breach)
        & (y.stress_rv_ratio <= spec.max_rv_ratio)
        & (y.cycle_dd <= -spec.min_current_drawdown)
        & y.maturity_regime_gate
    ).fillna(False)
    evidence = _family_evidence(y, spec.family)
    # A falling-200DMA bear candidate always requires two independent families,
    # even when the candidate label names one family for ablation attribution.
    bear_independence = (~y.maturity_bear_regime) | (y.stress_family_votes >= 2)
    return (common & evidence & bear_independence).fillna(False)


def run_mature_stress_candidate(
    x: pd.DataFrame,
    cfg: Config,
    spec: StressSpec,
    external: dict[str, pd.DataFrame],
    lags: dict[str, int],
    params: MaturityParams | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if cfg.symbol != spec.symbol:
        raise ValueError(f"Config/spec mismatch: {cfg.symbol} != {spec.symbol}")
    if not (cfg.min_tranche <= spec.tranche <= cfg.max_tranche):
        raise ValueError("Stress tranche outside configured bounds")
    params = params or PARAMS[cfg.symbol]
    y = add_maturity_features(x, external, lags, cfg, params)
    y["maturity_signal"] = _signal(y, spec)
    y["episode"] = episode_ids(y, cfg)
    catalog = episode_catalog(y, cfg)
    rows: list[dict[str, Any]] = []
    taken: set[int] = set()
    for i in range(200, len(y) - 1):
        row = y.iloc[i]
        eid = int(row.episode)
        if eid == 0 or eid in taken or not bool(row.maturity_signal):
            continue
        nxt = y.iloc[i + 1]
        raw_open = float(nxt.Open)
        execution = raw_open * (1 + cfg.all_in_cost_bps / 10_000)
        rows.append(
            {
                "symbol": cfg.symbol,
                "episode": eid,
                "signal_index": i,
                "execution_index": i + 1,
                "signal_date": row.Date.date(),
                "execution_date": nxt.Date.date(),
                "raw_open": raw_open,
                "execution_price": execution,
                "cost_bps": cfg.all_in_cost_bps,
                "tranche": float(spec.tranche),
                "cumulative": float(spec.tranche),
                "state": 4,
                "reason": spec.family,
                "spec": spec.name,
                "cycle_dd": float(row.cycle_dd),
                "underwater": int(row.underwater),
                "atrp": float(row.atrp),
                "rv20": float(row.rv20),
                "stress_rv_ratio": float(row.stress_rv_ratio),
                "stress_family_votes": int(row.stress_family_votes),
                "fsi_normalizing": bool(row.stress_fsi_normalizing),
                "vol_normalizing": bool(row.stress_vol_normalizing),
                "funding_normalizing": bool(row.stress_funding_normalizing),
                "ordinary_regime": bool(row.maturity_ordinary_regime),
                "mature_bear_regime": bool(row.maturity_bear_regime),
                "prior_stress_event_count": float(row.maturity_prior_stress_event_count),
                "sma200_flattening": bool(row.maturity_sma200_flattening),
                "sessions_since_breach_transition": float(row.maturity_sessions_since_breach),
            }
        )
        taken.add(eid)
    return pd.DataFrame(rows), catalog, y


def spec_dict(spec: StressSpec, params: MaturityParams) -> dict[str, Any]:
    return {"stress": asdict(spec), "maturity": asdict(params)}
