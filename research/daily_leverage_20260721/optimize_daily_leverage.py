from __future__ import annotations

import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

OUT = Path("research_outputs/daily_leverage_20260721")
OUT.mkdir(parents=True, exist_ok=True)
DAYS = 252


@dataclass(frozen=True)
class Spec:
    name: str
    native: tuple[tuple[str, float], ...]
    levered: tuple[tuple[str, float], ...]
    target_leverage: float
    start: str
    split: str
    regimes: tuple[int, ...]
    slopes: tuple[int, ...]
    rsi_entries: tuple[int, ...]
    looks: tuple[int, ...]
    reclaims: tuple[int, ...]
    rsi_exits: tuple[int, ...]
    exit_smas: tuple[int | None, ...]
    min_changes: int
    roll_years: tuple[int, ...]
    component_gate: bool = False


SPECS = (
    Spec(
        "SPY", (("SPY", 1.0),), (("SSO", 1.0),), 2.0,
        "2010-01-01", "2018-01-01",
        (150, 200, 250), (10, 20, 40), (15, 20, 25), (5, 10, 15),
        (5, 10, 15, 20), (85, 90, 95), (None, 50), 8, (3, 5),
    ),
    Spec(
        "SOXX", (("SOXX", 1.0),), (("USD", 1.0),), 2.0,
        "2010-01-01", "2018-01-01",
        (150, 200, 250), (5, 10, 20, 40), (5, 10, 15, 20), (2, 3, 5, 10),
        (5, 10, 15, 20, 30), (85, 90, 95), (None, 20, 50, 100), 6, (2, 3),
    ),
    Spec(
        "MAGS7_TSM", (("MAGS", 0.875), ("TSM", 0.125)),
        (("MAGX", 0.875), ("TSMX", 0.125)), 1.5,
        "2024-10-01", "2025-07-01",
        (150, 200), (10, 20, 40), (5, 10, 15), (3, 5, 10),
        (5, 10, 15, 20), (90, 95), (None, 20, 50), 2, (1,), True,
    ),
)


def rsi(close: pd.Series, n: int = 2) -> pd.Series:
    d = close.diff()
    gain = d.clip(lower=0)
    loss = -d.clip(upper=0)
    ag = gain.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    al = loss.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = ag / al.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    out[(al == 0) & (ag > 0)] = 100
    out[(ag == 0) & (al > 0)] = 0
    return out


def download() -> dict[str, pd.DataFrame]:
    tickers = sorted({t for s in SPECS for legs in (s.native, s.levered) for t, _ in legs})
    raw = yf.download(
        tickers, start="2009-01-01", auto_adjust=True, actions=False,
        progress=False, group_by="ticker", threads=True,
    )
    result: dict[str, pd.DataFrame] = {}
    for ticker in tickers:
        df = raw[ticker].copy() if isinstance(raw.columns, pd.MultiIndex) else raw.copy()
        df.columns = [str(c).title() for c in df.columns]
        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Open", "Close"])
        df.index = pd.to_datetime(df.index).tz_localize(None)
        if df.empty:
            raise RuntimeError(f"No data for {ticker}")
        result[ticker] = df
    return result


def basket(data: dict[str, pd.DataFrame], legs: tuple[tuple[str, float], ...]) -> pd.DataFrame:
    idx = None
    for ticker, _ in legs:
        idx = data[ticker].index if idx is None else idx.intersection(data[ticker].index)
    if idx is None or idx.empty:
        raise RuntimeError(f"No common dates for {legs}")
    out = pd.DataFrame(index=idx)
    for field in ("Open", "High", "Low", "Close"):
        parts = []
        for ticker, weight in legs:
            s = data[ticker].loc[idx, field]
            parts.append(weight * s / s.iloc[0])
        out[field] = pd.concat(parts, axis=1).sum(axis=1)
    out["Volume"] = 0.0
    return out


def open_return(df: pd.DataFrame) -> pd.Series:
    return df.Open.shift(-1) / df.Open - 1


def metrics(ret: pd.Series) -> dict[str, float]:
    x = ret.dropna()
    if len(x) < 40:
        return {"cagr": np.nan, "sharpe": np.nan, "maxdd": np.nan, "calmar": np.nan}
    eq = (1 + x).cumprod()
    years = max((x.index[-1] - x.index[0]).days / 365.25, len(x) / DAYS)
    cagr = float(eq.iloc[-1] ** (1 / years) - 1)
    vol = float(x.std(ddof=1) * math.sqrt(DAYS))
    sharpe = float(x.mean() * DAYS / vol) if vol > 0 else np.nan
    dd = eq / eq.cummax() - 1
    maxdd = float(dd.min())
    return {
        "cagr": cagr,
        "sharpe": sharpe,
        "maxdd": maxdd,
        "calmar": cagr / abs(maxdd) if maxdd < 0 else np.nan,
    }


def stateful(entry: pd.Series, exit_: pd.Series) -> pd.Series:
    active = False
    values = []
    for e, x in zip(entry.fillna(False), exit_.fillna(False)):
        if active and bool(x):
            active = False
        elif not active and bool(e):
            active = True
        values.append(active)
    return pd.Series(values, index=entry.index, dtype=bool)


def run_returns(
    native: pd.DataFrame,
    levered: pd.DataFrame,
    close_state: pd.Series,
    target_leverage: float,
    cost_bps: float,
) -> tuple[pd.Series, pd.Series]:
    idx = native.index.intersection(levered.index)
    native = native.loc[idx]
    levered = levered.loc[idx]
    held = close_state.reindex(idx).shift(1).fillna(False)
    native_ret = open_return(native)
    levered_ret = open_return(levered)
    blend = (target_leverage - 1.0) / (2.0 - 1.0)
    active_ret = (1 - blend) * native_ret + blend * levered_ret
    ret = native_ret.where(~held, active_ret)
    changes = held.astype(int).diff().abs().fillna(0)
    ret -= changes * cost_bps / 10_000.0
    return ret.iloc[:-1], held.iloc[:-1]


def rolling(strategy: pd.Series, benchmark: pd.Series, years: int) -> dict[str, float]:
    start = max(strategy.index.min(), benchmark.index.min())
    end = min(strategy.index.max(), benchmark.index.max())
    rows = []
    for finish in pd.date_range(start + pd.DateOffset(years=years), end, freq="MS"):
        begin = finish - pd.DateOffset(years=years)
        a = metrics(strategy.loc[begin:finish])
        b = metrics(benchmark.loc[begin:finish])
        if np.isfinite(a["cagr"]) and np.isfinite(b["cagr"]):
            rows.append((a["cagr"] - b["cagr"], a["sharpe"] - b["sharpe"], a["maxdd"] - b["maxdd"]))
    if not rows:
        return {"n": 0, "beat": np.nan, "worst": np.nan, "sharpe_beat": np.nan, "dd_beat": np.nan}
    arr = np.asarray(rows)
    return {
        "n": len(arr),
        "beat": float(np.mean(arr[:, 0] > 0)),
        "worst": float(np.min(arr[:, 0])),
        "sharpe_beat": float(np.mean(arr[:, 1] >= 0)),
        "dd_beat": float(np.mean(arr[:, 2] >= 0)),
    }


def make_candidates(spec: Spec, native: pd.DataFrame, data: dict[str, pd.DataFrame]):
    close = native.Close
    r2 = rsi(close, 2)
    windows = set(spec.regimes + spec.reclaims + tuple(x for x in spec.exit_smas if x))
    sma = {n: close.rolling(n).mean() for n in windows}
    component_ok = pd.Series(True, index=close.index)
    if spec.component_gate:
        common = close.index.intersection(data["MAGS"].index).intersection(data["TSM"].index)
        component_ok = pd.Series(False, index=close.index)
        component_ok.loc[common] = (
            (data["MAGS"].loc[common, "Close"] > data["MAGS"].loc[common, "Close"].rolling(100).mean())
            & (data["TSM"].loc[common, "Close"] > data["TSM"].loc[common, "Close"].rolling(100).mean())
        )
    for values in itertools.product(
        spec.regimes, spec.slopes, spec.rsi_entries, spec.looks,
        spec.reclaims, spec.rsi_exits, spec.exit_smas,
    ):
        regime, slope, rsi_entry, look, reclaim, rsi_exit, exit_sma = values
        trend = (close > sma[regime]) & (sma[regime] > sma[regime].shift(slope))
        oversold = r2.rolling(look).min() < rsi_entry
        cross = (close > sma[reclaim]) & (close.shift(1) <= sma[reclaim].shift(1))
        entry = trend & oversold & cross & component_ok
        exit_ = r2 > rsi_exit
        if exit_sma is not None:
            exit_ |= close < sma[exit_sma]
        yield {
            "regime": regime, "slope": slope, "rsi_entry": rsi_entry,
            "look": look, "reclaim": reclaim, "rsi_exit": rsi_exit,
            "exit_sma": exit_sma, "state": stateful(entry, exit_),
        }


def neighbour_stats(train: pd.DataFrame) -> pd.DataFrame:
    params = ["regime", "slope", "rsi_entry", "look", "reclaim", "rsi_exit", "exit_sma"]
    rows = []
    encoded = train[params].fillna(-1)
    for row in train.itertuples():
        target = np.array([-1 if pd.isna(getattr(row, c)) else getattr(row, c) for c in params])
        distance = (encoded.to_numpy() != target).sum(axis=1)
        neighbours = train[distance <= 1]
        rows.append({
            "candidate_id": row.candidate_id,
            "neighbour_count": len(neighbours),
            "neighbour_min_excess": neighbours.train_excess.min(),
            "neighbour_median_excess": neighbours.train_excess.median(),
        })
    return pd.DataFrame(rows)


def evaluate(spec: Spec, data: dict[str, pd.DataFrame]):
    native = basket(data, spec.native)
    levered = basket(data, spec.levered)
    idx = native.index.intersection(levered.index)
    idx = idx[idx >= pd.Timestamp(spec.start)]
    native = native.loc[idx]
    levered = levered.loc[idx]
    if len(idx) < 250:
        raise RuntimeError(f"{spec.name}: only {len(idx)} common actual-product sessions")

    split = pd.Timestamp(spec.split)
    if split <= idx.min() or split >= idx.max():
        split = idx[int(len(idx) * 0.6)]
    benchmark = open_return(native).iloc[:-1]
    btrain = metrics(benchmark.loc[: split - pd.Timedelta(days=1)])
    boos = metrics(benchmark.loc[split:])
    bfull = metrics(benchmark)

    rows = []
    states: dict[int, pd.Series] = {}
    for candidate_id, candidate in enumerate(make_candidates(spec, native, data)):
        ret, held = run_returns(native, levered, candidate["state"], spec.target_leverage, 10)
        train = metrics(ret.loc[: split - pd.Timedelta(days=1)])
        oos = metrics(ret.loc[split:])
        full = metrics(ret)
        changes = int(held.astype(int).diff().abs().fillna(0).sum())
        row = {k: v for k, v in candidate.items() if k != "state"}
        row.update({
            "candidate_id": candidate_id,
            "changes": changes,
            "avg_exposure": float(1 + held.mean() * (spec.target_leverage - 1)),
            "train_cagr": train["cagr"], "train_sharpe": train["sharpe"], "train_maxdd": train["maxdd"],
            "train_excess": train["cagr"] - btrain["cagr"],
            "train_sharpe_excess": train["sharpe"] - btrain["sharpe"],
            "train_dd_delta": train["maxdd"] - btrain["maxdd"],
            "oos_cagr": oos["cagr"], "oos_sharpe": oos["sharpe"], "oos_maxdd": oos["maxdd"],
            "oos_excess": oos["cagr"] - boos["cagr"],
            "oos_sharpe_excess": oos["sharpe"] - boos["sharpe"],
            "oos_dd_delta": oos["maxdd"] - boos["maxdd"],
            "full_cagr": full["cagr"], "full_sharpe": full["sharpe"], "full_maxdd": full["maxdd"],
            "full_excess": full["cagr"] - bfull["cagr"],
        })
        rows.append(row)
        states[candidate_id] = candidate["state"]

    grid = pd.DataFrame(rows)
    grid["train_pass"] = (
        (grid.train_excess > 0) & (grid.train_sharpe_excess >= 0)
        & (grid.train_dd_delta >= -0.03) & (grid.changes >= spec.min_changes)
    )
    train = grid[grid.train_pass].copy()
    if train.empty:
        raise RuntimeError(f"{spec.name}: no training candidate passed")
    for column in ("train_excess", "train_sharpe_excess", "train_dd_delta"):
        train[column + "_pct"] = train[column].rank(pct=True)
    train["train_score"] = (
        0.45 * train.train_excess_pct + 0.35 * train.train_sharpe_excess_pct
        + 0.20 * train.train_dd_delta_pct
    )
    train = train.merge(neighbour_stats(train), on="candidate_id", how="left")
    train["stable_pass"] = (train.neighbour_count >= 3) & (train.neighbour_min_excess >= -0.005)
    shortlist = train[train.stable_pass].nlargest(30, "train_score")
    if shortlist.empty:
        shortlist = train.nlargest(30, "train_score")

    validation = []
    for row in shortlist.itertuples():
        state = states[row.candidate_id]
        base_ret, _ = run_returns(native, levered, state, spec.target_leverage, 10)
        stress_ret, _ = run_returns(native, levered, state, spec.target_leverage, 25)
        stress = metrics(stress_ret)
        extra = {
            "candidate_id": row.candidate_id,
            "stress_excess": stress["cagr"] - bfull["cagr"],
            "current_state": "levered" if bool(state.iloc[-1]) else "native",
        }
        for years in spec.roll_years:
            r = rolling(base_ret, benchmark, years)
            extra.update({f"roll{years}_{k}": v for k, v in r.items()})
        validation.append(extra)
    shortlist = shortlist.merge(pd.DataFrame(validation), on="candidate_id", how="left")
    primary = spec.roll_years[0]
    shortlist["oos_pass"] = (
        (shortlist.oos_excess > 0) & (shortlist.oos_sharpe_excess >= 0)
        & (shortlist.oos_dd_delta >= -0.03) & (shortlist.stress_excess > 0)
        & (shortlist[f"roll{primary}_beat"] >= 0.70)
    )
    shortlist["final_score"] = (
        0.45 * shortlist.train_score
        + 0.20 * shortlist.oos_excess.rank(pct=True)
        + 0.15 * shortlist.oos_sharpe_excess.rank(pct=True)
        + 0.10 * shortlist.stress_excess.rank(pct=True)
        + 0.10 * shortlist[f"roll{primary}_beat"].rank(pct=True)
    )
    shortlist = shortlist.sort_values(["oos_pass", "final_score"], ascending=[False, False])
    winner = shortlist.iloc[0].to_dict()
    meta = {
        "asset": spec.name, "start": str(idx.min().date()), "end": str(idx.max().date()),
        "split": str(split.date()), "sessions": len(idx), "candidates": len(grid),
        "train_pass": int(grid.train_pass.sum()), "benchmark": bfull, "winner": winner,
    }
    return grid, shortlist, meta


def main() -> None:
    data = download()
    summary_rows = []
    report = [
        "# Daily leverage optimisation — actual-product validation", "",
        "Signals are calculated at the close and applied at the following regular-session open.", "",
    ]
    for spec in SPECS:
        grid, shortlist, meta = evaluate(spec, data)
        slug = spec.name.lower()
        grid.to_csv(OUT / f"{slug}_grid.csv", index=False)
        shortlist.to_csv(OUT / f"{slug}_shortlist.csv", index=False)
        (OUT / f"{slug}_meta.json").write_text(json.dumps(meta, indent=2, default=str))
        w = meta["winner"]
        summary_rows.append({
            "asset": spec.name, "start": meta["start"], "end": meta["end"],
            "oos_pass": bool(w["oos_pass"]), "current_state": w["current_state"],
            "regime": int(w["regime"]), "slope": int(w["slope"]),
            "rsi_entry": int(w["rsi_entry"]), "look": int(w["look"]),
            "reclaim": int(w["reclaim"]), "rsi_exit": int(w["rsi_exit"]),
            "exit_sma": None if pd.isna(w["exit_sma"]) else int(w["exit_sma"]),
            "full_cagr": w["full_cagr"], "benchmark_cagr": meta["benchmark"]["cagr"],
            "full_sharpe": w["full_sharpe"], "benchmark_sharpe": meta["benchmark"]["sharpe"],
            "full_maxdd": w["full_maxdd"], "benchmark_maxdd": meta["benchmark"]["maxdd"],
            "oos_excess": w["oos_excess"], "stress_excess": w["stress_excess"],
        })
        exit_text = f"RSI(2)>{int(w['rsi_exit'])}"
        if not pd.isna(w["exit_sma"]):
            exit_text += f" or close<SMA{int(w['exit_sma'])}"
        report += [
            f"## {spec.name}", "",
            f"- Actual-product overlap: {meta['start']} to {meta['end']} ({meta['sessions']} sessions)",
            f"- Search: {meta['candidates']:,} candidates; {meta['train_pass']:,} passed the training gate",
            f"- Entry: rising SMA{int(w['regime'])} over {int(w['slope'])} sessions; RSI(2)<{int(w['rsi_entry'])} within {int(w['look'])} sessions; reclaim SMA{int(w['reclaim'])}",
            f"- Exit: {exit_text}",
            f"- Full CAGR: {w['full_cagr']:.2%} vs native {meta['benchmark']['cagr']:.2%}",
            f"- Full Sharpe: {w['full_sharpe']:.2f} vs native {meta['benchmark']['sharpe']:.2f}",
            f"- Full MaxDD: {w['full_maxdd']:.2%} vs native {meta['benchmark']['maxdd']:.2%}",
            f"- OOS excess: {w['oos_excess']:.2%}; stress-cost excess: {w['stress_excess']:.2%}",
            f"- OOS gate: {'PASS' if w['oos_pass'] else 'FAIL'}; current state: **{w['current_state']}**", "",
        ]
    pd.DataFrame(summary_rows).to_csv(OUT / "optimised_summary.csv", index=False)
    (OUT / "optimised_summary.md").write_text("\n".join(report))
    print("\n".join(report))


if __name__ == "__main__":
    main()
