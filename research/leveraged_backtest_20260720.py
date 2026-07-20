from __future__ import annotations

import json
import math
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

END_DATE = "2026-07-21"
START_DATE = "1980-01-01"
OUT = Path("research_outputs/leveraged_backtest_20260720")
OUT.mkdir(parents=True, exist_ok=True)

BASE_COST_BPS = 10.0
STRESS_COST_BPS = 30.0
DEFAULT_DRAG = {2: 0.050, 3: 0.090}
STRESS_DRAG = {2: 0.082, 3: 0.152}


@dataclass(frozen=True)
class ActualProduct:
    ticker: str
    leverage: int
    valid_from: str | None = None


@dataclass(frozen=True)
class AssetSpec:
    ticker: str
    universe: str
    benchmark: str
    actual_products: tuple[ActualProduct, ...]


ASSETS: tuple[AssetSpec, ...] = (
    AssetSpec("SPY", "index", "SPY", (ActualProduct("SSO", 2), ActualProduct("SPXL", 3))),
    AssetSpec("QQQ", "index", "QQQ", (ActualProduct("QLD", 2), ActualProduct("TQQQ", 3))),
    AssetSpec("SOXX", "index", "SOXX", (ActualProduct("USD", 2), ActualProduct("SOXL", 3))),
    AssetSpec("AAPL", "stock", "QQQ", (ActualProduct("AAPU", 2, "2024-04-02"),)),
    AssetSpec("MSFT", "stock", "QQQ", (ActualProduct("MSFU", 2, "2024-04-02"),)),
    AssetSpec("AMZN", "stock", "QQQ", (ActualProduct("AMZU", 2, "2024-04-02"),)),
    AssetSpec("GOOGL", "stock", "QQQ", (ActualProduct("GGLL", 2, "2024-04-02"),)),
    AssetSpec("META", "stock", "QQQ", (ActualProduct("FBL", 2, "2024-04-02"), ActualProduct("METU", 2))),
    AssetSpec("NVDA", "stock", "QQQ", (ActualProduct("NVDL", 2, "2024-01-22"), ActualProduct("NVDU", 2))),
    AssetSpec("TSLA", "stock", "QQQ", (ActualProduct("TSLL", 2, "2024-04-02"),)),
    AssetSpec("AMD", "stock", "QQQ", (ActualProduct("AMDL", 2),)),
    AssetSpec("MU", "stock", "QQQ", (ActualProduct("MUU", 2), ActualProduct("MULL", 2))),
)


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        # yfinance may return (Price, Ticker) or (Ticker, Price).
        lv0 = list(df.columns.get_level_values(0))
        if "Open" in lv0 or "Close" in lv0:
            df.columns = df.columns.get_level_values(0)
        else:
            df.columns = df.columns.get_level_values(-1)
    return df


def download_one(ticker: str) -> pd.DataFrame:
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            df = yf.download(
                ticker,
                start=START_DATE,
                end=END_DATE,
                auto_adjust=True,
                progress=False,
                actions=False,
                threads=False,
                timeout=30,
            )
            df = _flatten_columns(df)
            rename = {str(c).strip().title(): str(c).strip().title() for c in df.columns}
            df = df.rename(columns=rename)
            needed = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
            df = df[needed].copy()
            df.index = pd.to_datetime(df.index).tz_localize(None)
            df = df[~df.index.duplicated(keep="last")].sort_index()
            for col in needed:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df.dropna(subset=["Open", "Close"])
            if len(df) >= 80:
                return df
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        time.sleep(2 ** attempt)
    raise RuntimeError(f"Unable to download {ticker}: {last_error}")


def rsi(series: pd.Series, n: int) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    avg_up = up.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    avg_down = down.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = avg_up / avg_down.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    return out.fillna(100.0).clip(0, 100)


def build_features(df: pd.DataFrame, benchmark_df: pd.DataFrame | None) -> pd.DataFrame:
    x = df.copy()
    c, o, h, l = x["Close"], x["Open"], x.get("High", x["Close"]), x.get("Low", x["Close"])
    for n in (3, 5, 10, 20, 30, 50, 100, 150, 200):
        x[f"sma{n}"] = c.rolling(n).mean()
    for n in (21, 42, 63, 126, 252):
        x[f"r{n}"] = c.pct_change(n)
    x["rsi2"] = rsi(c, 2)
    x["rsi5"] = rsi(c, 5)
    x["rsi14"] = rsi(c, 14)
    prev_c = c.shift(1)
    tr = pd.concat([(h - l).abs(), (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    x["atr14"] = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    x["atr_pct"] = x["atr14"] / c
    daily = c.pct_change()
    x["vol20"] = daily.rolling(20).std() * math.sqrt(252)
    x["vol63"] = daily.rolling(63).std() * math.sqrt(252)
    x["vol_ratio"] = x["vol20"] / x["vol63"].replace(0, np.nan)
    x["volume_ratio"] = x.get("Volume", pd.Series(index=x.index, dtype=float)) / x.get(
        "Volume", pd.Series(index=x.index, dtype=float)
    ).rolling(20).mean()
    x["gap"] = o / c.shift(1) - 1
    x["green"] = c > o
    for n in (10, 20, 50, 63, 126):
        x[f"high{n}"] = c.rolling(n).max().shift(1)
        x[f"low{n}"] = c.rolling(n).min().shift(1)
    x["dd20"] = c / x["high20"] - 1
    x["dd50"] = c / x["high50"] - 1

    if benchmark_df is not None and len(benchmark_df):
        b = benchmark_df["Close"].reindex(x.index).ffill()
        for n in (21, 63, 126):
            x[f"rs{n}"] = c.pct_change(n) - b.pct_change(n)
    else:
        for n in (21, 63, 126):
            x[f"rs{n}"] = np.nan
    return x


def add_strategy(store: list[dict[str, Any]], name: str, family: str, entry: pd.Series, exit_: pd.Series,
                 max_hold: int | None = None) -> None:
    store.append(
        {
            "strategy": name,
            "family": family,
            "entry": entry.fillna(False).astype(bool),
            "exit": exit_.fillna(False).astype(bool),
            "max_hold": max_hold,
        }
    )


def make_strategies(x: pd.DataFrame) -> list[dict[str, Any]]:
    c = x["Close"]
    s: list[dict[str, Any]] = []

    # Fast/slow trend families.
    for fast, slow in ((5, 20), (10, 20), (10, 30), (20, 50), (50, 200)):
        add_strategy(s, f"MA_{fast}_{slow}", "ma_crossover", x[f"sma{fast}"] > x[f"sma{slow}"],
                     x[f"sma{fast}"] < x[f"sma{slow}"])

    # Price-vs-average with explicit hysteresis to reduce whipsaw.
    for ma in (20, 50, 100, 200):
        for hys in (0.00, 0.01, 0.02, 0.03):
            add_strategy(
                s,
                f"PRICE_SMA{ma}_H{int(hys * 100)}",
                "price_hysteresis",
                c > x[f"sma{ma}"] * (1 + hys),
                c < x[f"sma{ma}"] * (1 - hys),
            )

    # Multi-horizon trend score: 3 moving-average and 3 momentum votes.
    score = (
        (c > x["sma50"]).astype(int)
        + (c > x["sma100"]).astype(int)
        + (c > x["sma200"]).astype(int)
        + (x["r42"] > 0).astype(int)
        + (x["r63"] > 0).astype(int)
        + (x["r126"] > 0).astype(int)
    )
    x["trend_score"] = score
    for enter in (4, 5, 6):
        for leave in (1, 2, 3):
            if leave < enter:
                add_strategy(s, f"MHT_E{enter}_X{leave}", "multi_horizon_trend", score >= enter, score <= leave)

    # Pure time-series momentum votes.
    mom_score = sum((x[f"r{n}"] > 0).astype(int) for n in (21, 42, 63, 126))
    for enter in (3, 4):
        for leave in (0, 1, 2):
            if leave < enter:
                add_strategy(s, f"TSMOM_E{enter}_X{leave}", "time_series_momentum", mom_score >= enter,
                             mom_score <= leave)

    # Donchian-style breakouts with slow trend filters and several exits.
    for lookback in (20, 50, 63, 126):
        for filt in (100, 200):
            base_entry = (c > x[f"high{lookback}"]) & (c > x[f"sma{filt}"])
            for exit_ma in (10, 20, 50):
                add_strategy(
                    s,
                    f"BRK{lookback}_F{filt}_XMA{exit_ma}",
                    "breakout",
                    base_entry,
                    c < x[f"sma{exit_ma}"],
                )
            for exit_low in (10, 20):
                add_strategy(
                    s,
                    f"BRK{lookback}_F{filt}_XLOW{exit_low}",
                    "breakout",
                    base_entry,
                    c < x[f"low{exit_low}"],
                )

    # Bull-regime short-term mean reversion / reclaim.
    regime = c > x["sma200"]
    for threshold in (5, 10, 15):
        oversold_recent = x["rsi2"].rolling(5).min() < threshold
        for reclaim in (3, 5, 10):
            cross_up = (c > x[f"sma{reclaim}"]) & (c.shift(1) <= x[f"sma{reclaim}"].shift(1))
            entry = regime & oversold_recent & cross_up
            for exit_rsi in (70, 90):
                for max_hold in (5, 10, 20):
                    add_strategy(
                        s,
                        f"RSI2_{threshold}_REC{reclaim}_XR{exit_rsi}_T{max_hold}",
                        "pullback_reclaim",
                        entry,
                        x["rsi2"] > exit_rsi,
                        max_hold=max_hold,
                    )

    # Drawdown then reclaim, designed to test buy-the-dip rather than assume it works.
    for dd_window in (20, 50):
        for dd_level in (0.05, 0.10, 0.15, 0.20):
            recent_dd = x[f"dd{dd_window}"].rolling(5).min() <= -dd_level
            reclaim = (c > x["sma5"]) & (c.shift(1) <= x["sma5"].shift(1))
            entry = regime & recent_dd & reclaim
            for max_hold in (10, 20, 40):
                add_strategy(
                    s,
                    f"DD{dd_window}_{int(dd_level * 100)}_REC5_T{max_hold}",
                    "drawdown_reclaim",
                    entry,
                    (c < x["sma20"]) | (x["rsi2"] > 90),
                    max_hold=max_hold,
                )

    # Trend conditioned on realized volatility not accelerating excessively.
    for ratio in (0.80, 1.00, 1.25):
        for enter in (4, 5):
            entry = (score >= enter) & (x["vol_ratio"] < ratio)
            exit_ = (score <= 2) | (x["vol_ratio"] > 1.50)
            add_strategy(s, f"MHT_VOL_E{enter}_VR{int(ratio * 100)}", "volatility_managed_trend", entry, exit_)

    # Relative-strength trend, mainly relevant for individual stocks.
    for n in (63, 126):
        for exit_ma in (20, 50):
            entry = (x[f"rs{n}"] > 0) & (c > x["sma200"]) & (x["r21"] > 0)
            exit_ = (x[f"rs{n}"] < 0) | (c < x[f"sma{exit_ma}"])
            add_strategy(s, f"RS{n}_XMA{exit_ma}", "relative_strength", entry, exit_)

    # Gap/volume continuation proxy. This is not a true point-in-time PEAD test.
    for gap in (0.03, 0.05):
        for volume_ratio in (1.5, 2.0):
            entry = (x["gap"] > gap) & x["green"] & (x["volume_ratio"] > volume_ratio) & (c > x["sma50"])
            for exit_ma in (10, 20):
                for max_hold in (5, 10, 20):
                    add_strategy(
                        s,
                        f"GAP{int(gap * 100)}_V{int(volume_ratio * 10)}_XMA{exit_ma}_T{max_hold}",
                        "gap_momentum_proxy",
                        entry,
                        c < x[f"sma{exit_ma}"],
                        max_hold=max_hold,
                    )

    return s


def build_target(entry: pd.Series, exit_: pd.Series, max_hold: int | None) -> pd.Series:
    idx = entry.index
    target = np.zeros(len(idx), dtype=float)
    state = 0.0
    held = 0
    e = entry.to_numpy(dtype=bool)
    z = exit_.to_numpy(dtype=bool)
    for i in range(len(idx)):
        if state == 0.0:
            if e[i]:
                state = 1.0
                held = 0
        else:
            held += 1
            if z[i] or (max_hold is not None and held >= max_hold):
                state = 0.0
                held = 0
        target[i] = state
    return pd.Series(target, index=idx, name="target")


def annualized_cagr(r: pd.Series) -> float:
    r = r.dropna()
    if len(r) < 2:
        return float("nan")
    total = float((1 + r).prod())
    years = max((r.index[-1] - r.index[0]).days / 365.25, len(r) / 252.0)
    if total <= 0 or years <= 0:
        return -1.0
    return total ** (1 / years) - 1


def performance(r: pd.Series, effective_position: pd.Series | None = None) -> dict[str, float]:
    r = r.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    if len(r) < 40:
        return {k: float("nan") for k in ("cagr", "sharpe", "vol", "maxdd", "calmar", "total_return",
                                                     "exposure", "trades", "worst_day")}
    eq = (1 + r).cumprod()
    dd = eq / eq.cummax() - 1
    vol = float(r.std(ddof=0) * math.sqrt(252))
    sharpe = float(r.mean() / r.std(ddof=0) * math.sqrt(252)) if r.std(ddof=0) > 0 else float("nan")
    cagr = annualized_cagr(r)
    maxdd = float(dd.min())
    calmar = float(cagr / abs(maxdd)) if maxdd < 0 and np.isfinite(cagr) else float("nan")
    exposure = float(effective_position.mean()) if effective_position is not None else 1.0
    trades = float((effective_position.diff() > 0).sum()) if effective_position is not None else 1.0
    return {
        "cagr": cagr,
        "sharpe": sharpe,
        "vol": vol,
        "maxdd": maxdd,
        "calmar": calmar,
        "total_return": float(eq.iloc[-1] - 1),
        "exposure": exposure,
        "trades": trades,
        "worst_day": float(r.min()),
    }


def rolling_stats(r: pd.Series, years: int) -> tuple[float, float, int]:
    window = int(252 * years)
    r = r.fillna(0.0)
    vals: list[float] = []
    if len(r) < window:
        return float("nan"), float("nan"), 0
    for end in range(window, len(r) + 1, 21):
        chunk = r.iloc[end - window:end]
        total = float((1 + chunk).prod())
        vals.append(total ** (1 / years) - 1 if total > 0 else -1.0)
    return float(np.median(vals)), float(np.min(vals)), len(vals)


def run_strategy(asset_ret: pd.Series, target: pd.Series, cost_bps: float) -> tuple[pd.Series, pd.Series]:
    idx = asset_ret.index.intersection(target.index)
    ret = asset_ret.reindex(idx).fillna(0.0)
    t = target.reindex(idx).ffill().fillna(0.0)
    # Signal is known at close t; trade at next open; first open-to-open return starts one session later.
    effective = t.shift(2).fillna(0.0)
    trade = t.diff().abs().fillna(t.abs()).shift(1).fillna(0.0)
    out = effective * ret - trade * (cost_bps / 10_000.0)
    return out, effective


def period_metrics(r: pd.Series, pos: pd.Series) -> dict[str, dict[str, float]]:
    valid = r.index
    cut = int(len(valid) * 0.60)
    periods = {
        "full": (0, len(valid)),
        "early": (0, max(cut, 1)),
        "late": (max(cut, 1), len(valid)),
    }
    out: dict[str, dict[str, float]] = {}
    for name, (a, b) in periods.items():
        out[name] = performance(r.iloc[a:b], pos.iloc[a:b])
    med3, worst3, n3 = rolling_stats(r, 3)
    med5, worst5, n5 = rolling_stats(r, 5)
    out["rolling"] = {
        "rolling3_median_cagr": med3,
        "rolling3_worst_cagr": worst3,
        "rolling3_windows": float(n3),
        "rolling5_median_cagr": med5,
        "rolling5_worst_cagr": worst5,
        "rolling5_windows": float(n5),
    }
    return out


def calibrate_drag(underlying: pd.DataFrame, etf: pd.DataFrame, leverage: int, valid_from: str | None) -> float:
    u = underlying["Open"].pct_change()
    e = etf["Open"].pct_change()
    aligned = pd.concat([u.rename("u"), e.rename("e")], axis=1).dropna()
    if valid_from:
        aligned = aligned.loc[pd.Timestamp(valid_from):]
    if len(aligned) < 120:
        return DEFAULT_DRAG[leverage]
    implied = float((leverage * aligned["u"] - aligned["e"]).median() * 252)
    if not np.isfinite(implied):
        return DEFAULT_DRAG[leverage]
    return max(DEFAULT_DRAG[leverage], min(0.25, implied))


def score_rows(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    out["row_score"] = np.nan
    for _, idx in out.groupby(group_cols).groups.items():
        part = out.loc[idx]
        valid = part[
            (part["trades"] >= 5)
            & (part["exposure"] >= 0.03)
            & (part["exposure"] <= 0.97)
            & part["cagr"].notna()
        ]
        if valid.empty:
            continue
        score = (
            0.25 * valid["cagr"].rank(pct=True)
            + 0.25 * valid["sharpe"].rank(pct=True)
            + 0.30 * valid["calmar"].rank(pct=True)
            + 0.20 * valid["maxdd"].rank(pct=True)
        )
        out.loc[valid.index, "row_score"] = score
    return out


def format_pct(v: Any) -> str:
    try:
        if not np.isfinite(float(v)):
            return "—"
        return f"{float(v):.1%}"
    except Exception:  # noqa: BLE001
        return "—"


def markdown_table(df: pd.DataFrame, cols: list[str], n: int = 10) -> str:
    if df.empty:
        return "No qualifying results."
    d = df.head(n)[cols].copy()
    for col in d.columns:
        if col in {"median_cagr", "median_late_cagr", "median_stress_cagr", "worst_maxdd", "actual_median_cagr",
                   "cagr", "maxdd", "stress_cagr", "late_cagr"}:
            d[col] = d[col].map(format_pct)
        elif pd.api.types.is_float_dtype(d[col]):
            d[col] = d[col].map(lambda x: "—" if not np.isfinite(x) else f"{x:.3f}")
    return d.to_markdown(index=False)


def main() -> None:
    all_tickers = {a.ticker for a in ASSETS} | {a.benchmark for a in ASSETS}
    for a in ASSETS:
        all_tickers.update(p.ticker for p in a.actual_products)

    data: dict[str, pd.DataFrame] = {}
    manifest_rows: list[dict[str, Any]] = []
    for ticker in sorted(all_tickers):
        try:
            df = download_one(ticker)
            data[ticker] = df
            manifest_rows.append(
                {
                    "ticker": ticker,
                    "status": "ok",
                    "start": df.index.min().date().isoformat(),
                    "end": df.index.max().date().isoformat(),
                    "rows": len(df),
                }
            )
        except Exception as exc:  # noqa: BLE001
            manifest_rows.append({"ticker": ticker, "status": f"failed: {exc}", "start": "", "end": "", "rows": 0})
    manifest = pd.DataFrame(manifest_rows)
    manifest.to_csv(OUT / "data_manifest.csv", index=False)

    synthetic_rows: list[dict[str, Any]] = []
    actual_rows: list[dict[str, Any]] = []
    target_cache: dict[tuple[str, str], pd.Series] = {}
    strategy_meta: dict[tuple[str, str], str] = {}
    drag_rows: list[dict[str, Any]] = []

    for spec in ASSETS:
        if spec.ticker not in data:
            continue
        underlying = data[spec.ticker]
        benchmark = data.get(spec.benchmark)
        features = build_features(underlying, benchmark)
        strategies = make_strategies(features)

        actual_by_leverage: dict[int, list[tuple[ActualProduct, pd.DataFrame]]] = {}
        for product in spec.actual_products:
            if product.ticker in data:
                actual_by_leverage.setdefault(product.leverage, []).append((product, data[product.ticker]))

        leverages = (2, 3) if spec.universe == "index" else (2,)
        for leverage in leverages:
            calibrated = DEFAULT_DRAG[leverage]
            calibration_product = "default"
            if leverage in actual_by_leverage:
                candidates: list[tuple[float, ActualProduct]] = []
                for product, etf_df in actual_by_leverage[leverage]:
                    drag = calibrate_drag(underlying, etf_df, leverage, product.valid_from)
                    candidates.append((drag, product))
                if candidates:
                    calibrated, selected = max(candidates, key=lambda z: len(data[z[1].ticker]))
                    calibration_product = selected.ticker
            drag_rows.append(
                {
                    "asset": spec.ticker,
                    "universe": spec.universe,
                    "leverage": leverage,
                    "annual_drag_used": calibrated,
                    "calibration_product": calibration_product,
                }
            )

            underlying_open_ret = underlying["Open"].pct_change()
            synth_ret = (leverage * underlying_open_ret - calibrated / 252.0).clip(lower=-0.99)
            stress_ret = (leverage * underlying_open_ret - STRESS_DRAG[leverage] / 252.0).clip(lower=-0.99)

            for st in strategies:
                target = build_target(st["entry"], st["exit"], st["max_hold"])
                target_cache[(spec.ticker, st["strategy"])] = target
                strategy_meta[(spec.ticker, st["strategy"])] = st["family"]
                base_r, pos = run_strategy(synth_ret, target, BASE_COST_BPS)
                stress_r, stress_pos = run_strategy(stress_ret, target, STRESS_COST_BPS)
                pm = period_metrics(base_r, pos)
                stress_full = performance(stress_r, stress_pos)
                full = pm["full"]
                early = pm["early"]
                late = pm["late"]
                rolling = pm["rolling"]
                synthetic_rows.append(
                    {
                        "asset": spec.ticker,
                        "universe": spec.universe,
                        "leverage": leverage,
                        "strategy": st["strategy"],
                        "family": st["family"],
                        **full,
                        "early_cagr": early["cagr"],
                        "early_sharpe": early["sharpe"],
                        "early_maxdd": early["maxdd"],
                        "early_calmar": early["calmar"],
                        "early_trades": early["trades"],
                        "late_cagr": late["cagr"],
                        "late_sharpe": late["sharpe"],
                        "late_maxdd": late["maxdd"],
                        "late_calmar": late["calmar"],
                        "late_trades": late["trades"],
                        "stress_cagr": stress_full["cagr"],
                        "stress_sharpe": stress_full["sharpe"],
                        "stress_maxdd": stress_full["maxdd"],
                        "stress_calmar": stress_full["calmar"],
                        **rolling,
                        "data_start": underlying.index.min().date().isoformat(),
                        "data_end": underlying.index.max().date().isoformat(),
                        "annual_drag": calibrated,
                    }
                )

                for product, etf_df in actual_by_leverage.get(leverage, []):
                    actual = etf_df.copy()
                    if product.valid_from:
                        actual = actual.loc[pd.Timestamp(product.valid_from):]
                    if len(actual) < 120:
                        continue
                    actual_open_ret = actual["Open"].pct_change()
                    act_r, act_pos = run_strategy(actual_open_ret, target, BASE_COST_BPS)
                    act_m = performance(act_r, act_pos)
                    actual_rows.append(
                        {
                            "asset": spec.ticker,
                            "universe": spec.universe,
                            "product": product.ticker,
                            "leverage": leverage,
                            "strategy": st["strategy"],
                            "family": st["family"],
                            **act_m,
                            "data_start": actual.index.min().date().isoformat(),
                            "data_end": actual.index.max().date().isoformat(),
                        }
                    )

    pd.DataFrame(drag_rows).to_csv(OUT / "tracking_drag_calibration.csv", index=False)
    synthetic = pd.DataFrame(synthetic_rows)
    actual = pd.DataFrame(actual_rows)
    synthetic.to_csv(OUT / "synthetic_full_results.csv", index=False)
    actual.to_csv(OUT / "actual_etf_validation.csv", index=False)

    if synthetic.empty:
        raise RuntimeError("No synthetic results were produced")

    synthetic = score_rows(synthetic, ["universe", "leverage", "asset"])
    synthetic.to_csv(OUT / "synthetic_scored_results.csv", index=False)

    # Pooled robust exact-strategy ranking.
    rank_rows: list[pd.DataFrame] = []
    family_rows: list[pd.DataFrame] = []
    for (universe, leverage), part in synthetic.groupby(["universe", "leverage"]):
        valid = part.dropna(subset=["row_score"]).copy()
        if valid.empty:
            continue
        grouped = valid.groupby(["strategy", "family"], as_index=False).agg(
            asset_count=("asset", "nunique"),
            median_asset_score=("row_score", "median"),
            median_cagr=("cagr", "median"),
            median_sharpe=("sharpe", "median"),
            median_calmar=("calmar", "median"),
            median_late_cagr=("late_cagr", "median"),
            median_stress_cagr=("stress_cagr", "median"),
            worst_maxdd=("maxdd", "min"),
            worst_late_cagr=("late_cagr", "min"),
            median_trades=("trades", "median"),
            median_exposure=("exposure", "median"),
        )
        grouped["robust_score"] = (
            0.45 * grouped["median_asset_score"].rank(pct=True)
            + 0.20 * grouped["median_late_cagr"].rank(pct=True)
            + 0.20 * grouped["median_stress_cagr"].rank(pct=True)
            + 0.15 * grouped["worst_maxdd"].rank(pct=True)
        )

        if not actual.empty:
            av = actual[(actual["universe"] == universe) & (actual["leverage"] == leverage)].copy()
            av = av[(av["trades"] >= 2) & av["cagr"].notna()]
            if not av.empty:
                ag = av.groupby("strategy", as_index=False).agg(
                    actual_asset_count=("asset", "nunique"),
                    actual_median_cagr=("cagr", "median"),
                    actual_median_sharpe=("sharpe", "median"),
                    actual_median_calmar=("calmar", "median"),
                    actual_positive_share=("cagr", lambda z: float((z > 0).mean())),
                )
                ag["actual_score"] = (
                    0.35 * ag["actual_median_cagr"].rank(pct=True)
                    + 0.30 * ag["actual_median_sharpe"].rank(pct=True)
                    + 0.25 * ag["actual_median_calmar"].rank(pct=True)
                    + 0.10 * ag["actual_positive_share"]
                )
                grouped = grouped.merge(ag, on="strategy", how="left")
                grouped["final_score"] = np.where(
                    grouped["actual_asset_count"].fillna(0) >= 2,
                    0.80 * grouped["robust_score"] + 0.20 * grouped["actual_score"].fillna(0),
                    grouped["robust_score"],
                )
            else:
                grouped["final_score"] = grouped["robust_score"]
        else:
            grouped["final_score"] = grouped["robust_score"]
        grouped["universe"] = universe
        grouped["leverage"] = leverage
        grouped = grouped.sort_values(["final_score", "median_late_cagr"], ascending=False)
        rank_rows.append(grouped)

        fam = grouped.groupby("family", as_index=False).agg(
            strategy_count=("strategy", "count"),
            best_final_score=("final_score", "max"),
            median_final_score=("final_score", "median"),
            median_cagr=("median_cagr", "median"),
            median_late_cagr=("median_late_cagr", "median"),
            median_stress_cagr=("median_stress_cagr", "median"),
            worst_maxdd=("worst_maxdd", "min"),
        )
        fam["universe"] = universe
        fam["leverage"] = leverage
        fam = fam.sort_values(["best_final_score", "median_final_score"], ascending=False)
        family_rows.append(fam)

    rankings = pd.concat(rank_rows, ignore_index=True) if rank_rows else pd.DataFrame()
    families = pd.concat(family_rows, ignore_index=True) if family_rows else pd.DataFrame()
    rankings.to_csv(OUT / "robust_strategy_ranking.csv", index=False)
    families.to_csv(OUT / "family_ranking.csv", index=False)

    # Pseudo-OOS: select on first 60%, evaluate on last 40%, separately for each asset.
    oos_rows: list[dict[str, Any]] = []
    for (universe, leverage, asset), part in synthetic.groupby(["universe", "leverage", "asset"]):
        candidates = part[(part["early_trades"] >= 3) & part["early_cagr"].notna()].copy()
        if candidates.empty:
            continue
        candidates["early_score"] = (
            0.30 * candidates["early_cagr"].rank(pct=True)
            + 0.25 * candidates["early_sharpe"].rank(pct=True)
            + 0.30 * candidates["early_calmar"].rank(pct=True)
            + 0.15 * candidates["early_maxdd"].rank(pct=True)
        )
        pick = candidates.sort_values("early_score", ascending=False).iloc[0]
        oos_rows.append(
            {
                "universe": universe,
                "leverage": leverage,
                "asset": asset,
                "selected_strategy": pick["strategy"],
                "family": pick["family"],
                "early_cagr": pick["early_cagr"],
                "early_sharpe": pick["early_sharpe"],
                "late_cagr": pick["late_cagr"],
                "late_sharpe": pick["late_sharpe"],
                "late_maxdd": pick["late_maxdd"],
                "late_calmar": pick["late_calmar"],
            }
        )
    oos = pd.DataFrame(oos_rows)
    oos.to_csv(OUT / "pseudo_oos_asset_selection.csv", index=False)

    # Leave-one-asset-out exact-strategy selection.
    loo_rows: list[dict[str, Any]] = []
    for (universe, leverage), part in synthetic.groupby(["universe", "leverage"]):
        assets = sorted(part["asset"].unique())
        for heldout in assets:
            train = part[(part["asset"] != heldout) & part["row_score"].notna()]
            test = part[part["asset"] == heldout]
            if train.empty or test.empty:
                continue
            pick_name = train.groupby("strategy")["row_score"].median().sort_values(ascending=False).index[0]
            row = test[test["strategy"] == pick_name]
            if row.empty:
                continue
            row = row.iloc[0]
            loo_rows.append(
                {
                    "universe": universe,
                    "leverage": leverage,
                    "heldout_asset": heldout,
                    "selected_strategy": pick_name,
                    "family": row["family"],
                    "heldout_cagr": row["cagr"],
                    "heldout_late_cagr": row["late_cagr"],
                    "heldout_sharpe": row["sharpe"],
                    "heldout_maxdd": row["maxdd"],
                    "heldout_calmar": row["calmar"],
                }
            )
    loo = pd.DataFrame(loo_rows)
    loo.to_csv(OUT / "leave_one_asset_out.csv", index=False)

    # Asset-specific best result constrained to the top pooled strategies, reducing per-asset mining.
    asset_best_rows: list[dict[str, Any]] = []
    current_rows: list[dict[str, Any]] = []
    for (universe, leverage), ranking_part in rankings.groupby(["universe", "leverage"]):
        top_pool = set(ranking_part.head(15)["strategy"])
        for asset, asset_part in synthetic[(synthetic["universe"] == universe) & (synthetic["leverage"] == leverage)].groupby("asset"):
            eligible = asset_part[asset_part["strategy"].isin(top_pool) & asset_part["row_score"].notna()]
            if eligible.empty:
                continue
            best = eligible.sort_values(["row_score", "late_cagr", "stress_cagr"], ascending=False).iloc[0]
            asset_best_rows.append(
                {
                    "universe": universe,
                    "leverage": leverage,
                    "asset": asset,
                    "strategy": best["strategy"],
                    "family": best["family"],
                    "cagr": best["cagr"],
                    "late_cagr": best["late_cagr"],
                    "stress_cagr": best["stress_cagr"],
                    "sharpe": best["sharpe"],
                    "maxdd": best["maxdd"],
                    "calmar": best["calmar"],
                    "trades": best["trades"],
                    "exposure": best["exposure"],
                }
            )
            target = target_cache[(asset, best["strategy"])]
            changes = target.diff().fillna(target)
            last_entry = changes[changes > 0].index.max() if (changes > 0).any() else pd.NaT
            last_exit = changes[changes < 0].index.max() if (changes < 0).any() else pd.NaT
            current_rows.append(
                {
                    "asset": asset,
                    "universe": universe,
                    "leverage": leverage,
                    "strategy": best["strategy"],
                    "family": best["family"],
                    "signal_date": target.index.max().date().isoformat(),
                    "target_position": int(target.iloc[-1]),
                    "last_entry_signal": "" if pd.isna(last_entry) else last_entry.date().isoformat(),
                    "last_exit_signal": "" if pd.isna(last_exit) else last_exit.date().isoformat(),
                }
            )
    asset_best = pd.DataFrame(asset_best_rows)
    current = pd.DataFrame(current_rows)
    asset_best.to_csv(OUT / "asset_best_constrained.csv", index=False)
    current.to_csv(OUT / "current_signals.csv", index=False)

    # Main report.
    report: list[str] = []
    report.append("# Leveraged ETF Entry/Exit Backtest — Full Rebuild")
    report.append("")
    report.append(f"Generated with data through {manifest.loc[manifest.status.eq('ok'), 'end'].max() if not manifest.empty else END_DATE}.")
    report.append("")
    report.append("## Method")
    report.append("")
    report.append("- Longest available adjusted daily history from Yahoo Finance; failed tickers are disclosed in `data_manifest.csv`.")
    report.append("- Signals use the unleveraged underlying. Trades are delayed to the next open; open-to-open returns are used.")
    report.append("- Long-history synthetic 2x/3x returns include conservative annual drag calibrated against actual ETFs where possible, never below 5% for 2x or 9% for 3x.")
    report.append("- Base transaction cost: 10 bps per side. Stress: 30 bps plus 8.2%/15.2% annual drag for 2x/3x.")
    report.append("- Strategy selection is evaluated with first-60%/last-40% pseudo-OOS, rolling 3Y/5Y windows, actual ETF validation and leave-one-asset-out tests.")
    report.append("- Gap/volume rules are price-event proxies, not true point-in-time earnings-surprise backtests.")
    report.append("")

    cols = ["strategy", "family", "final_score", "asset_count", "median_cagr", "median_late_cagr",
            "median_stress_cagr", "worst_maxdd", "median_sharpe", "median_trades"]
    for universe, leverage, title in (("index", 2, "Index universe — 2x"), ("index", 3, "Index universe — 3x"),
                                      ("stock", 2, "Single-stock universe — 2x")):
        rp = rankings[(rankings["universe"] == universe) & (rankings["leverage"] == leverage)] if not rankings.empty else pd.DataFrame()
        report.append(f"## {title}: top robust exact strategies")
        report.append("")
        report.append(markdown_table(rp, [c for c in cols if c in rp.columns], 12))
        report.append("")
        fp = families[(families["universe"] == universe) & (families["leverage"] == leverage)] if not families.empty else pd.DataFrame()
        report.append(f"### {title}: family ranking")
        report.append("")
        report.append(markdown_table(fp, [c for c in ["family", "best_final_score", "median_final_score", "median_cagr",
                                                       "median_late_cagr", "median_stress_cagr", "worst_maxdd"] if c in fp.columns], 12))
        report.append("")

    report.append("## SPY / QQQ / SOXX — best strategy constrained to pooled top 15")
    report.append("")
    idx_best = asset_best[asset_best["asset"].isin(["SPY", "QQQ", "SOXX"])] if not asset_best.empty else pd.DataFrame()
    report.append(markdown_table(idx_best, [c for c in ["asset", "leverage", "strategy", "family", "cagr", "late_cagr",
                                                               "stress_cagr", "sharpe", "maxdd", "calmar", "trades", "exposure"] if c in idx_best.columns], 20))
    report.append("")

    report.append("## Pseudo-OOS: strategy selected on first 60%, tested on final 40%")
    report.append("")
    report.append(markdown_table(oos, [c for c in ["universe", "leverage", "asset", "selected_strategy", "family",
                                                   "early_cagr", "late_cagr", "late_sharpe", "late_maxdd", "late_calmar"] if c in oos.columns], 30))
    report.append("")

    report.append("## Leave-one-asset-out")
    report.append("")
    report.append(markdown_table(loo, [c for c in ["universe", "leverage", "heldout_asset", "selected_strategy", "family",
                                                   "heldout_cagr", "heldout_late_cagr", "heldout_sharpe", "heldout_maxdd",
                                                   "heldout_calmar"] if c in loo.columns], 30))
    report.append("")

    report.append("## Current signals for constrained winners")
    report.append("")
    report.append(current.to_markdown(index=False) if not current.empty else "No signal table produced.")
    report.append("")

    failed = manifest[manifest["status"] != "ok"]
    report.append("## Data failures / exclusions")
    report.append("")
    report.append(failed.to_markdown(index=False) if not failed.empty else "None.")
    report.append("")
    report.append("## Interpretation guardrails")
    report.append("")
    report.append("- A high in-sample CAGR is not enough. Prefer strategies that remain near the top across assets, later samples, stress costs and actual ETF prices.")
    report.append("- Single-stock leveraged ETFs have short actual histories and some changed target leverage; synthetic history is therefore the primary long-cycle test and actual products are validation only.")
    report.append("- SOXX-to-SOXL/USD validation contains index-methodology and tracking differences; treat it as semiconductor-sector validation, not a perfect same-index replication.")
    report.append("- No strategy should be deployed at full size without paper trading and live fill/slippage validation.")

    (OUT / "research_report.md").write_text("\n".join(report), encoding="utf-8")
    (OUT / "run_metadata.json").write_text(
        json.dumps(
            {
                "end_date_requested": END_DATE,
                "base_cost_bps": BASE_COST_BPS,
                "stress_cost_bps": STRESS_COST_BPS,
                "assets": [a.ticker for a in ASSETS],
                "strategy_count_per_asset": int(synthetic["strategy"].nunique()),
                "synthetic_rows": int(len(synthetic)),
                "actual_rows": int(len(actual)),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print((OUT / "research_report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
