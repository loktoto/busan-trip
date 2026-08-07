#!/usr/bin/env python3
"""Orthogonal indicator candidates for market-bottom research v1.6.

The prior price-only experiments confused sharp bear-market rallies with cycle
bottoms, especially for SOXX.  V1.6 tests independent, reproducible proxy families:

- internal breadth: equal-weight / cap-weight ETF ratio;
- credit risk appetite: HYG / IEF ratio;
- volatility normalisation: VIX or VXN falling after a recent washout;
- relative strength: QQQ/SPY or SOXX/QQQ.

These are public reproducibility proxies, not full point-in-time production
features.  They may identify a feature family worth licensing/building, but cannot
be promoted directly.  Every signal uses completed close t and executes at next
open t+1 with stored costs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

from backtest import Config, episode_catalog, episode_ids


@dataclass(frozen=True)
class OrthogonalSpec:
    name: str
    symbol: str
    family: str
    recent_breach_window: int
    min_support_votes: int
    max_rv_ratio: float
    min_current_drawdown: float
    max_days_after_breach: int
    tranche: float


SPECS: dict[str, tuple[OrthogonalSpec, ...]] = {
    "SPY": (
        OrthogonalSpec("SPY_BREADTH_REVERSAL", "SPY", "BREADTH", 42, 1, 1.05, 0.035, 42, 0.03),
        OrthogonalSpec("SPY_BREADTH_CREDIT", "SPY", "BREADTH_CREDIT", 42, 2, 1.05, 0.035, 42, 0.03),
        OrthogonalSpec("SPY_BREADTH_VOL", "SPY", "BREADTH_VOL", 42, 2, 1.05, 0.035, 42, 0.03),
        OrthogonalSpec("SPY_MULTI_FACTOR", "SPY", "MULTI", 42, 2, 1.05, 0.035, 42, 0.03),
    ),
    "QQQ": (
        OrthogonalSpec("QQQ_BREADTH_REVERSAL", "QQQ", "BREADTH", 50, 1, 1.05, 0.050, 50, 0.04),
        OrthogonalSpec("QQQ_BREADTH_CREDIT", "QQQ", "BREADTH_CREDIT", 50, 2, 1.05, 0.050, 50, 0.04),
        OrthogonalSpec("QQQ_BREADTH_VOL", "QQQ", "BREADTH_VOL", 50, 2, 1.05, 0.050, 50, 0.04),
        OrthogonalSpec("QQQ_MULTI_FACTOR", "QQQ", "MULTI", 50, 3, 1.05, 0.050, 50, 0.04),
    ),
    "SOXX": (
        OrthogonalSpec("SOXX_BREADTH_REVERSAL", "SOXX", "BREADTH", 63, 1, 1.00, 0.090, 63, 0.05),
        OrthogonalSpec("SOXX_BREADTH_CREDIT", "SOXX", "BREADTH_CREDIT", 63, 2, 1.00, 0.090, 63, 0.05),
        OrthogonalSpec("SOXX_BREADTH_VOL", "SOXX", "BREADTH_VOL", 63, 2, 1.00, 0.090, 63, 0.05),
        OrthogonalSpec("SOXX_MULTI_FACTOR", "SOXX", "MULTI", 63, 3, 1.00, 0.090, 63, 0.05),
    ),
}


ASSET_PROXY_MAP = {
    "SPY": {"breadth": "RSP", "benchmark": None, "vol": "VIX", "term": "VIX3M"},
    "QQQ": {"breadth": "QQQE", "benchmark": "SPY", "vol": "VXN", "term": "VIX"},
    "SOXX": {"breadth": "XSD", "benchmark": "QQQ", "vol": "VXN", "term": "VIX"},
}


def _series_frame(series: pd.DataFrame, column: str) -> pd.DataFrame:
    required = {"Date", "Close"}
    if not required.issubset(series.columns):
        raise ValueError(f"Series {column} requires Date,Close")
    out = series[["Date", "Close"]].copy()
    out["Date"] = pd.to_datetime(out["Date"], utc=False).dt.tz_localize(None)
    out[column] = pd.to_numeric(out.pop("Close"), errors="coerce")
    return out.dropna().sort_values("Date").drop_duplicates("Date", keep="last")


def _ratio_features(x: pd.DataFrame, numerator: str, denominator: str, prefix: str) -> None:
    ratio = x[numerator] / x[denominator].replace(0, np.nan)
    x[f"{prefix}_ratio"] = ratio
    x[f"{prefix}_r5"] = ratio.pct_change(5)
    x[f"{prefix}_r10"] = ratio.pct_change(10)
    x[f"{prefix}_sma10"] = ratio.rolling(10).mean()
    x[f"{prefix}_above_sma10"] = ratio > x[f"{prefix}_sma10"]
    x[f"{prefix}_slope10"] = x[f"{prefix}_sma10"] / x[f"{prefix}_sma10"].shift(5) - 1.0


def _sessions_since(event: pd.Series) -> pd.Series:
    result: list[float] = []
    last: int | None = None
    for i, value in enumerate(event.fillna(False).astype(bool)):
        if value:
            last = i
        result.append(np.nan if last is None else float(i - last))
    return pd.Series(result, index=event.index, dtype=float)


def add_orthogonal_features(
    x: pd.DataFrame,
    symbol: str,
    proxies: dict[str, pd.DataFrame],
    cfg: Config,
) -> pd.DataFrame:
    """Merge public proxy histories and create causal support votes."""
    mapping = ASSET_PROXY_MAP[symbol]
    y = x.copy()
    y["Date"] = pd.to_datetime(y["Date"], utc=False).dt.tz_localize(None)

    required = {mapping["breadth"], "HYG", "IEF", mapping["vol"], mapping["term"]}
    if mapping["benchmark"]:
        required.add(mapping["benchmark"])
    missing = sorted(required - set(proxies))
    if missing:
        raise ValueError(f"Missing proxy histories for {symbol}: {missing}")

    for key in sorted(required):
        y = y.merge(_series_frame(proxies[key], f"proxy_{key}"), on="Date", how="left")
    proxy_cols = [c for c in y.columns if c.startswith("proxy_")]
    y[proxy_cols] = y[proxy_cols].ffill()

    y["proxy_asset"] = y.Close
    _ratio_features(y, f"proxy_{mapping['breadth']}", "proxy_asset", "breadth")
    _ratio_features(y, "proxy_HYG", "proxy_IEF", "credit")

    vol = y[f"proxy_{mapping['vol']}"]
    term = y[f"proxy_{mapping['term']}"]
    y["vol_r5"] = vol.pct_change(5)
    y["vol_r10"] = vol.pct_change(10)
    y["vol_sma10"] = vol.rolling(10).mean()
    y["vol_below_sma10"] = vol < y.vol_sma10
    y["vol_term_ratio"] = vol / term.replace(0, np.nan)
    y["vol_term_r5"] = y.vol_term_ratio.pct_change(5)

    if mapping["benchmark"]:
        _ratio_features(y, "proxy_asset", f"proxy_{mapping['benchmark']}", "relative")
        relative_support = (
            (y.relative_r5 > 0)
            & y.relative_above_sma10
            & (y.relative_slope10 > 0)
        ).fillna(False)
    else:
        relative_support = pd.Series(False, index=y.index)

    y["breadth_support"] = (
        (y.breadth_r5 > 0)
        & y.breadth_above_sma10
        & (y.breadth_slope10 > 0)
    ).fillna(False)
    y["credit_support"] = (
        (y.credit_r5 > 0)
        & y.credit_above_sma10
        & (y.credit_slope10 > 0)
    ).fillna(False)
    y["vol_support"] = (
        (y.vol_r5 < 0)
        & y.vol_below_sma10
        & ((y.vol_term_r5 < 0) | (y.vol_term_ratio <= 1.0))
    ).fillna(False)
    y["relative_support"] = relative_support
    y["orthogonal_support_votes"] = y[
        ["breadth_support", "credit_support", "vol_support", "relative_support"]
    ].sum(axis=1)

    breach = y.cycle_dd <= -cfg.watch_dd
    y["orthogonal_breach"] = breach
    y["orthogonal_sessions_since_breach"] = _sessions_since(breach)
    y["orthogonal_recent_breach"] = breach.shift(1).rolling(63, min_periods=1).max().fillna(0).astype(bool)
    low_now = y.Low.rolling(5, min_periods=3).min()
    low_prior = y.Low.shift(5).rolling(5, min_periods=3).min()
    y["orthogonal_higher_low"] = (low_now > low_prior).fillna(False)
    y["orthogonal_rv_ratio"] = y.rv20 / y.rv20.shift(5).replace(0, np.nan)
    y["orthogonal_price_quality"] = (
        (y.Close > y.sma10)
        & (y.sma10_slope > 0)
        & (y.r5 > 0)
        & y.orthogonal_higher_low
        & (~y.newlow20.astype(bool))
        & (~y.credit_veto.astype(bool))
    ).fillna(False)
    return y


def _family_signal(y: pd.DataFrame, spec: OrthogonalSpec) -> pd.Series:
    common = (
        y.orthogonal_price_quality
        & y.orthogonal_recent_breach
        & (y.orthogonal_sessions_since_breach <= spec.max_days_after_breach)
        & (y.orthogonal_rv_ratio <= spec.max_rv_ratio)
        & (y.cycle_dd <= -spec.min_current_drawdown)
    ).fillna(False)
    if spec.family == "BREADTH":
        support = y.breadth_support
    elif spec.family == "BREADTH_CREDIT":
        support = y.breadth_support & y.credit_support
    elif spec.family == "BREADTH_VOL":
        support = y.breadth_support & y.vol_support
    elif spec.family == "MULTI":
        support = y.orthogonal_support_votes >= spec.min_support_votes
    else:
        raise ValueError(f"Unknown family {spec.family}")
    return (common & support).fillna(False)


def run_orthogonal_candidate(
    x: pd.DataFrame,
    cfg: Config,
    spec: OrthogonalSpec,
    proxies: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if cfg.symbol != spec.symbol:
        raise ValueError(f"Config/spec mismatch: {cfg.symbol} != {spec.symbol}")
    if not (cfg.min_tranche <= spec.tranche <= cfg.max_tranche):
        raise ValueError("Tranche outside configured bounds")
    y = add_orthogonal_features(x, cfg.symbol, proxies, cfg)
    y["orthogonal_signal"] = _family_signal(y, spec)
    y["episode"] = episode_ids(y, cfg)
    catalog = episode_catalog(y, cfg)
    rows: list[dict[str, Any]] = []
    taken: set[int] = set()

    for i in range(200, len(y) - 1):
        row = y.iloc[i]
        eid = int(row.episode)
        if eid == 0 or eid in taken or not bool(row.orthogonal_signal):
            continue
        if bool(row.credit_veto):
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
                "atrp": float(row.atrp),
                "rv20": float(row.rv20),
                "orthogonal_rv_ratio": float(row.orthogonal_rv_ratio),
                "support_votes": int(row.orthogonal_support_votes),
                "breadth_support": bool(row.breadth_support),
                "credit_support": bool(row.credit_support),
                "vol_support": bool(row.vol_support),
                "relative_support": bool(row.relative_support),
                "breadth_r5": float(row.breadth_r5),
                "credit_r5": float(row.credit_r5),
                "vol_r5": float(row.vol_r5),
                "vol_term_ratio": float(row.vol_term_ratio),
                "sessions_since_breach": float(row.orthogonal_sessions_since_breach),
            }
        )
        taken.add(eid)
    return pd.DataFrame(rows), catalog, y


def spec_dict(spec: OrthogonalSpec) -> dict[str, Any]:
    return asdict(spec)
