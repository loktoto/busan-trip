from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "results"
INPUTS = HERE / "inputs"
OUT = HERE / "results"
OUT.mkdir(parents=True, exist_ok=True)

TRADING_DAYS = 252
OOS_START = pd.Timestamp("2013-01-01")
DEVELOPMENT_END = pd.Timestamp("2012-12-31")
BASE_COST_BPS = 9.0
PRODUCTS = {
    "USD_2X": {"ticker": "USD", "multiple": 2.0, "cost_bps": 25.0},
    "SOXL_3X": {"ticker": "SOXL", "multiple": 3.0, "cost_bps": 18.0},
}
BLOCKS = {
    "2013_2015": ("2013-01-01", "2015-12-31"),
    "2016_2020": ("2016-01-01", "2020-12-31"),
    "2021_2023": ("2021-01-01", "2023-12-31"),
    "2024_2026": ("2024-01-01", "2026-12-31"),
}


def load_equity(ticker: str) -> pd.DataFrame:
    path = SOURCE / f"input_{ticker}_adjusted_ohlc.csv"
    frame = pd.read_csv(path, index_col="Date", parse_dates=True)
    frame.index = pd.to_datetime(frame.index).normalize()
    frame.columns = [str(column).title() for column in frame.columns]
    return frame.sort_index()


def load_crypto() -> pd.DataFrame:
    spot = pd.read_csv(INPUTS / "binance_btcusdt_daily.csv", index_col="date", parse_dates=True)
    funding = pd.read_csv(
        INPUTS / "binance_btcusdt_funding_daily.csv", index_col="date", parse_dates=True
    )
    spot.index = pd.to_datetime(spot.index).normalize()
    funding.index = pd.to_datetime(funding.index).normalize()
    spot.columns = [str(column).lower() for column in spot.columns]
    funding.columns = [str(column).lower() for column in funding.columns]
    crypto = spot.join(funding[["mean_funding"]], how="left")
    crypto["btc_sma100"] = crypto["close"].rolling(100).mean()
    crypto["btc_sma200"] = crypto["close"].rolling(200).mean()
    crypto["btc_high63"] = crypto["close"].shift(1).rolling(63).max()
    crypto["funding_7d"] = crypto["mean_funding"].rolling(7, min_periods=4).mean()
    crypto["funding_expanding_p90"] = (
        crypto["funding_7d"].expanding(min_periods=90).quantile(0.90).shift(1)
    )
    # A UTC crypto bar dated t is not fully known at the US close on date t.
    # Shift one full calendar day before joining to US equity sessions.
    return crypto.shift(1)


def rsi(close: pd.Series, lookback: int = 2) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    avg_up = up.ewm(alpha=1 / lookback, adjust=False, min_periods=lookback).mean()
    avg_down = down.ewm(alpha=1 / lookback, adjust=False, min_periods=lookback).mean()
    ratio = avg_up / avg_down.replace(0, np.nan)
    value = 100 - 100 / (1 + ratio)
    return value.where(avg_down != 0, 100).where(avg_up != 0, 0)


def signal_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=frame.index)
    out["close"] = frame["Close"]
    out["rsi2"] = rsi(frame["Close"], 2)
    out["sma50"] = frame["Close"].rolling(50).mean()
    out["sma200"] = frame["Close"].rolling(200).mean()
    for length in (5, 10, 15):
        out[f"sma{length}"] = frame["Close"].rolling(length).mean()
    out["rv40"] = frame["Close"].pct_change().rolling(40).std(ddof=1) * math.sqrt(
        TRADING_DAYS
    )
    return out


def latched_pullback_state(
    features: pd.DataFrame, rsi_low: int, reclaim: int, hold: int, stop: float | None
) -> pd.Series:
    trend = features["sma50"] > features["sma200"]
    reclaim_cross = (features["close"] > features[f"sma{reclaim}"]) & (
        features["close"].shift(1) <= features[f"sma{reclaim}"].shift(1)
    )
    trigger = trend & (features["rsi2"].rolling(5).min() < rsi_low) & reclaim_cross
    closes = features["close"].to_numpy(float)
    triggers = trigger.fillna(False).to_numpy(bool)
    states = np.zeros(len(features), dtype=float)
    active = False
    armed = True
    days = 0
    peak = np.nan
    for idx, (price, fire) in enumerate(zip(closes, triggers)):
        if not fire:
            armed = True
        if not active and armed and fire and np.isfinite(price):
            active = True
            armed = False
            days = 0
            peak = price
        if active:
            peak = max(peak, price)
            stopped = stop is not None and price < peak * (1 - stop)
            expired = days >= hold
            if stopped or expired:
                active = False
                states[idx] = 0.0
            else:
                states[idx] = 1.0
                days += 1
    return pd.Series(states, index=features.index)


def candidate_states(features: pd.DataFrame) -> dict[str, pd.Series]:
    states: dict[str, pd.Series] = {}
    for rsi_low, reclaim, hold, stop in itertools.product(
        (5, 7, 10), (5, 10, 15), (30, 40, 50), (None, 0.12, 0.16)
    ):
        suffix = "NONE" if stop is None else str(int(stop * 100))
        name = f"SOXX_RSI{rsi_low}_R{reclaim}_H{hold}_LSTOP{suffix}"
        states[name] = latched_pullback_state(
            features, rsi_low=rsi_low, reclaim=reclaim, hold=hold, stop=stop
        )
    return states


def open_to_open(frame: pd.DataFrame) -> pd.Series:
    return frame["Open"].shift(-1).div(frame["Open"]).sub(1)


def signal_level_returns(
    soxx: pd.DataFrame, state: pd.Series, cost_multiplier: float = 1.0
) -> tuple[pd.Series, pd.Series]:
    exposure = 1.0 + 0.5 * state.reindex(soxx.index).ffill().fillna(0.0)
    held = exposure.shift(1).fillna(1.0)
    turnover = held.diff().abs().fillna(0.0)
    returns = held * open_to_open(soxx) - turnover * BASE_COST_BPS * cost_multiplier / 10_000
    returns = returns.iloc[:-1].dropna()
    return returns, held.reindex(returns.index)


def actual_product_returns(
    soxx: pd.DataFrame,
    product: pd.DataFrame,
    state: pd.Series,
    multiple: float,
    product_cost_bps: float,
    cost_multiplier: float = 1.0,
) -> tuple[pd.Series, pd.DataFrame]:
    common = soxx.index.intersection(product.index).intersection(state.index)
    base_return = open_to_open(soxx).reindex(common)
    leveraged_return = open_to_open(product).reindex(common)
    target_exposure = 1.0 + 0.5 * state.reindex(common).ffill().fillna(0.0)
    leveraged_weight = (target_exposure - 1.0) / (multiple - 1.0)
    base_weight = 1.0 - leveraged_weight
    held_base = base_weight.shift(1).fillna(1.0)
    held_leveraged = leveraged_weight.shift(1).fillna(0.0)
    cost = (
        held_base.diff().abs().fillna(0.0) * BASE_COST_BPS
        + held_leveraged.diff().abs().fillna(0.0) * product_cost_bps
    ) * cost_multiplier / 10_000
    returns = held_base * base_return + held_leveraged * leveraged_return - cost
    returns = returns.iloc[:-1].dropna()
    weights = pd.DataFrame(
        {
            "signal_state": state.reindex(common).ffill().fillna(0.0),
            "target_exposure": target_exposure,
            "held_base": held_base,
            "held_leveraged": held_leveraged,
            "cost": cost,
        }
    ).reindex(returns.index)
    return returns, weights


def static_production_proxy(soxx: pd.DataFrame, features: pd.DataFrame) -> pd.Series:
    trend = features["sma50"] > features["sma200"]
    raw = (0.40 / features["rv40"]).clip(0.50, 1.50).where(trend, 0.50)
    return raw.ewm(span=5, adjust=False).mean().reindex(soxx.index)


def proxy_returns(soxx: pd.DataFrame, exposure: pd.Series) -> pd.Series:
    held = exposure.shift(1).fillna(1.0)
    turnover = held.diff().abs().fillna(0.0)
    returns = held * open_to_open(soxx) - turnover * BASE_COST_BPS / 10_000
    return returns.iloc[:-1].dropna()


def metrics(returns: pd.Series) -> dict[str, float]:
    values = returns.replace([np.inf, -np.inf], np.nan).dropna()
    if len(values) < 100:
        return {}
    equity = (1 + values).cumprod()
    years = len(values) / TRADING_DAYS
    cagr = equity.iloc[-1] ** (1 / years) - 1
    volatility = values.std(ddof=1) * math.sqrt(TRADING_DAYS)
    sharpe = values.mean() / values.std(ddof=1) * math.sqrt(TRADING_DAYS)
    drawdown = equity / equity.cummax() - 1
    return {
        "cagr": float(cagr),
        "sharpe": float(sharpe),
        "volatility": float(volatility),
        "maxdd": float(drawdown.min()),
        "terminal": float(equity.iloc[-1]),
        "skew": float(values.skew()),
        "kurtosis": float(values.kurt() + 3),
    }


def markdown_table(frame: pd.DataFrame, digits: int = 4) -> str:
    def render(value: object) -> str:
        if isinstance(value, (float, np.floating)):
            return "" if not np.isfinite(value) else f"{float(value):.{digits}f}"
        return str(value)

    columns = [str(column) for column in frame.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(render(value) for value in row) + " |")
    return "\n".join(lines)


def comparison(strategy: pd.Series, benchmark: pd.Series) -> dict[str, float]:
    common = strategy.index.intersection(benchmark.index)
    strategy = strategy.reindex(common).dropna()
    benchmark = benchmark.reindex(strategy.index).dropna()
    strategy = strategy.reindex(benchmark.index)
    sm, bm = metrics(strategy), metrics(benchmark)
    return {
        "start": str(common.min().date()),
        "end": str(common.max().date()),
        "cagr": sm["cagr"],
        "benchmark_cagr": bm["cagr"],
        "cagr_delta": sm["cagr"] - bm["cagr"],
        "sharpe": sm["sharpe"],
        "benchmark_sharpe": bm["sharpe"],
        "sharpe_delta": sm["sharpe"] - bm["sharpe"],
        "maxdd": sm["maxdd"],
        "benchmark_maxdd": bm["maxdd"],
        "maxdd_improvement": sm["maxdd"] - bm["maxdd"],
        "terminal": sm["terminal"],
        "benchmark_terminal": bm["terminal"],
    }


def selection_score(strategy: pd.Series, benchmark: pd.Series) -> tuple[float, dict[str, float]]:
    result = comparison(strategy, benchmark)
    score = (
        3.0 * result["cagr_delta"]
        + 0.75 * result["sharpe_delta"]
        + 1.5 * result["maxdd_improvement"]
    )
    if result["cagr_delta"] <= 0:
        score -= 1.0
    if result["maxdd_improvement"] < -0.03:
        score -= 1.0
    return float(score), result


def moving_block_probability(
    excess: pd.Series, block: int = 20, repetitions: int = 2000
) -> float:
    values = excess.dropna().to_numpy(float)
    if len(values) < block * 4:
        return np.nan
    rng = np.random.default_rng(20260723)
    possible = np.arange(0, len(values) - block + 1)
    positive = 0
    required = math.ceil(len(values) / block)
    for _ in range(repetitions):
        starts = rng.choice(possible, size=required, replace=True)
        sample = np.concatenate([values[start : start + block] for start in starts])[: len(values)]
        positive += float(sample.mean() > 0)
    return positive / repetitions


def dsr_probability(excess: pd.Series, trials: int) -> float:
    values = excess.dropna()
    result = metrics(values)
    if not result:
        return np.nan
    years = max(len(values) / TRADING_DAYS, (values.index[-1] - values.index[0]).days / 365.25)
    sr = result["sharpe"]
    expected_max = math.sqrt(max(0.0, 2 * math.log(max(2, trials)))) / math.sqrt(years)
    denominator = math.sqrt(
        max(
            1e-9,
            1
            - result["skew"] * sr
            + ((result["kurtosis"] - 1) / 4) * sr * sr,
        )
    )
    z_score = (sr - expected_max) * math.sqrt(years) / denominator
    return float(norm.cdf(z_score))


def cscv_pbo(candidate_returns: pd.DataFrame, partitions: int = 8) -> float:
    clean = candidate_returns.dropna(how="all")
    blocks = np.array_split(np.arange(len(clean)), partitions)
    below_median = 0
    observations = 0
    all_blocks = range(partitions)
    for train_ids in itertools.combinations(all_blocks, partitions // 2):
        test_ids = tuple(block for block in all_blocks if block not in train_ids)
        train_rows = np.concatenate([blocks[block] for block in train_ids])
        test_rows = np.concatenate([blocks[block] for block in test_ids])
        train = clean.iloc[train_rows]
        test = clean.iloc[test_rows]
        train_score = train.mean() / train.std(ddof=1)
        selected = train_score.replace([np.inf, -np.inf], np.nan).idxmax()
        test_score = test.mean() / test.std(ddof=1)
        rank_pct = test_score.rank(pct=True).get(selected, np.nan)
        if np.isfinite(rank_pct):
            below_median += float(rank_pct <= 0.5)
            observations += 1
    return below_median / observations if observations else np.nan


def rolling_comparisons(
    strategy: pd.Series, benchmark: pd.Series, years: int
) -> pd.DataFrame:
    common = strategy.index.intersection(benchmark.index)
    start = common.min()
    end = common.max()
    rows: list[dict] = []
    while start + pd.DateOffset(years=years) <= end:
        stop = start + pd.DateOffset(years=years)
        mask = (common >= start) & (common <= stop)
        selected = common[mask]
        result = comparison(strategy.reindex(selected), benchmark.reindex(selected))
        rows.append({"years": years, **result})
        start += pd.DateOffset(months=3)
    return pd.DataFrame(rows)


def cross_asset_layers(
    state: pd.Series, equity_index: pd.DatetimeIndex, crypto: pd.DataFrame
) -> dict[str, pd.Series]:
    aligned = crypto.reindex(equity_index, method="ffill")
    layers = {
        "NO_CRYPTO_LAYER": pd.Series(True, index=equity_index),
        "BTC_ABOVE_SMA100": aligned["close"] > aligned["btc_sma100"],
        "BTC_ABOVE_SMA200": aligned["close"] > aligned["btc_sma200"],
        "BTC_NOT_IN_20PCT_63D_CRASH": aligned["close"] >= 0.80 * aligned["btc_high63"],
        "BTC_TREND_AND_FUNDING_NOT_EXTREME": (
            (aligned["close"] > aligned["btc_sma100"])
            & (
                aligned["funding_expanding_p90"].isna()
                | (aligned["funding_7d"] <= aligned["funding_expanding_p90"])
            )
        ),
    }
    return {
        name: state.reindex(equity_index).fillna(0.0) * allowed.fillna(False).astype(float)
        for name, allowed in layers.items()
    }


def main() -> None:
    soxx = load_equity("SOXX")
    smh = load_equity("SMH")
    product_data = {spec["ticker"]: load_equity(spec["ticker"]) for spec in PRODUCTS.values()}
    features = signal_features(soxx)
    states = candidate_states(features)
    signal_benchmark = open_to_open(soxx).iloc[:-1].dropna()

    development_rows: list[dict] = []
    signal_oos_returns: dict[str, pd.Series] = {}
    for name, state in states.items():
        returns, held = signal_level_returns(soxx, state)
        development = returns.loc[:DEVELOPMENT_END]
        benchmark_development = signal_benchmark.reindex(development.index)
        score, result = selection_score(development, benchmark_development)
        development_rows.append(
            {
                "candidate": name,
                "selection_score": score,
                "development_exposure": float(held.reindex(development.index).mean()),
                **result,
            }
        )
        signal_oos_returns[name] = returns.loc[OOS_START:]
    development = pd.DataFrame(development_rows).sort_values(
        ["selection_score", "candidate"], ascending=[False, True]
    )
    development.to_csv(OUT / "development_ranking.csv", index=False, float_format="%.10f")
    frozen_name = str(development.iloc[0]["candidate"])
    frozen_state = states[frozen_name]

    oos_matrix = pd.concat(signal_oos_returns, axis=1)
    search_pbo = cscv_pbo(oos_matrix)

    benchmark_oos = signal_benchmark.loc[OOS_START:]
    frozen_signal = signal_oos_returns[frozen_name].reindex(benchmark_oos.index).dropna()
    frozen_signal_comparison = comparison(
        frozen_signal, benchmark_oos.reindex(frozen_signal.index)
    )

    production_exposure = static_production_proxy(soxx, features)
    production_proxy_return = proxy_returns(soxx, production_exposure).loc[OOS_START:]
    proxy_comparison = comparison(frozen_signal, production_proxy_return)

    route_rows: list[dict] = []
    block_rows: list[dict] = []
    rolling_rows: list[pd.DataFrame] = []
    route_returns: dict[str, pd.Series] = {}
    for route, spec in PRODUCTS.items():
        product = product_data[spec["ticker"]]
        actual, weights = actual_product_returns(
            soxx,
            product,
            frozen_state,
            multiple=spec["multiple"],
            product_cost_bps=spec["cost_bps"],
            cost_multiplier=1.0,
        )
        stressed, _ = actual_product_returns(
            soxx,
            product,
            frozen_state,
            multiple=spec["multiple"],
            product_cost_bps=spec["cost_bps"],
            cost_multiplier=3.0,
        )
        actual = actual.loc[OOS_START:]
        stressed = stressed.reindex(actual.index)
        benchmark = signal_benchmark.reindex(actual.index).dropna()
        actual = actual.reindex(benchmark.index)
        stressed = stressed.reindex(benchmark.index)
        result = comparison(actual, benchmark)
        stressed_result = comparison(stressed, benchmark)
        excess = actual - benchmark
        bootstrap = moving_block_probability(excess)
        dsr = dsr_probability(actual, len(states))
        route_rows.append(
            {
                "route": route,
                "frozen_candidate": frozen_name,
                "bootstrap_p_positive_excess": bootstrap,
                "dsr_vs_cash_probability": dsr,
                "search_pbo": search_pbo,
                "stress_3x_cost_cagr_delta": stressed_result["cagr_delta"],
                "average_target_exposure": float(
                    weights.reindex(actual.index)["target_exposure"].mean()
                ),
                "average_leveraged_weight": float(
                    weights.reindex(actual.index)["held_leveraged"].mean()
                ),
                **result,
            }
        )
        route_returns[route] = actual
        for block, (start, end) in BLOCKS.items():
            segment = actual.loc[start:end]
            segment_benchmark = benchmark.reindex(segment.index)
            if len(segment) >= 100:
                block_rows.append(
                    {"route": route, "block": block, **comparison(segment, segment_benchmark)}
                )
        for years in (3, 5, 10):
            rolling = rolling_comparisons(actual, benchmark, years)
            if not rolling.empty:
                rolling.insert(0, "route", route)
                rolling_rows.append(rolling)

    routes = pd.DataFrame(route_rows)
    blocks = pd.DataFrame(block_rows)
    rolling = pd.concat(rolling_rows, ignore_index=True)
    routes.to_csv(OUT / "frozen_actual_product_results.csv", index=False, float_format="%.10f")
    blocks.to_csv(OUT / "nonoverlap_blocks.csv", index=False, float_format="%.10f")
    rolling.to_csv(OUT / "rolling_windows.csv", index=False, float_format="%.10f")

    neighbour_rows: list[dict] = []
    for route, spec in PRODUCTS.items():
        product = product_data[spec["ticker"]]
        for name, state in states.items():
            actual, _ = actual_product_returns(
                soxx,
                product,
                state,
                multiple=spec["multiple"],
                product_cost_bps=spec["cost_bps"],
                cost_multiplier=1.0,
            )
            actual = actual.loc[OOS_START:]
            benchmark = signal_benchmark.reindex(actual.index).dropna()
            result = comparison(actual.reindex(benchmark.index), benchmark)
            neighbour_rows.append({"route": route, "candidate": name, **result})
    neighbours = pd.DataFrame(neighbour_rows)
    neighbours["all_three_pass"] = (
        (neighbours["cagr_delta"] > 0)
        & (neighbours["sharpe_delta"] >= 0)
        & (neighbours["maxdd_improvement"] >= 0)
    )
    neighbours.to_csv(OUT / "neighbour_stability.csv", index=False, float_format="%.10f")

    rolling_summary = (
        rolling.groupby(["route", "years"])
        .agg(
            windows=("cagr_delta", "size"),
            positive_cagr_rate=("cagr_delta", lambda x: float((x > 0).mean())),
            positive_sharpe_rate=("sharpe_delta", lambda x: float((x >= 0).mean())),
            nonworse_drawdown_rate=(
                "maxdd_improvement",
                lambda x: float((x >= 0).mean()),
            ),
            median_cagr_delta=("cagr_delta", "median"),
            worst_cagr_delta=("cagr_delta", "min"),
        )
        .reset_index()
    )
    rolling_full_gate = (
        rolling.assign(
            full_gate=(
                (rolling["cagr_delta"] > 0)
                & (rolling["sharpe_delta"] >= 0)
                & (rolling["maxdd_improvement"] >= -0.03)
            )
        )
        .groupby(["route", "years"])["full_gate"]
        .mean()
        .rename("full_gate_rate")
        .reset_index()
    )
    rolling_summary = rolling_summary.merge(
        rolling_full_gate, on=["route", "years"], how="left"
    )
    rolling_summary.to_csv(OUT / "rolling_summary.csv", index=False, float_format="%.10f")

    crypto = load_crypto()
    cross_rows: list[dict] = []
    cross_blocks: list[dict] = []
    layers = cross_asset_layers(frozen_state, soxx.index, crypto)
    for route, spec in PRODUCTS.items():
        product = product_data[spec["ticker"]]
        for layer_name, layered_state in layers.items():
            actual, _ = actual_product_returns(
                soxx,
                product,
                layered_state,
                multiple=spec["multiple"],
                product_cost_bps=spec["cost_bps"],
                cost_multiplier=1.0,
            )
            actual = actual.loc["2018-01-01":]
            benchmark = signal_benchmark.reindex(actual.index).dropna()
            actual = actual.reindex(benchmark.index)
            cross_rows.append(
                {"route": route, "layer": layer_name, **comparison(actual, benchmark)}
            )
            for block, (start, end) in {
                "2018_2020": ("2018-01-01", "2020-12-31"),
                "2021_2023": ("2021-01-01", "2023-12-31"),
                "2024_2026": ("2024-01-01", "2026-12-31"),
            }.items():
                segment = actual.loc[start:end]
                if len(segment) >= 100:
                    cross_blocks.append(
                        {
                            "route": route,
                            "layer": layer_name,
                            "block": block,
                            **comparison(segment, benchmark.reindex(segment.index)),
                        }
                    )
    cross = pd.DataFrame(cross_rows)
    cross_block_frame = pd.DataFrame(cross_blocks)
    cross.to_csv(OUT / "binance_ablation.csv", index=False, float_format="%.10f")
    cross_block_frame.to_csv(
        OUT / "binance_ablation_blocks.csv", index=False, float_format="%.10f"
    )

    route_gate_rows: list[dict] = []
    for row in routes.to_dict("records"):
        route = row["route"]
        route_blocks = blocks[blocks["route"] == route]
        rolling_3 = rolling_summary[
            (rolling_summary["route"] == route) & (rolling_summary["years"] == 3)
        ].iloc[0]
        rolling_5 = rolling_summary[
            (rolling_summary["route"] == route) & (rolling_summary["years"] == 5)
        ].iloc[0]
        neighbour_rate = float(
            neighbours[neighbours["route"] == route]["all_three_pass"].mean()
        )
        gates = {
            "oos_return": row["cagr_delta"] >= 0.005,
            "oos_sharpe": row["sharpe_delta"] >= 0,
            "oos_drawdown": row["maxdd_improvement"] >= -0.03,
            "cost_stress": row["stress_3x_cost_cagr_delta"] > 0,
            "bootstrap": row["bootstrap_p_positive_excess"] >= 0.80,
            "dsr": row["dsr_vs_cash_probability"] >= 0.80,
            "search_pbo": row["search_pbo"] <= 0.30,
            "blocks": int(
                (
                    (route_blocks["cagr_delta"] > 0)
                    & (route_blocks["sharpe_delta"] >= 0)
                    & (route_blocks["maxdd_improvement"] >= -0.03)
                ).sum()
            )
            >= 3,
            "rolling_3y": rolling_3["full_gate_rate"] >= 0.60,
            "rolling_5y": rolling_5["full_gate_rate"] >= 0.70,
            "neighbours": neighbour_rate >= 0.30,
        }
        route_gate_rows.append(
            {
                "route": route,
                "neighbour_all_three_pass_rate": neighbour_rate,
                **{f"gate_{name}": value for name, value in gates.items()},
                "all_gates_pass": all(gates.values()),
            }
        )
    gates = pd.DataFrame(route_gate_rows)
    gates.to_csv(OUT / "production_gate.csv", index=False)

    smh_soxx = pd.concat(
        [soxx["Close"].pct_change().rename("SOXX"), smh["Close"].pct_change().rename("SMH")],
        axis=1,
    ).loc["2013-01-01":]
    parity = {
        "daily_return_correlation": float(smh_soxx.corr().loc["SOXX", "SMH"]),
        "mean_absolute_daily_return_difference": float(
            (smh_soxx["SOXX"] - smh_soxx["SMH"]).abs().mean()
        ),
        "interpretation": "SMH is diagnostic only and does not generate a candidate or trade row.",
    }

    baseline_crypto = cross[cross["layer"] == "NO_CRYPTO_LAYER"].set_index("route")
    crypto_verdict_rows = []
    for route in PRODUCTS:
        baseline = baseline_crypto.loc[route]
        options = cross[(cross["route"] == route) & (cross["layer"] != "NO_CRYPTO_LAYER")]
        for row in options.to_dict("records"):
            block_option = cross_block_frame[
                (cross_block_frame["route"] == route)
                & (cross_block_frame["layer"] == row["layer"])
            ]
            block_base = cross_block_frame[
                (cross_block_frame["route"] == route)
                & (cross_block_frame["layer"] == "NO_CRYPTO_LAYER")
            ].set_index("block")
            improved_blocks = 0
            for block_row in block_option.to_dict("records"):
                base_row = block_base.loc[block_row["block"]]
                improved_blocks += int(
                    block_row["cagr"] > base_row["cagr"]
                    and block_row["sharpe"] >= base_row["sharpe"]
                    and block_row["maxdd"] >= base_row["maxdd"] - 0.03
                )
            pass_ablation = (
                row["cagr"] > baseline["cagr"]
                and row["sharpe"] >= baseline["sharpe"]
                and row["maxdd"] >= baseline["maxdd"] - 0.03
                and improved_blocks >= 2
            )
            crypto_verdict_rows.append(
                {
                    "route": route,
                    "layer": row["layer"],
                    "improved_nonoverlap_blocks": improved_blocks,
                    "ablation_pass": pass_ablation,
                }
            )
    crypto_verdict = pd.DataFrame(crypto_verdict_rows)
    crypto_verdict.to_csv(OUT / "binance_ablation_gate.csv", index=False)

    decision = (
        "PROMOTION_CANDIDATE_REQUIRES_INDEPENDENT_RERUN"
        if bool(gates["all_gates_pass"].any())
        else "REJECT_CHALLENGER_RETAIN_PRODUCTION"
    )
    metadata = {
        "calculation_date": "2026-07-23",
        "equity_cutoff": str(soxx.index.max().date()),
        "production_authority_unchanged": "main:production/leverage_signal.json",
        "candidate_scope": "SOXX-only signal; actual USD and SOXL product paths; no capital-allocation selection",
        "frozen_development_end": str(DEVELOPMENT_END.date()),
        "frozen_oos_start": str(OOS_START.date()),
        "candidate_count": len(states),
        "frozen_candidate": frozen_name,
        "search_pbo": search_pbo,
        "signal_level_oos": frozen_signal_comparison,
        "comparison_to_static_current_rule_proxy": proxy_comparison,
        "smh_reference_only": parity,
        "binance_open_interest": "forward shadow only; historical endpoint limited to latest 30 days",
        "decision": decision,
        "no_order_authority": True,
    }
    (OUT / "run_metadata.json").write_text(json.dumps(metadata, indent=2))

    route_display = routes[
        [
            "route",
            "cagr",
            "benchmark_cagr",
            "cagr_delta",
            "sharpe_delta",
            "maxdd_improvement",
            "stress_3x_cost_cagr_delta",
            "bootstrap_p_positive_excess",
            "dsr_vs_cash_probability",
            "search_pbo",
        ]
    ].copy()
    production_reference = json.loads((HERE / "production_reference.json").read_text())
    canonical_rows = []
    for row in routes.to_dict("records"):
        reference = production_reference["routes"][row["route"]]
        canonical_rows.append(
            {
                "route": row["route"],
                "challenger_cagr": row["cagr"],
                "production_cagr": reference["cagr"],
                "challenger_minus_production_cagr": row["cagr"] - reference["cagr"],
                "challenger_sharpe_delta": row["sharpe_delta"],
                "production_sharpe_delta": reference["sharpe_delta"],
                "challenger_maxdd_improvement": row["maxdd_improvement"],
                "production_maxdd_improvement": reference["maxdd_improvement"],
            }
        )
    canonical_display = pd.DataFrame(canonical_rows)
    proxy_display = pd.DataFrame(
        [
            {
                "comparison": "Frozen challenger vs static current-rule proxy",
                "cagr_delta": proxy_comparison["cagr_delta"],
                "sharpe_delta": proxy_comparison["sharpe_delta"],
                "maxdd_improvement": proxy_comparison["maxdd_improvement"],
            }
        ]
    )
    report = [
        "# Frozen SOXX leverage challenger — regime/pullback audit",
        "",
        f"**Equity cutoff:** {soxx.index.max().date()}  ",
        f"**Frozen development cutoff:** {DEVELOPMENT_END.date()}  ",
        f"**OOS start:** {OOS_START.date()}  ",
        f"**Decision:** `{decision}`",
        "",
        "## What was tested",
        "",
        "- Signal authority is SOXX only. SMH is retained as a diagnostic reference and cannot create a trade row.",
        "- 81 pre-registered RSI2 pullback/reclaim variants use a genuinely latched hold/stop state.",
        "- One signal was selected only on data through 2012-12-31, then frozen.",
        "- OOS validation uses actual adjusted USD and SOXL paths with next-open execution.",
        "- The overlay raises exposure from 1.0x to 1.5x only while the signal is active; capital allocation is not a selection variable.",
        "- Binance data is a separate lagged ablation. Open interest is forward-shadow only because long history is unavailable.",
        "",
        f"Frozen candidate: `{frozen_name}`",
        "",
        "## Actual-product OOS results versus SOXX Buy & Hold",
        "",
        markdown_table(route_display),
        "",
        "## Direct comparison with canonical production evidence",
        "",
        markdown_table(canonical_display),
        "",
        "The canonical figures come from `main:production/leverage_signal.json`; windows differ by one completed session, so this is a decision audit rather than a return-series splice.",
        "",
        "## Diagnostic comparison to the static current-rule formula",
        "",
        markdown_table(proxy_display),
        "",
        "The proxy applies the current 2026 formula unchanged over history. It is not the canonical annual-anchored production path.",
        "",
        "## Production gate",
        "",
        markdown_table(gates),
        "",
        "## Binance ablation gate",
        "",
        markdown_table(crypto_verdict),
        "",
        "## Interpretation",
        "",
        "- A candidate is not promoted because it looks good in aggregate. Every mandatory gate must pass.",
        "- The static current-rule proxy is only an implementation cross-check; the canonical anchored production evidence remains the manifest pinned on main.",
        "- No production file was changed and no order or order instruction was created.",
    ]
    (OUT / "REPORT.md").write_text("\n".join(report))
    print("\n".join(report))


if __name__ == "__main__":
    main()
