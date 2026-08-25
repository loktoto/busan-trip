from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import yfinance as yf

OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)
COST = 0.001
START_CAPITAL = 10_000.0
TICKERS = ["SOXX", "SMH", "USD", "SOXL"]


def download_data() -> dict[str, pd.DataFrame]:
    data: dict[str, pd.DataFrame] = {}
    for ticker in TICKERS:
        df = yf.download(ticker, period="max", interval="1d", auto_adjust=True,
                         actions=False, progress=False, threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.rename(columns=str.title)[["Open", "High", "Low", "Close", "Volume"]]
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df = df[~df.index.duplicated(keep="last")].sort_index().dropna(subset=["Open", "Close"])
        if len(df) < 500:
            raise RuntimeError(f"Insufficient history for {ticker}: {len(df)} rows")
        data[ticker] = df
    common_last = min(df.index.max() for df in data.values())
    return {k: v.loc[:common_last].copy() for k, v in data.items()}


def rsi_wilder(close: pd.Series, n: int = 2) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0.0)
    down = -delta.clip(upper=0.0)
    avg_up = up.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    avg_down = down.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = avg_up / avg_down.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.where(avg_down != 0, 100.0)
    rsi = rsi.where(avg_up != 0, 0.0)
    return rsi


def state_from_rules(entry: pd.Series, exit_: pd.Series) -> pd.Series:
    entry_np = entry.fillna(False).to_numpy(dtype=bool)
    exit_np = exit_.fillna(False).to_numpy(dtype=bool)
    out = np.zeros(len(entry_np), dtype=np.int8)
    state = 0
    for i in range(len(entry_np)):
        if state == 0 and entry_np[i]:
            state = 1
        elif state == 1 and exit_np[i]:
            state = 0
        out[i] = state
    return pd.Series(out, index=entry.index, dtype=float)


def state_fixed_hold(entry: pd.Series, hold_days: int) -> pd.Series:
    e = entry.fillna(False).to_numpy(dtype=bool)
    out = np.zeros(len(e), dtype=np.int8)
    left = 0
    for i in range(len(e)):
        if left <= 0 and e[i]:
            left = hold_days
        if left > 0:
            out[i] = 1
            left -= 1
    return pd.Series(out, index=entry.index, dtype=float)


def strategy_returns(product: pd.DataFrame, signal_state: pd.Series,
                     cost: float = COST) -> tuple[pd.Series, pd.Series]:
    idx = product.index.intersection(signal_state.index)
    p = product.loc[idx]
    target_after_close = signal_state.reindex(idx).ffill().fillna(0.0)
    pos_at_open = target_after_close.shift(1).fillna(0.0)
    open_to_open = p["Open"].shift(-1).div(p["Open"]).sub(1.0)
    turnover = pos_at_open.diff().abs().fillna(pos_at_open.abs())
    ret = pos_at_open * open_to_open - cost * turnover
    ret = ret.dropna()
    return ret, pos_at_open.reindex(ret.index)


def buy_hold_returns(product: pd.DataFrame, cost: float = COST) -> tuple[pd.Series, pd.Series]:
    open_to_open = product["Open"].shift(-1).div(product["Open"]).sub(1.0).dropna()
    pos = pd.Series(1.0, index=open_to_open.index)
    ret = open_to_open.copy()
    if len(ret):
        ret.iloc[0] -= cost
    return ret, pos


def metrics(ret: pd.Series, pos: pd.Series) -> dict[str, float]:
    ret = ret.dropna()
    pos = pos.reindex(ret.index).fillna(0.0)
    if len(ret) < 2:
        return {k: np.nan for k in ["total_return", "end_value", "cagr", "ann_vol",
                                           "sharpe", "max_drawdown", "calmar", "exposure", "trades"]}
    eq = (1.0 + ret).cumprod()
    years = len(ret) / 252.0
    total = float(eq.iloc[-1] - 1.0)
    cagr = float(eq.iloc[-1] ** (1 / years) - 1.0) if years > 0 and eq.iloc[-1] > 0 else np.nan
    vol = float(ret.std(ddof=0) * math.sqrt(252))
    sharpe = float(ret.mean() / ret.std(ddof=0) * math.sqrt(252)) if ret.std(ddof=0) > 0 else np.nan
    dd = eq.div(eq.cummax()).sub(1.0)
    maxdd = float(dd.min())
    calmar = float(cagr / abs(maxdd)) if maxdd < 0 and np.isfinite(cagr) else np.nan
    trades = float(pos.diff().abs().fillna(pos.abs()).sum() / 2.0)
    return {"total_return": total, "end_value": START_CAPITAL * (1.0 + total),
            "cagr": cagr, "ann_vol": vol, "sharpe": sharpe,
            "max_drawdown": maxdd, "calmar": calmar,
            "exposure": float(pos.mean()), "trades": trades}


def window_start(index: pd.DatetimeIndex, window: str) -> pd.Timestamp:
    end = index.max()
    if window == "MAX":
        return index.min()
    years = int(window[:-1])
    target = end - pd.DateOffset(years=years)
    return index[index.searchsorted(target)]


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame(index=df.index)
    f["close"] = df["Close"]
    f["rsi2"] = rsi_wilder(df["Close"], 2)
    for n in [10, 20, 30, 40, 50, 63, 90, 100, 126, 150, 160, 200, 250]:
        f[f"sma{n}"] = df["Close"].rolling(n).mean()
    for n in [20, 40, 50, 63, 90, 126]:
        f[f"high{n}"] = df["Close"].shift(1).rolling(n).max()
    for n in [21, 63, 126]:
        f[f"ret{n}"] = df["Close"].pct_change(n)
    return f


@dataclass(frozen=True)
class Candidate:
    family: str
    name: str
    state_builder: Callable[[pd.DataFrame], pd.Series]
    params: dict


def candidate_grid() -> list[Candidate]:
    out: list[Candidate] = []
    for ent in [20, 30, 40, 50, 63, 90, 100]:
        for ex in [100, 150, 160, 200, 250]:
            if ent >= ex:
                continue
            def build(f: pd.DataFrame, ent=ent, ex=ex):
                return state_from_rules(f["close"] > f[f"sma{ent}"],
                                        f["close"] < f[f"sma{ex}"])
            out.append(Candidate("MA_REGIME", f"MA{ent}_EXIT{ex}", build,
                                 {"entry_ma": ent, "exit_ma": ex}))

    for look in [20, 40, 50, 63, 90, 126]:
        for rx in [85, 90, 92, 95]:
            def build(f: pd.DataFrame, look=look, rx=rx):
                entry = (f["close"] > f[f"high{look}"]) & (f["close"] > f["sma200"])
                return state_from_rules(entry, f["rsi2"] > rx)
            out.append(Candidate("BREAKOUT_RSI", f"B{look}_RSI{rx}", build,
                                 {"breakout": look, "exit_rsi": rx}))

    for low in [5, 10, 15]:
        for reclaim in [10, 20]:
            for hold in [10, 20, 40]:
                def build(f: pd.DataFrame, low=low, reclaim=reclaim, hold=hold):
                    recent_low = f["rsi2"].rolling(5).min() < low
                    cross = ((f["close"] > f[f"sma{reclaim}"]) &
                             (f["close"].shift(1) <= f[f"sma{reclaim}"].shift(1)))
                    entry = (f["close"] > f["sma200"]) & recent_low & cross
                    return state_fixed_hold(entry, hold)
                out.append(Candidate("PULLBACK_RECLAIM", f"RSI{low}_R{reclaim}_H{hold}", build,
                                     {"rsi_low": low, "reclaim": reclaim, "hold": hold}))

    for entry_score in [4, 5, 6]:
        for exit_score in [1, 2, 3]:
            if exit_score >= entry_score:
                continue
            def build(f: pd.DataFrame, entry_score=entry_score, exit_score=exit_score):
                score = ((f["close"] > f["sma20"]).astype(int)
                         + (f["close"] > f["sma50"]).astype(int)
                         + (f["close"] > f["sma100"]).astype(int)
                         + (f["ret21"] > 0).astype(int)
                         + (f["ret63"] > 0).astype(int)
                         + (f["ret126"] > 0).astype(int))
                return state_from_rules(score >= entry_score, score <= exit_score)
            out.append(Candidate("MHT", f"MHT{entry_score}_{exit_score}", build,
                                 {"entry_score": entry_score, "exit_score": exit_score}))
    return out


def evaluate():
    data = download_data()
    features = {s: make_features(data[s]) for s in ["SOXX", "SMH"]}
    candidates = candidate_grid()
    rows: list[dict] = []
    cache: dict[str, pd.DataFrame] = {}

    for product in ["USD", "SOXL"]:
        bh_ret, bh_pos = buy_hold_returns(data[product])
        cache[f"{product}|{product}|BUY_HOLD"] = pd.DataFrame({"ret": bh_ret, "pos": bh_pos})
        for window in ["1Y", "3Y", "5Y", "10Y", "MAX"]:
            start = window_start(bh_ret.index, window)
            rows.append({"product": product, "signal": product, "family": "BUY_HOLD",
                         "strategy": "BUY_HOLD", "window": window, "start": start.date(),
                         "end": bh_ret.index.max().date(), **metrics(bh_ret.loc[start:], bh_pos.loc[start:])})

        for signal in ["SOXX", "SMH"]:
            f = features[signal]
            for c in candidates:
                ret, pos = strategy_returns(data[product], c.state_builder(f))
                cache[f"{product}|{signal}|{c.name}"] = pd.DataFrame({"ret": ret, "pos": pos})
                for window in ["1Y", "3Y", "5Y", "10Y", "MAX"]:
                    start = window_start(ret.index, window)
                    rows.append({"product": product, "signal": signal, "family": c.family,
                                 "strategy": c.name, "window": window, "start": start.date(),
                                 "end": ret.index.max().date(), **c.params,
                                 **metrics(ret.loc[start:], pos.loc[start:])})

    results = pd.DataFrame(rows)
    base = results[(results["family"] != "BUY_HOLD") &
                   results["window"].isin(["3Y", "5Y", "10Y", "MAX"])].copy()
    agg = base.groupby(["product", "signal", "family", "strategy"], as_index=False).agg(
        median_cagr=("cagr", "median"), worst_cagr=("cagr", "min"),
        median_sharpe=("sharpe", "median"), worst_sharpe=("sharpe", "min"),
        median_calmar=("calmar", "median"), worst_maxdd=("max_drawdown", "min"),
        median_exposure=("exposure", "median"), total_trades=("trades", "sum"),
        windows=("window", "count"))
    agg["robust_score"] = (agg["median_sharpe"].clip(-1, 3)
                           + agg["median_calmar"].clip(-1, 3)
                           + 0.5 * agg["worst_cagr"].clip(-1, 1)
                           + 0.25 * agg["worst_sharpe"].clip(-1, 2))
    return results, agg.sort_values(["product", "robust_score"], ascending=[True, False]), cache


def rolling_metrics(series: pd.DataFrame, years: int, step_months: int = 3) -> list[dict]:
    out = []
    cur, end = series.index.min(), series.index.max()
    while cur + pd.DateOffset(years=years) <= end:
        stop = cur + pd.DateOffset(years=years)
        mask = (series.index >= cur) & (series.index <= stop)
        if mask.sum() >= years * 200:
            out.append({"roll_years": years, "start": cur.date(), "end": stop.date(),
                        **metrics(series.loc[mask, "ret"], series.loc[mask, "pos"])})
        cur += pd.DateOffset(months=step_months)
    return out


def build_report(results: pd.DataFrame, agg: pd.DataFrame,
                 cache: dict[str, pd.DataFrame]) -> None:
    results.to_csv(OUT / "all_strategy_windows.csv", index=False)
    agg.to_csv(OUT / "robust_rank.csv", index=False)
    selected_rows, rolling_rows = [], []
    for product in ["USD", "SOXL"]:
        pa = agg[agg.product == product]
        picks = [("ROBUST_OVERALL", pa),
                 ("BEST_MA_REGIME", pa[pa.family == "MA_REGIME"]),
                 ("BEST_BREAKOUT", pa[pa.family == "BREAKOUT_RSI"]),
                 ("BEST_PULLBACK", pa[pa.family == "PULLBACK_RECLAIM"]),
                 ("BEST_MHT", pa[pa.family == "MHT"])]
        seen = set()
        for label, subset in picks:
            if subset.empty:
                continue
            r = subset.iloc[0]
            ident = (r.product, r.signal, r.strategy)
            if ident in seen:
                continue
            seen.add(ident)
            selected_rows.append({"selection": label, **r.to_dict()})
            key = f"{r.product}|{r.signal}|{r.strategy}"
            for years in [3, 5]:
                for x in rolling_metrics(cache[key], years):
                    rolling_rows.append({"product": r.product, "signal": r.signal,
                                         "family": r.family, "strategy": r.strategy, **x})
    selected = pd.DataFrame(selected_rows)
    selected.to_csv(OUT / "selected_strategies.csv", index=False)
    pd.DataFrame(rolling_rows).to_csv(OUT / "selected_rolling_windows.csv", index=False)

    compare = []
    ids = [(r["product"], r["signal"], r["strategy"], r["selection"])
           for _, r in selected.iterrows()]
    ids += [(p, p, "BUY_HOLD", "BUY_HOLD") for p in ["USD", "SOXL"]]
    for p, s, strat, selection in ids:
        for _, x in results[(results.product == p) &
                            (results.signal == s) &
                            (results.strategy == strat)].iterrows():
            compare.append({"selection": selection, **x.to_dict()})
    pd.DataFrame(compare).to_csv(OUT / "selected_10000_comparison.csv", index=False)

    meta = {"generated_utc": pd.Timestamp.utcnow().isoformat(),
            "method": "adjusted daily OHLC; signal at close; next-open execution; 10 bps per change; cash 0%",
            "tickers": TICKERS,
            "selection_note": "1Y excluded from robust selection because the latest semiconductor year is exceptional."}
    (OUT / "methodology.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    def pct(x):
        return "n/a" if pd.isna(x) else f"{x:.1%}"
    lines = ["# Semiconductor Leverage Daily Strategy Audit", "",
             "## Method",
             "- Signal at completed close; execute at next regular-session open.",
             "- Adjusted OHLC; 10 bps per position change; cash return 0%.",
             "- Signal sources: SOXX and SMH. Products: USD and SOXL.",
             "- Robust ranking uses 3Y, 5Y, 10Y and MAX; 1Y excluded from selection.", "",
             "## Selected candidates", "",
             "| Product | Selection | Signal | Family | Strategy | Median CAGR | Worst CAGR | Median Sharpe | Median Calmar | Worst MaxDD |",
             "|---|---|---|---|---|---:|---:|---:|---:|---:|"]
    for _, r in selected.iterrows():
        lines.append(f"| {r['product']} | {r['selection']} | {r['signal']} | {r['family']} | {r['strategy']} | "
                     f"{pct(r['median_cagr'])} | {pct(r['worst_cagr'])} | {r['median_sharpe']:.2f} | "
                     f"{r['median_calmar']:.2f} | {pct(r['worst_maxdd'])} |")
    lines += ["", "## Guardrails",
              "- USD and SOXL are not the same index at different leverage; keep results product-specific.",
              "- SOXL changed benchmark historically; this report uses actual ETF history only.",
              "- No result is a guarantee of future outperformance."]
    (OUT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    results, agg, cache = evaluate()
    build_report(results, agg, cache)
    print((OUT / "REPORT.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
