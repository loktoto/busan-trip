#!/usr/bin/env python3
"""Cross-sectional sector/internal bottom indicators v1.9.

This research asks whether breadth and dispersion *inside* the relevant market
improve before a cap-weighted ETF's final trough.  It is more granular than an
equal-weight ETF ratio but uses fixed current-survivor panels, so it is explicitly
survivorship-biased and can never be promoted directly.

Signals use completed close t and execute next regular-session open t+1.  Ordinary
corrections require both price above the 200DMA and a non-negative 200DMA slope.
Ambiguous transition regimes are blocked.  Falling-200DMA bear regimes require a
deep drawdown, >=90 sessions underwater, a flattening 200DMA decline and at least
two independent internal-repair families.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

from backtest import Config, causal_zscore, episode_catalog, episode_ids


PANELS: dict[str, tuple[str, ...]] = {
    "SPY": ("XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"),
    "QQQ": ("AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "AVGO", "COST", "NFLX", "TSLA", "AMD", "QCOM"),
    "SOXX": ("AMD", "INTC", "NVDA", "TXN", "QCOM", "AMAT", "LRCX", "KLAC", "MU", "ADI", "MCHP", "MRVL", "ON"),
}


@dataclass(frozen=True)
class InternalSpec:
    name: str
    symbol: str
    family: str
    min_current_drawdown: float
    max_sessions_after_breach: int
    max_rv_ratio: float
    tranche: float


SPECS: dict[str, tuple[InternalSpec, ...]] = {
    "SPY": (
        InternalSpec("SPY_INTERNAL_BREADTH_THRUST", "SPY", "BREADTH_THRUST", 0.035, 63, 1.05, 0.03),
        InternalSpec("SPY_INTERNAL_DISPERSION", "SPY", "DISPERSION", 0.035, 63, 1.05, 0.03),
        InternalSpec("SPY_INTERNAL_DIVERGENCE", "SPY", "DIVERGENCE", 0.035, 63, 1.05, 0.03),
        InternalSpec("SPY_INTERNAL_MULTI", "SPY", "MULTI", 0.035, 63, 1.05, 0.03),
    ),
    "QQQ": (
        InternalSpec("QQQ_INTERNAL_BREADTH_THRUST", "QQQ", "BREADTH_THRUST", 0.050, 63, 1.05, 0.04),
        InternalSpec("QQQ_INTERNAL_DISPERSION", "QQQ", "DISPERSION", 0.050, 63, 1.05, 0.04),
        InternalSpec("QQQ_INTERNAL_DIVERGENCE", "QQQ", "DIVERGENCE", 0.050, 63, 1.05, 0.04),
        InternalSpec("QQQ_INTERNAL_MULTI", "QQQ", "MULTI", 0.050, 63, 1.05, 0.04),
    ),
    "SOXX": (
        InternalSpec("SOXX_INTERNAL_BREADTH_THRUST", "SOXX", "BREADTH_THRUST", 0.090, 84, 1.00, 0.05),
        InternalSpec("SOXX_INTERNAL_DISPERSION", "SOXX", "DISPERSION", 0.090, 84, 1.00, 0.05),
        InternalSpec("SOXX_INTERNAL_DIVERGENCE", "SOXX", "DIVERGENCE", 0.090, 84, 1.00, 0.05),
        InternalSpec("SOXX_INTERNAL_MULTI", "SOXX", "MULTI", 0.090, 84, 1.00, 0.05),
    ),
}


DEEP_BEAR_DD = {"SPY": 0.15, "QQQ": 0.20, "SOXX": 0.30}


def _normalise_member(frame: pd.DataFrame, member: str) -> pd.DataFrame:
    if not {"Date", "Close"}.issubset(frame.columns):
        raise ValueError(f"{member} requires Date,Close")
    out = frame[["Date", "Close"]].copy()
    out["Date"] = pd.to_datetime(out.Date, utc=False).dt.tz_localize(None)
    out["Close"] = pd.to_numeric(out.Close, errors="coerce")
    out = out.dropna().sort_values("Date").drop_duplicates("Date", keep="last")
    close = out.Close
    out[f"{member}_above20"] = close > close.rolling(20).mean()
    out[f"{member}_above50"] = close > close.rolling(50).mean()
    out[f"{member}_r5"] = close.pct_change(5)
    out[f"{member}_positive5"] = out[f"{member}_r5"] > 0
    out[f"{member}_newlow20"] = close <= close.shift(1).rolling(20).min()
    return out.drop(columns="Close")


def _sessions_since_transition(event: pd.Series) -> pd.Series:
    result: list[float] = []
    last: int | None = None
    for i, value in enumerate(event.fillna(False).astype(bool)):
        if value:
            last = i
        result.append(np.nan if last is None else float(i - last))
    return pd.Series(result, index=event.index, dtype=float)


def add_internal_features(
    x: pd.DataFrame,
    symbol: str,
    members: dict[str, pd.DataFrame],
    cfg: Config,
) -> pd.DataFrame:
    expected = set(PANELS[symbol])
    missing = sorted(expected - set(members))
    if missing:
        raise ValueError(f"Missing {symbol} panel members: {missing}")
    y = x.copy()
    y["Date"] = pd.to_datetime(y.Date, utc=False).dt.tz_localize(None)
    for member in PANELS[symbol]:
        y = y.merge(_normalise_member(members[member], member), on="Date", how="left")
    panel_columns = [c for c in y if any(c.startswith(f"{m}_") for m in PANELS[symbol])]
    y[panel_columns] = y[panel_columns].ffill()

    above20 = [f"{m}_above20" for m in PANELS[symbol]]
    above50 = [f"{m}_above50" for m in PANELS[symbol]]
    positive5 = [f"{m}_positive5" for m in PANELS[symbol]]
    newlow20 = [f"{m}_newlow20" for m in PANELS[symbol]]
    returns5 = [f"{m}_r5" for m in PANELS[symbol]]
    y["internal_pct_above20"] = y[above20].astype(float).mean(axis=1)
    y["internal_pct_above50"] = y[above50].astype(float).mean(axis=1)
    y["internal_pct_positive5"] = y[positive5].astype(float).mean(axis=1)
    y["internal_pct_newlow20"] = y[newlow20].astype(float).mean(axis=1)
    y["internal_median_r5"] = y[returns5].median(axis=1, skipna=True)
    y["internal_dispersion_r5"] = y[returns5].std(axis=1, ddof=0, skipna=True)
    y["internal_dispersion_z"] = causal_zscore(y.internal_dispersion_r5, 252, 60)
    y["internal_breadth_score"] = (
        y.internal_pct_above20
        + y.internal_pct_above50
        + y.internal_pct_positive5
        + (1.0 - y.internal_pct_newlow20)
    ) / 4.0

    prior_breadth_min = y.internal_breadth_score.shift(1).rolling(20, min_periods=5).min()
    prior_dispersion_max = y.internal_dispersion_z.shift(1).rolling(20, min_periods=5).max()
    y["internal_breadth_thrust"] = (
        (prior_breadth_min <= 0.35)
        & (y.internal_breadth_score >= 0.55)
        & ((y.internal_breadth_score - y.internal_breadth_score.shift(10)) >= 0.20)
        & (y.internal_pct_above20 >= 0.50)
    ).fillna(False)
    y["internal_dispersion_normalizing"] = (
        (prior_dispersion_max >= 1.25)
        & ((prior_dispersion_max - y.internal_dispersion_z) >= 0.50)
        & (y.internal_median_r5 > 0)
        & (y.internal_pct_positive5 >= 0.55)
    ).fillna(False)

    prior_price_low = y.Close.shift(1).rolling(20).min()
    near_low = y.Close <= prior_price_low * 1.03
    y["internal_positive_divergence"] = (
        near_low
        & (y.internal_breadth_score > prior_breadth_min + 0.12)
        & (y.internal_pct_newlow20 < y.internal_pct_newlow20.shift(5))
        & (y.internal_median_r5 > y.internal_median_r5.shift(5))
    ).fillna(False)
    y["internal_family_votes"] = y[
        ["internal_breadth_thrust", "internal_dispersion_normalizing", "internal_positive_divergence"]
    ].sum(axis=1)

    breach = (y.cycle_dd <= -cfg.watch_dd).fillna(False)
    transition = breach & (~breach.shift(1).fillna(False).astype(bool))
    y["internal_breach_transition"] = transition
    y["internal_sessions_since_breach"] = _sessions_since_transition(transition)
    y["internal_recent_breach_63"] = transition.shift(1).rolling(63, min_periods=1).max().fillna(0).astype(bool)
    y["internal_recent_breach_84"] = transition.shift(1).rolling(84, min_periods=1).max().fillna(0).astype(bool)
    low_now = y.Low.rolling(5, min_periods=3).min()
    low_prior = y.Low.shift(5).rolling(5, min_periods=3).min()
    y["internal_higher_low"] = (low_now > low_prior).fillna(False)
    y["internal_rv_ratio"] = y.rv20 / y.rv20.shift(5).replace(0, np.nan)
    y["internal_price_quality"] = (
        (y.Close > y.sma10)
        & (y.sma10_slope > 0)
        & (y.r5 > 0)
        & y.internal_higher_low
        & (~y.newlow20.astype(bool))
        & (~y.credit_veto.astype(bool))
    ).fillna(False)

    y["internal_ordinary_regime"] = (
        (y.Close >= y.sma200)
        & (y.sma200_slope >= 0)
        & (y.underwater < 60)
    ).fillna(False)
    y["internal_sma200_flattening"] = (y.sma200_slope > y.sma200_slope.shift(20)).fillna(False)
    y["internal_mature_bear_regime"] = (
        (y.Close < y.sma200)
        & (y.sma200_slope < 0)
        & (y.cycle_dd <= -DEEP_BEAR_DD[symbol])
        & (y.underwater >= 90)
        & y.internal_sma200_flattening
        & (y.internal_family_votes >= 2)
        & (~y.credit_veto.astype(bool))
    ).fillna(False)
    y["internal_regime_gate"] = (
        y.internal_ordinary_regime | y.internal_mature_bear_regime
    ).fillna(False)
    return y


def _evidence(y: pd.DataFrame, family: str) -> pd.Series:
    if family == "BREADTH_THRUST":
        return y.internal_breadth_thrust
    if family == "DISPERSION":
        return y.internal_dispersion_normalizing
    if family == "DIVERGENCE":
        return y.internal_positive_divergence
    if family == "MULTI":
        return y.internal_family_votes >= 2
    raise ValueError(f"Unknown family {family}")


def _signal(y: pd.DataFrame, spec: InternalSpec) -> pd.Series:
    recent = y.internal_recent_breach_84 if spec.max_sessions_after_breach > 63 else y.internal_recent_breach_63
    common = (
        y.internal_price_quality
        & recent
        & (y.internal_sessions_since_breach >= 1)
        & (y.internal_sessions_since_breach <= spec.max_sessions_after_breach)
        & (y.internal_rv_ratio <= spec.max_rv_ratio)
        & (y.cycle_dd <= -spec.min_current_drawdown)
        & y.internal_regime_gate
    ).fillna(False)
    return (common & _evidence(y, spec.family)).fillna(False)


def run_internal_candidate(
    x: pd.DataFrame,
    cfg: Config,
    spec: InternalSpec,
    members: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if cfg.symbol != spec.symbol:
        raise ValueError(f"Config/spec mismatch: {cfg.symbol} != {spec.symbol}")
    if not (cfg.min_tranche <= spec.tranche <= cfg.max_tranche):
        raise ValueError("Internal tranche outside configured bounds")
    y = add_internal_features(x, cfg.symbol, members, cfg)
    y["internal_signal"] = _signal(y, spec)
    y["episode"] = episode_ids(y, cfg)
    catalog = episode_catalog(y, cfg)
    rows: list[dict[str, Any]] = []
    taken: set[int] = set()
    for i in range(200, len(y) - 1):
        row = y.iloc[i]
        eid = int(row.episode)
        if eid == 0 or eid in taken or not bool(row.internal_signal):
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
                "internal_rv_ratio": float(row.internal_rv_ratio),
                "internal_family_votes": int(row.internal_family_votes),
                "pct_above20": float(row.internal_pct_above20),
                "pct_above50": float(row.internal_pct_above50),
                "pct_positive5": float(row.internal_pct_positive5),
                "pct_newlow20": float(row.internal_pct_newlow20),
                "breadth_score": float(row.internal_breadth_score),
                "dispersion_z": float(row.internal_dispersion_z) if np.isfinite(row.internal_dispersion_z) else np.nan,
                "breadth_thrust": bool(row.internal_breadth_thrust),
                "dispersion_normalizing": bool(row.internal_dispersion_normalizing),
                "positive_divergence": bool(row.internal_positive_divergence),
                "ordinary_regime": bool(row.internal_ordinary_regime),
                "mature_bear_regime": bool(row.internal_mature_bear_regime),
                "sessions_since_breach_transition": float(row.internal_sessions_since_breach),
            }
        )
        taken.add(eid)
    return pd.DataFrame(rows), catalog, y


def spec_dict(spec: InternalSpec) -> dict[str, Any]:
    return asdict(spec)
