from __future__ import annotations

import hashlib
import json
import math
import os
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DAYS = 252
HYST = 0.0001
START_CAPITAL = 10_000.0
START_DATE = "2005-01-01"
END_DATE = "2026-07-22"
OUT = Path("research_outputs/index_mags_trend_hybrid_20260722")
OUT.mkdir(parents=True, exist_ok=True)
INPUT_DIR = OUT / "inputs"
INPUT_DIR.mkdir(parents=True, exist_ok=True)
ASSETS = ["SPY", "QQQ", "SOXX", "SMH", "MAGS7", "MAGS10"]
MEMBERS = {
    "MAGS7": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA"],
    "MAGS10": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "AMD", "PLTR"],
}
REQUIRED = sorted({"SPY", "QQQ", "SOXX", "SMH", "BIL", "QQEW", *MEMBERS["MAGS10"]})
COST_BPS = {"SPY": 4, "QQQ": 5, "SOXX": 8, "SMH": 7, "MAGS7": 10, "MAGS10": 12}
DEV_END = {
    "SPY": "2021-12-31", "QQQ": "2021-12-31", "SOXX": "2021-12-31",
    "SMH": "2021-12-31", "MAGS7": "2021-12-31", "MAGS10": "2024-09-09",
}


def clean_frame(raw: pd.DataFrame, ticker: str) -> pd.DataFrame | None:
    if raw is None or raw.empty:
        return None
    frame = raw.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        if ticker in frame.columns.get_level_values(0): frame = frame[ticker].copy()
        elif ticker in frame.columns.get_level_values(1): frame = frame.xs(ticker, axis=1, level=1).copy()
        else: return None
    frame.columns = [str(column).title() for column in frame.columns]
    needed = ["Open", "High", "Low", "Close", "Volume"]
    if any(column not in frame.columns for column in needed): return None
    frame = frame[needed].apply(pd.to_numeric, errors="coerce").dropna(subset=["Open", "Close"])
    index = pd.to_datetime(frame.index)
    if getattr(index, "tz", None) is not None: index = index.tz_convert(None)
    frame.index = index.normalize()
    frame = frame[~frame.index.duplicated(keep="last")].sort_index()
    return None if len(frame) < 80 else frame


def frame_hash(frame: pd.DataFrame) -> str:
    canonical = frame.copy().round({"Open": 8, "High": 8, "Low": 8, "Close": 8, "Volume": 2})
    return hashlib.sha256(canonical.to_csv(date_format="%Y-%m-%d").encode()).hexdigest()


def download_ticker(ticker: str) -> pd.DataFrame:
    import yfinance as yf
    errors: list[str] = []
    for attempt in range(4):
        try:
            raw = yf.download(ticker, start=START_DATE, end=END_DATE, auto_adjust=True, actions=False, progress=False, threads=False)
            frame = clean_frame(raw, ticker)
            if frame is not None: return frame
            errors.append(f"attempt {attempt + 1}: empty/invalid")
        except Exception as exc:
            errors.append(f"attempt {attempt + 1}: {type(exc).__name__}: {exc}")
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{ticker}: {' | '.join(errors)}")


def quarterly_equal_weight_ohlc(data: dict[str, pd.DataFrame], members: list[str], name: str) -> pd.DataFrame:
    common = data[members[0]].index
    for member in members[1:]: common = common.intersection(data[member].index)
    common = common.sort_values()
    fields = {field: pd.concat({member: data[member][field].reindex(common) for member in members}, axis=1) for field in ["Open", "High", "Low", "Close", "Volume"]}
    previous_close = fields["Close"].shift(1)
    valid = previous_close.notna().all(axis=1) & fields["Close"].notna().all(axis=1)
    common = common[valid]
    for field in fields: fields[field] = fields[field].reindex(common)
    previous_close = fields["Close"].shift(1)
    output = pd.DataFrame(index=common, columns=["Open", "High", "Low", "Close", "Volume"], dtype=float)
    weights = np.full(len(members), 1.0 / len(members)); level = 100.0; previous_quarter = None
    for position, date in enumerate(common):
        quarter = (date.year, (date.month - 1) // 3 + 1)
        if position == 0:
            output.iloc[position] = [level, level, level, level, float(fields["Volume"].iloc[position].fillna(0).sum())]
            previous_quarter = quarter; continue
        if quarter != previous_quarter:
            weights = np.full(len(members), 1.0 / len(members)); previous_quarter = quarter
        prior = previous_close.iloc[position].to_numpy(dtype=float)
        ratios = {field: fields[field].iloc[position].to_numpy(dtype=float) / prior for field in ["Open", "High", "Low", "Close"]}
        if not np.isfinite(prior).all() or (prior <= 0).any() or not all(np.isfinite(values).all() for values in ratios.values()): continue
        open_ratio = float(np.dot(weights, ratios["Open"])); high_ratio = float(np.dot(weights, ratios["High"])); low_ratio = float(np.dot(weights, ratios["Low"])); close_ratio = float(np.dot(weights, ratios["Close"]))
        basket_open = level * open_ratio; basket_close = level * close_ratio
        output.iloc[position] = [basket_open, level * max(high_ratio, open_ratio, close_ratio), level * min(low_ratio, open_ratio, close_ratio), basket_close, float(fields["Volume"].iloc[position].fillna(0).sum())]
        drifted = weights * ratios["Close"]; weights = drifted / drifted.sum(); level = basket_close
    frame = output.dropna().copy()
    if len(frame) < 252: raise RuntimeError(f"{name}: synthetic frame too short ({len(frame)})")
    return frame


def load_data() -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    data = {}; manifest: dict[str, Any] = {"tickers": {}, "synthetic": {}}
    for ticker in REQUIRED:
        frame = download_ticker(ticker); data[ticker] = frame
        frame.to_csv(INPUT_DIR / f"{ticker}.csv.gz", compression="gzip")
        manifest["tickers"][ticker] = {"rows": len(frame), "start": str(frame.index.min().date()), "end": str(frame.index.max().date()), "sha256": frame_hash(frame), "last_close": float(frame.Close.iloc[-1])}
    for name, members in MEMBERS.items():
        frame = quarterly_equal_weight_ohlc(data, members, name); data[name] = frame
        frame.to_csv(INPUT_DIR / f"{name}.csv.gz", compression="gzip")
        manifest["synthetic"][name] = {"members": members, "method": "quarterly equal weight adjusted-OHLC approximation", "rows": len(frame), "start": str(frame.index.min().date()), "end": str(frame.index.max().date()), "sha256": frame_hash(frame), "last_close": float(frame.Close.iloc[-1])}
    aggregate = []
    for section in ["tickers", "synthetic"]: aggregate.extend(f"{ticker}:{manifest[section][ticker]['sha256']}" for ticker in sorted(manifest[section]))
    manifest["aggregate_sha256"] = hashlib.sha256(("\n".join(aggregate) + "\n").encode()).hexdigest()
    (OUT / "input_manifest.json").write_text(json.dumps(manifest, indent=2))
    return data, manifest


def rsi(close: pd.Series, n: int = 2) -> pd.Series:
    delta = close.diff(); gain = delta.clip(lower=0); loss = -delta.clip(upper=0)
    average_gain = gain.ewm(alpha=1 / n, adjust=False, min_periods=n).mean(); average_loss = loss.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = average_gain / average_loss.replace(0, np.nan); output = 100 - 100 / (1 + rs)
    output[(average_loss == 0) & (average_gain > 0)] = 100; output[(average_gain == 0) & (average_loss > 0)] = 0
    return output


def atr(frame: pd.DataFrame, n: int = 14) -> pd.Series:
    previous_close = frame.Close.shift(1)
    true_range = pd.concat([frame.High - frame.Low, (frame.High - previous_close).abs(), (frame.Low - previous_close).abs()], axis=1).max(axis=1)
    return true_range.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def open_returns(frame: pd.DataFrame) -> pd.Series: return frame.Open.shift(-1) / frame.Open - 1


def metrics(returns: pd.Series) -> dict[str, float]:
    values = returns.replace([np.inf, -np.inf], np.nan).dropna()
    if len(values) < 20: return {key: np.nan for key in ["cagr", "sharpe", "maxdd", "vol", "calmar", "terminal"]}
    equity = (1 + values).cumprod(); years = max((values.index[-1] - values.index[0]).days / 365.25, len(values) / DAYS)
    cagr = float(equity.iloc[-1] ** (1 / years) - 1); volatility = float(values.std(ddof=1) * math.sqrt(DAYS)); sharpe = float(values.mean() * DAYS / volatility) if volatility > 0 else np.nan
    drawdown = equity / equity.cummax() - 1; maxdd = float(drawdown.min())
    return {"cagr": cagr, "sharpe": sharpe, "maxdd": maxdd, "vol": volatility, "calmar": cagr / abs(maxdd) if maxdd < 0 else np.nan, "terminal": float(START_CAPITAL * equity.iloc[-1])}


def returns_from_exposure(frame: pd.DataFrame, cash: pd.DataFrame, exposure: pd.Series, cost_bps: float) -> tuple[pd.Series, pd.Series]:
    index = frame.index; asset_return = open_returns(frame); cash_return = open_returns(cash).reindex(index).fillna(0)
    held = exposure.reindex(index).shift(1).fillna(float(exposure.iloc[0])).astype(float)
    returns = held * asset_return + (1 - held) * cash_return; turnover = held.diff().abs().fillna(0); returns -= turnover * cost_bps / 10_000.0
    return returns.iloc[:-1], held.iloc[:-1]


def hysteresis_state(condition_up: pd.Series, condition_down: pd.Series) -> pd.Series:
    active = False; output = []
    for up, down in zip(condition_up.fillna(False), condition_down.fillna(False)):
        if active and bool(down): active = False
        elif not active and bool(up): active = True
        output.append(active)
    return pd.Series(output, index=condition_up.index, dtype=bool)


def trend_signals(frame: pd.DataFrame) -> dict[str, pd.Series]:
    close = frame.Close; output = {}
    for window in [100, 150, 200, 250]:
        moving_average = close.rolling(window).mean(); output[f"price_sma{window}"] = hysteresis_state(close > moving_average * (1 + HYST), close < moving_average * (1 - HYST))
    for short, long in [(50, 200), (100, 200)]:
        short_average = close.rolling(short).mean(); long_average = close.rolling(long).mean(); output[f"dual_{short}_{long}"] = hysteresis_state(short_average > long_average * (1 + HYST), short_average < long_average * (1 - HYST))
    momentum = close / close.shift(252) - 1; output["tsmom252"] = hysteresis_state(momentum > 0.01, momentum < -0.01)
    majority = pd.concat([close > close.rolling(200).mean(), close.rolling(50).mean() > close.rolling(200).mean(), momentum > 0], axis=1).sum(axis=1) >= 2
    output["composite_200"] = hysteresis_state(majority, ~majority)
    slow_majority = pd.concat([close > close.rolling(150).mean(), close > close.rolling(250).mean(), momentum > 0], axis=1).sum(axis=1) >= 2
    output["composite_slow"] = hysteresis_state(slow_majority, ~slow_majority)
    return output


def managed_state(entry: pd.Series, exit_signal: pd.Series, frame: pd.DataFrame, stop: str = "none", max_hold: int = 0) -> pd.Series:
    index = frame.index; entries = entry.reindex(index).fillna(False).to_numpy(bool); exits = exit_signal.reindex(index).fillna(False).to_numpy(bool)
    opens = frame.Open.to_numpy(float); highs = frame.High.to_numpy(float); closes = frame.Close.to_numpy(float); atr_values = atr(frame, 14).to_numpy(float)
    state = np.zeros(len(index), dtype=bool); active = False; pending = False; age = 0; high_water = np.nan
    for position in range(len(index)):
        exited = False
        if active:
            if pending: high_water = max(opens[position], highs[position]); pending = False; age = 1
            else: high_water = max(high_water, highs[position]) if np.isfinite(high_water) else highs[position]; age += 1
            stop_hit = False
            if stop == "atr3" and np.isfinite(high_water) and np.isfinite(atr_values[position]): stop_hit = closes[position] < high_water - 3.0 * atr_values[position]
            elif stop == "atr4" and np.isfinite(high_water) and np.isfinite(atr_values[position]): stop_hit = closes[position] < high_water - 4.0 * atr_values[position]
            if exits[position] or stop_hit or (max_hold > 0 and age >= max_hold): active = False; pending = False; age = 0; exited = True
        if not active and not exited and entries[position]: active = True; pending = True; age = 0
        state[position] = active
    return pd.Series(state, index=index, dtype=bool)


def frozen_pullback_addon(symbol: str, frame: pd.DataFrame, data: dict[str, pd.DataFrame]) -> pd.Series:
    close = frame.Close; rsi2 = rsi(close, 2)
    if symbol == "SOXX":
        sma200 = close.rolling(200).mean(); zscore = (close - close.rolling(20).mean()) / close.rolling(20).std(ddof=1); rv20 = close.pct_change().rolling(20).std(ddof=1) * math.sqrt(DAYS); rv100 = close.pct_change().rolling(100).std(ddof=1) * math.sqrt(DAYS)
        entry_one = (close > sma200 * (1 + HYST)) & (rsi2 < 5) & (zscore < -1.0) & (rv20 < 1.20 * rv100)
        state_one = managed_state(entry_one, pd.Series(False, index=close.index), frame, stop="atr3", max_hold=30)
        sma100 = close.rolling(100).mean(); sma20 = close.rolling(20).mean()
        entry_two = (close > sma100 * (1 + HYST)) & (sma100 > sma100.shift(20) * (1 + HYST)) & (rsi2.rolling(5).min() < 5) & (close > sma20 * (1 + HYST)) & (close.shift(1) <= sma20.shift(1) * (1 + HYST))
        state_two = managed_state(entry_two, pd.Series(False, index=close.index), frame, max_hold=30)
        return 0.25 * state_one.astype(float) + 0.25 * state_two.astype(float)
    if symbol == "SMH":
        sma100 = close.rolling(100).mean(); sma20 = close.rolling(20).mean(); drawdown63 = close / close.rolling(63).max() - 1; rv20 = close.pct_change().rolling(20).std(ddof=1) * math.sqrt(DAYS); rv100 = close.pct_change().rolling(100).std(ddof=1) * math.sqrt(DAYS)
        entry = (close > sma100 * (1 + HYST)) & (drawdown63.rolling(10).min() <= -0.10) & (close > sma20 * (1 + HYST)) & (close.shift(1) <= sma20.shift(1) * (1 + HYST)) & (rv20 < 1.20 * rv100)
        return 0.5 * managed_state(entry, pd.Series(False, index=close.index), frame, max_hold=40).astype(float)
    if symbol == "MAGS7":
        sma200 = close.rolling(200).mean(); sma10 = close.rolling(10).mean(); sma50 = close.rolling(50).mean(); qqq_equal = data["QQEW"].Close.reindex(close.index); qqq = data["QQQ"].Close.reindex(close.index); breadth = qqq_equal / qqq
        entry = (close > sma200 * (1 + HYST)) & (sma200 > sma200.shift(10) * (1 + HYST)) & (rsi2.rolling(3).min() < 20) & (close > sma10 * (1 + HYST)) & (close.shift(1) <= sma10.shift(1) * (1 + HYST)) & (breadth > breadth.rolling(50).mean() * (1 + HYST))
        rv20 = close.pct_change().rolling(20).std(ddof=1) * math.sqrt(DAYS); rv100 = close.pct_change().rolling(100).std(ddof=1) * math.sqrt(DAYS); exit_signal = (rv20 > 1.5 * rv100) | (close < sma50 * (1 - HYST))
        return 0.5 * managed_state(entry, exit_signal, frame, stop="atr4").astype(float)
    return pd.Series(0.0, index=frame.index)


def select_trend(symbol: str, frame: pd.DataFrame, cash: pd.DataFrame):
    candidates = trend_signals(frame); dev_end = pd.Timestamp(DEV_END[symbol]); benchmark_returns, _ = returns_from_exposure(frame, cash, pd.Series(1.0, index=frame.index), COST_BPS[symbol]); benchmark = metrics(benchmark_returns.loc[:dev_end])
    development_index = frame.index[frame.index <= dev_end]; valid = development_index[development_index >= frame.index[min(300, len(frame) - 1)]]; first_cut = valid[int(len(valid) * 0.33)]; second_cut = valid[int(len(valid) * 0.66)]; blocks = [(valid.min(), first_cut - pd.Timedelta(days=1)), (first_cut, second_cut - pd.Timedelta(days=1)), (second_cut, valid.max())]
    rows = []
    for name, state in candidates.items():
        for off_exposure in [0.0, 0.5]:
            exposure = pd.Series(np.where(state, 1.0, off_exposure), index=frame.index, dtype=float); returns, _ = returns_from_exposure(frame, cash, exposure, COST_BPS[symbol]); result = metrics(returns.loc[:dev_end]); changes = int((exposure.diff().abs() > 1e-9).sum())
            block_deltas = []
            for start, end in blocks:
                strategy_block = metrics(returns.loc[start:end]); benchmark_block = metrics(benchmark_returns.loc[start:end]); block_deltas.append([strategy_block["cagr"] - benchmark_block["cagr"], strategy_block["sharpe"] - benchmark_block["sharpe"], strategy_block["maxdd"] - benchmark_block["maxdd"]])
            array = np.asarray(block_deltas, dtype=float); good_blocks = int(((array[:, 1] >= -0.05) & (array[:, 2] >= -0.03)).sum())
            eligible = bool(result["cagr"] >= benchmark["cagr"] - 0.03 and result["sharpe"] >= benchmark["sharpe"] - 0.02 and good_blocks >= 2 and changes >= 4)
            quality = (result["sharpe"] - benchmark["sharpe"]) + 0.35 * (result["calmar"] - benchmark["calmar"]) + 0.25 * (result["cagr"] - benchmark["cagr"]) + 0.15 * float(np.mean(array[:, 1])) + 0.10 * float(np.mean(array[:, 2]))
            rows.append({"symbol": symbol, "trend": name, "off_exposure": off_exposure, "eligible": eligible, "quality": round(float(quality), 8), "changes": changes, "good_blocks": good_blocks, **result, "benchmark_cagr": benchmark["cagr"], "benchmark_sharpe": benchmark["sharpe"], "benchmark_maxdd": benchmark["maxdd"]})
    grid = pd.DataFrame(rows).sort_values(["eligible", "quality", "trend", "off_exposure"], ascending=[False, False, True, False]).reset_index(drop=True); winner = grid.iloc[0]
    return candidates[str(winner.trend)], grid, str(winner.trend), float(winner.off_exposure)


def trailing_start(index: pd.DatetimeIndex, years: int) -> pd.Timestamp:
    values = index[index >= index.max() - pd.DateOffset(years=years)]; return values.min()


def markdown_table(frame: pd.DataFrame) -> str:
    table = frame.copy(); table.index = table.index.astype(str); columns = [str(column) for column in table.columns]
    lines = ["| symbol | " + " | ".join(columns) + " |", "|---|" + "---:|" * len(columns)]
    for index, row in table.iterrows(): lines.append(f"| {index} | " + " | ".join("" if pd.isna(value) else f"{float(value):.0f}" for value in row) + " |")
    return "\n".join(lines)


def main() -> None:
    data, manifest = load_data(); summary_rows = []; window_rows = []; grids = []; identities = []
    for symbol in ASSETS:
        frame = data[symbol]; trend_state, grid, trend_rule, off_exposure = select_trend(symbol, frame, data["BIL"]); grids.append(grid); pullback_addon = frozen_pullback_addon(symbol, frame, data)
        exposures = {"Buy & Hold": pd.Series(1.0, index=frame.index), "Trend-only": pd.Series(np.where(trend_state, 1.0, off_exposure), index=frame.index, dtype=float), "Pullback-only": 1.0 + pullback_addon}
        exposures["Hybrid"] = exposures["Trend-only"] + pullback_addon.where(trend_state, 0.0)
        for strategy, exposure in exposures.items():
            returns, _ = returns_from_exposure(frame, data["BIL"], exposure, COST_BPS[symbol]); result = metrics(returns)
            summary_rows.append({"symbol": symbol, "strategy": strategy, "trend_rule": trend_rule if strategy in {"Trend-only", "Hybrid"} else "", "off_exposure": off_exposure if strategy in {"Trend-only", "Hybrid"} else np.nan, "changes": int((exposure.diff().abs() > 1e-9).sum()), "average_exposure": float(exposure.mean()), "current_exposure": float(exposure.iloc[-1]), **result})
            for label, years in [("1Y", 1), ("3Y", 3), ("5Y", 5), ("10Y", 10)]:
                if (returns.index.max() - returns.index.min()).days < years * 365 * 0.95: continue
                start = trailing_start(returns.index, years); period = metrics(returns.loc[start:]); window_rows.append({"symbol": symbol, "strategy": strategy, "window": label, "start": str(start.date()), "end": str(returns.index.max().date()), **period})
            window_rows.append({"symbol": symbol, "strategy": strategy, "window": "MAX", "start": str(returns.index.min().date()), "end": str(returns.index.max().date()), **result})
        identities.append({"symbol": symbol, "trend_rule": trend_rule, "off_exposure": off_exposure, "pullback_available": bool(float(pullback_addon.max()) > 0), "current_trend_on": bool(trend_state.iloc[-1]), "current_pullback_addon": float(pullback_addon.iloc[-1]), "current_hybrid_exposure": float(exposures["Hybrid"].iloc[-1])})
    summary = pd.DataFrame(summary_rows); windows = pd.DataFrame(window_rows); grid = pd.concat(grids, ignore_index=True); identity_frame = pd.DataFrame(identities).sort_values("symbol")
    summary.to_csv(OUT / "strategy_summary.csv", index=False, float_format="%.8f"); windows.to_csv(OUT / "window_comparison.csv", index=False, float_format="%.8f"); grid.to_csv(OUT / "trend_candidate_grid.csv", index=False, float_format="%.8f"); identity_frame.to_csv(OUT / "strategy_identity.csv", index=False, float_format="%.8f")
    identity_sha = hashlib.sha256(identity_frame.to_csv(index=False, float_format="%.8f").encode()).hexdigest(); manifest.update({"version": "trend-hybrid-v1", "capital": START_CAPITAL, "strategies": ["Buy & Hold", "Trend-only", "Pullback-only", "Hybrid"], "identity_sha256": identity_sha, "completed_close_cutoff": "2026-07-21"}); (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2))
    lines = ["# Index + MAGS trend and pullback hybrid", "", f"Capital: US${START_CAPITAL:,.0f}. Completed-close data through 2026-07-21; next-open execution.", f"Strategy identity SHA-256: `{identity_sha}`.", "", "## Selected trend rules", ""]
    for row in identity_frame.itertuples(): lines.append(f"- {row.symbol}: `{row.trend_rule}`, risk-off {row.off_exposure:.1f}x; current hybrid {row.current_hybrid_exposure:.2f}x")
    lines += ["", "## US$10,000 terminal values", ""]
    for window in ["1Y", "3Y", "5Y", "10Y", "MAX"]:
        view = windows[windows.window == window]
        if not view.empty: lines += [f"### {window}", "", markdown_table(view.pivot(index="symbol", columns="strategy", values="terminal").round(0)), ""]
    (OUT / "report.md").write_text("\n".join(lines)); print("\n".join(lines))


if __name__ == "__main__": main()
