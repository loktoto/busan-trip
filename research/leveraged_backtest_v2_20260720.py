from __future__ import annotations

import json
import math
import time
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

from research.leveraged_backtest_20260720 import (
    ASSETS,
    ActualProduct,
    AssetSpec,
    build_features,
    build_target,
    make_strategies,
    performance,
    rsi,
)

warnings.filterwarnings("ignore")

END_DATE = "2026-07-20"  # exclusive; completed data through 2026-07-17
OUT = Path("research_outputs/leveraged_backtest_v2_20260720")
OUT.mkdir(parents=True, exist_ok=True)

BASE_COST_BPS = 10.0
STRESS_COST_BPS = 30.0
DEFAULT_DRAG = {2: 0.050, 3: 0.090}
STRESS_DRAG = {2: 0.082, 3: 0.152}
INDEX_PROXIES = {"SPY": "^GSPC", "QQQ": "^NDX", "SOXX": "^SOX"}


def flatten(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        lv0 = list(df.columns.get_level_values(0))
        df.columns = df.columns.get_level_values(0 if "Close" in lv0 else -1)
    return df


def download(ticker: str, start: str = "1900-01-01") -> pd.DataFrame:
    err: Exception | None = None
    for n in range(4):
        try:
            x = yf.download(
                ticker,
                start=start,
                end=END_DATE,
                auto_adjust=True,
                progress=False,
                actions=False,
                threads=False,
                timeout=30,
            )
            x = flatten(x)
            x.columns = [str(c).title() for c in x.columns]
            keep = [c for c in ("Open", "High", "Low", "Close", "Volume") if c in x.columns]
            x = x[keep].copy()
            x.index = pd.to_datetime(x.index).tz_localize(None)
            x = x[~x.index.duplicated(keep="last")].sort_index()
            for c in keep:
                x[c] = pd.to_numeric(x[c], errors="coerce")
            x = x.dropna(subset=["Close"])
            if len(x) >= 80:
                if "Open" not in x:
                    x["Open"] = x["Close"]
                if "High" not in x:
                    x["High"] = x["Close"]
                if "Low" not in x:
                    x["Low"] = x["Close"]
                if "Volume" not in x:
                    x["Volume"] = np.nan
                return x
        except Exception as exc:  # noqa: BLE001
            err = exc
        time.sleep(2 ** n)
    raise RuntimeError(f"download failed for {ticker}: {err}")


def cagr(r: pd.Series) -> float:
    r = r.dropna()
    if len(r) < 2:
        return float("nan")
    total = float((1 + r).prod())
    years = max((r.index[-1] - r.index[0]).days / 365.25, len(r) / 252)
    return total ** (1 / years) - 1 if total > 0 and years > 0 else -1.0


def rolling_cagr(r: pd.Series, years: int) -> tuple[float, float, float, int]:
    n = 252 * years
    if len(r) < n:
        return float("nan"), float("nan"), float("nan"), 0
    vals = []
    for end in range(n, len(r) + 1, 21):
        z = r.iloc[end - n:end]
        total = float((1 + z).prod())
        vals.append(total ** (1 / years) - 1 if total > 0 else -1.0)
    a = np.asarray(vals, dtype=float)
    return float(np.median(a)), float(np.min(a)), float((a > 0).mean()), len(a)


def metric_pack(r: pd.Series, w: pd.Series) -> dict[str, float]:
    m = performance(r, w)
    med3, worst3, pos3, n3 = rolling_cagr(r.fillna(0), 3)
    med5, worst5, pos5, n5 = rolling_cagr(r.fillna(0), 5)
    m.update(
        {
            "rolling3_median_cagr": med3,
            "rolling3_worst_cagr": worst3,
            "rolling3_positive_share": pos3,
            "rolling3_windows": n3,
            "rolling5_median_cagr": med5,
            "rolling5_worst_cagr": worst5,
            "rolling5_positive_share": pos5,
            "rolling5_windows": n5,
        }
    )
    return m


def split_metrics(r: pd.Series, w: pd.Series) -> dict[str, float]:
    k = int(len(r) * 0.60)
    early = performance(r.iloc[:k], w.iloc[:k])
    late = performance(r.iloc[k:], w.iloc[k:])
    return {
        "early_cagr": early["cagr"],
        "early_sharpe": early["sharpe"],
        "early_maxdd": early["maxdd"],
        "late_cagr": late["cagr"],
        "late_sharpe": late["sharpe"],
        "late_maxdd": late["maxdd"],
        "late_calmar": late["calmar"],
    }


def apply_locked_stop(base: pd.Series, feat: pd.DataFrame, stop_name: str) -> pd.Series:
    if stop_name == "none":
        return base.copy()
    close = feat["Close"].reindex(base.index)
    atr = feat["atr14"].reindex(base.index)
    out = np.zeros(len(base), dtype=float)
    state = False
    locked = False
    peak = float("nan")
    b = base.to_numpy(dtype=float)
    c = close.to_numpy(dtype=float)
    a = atr.to_numpy(dtype=float)
    for i in range(len(base)):
        if b[i] <= 0:
            state = False
            locked = False
            peak = float("nan")
        elif not state and not locked:
            state = True
            peak = c[i]
        elif state:
            peak = max(peak, c[i]) if np.isfinite(peak) else c[i]
            stop = False
            if stop_name.startswith("trail"):
                pct = float(stop_name.replace("trail", "")) / 100.0
                stop = c[i] < peak * (1 - pct)
            elif stop_name.startswith("atr"):
                multiple = float(stop_name.replace("atr", ""))
                stop = np.isfinite(a[i]) and c[i] < peak - multiple * a[i]
            elif stop_name == "sma200":
                stop = c[i] < float(feat["sma200"].iloc[i])
            if stop:
                state = False
                locked = True
        out[i] = 1.0 if state else 0.0
    return pd.Series(out, index=base.index)


def lagged_weight(target_weight: pd.Series) -> tuple[pd.Series, pd.Series]:
    effective = target_weight.shift(2).fillna(0.0)
    traded = target_weight.diff().abs().fillna(target_weight.abs()).shift(1).fillna(0.0)
    return effective, traded


def risk_weight(scheme: str, target: pd.Series, feat: pd.DataFrame, leverage: int) -> pd.Series:
    if scheme == "full":
        raw = target
    elif scheme == "half":
        raw = 0.50 * target
    elif scheme == "quarter":
        raw = 0.25 * target
    elif scheme.startswith("vol"):
        tv = float(scheme.replace("vol", "")) / 100.0
        rv = feat["vol20"].reindex(target.index)
        raw = target * (tv / (leverage * rv.replace(0, np.nan))).clip(0.0, 1.0).fillna(0.0)
        # Weekly rebalance approximation; avoids pretending costless daily resizing.
        raw = raw.where(np.arange(len(raw)) % 5 == 0).ffill().fillna(0.0)
    else:
        raise ValueError(scheme)
    return raw.clip(0.0, 1.0)


def run_cash_tactical(
    leveraged_ret: pd.Series,
    target: pd.Series,
    feat: pd.DataFrame,
    leverage: int,
    scheme: str,
    cost_bps: float,
) -> tuple[pd.Series, pd.Series]:
    idx = leveraged_ret.index.intersection(target.index)
    tw = risk_weight(scheme, target.reindex(idx).fillna(0.0), feat.reindex(idx), leverage)
    ew, traded = lagged_weight(tw)
    r = ew * leveraged_ret.reindex(idx).fillna(0.0) - traded * cost_bps / 10_000.0
    return r, ew


def run_switch_1x_2x(
    underlying_ret: pd.Series,
    leveraged_ret: pd.Series,
    target: pd.Series,
    cost_bps: float,
) -> tuple[pd.Series, pd.Series]:
    idx = underlying_ret.index.intersection(leveraged_ret.index).intersection(target.index)
    t = target.reindex(idx).fillna(0.0)
    high = t.shift(2).fillna(0.0)
    switch = t.diff().abs().fillna(0.0).shift(1).fillna(0.0)
    u = underlying_ret.reindex(idx).fillna(0.0)
    l = leveraged_ret.reindex(idx).fillna(0.0)
    r = (1 - high) * u + high * l - switch * (2 * cost_bps / 10_000.0)
    exposure = 1.0 + high
    return r, exposure


def actual_product_returns(product: ActualProduct, data: dict[str, pd.DataFrame]) -> pd.Series | None:
    if product.ticker not in data:
        return None
    x = data[product.ticker]
    if product.valid_from:
        x = x.loc[pd.Timestamp(product.valid_from):]
    if len(x) < 120:
        return None
    return x["Close"].pct_change()


def benchmark_rows(
    asset: str,
    universe: str,
    leverage: int,
    history_type: str,
    under_ret: pd.Series,
    lev_ret: pd.Series,
) -> list[dict[str, Any]]:
    rows = []
    one = pd.Series(1.0, index=under_ret.index)
    for name, r, w in (
        ("Underlying_BuyHold", under_ret, one),
        (f"Synthetic_{leverage}x_BuyHold", lev_ret, one),
        (f"Synthetic_{leverage}x_50pct", 0.5 * lev_ret, pd.Series(0.5, index=lev_ret.index)),
        (f"Synthetic_{leverage}x_25pct", 0.25 * lev_ret, pd.Series(0.25, index=lev_ret.index)),
    ):
        idx = r.dropna().index
        rr, ww = r.reindex(idx).fillna(0), w.reindex(idx).fillna(0)
        rows.append(
            {
                "asset": asset,
                "universe": universe,
                "leverage": leverage,
                "history_type": history_type,
                "strategy": name,
                "family": "benchmark",
                "stop": "none",
                "scheme": "benchmark",
                **metric_pack(rr, ww),
                **split_metrics(rr, ww),
                "stress_cagr": float("nan"),
                "stress_sharpe": float("nan"),
                "stress_maxdd": float("nan"),
            }
        )
    return rows


def run_history(
    asset_spec: AssetSpec,
    hist_name: str,
    signal_df: pd.DataFrame,
    benchmark_df: pd.DataFrame | None,
    actual_data: dict[str, pd.DataFrame],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    feat = build_features(signal_df, benchmark_df)
    strategies = make_strategies(feat)
    under_ret = signal_df["Close"].pct_change()
    rows: list[dict[str, Any]] = []
    actual_rows: list[dict[str, Any]] = []
    leverages = (2, 3) if asset_spec.universe == "index" else (2,)
    stops = ("none", "trail10", "trail15", "trail20", "atr3", "atr4", "atr5", "sma200")
    schemes = ("full", "half", "quarter", "vol15", "vol20", "vol25")

    for lev in leverages:
        lev_ret = (lev * under_ret - DEFAULT_DRAG[lev] / 252.0).clip(lower=-0.99)
        stress_ret = (lev * under_ret - STRESS_DRAG[lev] / 252.0).clip(lower=-0.99)
        rows.extend(benchmark_rows(asset_spec.ticker, asset_spec.universe, lev, hist_name, under_ret, lev_ret))

        # Underlying signal to actual products; history is restricted later by return intersection.
        products = [p for p in asset_spec.actual_products if p.leverage == lev]
        actual_returns = [(p, actual_product_returns(p, actual_data)) for p in products]
        actual_returns = [(p, r) for p, r in actual_returns if r is not None]

        for st in strategies:
            base = build_target(st["entry"], st["exit"], st["max_hold"])
            for stop_name in stops:
                stopped = apply_locked_stop(base, feat, stop_name)
                for scheme in schemes:
                    r, w = run_cash_tactical(lev_ret, stopped, feat, lev, scheme, BASE_COST_BPS)
                    rs, ws = run_cash_tactical(stress_ret, stopped, feat, lev, scheme, STRESS_COST_BPS)
                    m = metric_pack(r, w)
                    sm = performance(rs, ws)
                    row = {
                        "asset": asset_spec.ticker,
                        "universe": asset_spec.universe,
                        "leverage": lev,
                        "history_type": hist_name,
                        "strategy": st["strategy"],
                        "family": st["family"],
                        "stop": stop_name,
                        "scheme": scheme,
                        **m,
                        **split_metrics(r, w),
                        "stress_cagr": sm["cagr"],
                        "stress_sharpe": sm["sharpe"],
                        "stress_maxdd": sm["maxdd"],
                    }
                    rows.append(row)

                    if hist_name == "tradeable_etf_history" and stop_name in ("none", "trail15", "atr4") and scheme in (
                        "full", "half", "vol20"
                    ):
                        for p, ar in actual_returns:
                            assert ar is not None
                            idx = ar.dropna().index.intersection(stopped.index)
                            if len(idx) < 120:
                                continue
                            rr, ww = run_cash_tactical(ar.reindex(idx), stopped.reindex(idx), feat.reindex(idx), lev, scheme,
                                                       BASE_COST_BPS)
                            am = metric_pack(rr, ww)
                            actual_rows.append(
                                {
                                    "asset": asset_spec.ticker,
                                    "universe": asset_spec.universe,
                                    "product": p.ticker,
                                    "leverage": lev,
                                    "strategy": st["strategy"],
                                    "family": st["family"],
                                    "stop": stop_name,
                                    "scheme": scheme,
                                    **am,
                                    **split_metrics(rr, ww),
                                    "data_start": idx.min().date().isoformat(),
                                    "data_end": idx.max().date().isoformat(),
                                }
                            )

                if asset_spec.universe == "index":
                    r, w = run_switch_1x_2x(under_ret, lev_ret, stopped, BASE_COST_BPS)
                    rs, ws = run_switch_1x_2x(under_ret, stress_ret, stopped, STRESS_COST_BPS)
                    m = metric_pack(r, w)
                    sm = performance(rs, ws)
                    rows.append(
                        {
                            "asset": asset_spec.ticker,
                            "universe": asset_spec.universe,
                            "leverage": lev,
                            "history_type": hist_name,
                            "strategy": st["strategy"],
                            "family": st["family"],
                            "stop": stop_name,
                            "scheme": "switch_1x_to_2x" if lev == 2 else "switch_1x_to_3x",
                            **m,
                            **split_metrics(r, w),
                            "stress_cagr": sm["cagr"],
                            "stress_sharpe": sm["sharpe"],
                            "stress_maxdd": sm["maxdd"],
                        }
                    )
    return rows, actual_rows


def rank_within_asset(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x["eligible"] = (
        (x["trades"] >= 5)
        & (x["late_cagr"].notna())
        & (x["stress_cagr"].notna())
        & (x["rolling3_windows"] >= 3)
    )
    x["asset_score"] = np.nan
    for _, ids in x.groupby(["asset", "leverage", "history_type"]).groups.items():
        p = x.loc[ids]
        p = p[p["eligible"]]
        if p.empty:
            continue
        s = (
            0.18 * p["cagr"].rank(pct=True)
            + 0.18 * p["late_cagr"].rank(pct=True)
            + 0.15 * p["stress_cagr"].rank(pct=True)
            + 0.15 * p["sharpe"].rank(pct=True)
            + 0.17 * p["calmar"].rank(pct=True)
            + 0.10 * p["maxdd"].rank(pct=True)
            + 0.07 * p["rolling3_worst_cagr"].rank(pct=True)
        )
        x.loc[p.index, "asset_score"] = s
    return x


def pooled_rank(df: pd.DataFrame, history_type: str) -> pd.DataFrame:
    x = df[(df["history_type"] == history_type) & df["asset_score"].notna() & (df["family"] != "benchmark")].copy()
    groups = []
    for (universe, leverage), p in x.groupby(["universe", "leverage"]):
        g = p.groupby(["strategy", "family", "stop", "scheme"], as_index=False).agg(
            asset_count=("asset", "nunique"),
            median_asset_score=("asset_score", "median"),
            median_cagr=("cagr", "median"),
            median_late_cagr=("late_cagr", "median"),
            median_stress_cagr=("stress_cagr", "median"),
            median_sharpe=("sharpe", "median"),
            median_calmar=("calmar", "median"),
            worst_maxdd=("maxdd", "min"),
            worst_late_cagr=("late_cagr", "min"),
            positive_asset_share=("cagr", lambda z: float((z > 0).mean())),
            late_positive_share=("late_cagr", lambda z: float((z > 0).mean())),
            median_trades=("trades", "median"),
            median_exposure=("exposure", "median"),
        )
        g["robust_score"] = (
            0.30 * g["median_asset_score"].rank(pct=True)
            + 0.18 * g["median_late_cagr"].rank(pct=True)
            + 0.15 * g["median_stress_cagr"].rank(pct=True)
            + 0.15 * g["median_calmar"].rank(pct=True)
            + 0.10 * g["worst_maxdd"].rank(pct=True)
            + 0.07 * g["positive_asset_share"]
            + 0.05 * g["late_positive_share"]
        )
        g["universe"] = universe
        g["leverage"] = leverage
        groups.append(g.sort_values("robust_score", ascending=False))
    return pd.concat(groups, ignore_index=True) if groups else pd.DataFrame()


def merge_actual_score(rank: pd.DataFrame, actual: pd.DataFrame) -> pd.DataFrame:
    if rank.empty or actual.empty:
        rank["final_score"] = rank.get("robust_score", np.nan)
        return rank
    av = actual[(actual["trades"] >= 2) & actual["cagr"].notna()].copy()
    ag = av.groupby(["universe", "leverage", "strategy", "family", "stop", "scheme"], as_index=False).agg(
        actual_product_count=("product", "nunique"),
        actual_asset_count=("asset", "nunique"),
        actual_median_cagr=("cagr", "median"),
        actual_median_sharpe=("sharpe", "median"),
        actual_median_calmar=("calmar", "median"),
        actual_worst_maxdd=("maxdd", "min"),
        actual_positive_share=("cagr", lambda z: float((z > 0).mean())),
    )
    ag["actual_score"] = (
        0.25 * ag["actual_median_cagr"].rank(pct=True)
        + 0.25 * ag["actual_median_sharpe"].rank(pct=True)
        + 0.25 * ag["actual_median_calmar"].rank(pct=True)
        + 0.15 * ag["actual_worst_maxdd"].rank(pct=True)
        + 0.10 * ag["actual_positive_share"]
    )
    keys = ["universe", "leverage", "strategy", "family", "stop", "scheme"]
    z = rank.merge(ag, on=keys, how="left")
    z["final_score"] = np.where(
        z["actual_asset_count"].fillna(0) >= 2,
        0.80 * z["robust_score"] + 0.20 * z["actual_score"].fillna(0),
        z["robust_score"],
    )
    return z.sort_values(["universe", "leverage", "final_score"], ascending=[True, True, False])


def fmt(v: Any, pct: bool = False) -> str:
    try:
        f = float(v)
        if not np.isfinite(f):
            return "—"
        return f"{f:.1%}" if pct else f"{f:.3f}"
    except Exception:  # noqa: BLE001
        return "—"


def md(df: pd.DataFrame, cols: list[str], n: int = 15) -> str:
    if df.empty:
        return "No qualifying rows."
    x = df.head(n)[[c for c in cols if c in df.columns]].copy()
    pct_cols = {
        "cagr", "late_cagr", "stress_cagr", "maxdd", "median_cagr", "median_late_cagr",
        "median_stress_cagr", "worst_maxdd", "worst_late_cagr", "actual_median_cagr",
        "actual_worst_maxdd", "benchmark_cagr", "benchmark_maxdd",
    }
    for c in x.columns:
        if c in pct_cols:
            x[c] = x[c].map(lambda v: fmt(v, True))
        elif pd.api.types.is_float_dtype(x[c]):
            x[c] = x[c].map(lambda v: fmt(v, False))
    return x.to_markdown(index=False)


def main() -> None:
    tickers = {a.ticker for a in ASSETS} | {a.benchmark for a in ASSETS} | set(INDEX_PROXIES.values())
    for a in ASSETS:
        tickers.update(p.ticker for p in a.actual_products)
    data: dict[str, pd.DataFrame] = {}
    manifest = []
    for t in sorted(tickers):
        try:
            x = download(t)
            data[t] = x
            manifest.append({"ticker": t, "status": "ok", "start": x.index.min().date().isoformat(),
                             "end": x.index.max().date().isoformat(), "rows": len(x)})
        except Exception as exc:  # noqa: BLE001
            manifest.append({"ticker": t, "status": f"failed: {exc}", "start": "", "end": "", "rows": 0})
    pd.DataFrame(manifest).to_csv(OUT / "data_manifest.csv", index=False)

    all_rows: list[dict[str, Any]] = []
    actual_rows: list[dict[str, Any]] = []
    for spec in ASSETS:
        if spec.ticker not in data:
            continue
        bench = data.get(spec.benchmark)
        rows, av = run_history(spec, "tradeable_etf_history", data[spec.ticker], bench, data)
        all_rows.extend(rows)
        actual_rows.extend(av)
        if spec.universe == "index" and spec.ticker in INDEX_PROXIES and INDEX_PROXIES[spec.ticker] in data:
            proxy = data[INDEX_PROXIES[spec.ticker]]
            # Relative-strength fields are not central for index proxy validation; use the proxy itself as benchmark.
            rows, _ = run_history(spec, "long_index_proxy", proxy, proxy, data)
            all_rows.extend(rows)

    results = pd.DataFrame(all_rows)
    actual = pd.DataFrame(actual_rows)
    results.to_csv(OUT / "all_results.csv", index=False)
    actual.to_csv(OUT / "actual_etf_validation.csv", index=False)
    scored = rank_within_asset(results)
    scored.to_csv(OUT / "scored_results.csv", index=False)

    trade_rank = merge_actual_score(pooled_rank(scored, "tradeable_etf_history"), actual)
    long_rank = pooled_rank(scored, "long_index_proxy")
    trade_rank.to_csv(OUT / "tradeable_history_pooled_rank.csv", index=False)
    long_rank.to_csv(OUT / "long_proxy_pooled_rank.csv", index=False)

    # Risk-constrained winners. Require drawdown discipline and positive late/stress results.
    constrained = scored[
        scored["asset_score"].notna()
        & (scored["family"] != "benchmark")
        & (scored["late_cagr"] > 0)
        & (scored["stress_cagr"] > 0)
    ].copy()
    constrained["dd_limit"] = np.where(constrained["universe"].eq("stock"), -0.55,
                                        np.where(constrained["leverage"].eq(3), -0.60, -0.50))
    constrained = constrained[constrained["maxdd"] >= constrained["dd_limit"]]
    constrained = constrained.sort_values(["asset", "leverage", "history_type", "asset_score"], ascending=False)
    winners = constrained.groupby(["asset", "leverage", "history_type"], as_index=False).head(1)
    winners.to_csv(OUT / "risk_constrained_asset_winners.csv", index=False)

    # Benchmark comparison table for winners.
    compare_rows = []
    benchmark = results[results["family"] == "benchmark"]
    for _, w in winners.iterrows():
        b = benchmark[
            (benchmark["asset"] == w["asset"])
            & (benchmark["leverage"] == w["leverage"])
            & (benchmark["history_type"] == w["history_type"])
            & (benchmark["strategy"] == "Underlying_BuyHold")
        ]
        if b.empty:
            continue
        b = b.iloc[0]
        compare_rows.append(
            {
                "asset": w["asset"],
                "universe": w["universe"],
                "leverage": w["leverage"],
                "history_type": w["history_type"],
                "strategy": w["strategy"],
                "family": w["family"],
                "stop": w["stop"],
                "scheme": w["scheme"],
                "cagr": w["cagr"],
                "late_cagr": w["late_cagr"],
                "stress_cagr": w["stress_cagr"],
                "sharpe": w["sharpe"],
                "maxdd": w["maxdd"],
                "calmar": w["calmar"],
                "trades": w["trades"],
                "exposure": w["exposure"],
                "benchmark_cagr": b["cagr"],
                "benchmark_sharpe": b["sharpe"],
                "benchmark_maxdd": b["maxdd"],
            }
        )
    compare = pd.DataFrame(compare_rows)
    compare.to_csv(OUT / "winner_vs_underlying.csv", index=False)

    # Strategy family/sizing diagnostics: where do 5/20, 10/30 and MHT land?
    diagnostics = trade_rank[
        trade_rank["strategy"].isin(["MA_5_20", "MA_10_30", "MA_50_200", "MHT_E4_X1", "MHT_E5_X1", "TSMOM_E4_X0"])
    ].copy()
    diagnostics.to_csv(OUT / "named_strategy_diagnostics.csv", index=False)

    report = []
    report.append("# Leveraged ETF Backtest V2 — Risk-Sized, Close-to-Close Validation")
    report.append("")
    report.append("Data are complete through 2026-07-17. Signals are based on completed closes and executed at the following close; synthetic leverage therefore uses close-to-close daily-reset arithmetic rather than the less defensible open-to-open approximation.")
    report.append("")
    report.append("## Validation changes versus V1")
    report.append("")
    report.append("- Added underlying, synthetic leveraged and fractional-leverage buy-and-hold benchmarks.")
    report.append("- Added 25%/50% tactical sleeves, 15%/20%/25% volatility targets and index 1x-to-leveraged switching.")
    report.append("- Added fixed 10%/15%/20%, ATR 3/4/5 and 200DMA locked stop overlays.")
    report.append("- Added long index proxies (^GSPC, ^NDX, ^SOX) where available; proxy histories are price-index robustness tests, not total-return replications.")
    report.append("- Retained actual ETF validation and conservative drag/cost stress.")
    report.append("")

    cols = ["strategy", "family", "stop", "scheme", "final_score", "asset_count", "median_cagr",
            "median_late_cagr", "median_stress_cagr", "median_sharpe", "median_calmar", "worst_maxdd",
            "actual_median_cagr", "actual_worst_maxdd"]
    for universe, lev, title in (("index", 2, "Index 2x"), ("index", 3, "Index 3x"), ("stock", 2, "Single-stock 2x")):
        p = trade_rank[(trade_rank["universe"] == universe) & (trade_rank["leverage"] == lev)]
        report.append(f"## {title}: pooled tradeable-history ranking")
        report.append("")
        report.append(md(p, cols, 15))
        report.append("")
        if universe == "index":
            lp = long_rank[(long_rank["universe"] == universe) & (long_rank["leverage"] == lev)]
            report.append(f"### {title}: long-index-proxy ranking")
            report.append("")
            report.append(md(lp, [c for c in cols if c != "final_score"], 12))
            report.append("")

    report.append("## Risk-constrained asset winners versus underlying buy-and-hold")
    report.append("")
    report.append(md(compare, ["asset", "leverage", "history_type", "strategy", "family", "stop", "scheme",
                               "cagr", "late_cagr", "stress_cagr", "sharpe", "maxdd", "calmar", "trades",
                               "exposure", "benchmark_cagr", "benchmark_sharpe", "benchmark_maxdd"], 50))
    report.append("")

    report.append("## Named-strategy diagnostics")
    report.append("")
    report.append(md(diagnostics, cols, 50))
    report.append("")
    report.append("## Guardrails")
    report.append("")
    report.append("- A result is not called a winner merely because its CAGR is highest; the risk-constrained table requires positive late and stress CAGR plus maximum-drawdown limits.")
    report.append("- Full-allocation single-stock 2x results frequently approach ruin. The practical contest is therefore between fractional sleeves, volatility targets and 1x-to-leveraged switching, not naked full allocation.")
    report.append("- Actual single-stock leveraged ETF histories remain short. Long underlying histories test the signal family; actual ETF histories validate implementation direction only.")
    report.append("- Earnings-calendar and analyst-surprise data were not point-in-time available, so the gap/volume family must not be described as a validated PEAD strategy.")

    (OUT / "research_report.md").write_text("\n".join(report), encoding="utf-8")
    (OUT / "run_metadata.json").write_text(
        json.dumps(
            {
                "completed_through": "2026-07-17",
                "base_cost_bps": BASE_COST_BPS,
                "stress_cost_bps": STRESS_COST_BPS,
                "strategy_rules_per_asset": 188,
                "stop_overlays": 8,
                "position_schemes": 6,
                "result_rows": len(results),
                "actual_validation_rows": len(actual),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print((OUT / "research_report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
