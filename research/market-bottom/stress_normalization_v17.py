#!/usr/bin/env python3
"""Stress-peak normalisation candidates for market-bottom research v1.7.

Price-only confirmation frequently mistakes bear-market rallies for completed
QQQ/SOXX cycle bottoms.  This module tests three independent stress families:

- OFR Financial Stress Index and category contributions;
- options/rates volatility term structure and volatility-of-volatility;
- secured-funding rate dispersion, repo spreads and dealer settlement fails.

Every raw observation is aligned to its first conservative strategy-available
session.  Signals use completed close t and execute next regular-session open t+1.
The public files are current/revised histories rather than immutable vintages, so
this module is research-only and cannot directly promote a production trade.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

from backtest import Config, causal_zscore, episode_catalog, episode_ids


@dataclass(frozen=True)
class StressSpec:
    name: str
    symbol: str
    family: str
    min_current_drawdown: float
    recent_breach_window: int
    max_sessions_after_breach: int
    max_rv_ratio: float
    tranche: float


SPECS: dict[str, tuple[StressSpec, ...]] = {
    "SPY": (
        StressSpec("SPY_FSI_NORMALIZATION", "SPY", "FSI", 0.035, 63, 63, 1.05, 0.03),
        StressSpec("SPY_VOL_NORMALIZATION", "SPY", "VOL", 0.035, 63, 63, 1.05, 0.03),
        StressSpec("SPY_FUNDING_NORMALIZATION", "SPY", "FUNDING", 0.035, 63, 63, 1.05, 0.03),
        StressSpec("SPY_STRESS_COMPOSITE", "SPY", "COMPOSITE", 0.035, 63, 63, 1.05, 0.03),
    ),
    "QQQ": (
        StressSpec("QQQ_FSI_NORMALIZATION", "QQQ", "FSI", 0.050, 63, 63, 1.05, 0.04),
        StressSpec("QQQ_VOL_NORMALIZATION", "QQQ", "VOL", 0.050, 63, 63, 1.05, 0.04),
        StressSpec("QQQ_FUNDING_NORMALIZATION", "QQQ", "FUNDING", 0.050, 63, 63, 1.05, 0.04),
        StressSpec("QQQ_STRESS_COMPOSITE", "QQQ", "COMPOSITE", 0.050, 63, 63, 1.05, 0.04),
    ),
    "SOXX": (
        StressSpec("SOXX_FSI_NORMALIZATION", "SOXX", "FSI", 0.090, 84, 84, 1.00, 0.05),
        StressSpec("SOXX_VOL_NORMALIZATION", "SOXX", "VOL", 0.090, 84, 84, 1.00, 0.05),
        StressSpec("SOXX_FUNDING_NORMALIZATION", "SOXX", "FUNDING", 0.090, 84, 84, 1.00, 0.05),
        StressSpec("SOXX_STRESS_COMPOSITE", "SOXX", "COMPOSITE", 0.090, 84, 84, 1.00, 0.05),
    ),
}


FAMILY_REQUIRED = {
    "FSI": {"fsi"},
    "VOL": {"VIX", "VIX3M", "VIX9D", "VVIX", "VXN", "MOVE"},
    "FUNDING": {
        "SOFR",
        "SOFR_1P",
        "SOFR_99P",
        "BGCR",
        "DVP_RATE",
        "DVP_VOLUME",
        "FAILS_TOTAL",
        "FAILS_CORP",
    },
    "COMPOSITE": {
        "fsi",
        "VIX",
        "VIX3M",
        "VIX9D",
        "VVIX",
        "VXN",
        "MOVE",
        "SOFR",
        "SOFR_1P",
        "SOFR_99P",
        "BGCR",
        "DVP_RATE",
        "DVP_VOLUME",
        "FAILS_TOTAL",
        "FAILS_CORP",
    },
}


def load_value_series(frame: pd.DataFrame, value_column: str | None = None) -> pd.DataFrame:
    """Normalise an external series to Date,Value."""
    if "Date" not in frame:
        raise ValueError("External series requires Date")
    candidates = [value_column] if value_column else ["Value", "Close"]
    column = next((c for c in candidates if c and c in frame), None)
    if column is None:
        raise ValueError(f"No value column found; tried {candidates}")
    out = frame[["Date", column]].copy()
    out["Date"] = pd.to_datetime(out.Date, utc=False).dt.tz_localize(None)
    out["Value"] = pd.to_numeric(out[column], errors="coerce")
    return (
        out[["Date", "Value"]]
        .dropna()
        .sort_values("Date")
        .drop_duplicates("Date", keep="last")
        .reset_index(drop=True)
    )


def align_to_strategy_sessions(
    raw: pd.DataFrame,
    trading_dates: pd.Series,
    lag_sessions: int,
) -> pd.DataFrame:
    """Map each observation to the first conservative strategy-available session."""
    if lag_sessions < 0:
        raise ValueError("lag_sessions cannot be negative")
    dates = pd.DatetimeIndex(pd.to_datetime(trading_dates).dt.tz_localize(None))
    rows: list[tuple[pd.Timestamp, float]] = []
    for row in raw.itertuples(index=False):
        observation = pd.Timestamp(row.Date)
        position = int(dates.searchsorted(observation, side="left"))
        available_position = position + lag_sessions
        if available_position >= len(dates):
            continue
        rows.append((dates[available_position], float(row.Value)))
    if not rows:
        return pd.DataFrame(columns=["Date", "Value"])
    return (
        pd.DataFrame(rows, columns=["Date", "Value"])
        .sort_values("Date")
        .drop_duplicates("Date", keep="last")
        .reset_index(drop=True)
    )


def _merge_aligned(
    y: pd.DataFrame,
    external: dict[str, pd.DataFrame],
    lags: dict[str, int],
) -> pd.DataFrame:
    trading_dates = y.Date
    for name, raw in external.items():
        lag = int(lags.get(name, 0))
        aligned = align_to_strategy_sessions(load_value_series(raw), trading_dates, lag)
        aligned = aligned.rename(columns={"Value": f"stress_raw_{name}"})
        y = y.merge(aligned, on="Date", how="left")
    columns = [c for c in y if c.startswith("stress_raw_")]
    y[columns] = y[columns].ffill()
    return y


def _row_mean_z(y: pd.DataFrame, columns: list[str], window: int = 252, min_periods: int = 60) -> pd.Series:
    z = [causal_zscore(y[c], window, min_periods).rename(c) for c in columns]
    return pd.concat(z, axis=1).mean(axis=1, skipna=True)


def _stress_normalizing(
    stress_z: pd.Series,
    peak_window: int = 20,
    min_peak_z: float = 1.0,
    min_peak_decline: float = 0.50,
) -> pd.Series:
    prior_peak = stress_z.shift(1).rolling(peak_window, min_periods=5).max()
    falling = stress_z < stress_z.shift(5)
    return (
        (prior_peak >= min_peak_z)
        & ((prior_peak - stress_z) >= min_peak_decline)
        & falling
    ).fillna(False)


def _sessions_since(event: pd.Series) -> pd.Series:
    result: list[float] = []
    last: int | None = None
    for i, value in enumerate(event.fillna(False).astype(bool)):
        if value:
            last = i
        result.append(np.nan if last is None else float(i - last))
    return pd.Series(result, index=event.index, dtype=float)


def add_stress_features(
    x: pd.DataFrame,
    external: dict[str, pd.DataFrame],
    lags: dict[str, int],
    cfg: Config,
) -> pd.DataFrame:
    """Build causal stress-family composites and normalisation events."""
    y = _merge_aligned(x.copy(), external, lags)

    # OFR FSI composite.  All components are stress-positive by construction.
    fsi_columns = [
        "stress_raw_FSI_TOTAL",
        "stress_raw_FSI_CREDIT",
        "stress_raw_FSI_FUNDING",
        "stress_raw_FSI_VOL",
        "stress_raw_FSI_US",
    ]
    if all(c in y for c in fsi_columns):
        y["stress_fsi_z"] = _row_mean_z(y, fsi_columns)
        y["stress_fsi_normalizing"] = _stress_normalizing(y.stress_fsi_z)
    else:
        y["stress_fsi_z"] = np.nan
        y["stress_fsi_normalizing"] = False

    # Volatility stack: short/medium term structure, vol-of-vol, tech versus broad
    # volatility and rates volatility.  Higher values represent greater stress.
    vol_required = [
        "stress_raw_VIX",
        "stress_raw_VIX3M",
        "stress_raw_VIX9D",
        "stress_raw_VVIX",
        "stress_raw_VXN",
        "stress_raw_MOVE",
    ]
    if all(c in y for c in vol_required):
        y["stress_vix9d_vix"] = y.stress_raw_VIX9D / y.stress_raw_VIX.replace(0, np.nan)
        y["stress_vix_vix3m"] = y.stress_raw_VIX / y.stress_raw_VIX3M.replace(0, np.nan)
        y["stress_vvix_vix"] = y.stress_raw_VVIX / y.stress_raw_VIX.replace(0, np.nan)
        y["stress_vxn_vix"] = y.stress_raw_VXN / y.stress_raw_VIX.replace(0, np.nan)
        vol_columns = [
            "stress_vix9d_vix",
            "stress_vix_vix3m",
            "stress_vvix_vix",
            "stress_vxn_vix",
            "stress_raw_MOVE",
        ]
        y["stress_vol_z"] = _row_mean_z(y, vol_columns)
        y["stress_vol_normalizing"] = _stress_normalizing(y.stress_vol_z)
        y["stress_vol_curve_normalizing"] = (
            (y.stress_vix9d_vix < y.stress_vix9d_vix.shift(5))
            & (y.stress_vix_vix3m < y.stress_vix_vix3m.shift(5))
            & (y.stress_raw_VIX < y.stress_raw_VIX.shift(5))
        ).fillna(False)
        y["stress_vol_normalizing"] = (
            y.stress_vol_normalizing & y.stress_vol_curve_normalizing
        )
    else:
        y["stress_vol_z"] = np.nan
        y["stress_vol_normalizing"] = False
        y["stress_vol_curve_normalizing"] = False

    # Funding stack: SOFR transaction dispersion, DVP-SOFR rate basis, rate basis
    # versus BGCR, repo-volume shock and settlement fails. Absolute bases are used
    # because either sign can indicate impaired collateral distribution.
    funding_required = [
        "stress_raw_SOFR",
        "stress_raw_SOFR_1P",
        "stress_raw_SOFR_99P",
        "stress_raw_BGCR",
        "stress_raw_DVP_RATE",
        "stress_raw_DVP_VOLUME",
        "stress_raw_FAILS_TOTAL",
        "stress_raw_FAILS_CORP",
    ]
    if all(c in y for c in funding_required):
        y["stress_sofr_dispersion"] = y.stress_raw_SOFR_99P - y.stress_raw_SOFR_1P
        y["stress_dvp_sofr_basis"] = (y.stress_raw_DVP_RATE - y.stress_raw_SOFR).abs()
        y["stress_sofr_bgcr_basis"] = (y.stress_raw_SOFR - y.stress_raw_BGCR).abs()
        y["stress_repo_volume_log"] = np.log(y.stress_raw_DVP_VOLUME.clip(lower=1.0))
        y["stress_fails_total_log"] = np.log(y.stress_raw_FAILS_TOTAL.clip(lower=1.0))
        y["stress_fails_corp_log"] = np.log(y.stress_raw_FAILS_CORP.clip(lower=1.0))
        funding_columns = [
            "stress_sofr_dispersion",
            "stress_dvp_sofr_basis",
            "stress_sofr_bgcr_basis",
            "stress_fails_total_log",
            "stress_fails_corp_log",
        ]
        # Repo volume is evaluated as a deviation from its own trailing mean; both a
        # freeze and a scramble for balance-sheet capacity can be stress events.
        repo_volume_z = causal_zscore(y.stress_repo_volume_log, 252, 60).abs()
        funding_parts = [
            causal_zscore(y[c], 252, 60).rename(c) for c in funding_columns
        ] + [repo_volume_z.rename("stress_repo_volume_abs_z")]
        y["stress_funding_z"] = pd.concat(funding_parts, axis=1).mean(axis=1, skipna=True)
        y["stress_funding_normalizing"] = _stress_normalizing(
            y.stress_funding_z,
            peak_window=20,
            min_peak_z=0.75,
            min_peak_decline=0.35,
        )
    else:
        y["stress_funding_z"] = np.nan
        y["stress_funding_normalizing"] = False

    y["stress_family_votes"] = y[
        [
            "stress_fsi_normalizing",
            "stress_vol_normalizing",
            "stress_funding_normalizing",
        ]
    ].sum(axis=1)
    breach = y.cycle_dd <= -cfg.watch_dd
    y["stress_sessions_since_breach"] = _sessions_since(breach)
    y["stress_recent_breach_63"] = breach.shift(1).rolling(63, min_periods=1).max().fillna(0).astype(bool)
    y["stress_recent_breach_84"] = breach.shift(1).rolling(84, min_periods=1).max().fillna(0).astype(bool)
    low_now = y.Low.rolling(5, min_periods=3).min()
    low_prior = y.Low.shift(5).rolling(5, min_periods=3).min()
    y["stress_higher_low"] = (low_now > low_prior).fillna(False)
    y["stress_rv_ratio"] = y.rv20 / y.rv20.shift(5).replace(0, np.nan)
    y["stress_price_quality"] = (
        (y.Close > y.sma10)
        & (y.sma10_slope > 0)
        & (y.r5 > 0)
        & y.stress_higher_low
        & (~y.newlow20.astype(bool))
        & (~y.credit_veto.astype(bool))
    ).fillna(False)
    return y


def _signal(y: pd.DataFrame, spec: StressSpec) -> pd.Series:
    recent = y.stress_recent_breach_84 if spec.recent_breach_window > 63 else y.stress_recent_breach_63
    common = (
        y.stress_price_quality
        & recent
        & (y.stress_sessions_since_breach <= spec.max_sessions_after_breach)
        & (y.stress_rv_ratio <= spec.max_rv_ratio)
        & (y.cycle_dd <= -spec.min_current_drawdown)
    ).fillna(False)
    if spec.family == "FSI":
        evidence = y.stress_fsi_normalizing
    elif spec.family == "VOL":
        evidence = y.stress_vol_normalizing
    elif spec.family == "FUNDING":
        evidence = y.stress_funding_normalizing
    elif spec.family == "COMPOSITE":
        evidence = y.stress_family_votes >= 2
    else:
        raise ValueError(f"Unknown stress family {spec.family}")
    return (common & evidence).fillna(False)


def run_stress_candidate(
    x: pd.DataFrame,
    cfg: Config,
    spec: StressSpec,
    external: dict[str, pd.DataFrame],
    lags: dict[str, int],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if cfg.symbol != spec.symbol:
        raise ValueError(f"Config/spec mismatch: {cfg.symbol} != {spec.symbol}")
    if not (cfg.min_tranche <= spec.tranche <= cfg.max_tranche):
        raise ValueError("Stress tranche outside configured bounds")
    y = add_stress_features(x, external, lags, cfg)
    y["stress_signal"] = _signal(y, spec)
    y["episode"] = episode_ids(y, cfg)
    catalog = episode_catalog(y, cfg)
    rows: list[dict[str, Any]] = []
    taken: set[int] = set()
    for i in range(200, len(y) - 1):
        row = y.iloc[i]
        eid = int(row.episode)
        if eid == 0 or eid in taken or not bool(row.stress_signal):
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
                "stress_rv_ratio": float(row.stress_rv_ratio),
                "stress_family_votes": int(row.stress_family_votes),
                "fsi_normalizing": bool(row.stress_fsi_normalizing),
                "vol_normalizing": bool(row.stress_vol_normalizing),
                "funding_normalizing": bool(row.stress_funding_normalizing),
                "stress_fsi_z": float(row.stress_fsi_z) if np.isfinite(row.stress_fsi_z) else np.nan,
                "stress_vol_z": float(row.stress_vol_z) if np.isfinite(row.stress_vol_z) else np.nan,
                "stress_funding_z": float(row.stress_funding_z) if np.isfinite(row.stress_funding_z) else np.nan,
                "sessions_since_breach": float(row.stress_sessions_since_breach),
            }
        )
        taken.add(eid)
    return pd.DataFrame(rows), catalog, y


def spec_dict(spec: StressSpec) -> dict[str, Any]:
    return asdict(spec)
