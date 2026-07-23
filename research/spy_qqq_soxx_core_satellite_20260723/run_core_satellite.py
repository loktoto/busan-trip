from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE_OUT = Path("research_outputs/spy_qqq_soxx_alpha_search_20260722")
OUT = Path("research_outputs/spy_qqq_soxx_core_satellite_20260723")
OUT.mkdir(parents=True, exist_ok=True)

OOS_START = pd.Timestamp("2013-01-01")
CAPITAL = 10_000.0
CORE_SPLIT = {"SPY": 0.5, "QQQ": 0.5}
SLEEVES = [0.10, 0.15, 0.20, 0.25, 0.30]
PRODUCTS = {
    "USD": {"multiple": 2.0, "cost_bps": 25.0},
    "SOXL": {"multiple": 3.0, "cost_bps": 18.0},
}
ASSET_COST_BPS = {"SPY": 4.0, "QQQ": 5.0, "SOXX": 9.0, "CASH": 2.0}
FAMILY_VARIANTS = [
    "raw_daily",
    "raw_band10",
    "volcap30_daily",
    "volcap30_band10",
    "corr_cap_daily",
    "corr_cap_band10",
]
TRIAL_FLOOR = len(PRODUCTS) * len(FAMILY_VARIANTS)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_input(name: str) -> pd.DataFrame:
    frame = pd.read_csv(BASE_OUT / "inputs" / f"{name}.csv.gz", index_col=0, parse_dates=True)
    frame.index = pd.to_datetime(frame.index).normalize()
    frame.columns = [str(column).title() for column in frame.columns]
    return frame.sort_index()


def common_index(frames: list[pd.DataFrame]) -> pd.DatetimeIndex:
    index = frames[0].index
    for frame in frames[1:]:
        index = index.intersection(frame.index)
    return index.sort_values()


def buy_hold_returns(asset_returns: pd.DataFrame, initial_weights: pd.Series) -> tuple[pd.Series, pd.DataFrame]:
    values = initial_weights.astype(float) * CAPITAL
    returns: list[float] = []
    weights: list[pd.Series] = []
    for date, row in asset_returns.iterrows():
        before = float(values.sum())
        values = values * (1.0 + row.fillna(0.0))
        after = float(values.sum())
        returns.append(after / before - 1.0 if before > 0 else 0.0)
        weights.append(values / after if after > 0 else initial_weights)
    return pd.Series(returns, index=asset_returns.index), pd.DataFrame(weights, index=asset_returns.index)


def matched_portfolio(
    returns: pd.DataFrame,
    target: pd.DataFrame,
    rebalance_signal: pd.Series,
    cost_bps: pd.Series,
    cost_multiplier: float = 1.0,
) -> tuple[pd.Series, pd.DataFrame, pd.Series]:
    columns = list(returns.columns)
    target = target.reindex(returns.index).ffill()[columns]
    desired = target.shift(1)
    rebalance = rebalance_signal.reindex(returns.index).fillna(False).shift(1).fillna(False)
    initial = target.iloc[0].astype(float)
    current = initial.copy()
    output_returns: list[float] = []
    output_weights: list[pd.Series] = []
    output_turnover: list[float] = []
    for position, date in enumerate(returns.index):
        if position == 0:
            trade_to = initial.copy()
        else:
            do_rebalance = bool(rebalance.loc[date]) and desired.loc[date].notna().all()
            trade_to = desired.loc[date].astype(float) if do_rebalance else current.copy()
        if abs(float(trade_to.sum()) - 1.0) > 1e-8:
            trade_to["CASH"] += 1.0 - float(trade_to.sum())
        changes = (trade_to - current).abs() if position > 0 else pd.Series(0.0, index=columns)
        cost = float((changes * cost_bps).sum()) * cost_multiplier / 10_000.0
        component = returns.loc[date].fillna(0.0)
        gross = float((trade_to * component).sum())
        net = gross - cost
        end_values = trade_to * (1.0 + component)
        total = float(end_values.sum())
        current = end_values / total if total != 0 else trade_to
        output_returns.append(net)
        output_weights.append(trade_to)
        output_turnover.append(float(changes.drop(labels=["CASH"], errors="ignore").sum()))
    return (
        pd.Series(output_returns, index=returns.index),
        pd.DataFrame(output_weights, index=returns.index),
        pd.Series(output_turnover, index=returns.index),
    )


def static_target(index: pd.DatetimeIndex, sleeve: float, product: str) -> pd.DataFrame:
    core = 1.0 - sleeve
    return pd.DataFrame(
        {
            "SPY": core * CORE_SPLIT["SPY"],
            "QQQ": core * CORE_SPLIT["QQQ"],
            "SOXX": sleeve,
            product: 0.0,
            "CASH": 0.0,
        },
        index=index,
    )


def product_target(
    index: pd.DatetimeIndex,
    exposure: pd.Series,
    sleeve: float,
    product: str,
    multiple: float,
) -> pd.DataFrame:
    e = exposure.reindex(index).ffill().fillna(1.0).clip(0.5, 1.5)
    core = 1.0 - sleeve
    result = pd.DataFrame(0.0, index=index, columns=["SPY", "QQQ", "SOXX", product, "CASH"])
    result["SPY"] = core * CORE_SPLIT["SPY"]
    result["QQQ"] = core * CORE_SPLIT["QQQ"]
    low = e <= 1.0
    result.loc[low, "SOXX"] = sleeve * e.loc[low]
    result.loc[low, "CASH"] = sleeve * (1.0 - e.loc[low])
    high = ~low
    leveraged_weight = sleeve * (e.loc[high] - 1.0) / (multiple - 1.0)
    result.loc[high, product] = leveraged_weight
    result.loc[high, "SOXX"] = sleeve - leveraged_weight
    result["CASH"] += 1.0 - result.sum(axis=1)
    return result


def apply_vol_cap(
    close_returns: pd.DataFrame,
    sleeve: float,
    exposure: pd.Series,
    target_vol: float = 0.30,
) -> pd.Series:
    result = exposure.copy().astype(float)
    core = 1.0 - sleeve
    window = 60
    for i in range(window, len(close_returns)):
        sample = close_returns.iloc[i - window : i].dropna()
        if len(sample) < int(window * 0.8):
            continue
        covariance = sample.cov().to_numpy(float) * 252.0
        raw = float(result.iloc[i])

        def predicted(test_exposure: float) -> float:
            weights = np.array([core * 0.5, core * 0.5, sleeve * test_exposure], dtype=float)
            return math.sqrt(max(0.0, float(weights @ covariance @ weights)))

        if predicted(raw) <= target_vol:
            continue
        lower, upper = 0.5, raw
        if predicted(lower) > target_vol:
            result.iloc[i] = lower
            continue
        for _ in range(30):
            midpoint = (lower + upper) / 2.0
            if predicted(midpoint) <= target_vol:
                lower = midpoint
            else:
                upper = midpoint
        result.iloc[i] = lower
    return result.clip(0.5, 1.5)


def apply_corr_cap(close: pd.DataFrame, exposure: pd.Series) -> pd.Series:
    returns = close.pct_change()
    corr_spy = returns["SOXX"].rolling(63).corr(returns["SPY"])
    corr_qqq = returns["SOXX"].rolling(63).corr(returns["QQQ"])
    average_corr = (corr_spy + corr_qqq) / 2.0
    rv40 = returns["SOXX"].rolling(40).std(ddof=1) * math.sqrt(252.0)
    result = exposure.copy().astype(float)
    first = (average_corr > 0.85) & (rv40 > 0.40)
    severe = (average_corr > 0.90) & (rv40 > 0.55)
    result.loc[first] = np.minimum(result.loc[first], 1.0)
    result.loc[severe] = np.minimum(result.loc[severe], 0.75)
    return result.clip(0.5, 1.5)


def rebalance_mask(exposure: pd.Series, policy: str) -> pd.Series:
    if policy == "daily":
        return pd.Series(True, index=exposure.index)
    if policy != "band10":
        raise ValueError(policy)
    output = pd.Series(False, index=exposure.index)
    last = float(exposure.iloc[0])
    last_month = exposure.index[0].to_period("M")
    output.iloc[0] = True
    for i in range(1, len(exposure)):
        current_month = exposure.index[i].to_period("M")
        value = float(exposure.iloc[i])
        if current_month != last_month or abs(value - last) >= 0.10:
            output.iloc[i] = True
            last = value
            last_month = current_month
    return output


def contiguous_block_diagnostics(engine, strategy: pd.Series, benchmark: pd.Series) -> tuple[int, int, list[dict]]:
    common = strategy.dropna().index.intersection(benchmark.dropna().index)
    periods = engine.contiguous_periods(common, 4)
    positive_cagr = 0
    positive_sharpe = 0
    rows: list[dict] = []
    for block, (start, end) in enumerate(periods, 1):
        sm = engine.metrics(strategy.loc[start:end])
        bm = engine.metrics(benchmark.loc[start:end])
        cagr_delta = sm["cagr"] - bm["cagr"]
        sharpe_delta = sm["sharpe"] - bm["sharpe"]
        positive_cagr += int(cagr_delta > 0.0)
        positive_sharpe += int(sharpe_delta > 0.0)
        rows.append(
            {
                "block": block,
                "start": str(start.date()),
                "end": str(end.date()),
                "cagr_delta": cagr_delta,
                "sharpe_delta": sharpe_delta,
                "dd_delta": sm["maxdd"] - bm["maxdd"],
            }
        )
    return positive_cagr, positive_sharpe, rows


def cscv_pbo(excess_returns: dict[str, pd.Series], blocks: int = 8) -> tuple[float, dict[str, dict[str, float]]]:
    frame = pd.concat(excess_returns, axis=1).dropna()
    if len(frame) < 1000 or len(frame.columns) < 2:
        return np.nan, {}
    block_indices = np.array_split(np.arange(len(frame)), blocks)
    half = blocks // 2
    failures = 0
    total = 0
    selected_count = {name: 0 for name in frame.columns}
    conditional_fail = {name: 0 for name in frame.columns}
    for in_blocks in itertools.combinations(range(blocks), half):
        in_set = set(in_blocks)
        in_idx = np.concatenate([block_indices[i] for i in in_blocks])
        out_idx = np.concatenate([block_indices[i] for i in range(blocks) if i not in in_set])
        in_sample = frame.iloc[in_idx]
        out_sample = frame.iloc[out_idx]
        in_sharpe = in_sample.mean() / in_sample.std(ddof=1).replace(0.0, np.nan)
        if in_sharpe.dropna().empty:
            continue
        winner = str(in_sharpe.idxmax())
        out_sharpe = out_sample.mean() / out_sample.std(ddof=1).replace(0.0, np.nan)
        ranks = out_sharpe.rank(pct=True, method="average")
        fail = bool(float(ranks.get(winner, 0.0)) <= 0.5)
        total += 1
        selected_count[winner] += 1
        conditional_fail[winner] += int(fail)
        failures += int(fail)
    details = {
        name: {
            "selection_frequency": selected_count[name] / total if total else np.nan,
            "conditional_pbo": conditional_fail[name] / selected_count[name] if selected_count[name] else np.nan,
        }
        for name in frame.columns
    }
    return failures / total if total else np.nan, details


def effective_trial_count(excess_returns: dict[str, pd.Series]) -> tuple[int, float]:
    frame = pd.concat(excess_returns, axis=1).dropna(how="all")
    corr = frame.corr(min_periods=252).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    if len(corr) < 2:
        return TRIAL_FLOOR, float(TRIAL_FLOOR)
    matrix = (corr.to_numpy(float) + corr.to_numpy(float).T) / 2.0
    np.fill_diagonal(matrix, 1.0)
    eigenvalues = np.clip(np.linalg.eigvalsh(matrix), 0.0, None)
    participation = float(eigenvalues.sum() ** 2 / max(1e-12, np.square(eigenvalues).sum()))
    return max(TRIAL_FLOOR, int(math.ceil(participation))), participation


def main() -> None:
    engine = load_module(BASE_OUT / "engine_patched.py", "core_satellite_engine")
    helper = load_module(
        Path("research/spy_qqq_soxx_alpha_search_20260722/validate_actual_products.py"),
        "core_satellite_helper",
    )
    data = {
        "SPY": load_input("SPY"),
        "QQQ": load_input("QQQ"),
        "SOXX": load_input("SOXX"),
        "RSP": load_input("RSP"),
        "QQEW": load_input("QQEW"),
        "XSD": load_input("XSD"),
        "HYG": load_input("HYG"),
        "LQD": load_input("LQD"),
        "^VIX": load_input("VIX"),
        "^VIX3M": load_input("VIX3M"),
    }
    soxx_bundle = helper.reconstruct_family_stream(engine, "SOXX", data)
    base_exposure = soxx_bundle["final_exposures"]["wf_trend_vol"].clip(0.5, 1.5)

    product_frames = {name: engine.download(name) for name in ["USD", "SOXL", "BIL"]}
    for name, frame in product_frames.items():
        frame.to_csv(OUT / f"{name}.csv.gz", compression="gzip")

    index = common_index([data["SPY"], data["QQQ"], data["SOXX"], product_frames["USD"], product_frames["SOXL"], product_frames["BIL"]])
    index = index[index >= OOS_START]
    close = pd.concat(
        {symbol: data[symbol]["Close"].reindex(index) for symbol in ["SPY", "QQQ", "SOXX"]},
        axis=1,
    )
    close_returns = close.pct_change()
    underlying_returns = pd.concat(
        {symbol: engine.open_to_open(data[symbol]).reindex(index) for symbol in ["SPY", "QQQ", "SOXX"]},
        axis=1,
    )
    bil_return = engine.open_to_open(product_frames["BIL"]).reindex(index)
    synthetic_cash = engine.load_cash(index).reindex(index).ffill().fillna(0.0)
    bil_return = bil_return.fillna(synthetic_cash)

    raw_exposure = base_exposure.reindex(index).ffill().fillna(1.0).clip(0.5, 1.5)
    exposure_variants: dict[tuple[str, float], pd.Series] = {}
    for sleeve in SLEEVES:
        exposure_variants[("raw", sleeve)] = raw_exposure
        exposure_variants[("volcap30", sleeve)] = apply_vol_cap(close_returns, sleeve, raw_exposure, 0.30)
        exposure_variants[("corr_cap", sleeve)] = apply_corr_cap(close, raw_exposure)

    candidate_returns: dict[str, pd.Series] = {}
    candidate_weights: dict[str, pd.DataFrame] = {}
    candidate_turnover: dict[str, pd.Series] = {}
    candidate_benchmarks: dict[str, pd.Series] = {}
    candidate_benchmark_stress3: dict[str, pd.Series] = {}
    candidate_stress2: dict[str, pd.Series] = {}
    candidate_stress3: dict[str, pd.Series] = {}
    candidate_metadata: dict[str, dict] = {}
    block_rows: list[dict] = []

    for product, spec in PRODUCTS.items():
        leveraged_return = engine.open_to_open(product_frames[product]).reindex(index)
        returns = underlying_returns.copy()
        returns[product] = leveraged_return
        returns["CASH"] = bil_return
        cost_bps = pd.Series({**ASSET_COST_BPS, product: spec["cost_bps"]}).reindex(returns.columns)
        for sleeve in SLEEVES:
            for variant in FAMILY_VARIANTS:
                exposure_name, policy = variant.rsplit("_", 1)
                exposure = exposure_variants[(exposure_name, sleeve)]
                mask = rebalance_mask(exposure, policy)
                target = product_target(index, exposure, sleeve, product, spec["multiple"])
                baseline_target = static_target(index, sleeve, product)
                candidate_name = f"{product}_{variant}_s{int(round(sleeve * 100)):02d}"
                strategy, held, turn = matched_portfolio(returns, target, mask, cost_bps, 1.0)
                benchmark, _, _ = matched_portfolio(returns, baseline_target, mask, cost_bps, 1.0)
                stress2, _, _ = matched_portfolio(returns, target, mask, cost_bps, 2.0)
                stress3, _, _ = matched_portfolio(returns, target, mask, cost_bps, 3.0)
                benchmark3, _, _ = matched_portfolio(returns, baseline_target, mask, cost_bps, 3.0)
                candidate_returns[candidate_name] = strategy
                candidate_weights[candidate_name] = held
                candidate_turnover[candidate_name] = turn
                candidate_benchmarks[candidate_name] = benchmark
                candidate_stress2[candidate_name] = stress2
                candidate_stress3[candidate_name] = stress3
                candidate_benchmark_stress3[candidate_name] = benchmark3
                candidate_metadata[candidate_name] = {
                    "product": product,
                    "variant": variant,
                    "family": f"{product}_{variant}",
                    "sleeve": sleeve,
                    "policy": policy,
                    "exposure_variant": exposure_name,
                }

    drift_returns = underlying_returns.copy()
    drift_returns["CASH"] = bil_return
    buy_hold_402020, _ = buy_hold_returns(
        drift_returns[["SPY", "QQQ", "SOXX", "CASH"]],
        pd.Series({"SPY": 0.40, "QQQ": 0.40, "SOXX": 0.20, "CASH": 0.0}),
    )

    excess_returns = {
        name: candidate_returns[name] - candidate_benchmarks[name].reindex(candidate_returns[name].index)
        for name in candidate_returns
    }
    search_pbo, pbo_details = cscv_pbo(excess_returns)
    effective_trials, participation_ratio = effective_trial_count(excess_returns)

    rows: list[dict] = []
    for name, strategy in candidate_returns.items():
        benchmark = candidate_benchmarks[name].reindex(strategy.index)
        common = strategy.dropna().index.intersection(benchmark.dropna().index)
        strategy = strategy.reindex(common)
        benchmark = benchmark.reindex(common)
        stress2 = candidate_stress2[name].reindex(common)
        stress3 = candidate_stress3[name].reindex(common)
        benchmark3 = candidate_benchmark_stress3[name].reindex(common)
        sm = engine.metrics(strategy)
        bm = engine.metrics(benchmark)
        drift_common = buy_hold_402020.reindex(common).dropna()
        drift_strategy = strategy.reindex(drift_common.index)
        drift_metrics = engine.metrics(drift_common)
        alpha, beta = engine.regression_alpha(strategy, benchmark)
        excess = strategy - benchmark
        p_positive = engine.moving_block_probability(excess)
        dsr = engine.deflated_sharpe_probability(strategy - bil_return.reindex(common).fillna(synthetic_cash.reindex(common)), effective_trials)
        positive_cagr, positive_sharpe, blocks = contiguous_block_diagnostics(engine, strategy, benchmark)
        for block in blocks:
            block_rows.append({"candidate": name, **block})
        cagr_delta = sm["cagr"] - bm["cagr"]
        cagr_delta_buy_hold = engine.metrics(drift_strategy)["cagr"] - drift_metrics["cagr"]
        sharpe_delta = sm["sharpe"] - bm["sharpe"]
        dd_delta = sm["maxdd"] - bm["maxdd"]
        stress2_delta = engine.metrics(stress2)["cagr"] - bm["cagr"]
        stress3_delta = engine.metrics(stress3)["cagr"] - engine.metrics(benchmark3)["cagr"]
        strict_gate = bool(
            cagr_delta >= 0.005
            and cagr_delta_buy_hold >= 0.0
            and sharpe_delta >= 0.0
            and dd_delta >= -0.03
            and alpha >= 0.005
            and positive_cagr >= 3
            and stress3_delta > 0.0
            and p_positive >= 0.80
            and dsr >= 0.80
            and search_pbo <= 0.30
        )
        details = pbo_details.get(name, {"selection_frequency": np.nan, "conditional_pbo": np.nan})
        meta = candidate_metadata[name]
        quality = 2.0 * alpha + cagr_delta + 0.5 * sharpe_delta + 0.25 * dd_delta + 0.25 * stress3_delta
        rows.append(
            {
                "candidate": name,
                **meta,
                "return_alpha_gate": strict_gate,
                "cagr": sm["cagr"],
                "benchmark_cagr": bm["cagr"],
                "cagr_delta": cagr_delta,
                "cagr_delta_vs_402020_buy_hold": cagr_delta_buy_hold,
                "sharpe": sm["sharpe"],
                "benchmark_sharpe": bm["sharpe"],
                "sharpe_delta": sharpe_delta,
                "maxdd": sm["maxdd"],
                "benchmark_maxdd": bm["maxdd"],
                "dd_delta": dd_delta,
                "annual_alpha": alpha,
                "beta": beta,
                "stress_2x_cagr_delta": stress2_delta,
                "stress_3x_cagr_delta": stress3_delta,
                "positive_cagr_blocks": positive_cagr,
                "positive_sharpe_blocks": positive_sharpe,
                "bootstrap_p_positive": p_positive,
                "dsr_probability": dsr,
                "search_pbo": search_pbo,
                "effective_trials": effective_trials,
                "trial_participation_ratio": participation_ratio,
                "selection_frequency": details["selection_frequency"],
                "conditional_pbo": details["conditional_pbo"],
                "average_turnover": float(candidate_turnover[name].mean() * 252.0),
                "current_signal_exposure": float(exposure_variants[(meta["exposure_variant"], meta["sleeve"])].iloc[-1]),
                "terminal": sm["terminal"],
                "benchmark_terminal": bm["terminal"],
                "quality": quality,
                "start": str(common.min().date()),
                "end": str(common.max().date()),
            }
        )
    grid = pd.DataFrame(rows).sort_values(
        ["return_alpha_gate", "quality", "candidate"], ascending=[False, False, True]
    ).reset_index(drop=True)

    family_rows: list[dict] = []
    for family, group in grid.groupby("family", sort=True):
        group = group.sort_values("sleeve")
        central = group.loc[np.isclose(group["sleeve"], 0.20)].iloc[0]
        robust = group[group["sleeve"].isin([0.15, 0.20, 0.25])]
        family_gate = bool(
            bool(central.return_alpha_gate)
            and (group["cagr_delta"] > 0.0).sum() >= 4
            and (group["stress_3x_cagr_delta"] > 0.0).sum() >= 4
            and (group["annual_alpha"] > 0.0).sum() >= 4
            and (robust["cagr_delta"] > 0.0).all()
            and (robust["stress_3x_cagr_delta"] > 0.0).all()
            and (robust["sharpe_delta"] >= 0.0).all()
        )
        family_rows.append(
            {
                "family": family,
                "product": str(central.product),
                "variant": str(central.variant),
                "family_gate": family_gate,
                "strict_pass_count": int(group["return_alpha_gate"].sum()),
                "positive_cagr_sleeves": int((group["cagr_delta"] > 0.0).sum()),
                "positive_stress3_sleeves": int((group["stress_3x_cagr_delta"] > 0.0).sum()),
                "central_candidate": str(central.candidate),
                "central_cagr_delta": float(central.cagr_delta),
                "central_sharpe_delta": float(central.sharpe_delta),
                "central_dd_delta": float(central.dd_delta),
                "central_annual_alpha": float(central.annual_alpha),
                "central_stress3_delta": float(central.stress_3x_cagr_delta),
                "central_bootstrap": float(central.bootstrap_p_positive),
                "central_dsr": float(central.dsr_probability),
                "median_quality": float(group["quality"].median()),
            }
        )
    family_summary = pd.DataFrame(family_rows).sort_values(
        ["family_gate", "median_quality", "family"], ascending=[False, False, True]
    ).reset_index(drop=True)
    selected_family = family_summary.iloc[0]
    selected_name = str(selected_family.central_candidate)
    selected_row = grid.set_index("candidate").loc[selected_name]
    classification = "RETURN_ALPHA" if bool(selected_family.family_gate) else "RESEARCH_ONLY"
    current_weights = candidate_weights[selected_name].iloc[-1]

    identity = pd.DataFrame(
        [
            {
                "classification": classification,
                "family": str(selected_family.family),
                "candidate": selected_name,
                "product": str(selected_row.product),
                "variant": str(selected_row.variant),
                "production_sleeve": 0.20,
                "family_gate": bool(selected_family.family_gate),
                "return_alpha_gate": bool(selected_row.return_alpha_gate),
                "current_spy_weight": float(current_weights.get("SPY", 0.0)),
                "current_qqq_weight": float(current_weights.get("QQQ", 0.0)),
                "current_soxx_weight": float(current_weights.get("SOXX", 0.0)),
                "current_leveraged_weight": float(current_weights.get(str(selected_row.product), 0.0)),
                "current_cash_weight": float(current_weights.get("CASH", 0.0)),
                "current_effective_soxx_exposure": float(
                    current_weights.get("SOXX", 0.0)
                    + PRODUCTS[str(selected_row.product)]["multiple"]
                    * current_weights.get(str(selected_row.product), 0.0)
                ),
                "cagr_delta": float(selected_row.cagr_delta),
                "cagr_delta_vs_402020_buy_hold": float(selected_row.cagr_delta_vs_402020_buy_hold),
                "sharpe_delta": float(selected_row.sharpe_delta),
                "dd_delta": float(selected_row.dd_delta),
                "annual_alpha": float(selected_row.annual_alpha),
                "stress_3x_cagr_delta": float(selected_row.stress_3x_cagr_delta),
                "bootstrap_p_positive": float(selected_row.bootstrap_p_positive),
                "dsr_probability": float(selected_row.dsr_probability),
                "search_pbo": float(selected_row.search_pbo),
                "start": str(selected_row.start),
                "end": str(selected_row.end),
            }
        ]
    )

    selected_returns = candidate_returns[selected_name]
    selected_benchmark = candidate_benchmarks[selected_name]
    windows: list[dict] = []
    for candidate_name, ret in [
        ("matched_static_core_satellite", selected_benchmark),
        ("buy_hold_40_40_20", buy_hold_402020.reindex(selected_returns.index)),
        (selected_name, selected_returns),
    ]:
        ret = ret.dropna()
        for label, years in [("1Y", 1), ("3Y", 3), ("5Y", 5), ("10Y", 10)]:
            start = ret.index[ret.index >= ret.index.max() - pd.DateOffset(years=years)].min()
            result = engine.metrics(ret.loc[start:])
            windows.append(
                {
                    "candidate": candidate_name,
                    "window": label,
                    "start": str(start.date()),
                    "end": str(ret.index.max().date()),
                    **result,
                }
            )
        result = engine.metrics(ret)
        windows.append(
            {
                "candidate": candidate_name,
                "window": "MAX",
                "start": str(ret.index.min().date()),
                "end": str(ret.index.max().date()),
                **result,
            }
        )
    window_frame = pd.DataFrame(windows)

    bil_common = bil_return.dropna().index.intersection(synthetic_cash.dropna().index)
    bil_metrics = engine.metrics(bil_return.reindex(bil_common))
    synthetic_metrics = engine.metrics(synthetic_cash.reindex(bil_common))
    cash_validation = pd.DataFrame(
        [
            {
                "start": str(bil_common.min().date()),
                "end": str(bil_common.max().date()),
                "bil_cagr": bil_metrics["cagr"],
                "synthetic_cash_cagr": synthetic_metrics["cagr"],
                "cagr_difference": bil_metrics["cagr"] - synthetic_metrics["cagr"],
                "daily_return_correlation": float(
                    bil_return.reindex(bil_common).corr(synthetic_cash.reindex(bil_common))
                ),
            }
        ]
    )

    grid.to_csv(OUT / "candidate_grid.csv", index=False, float_format="%.8f")
    family_summary.to_csv(OUT / "family_summary.csv", index=False, float_format="%.8f")
    identity.to_csv(OUT / "strategy_identity.csv", index=False, float_format="%.8f")
    pd.DataFrame(block_rows).to_csv(OUT / "block_diagnostics.csv", index=False, float_format="%.8f")
    window_frame.to_csv(OUT / "window_comparison.csv", index=False, float_format="%.8f")
    candidate_weights[selected_name].to_csv(OUT / "current_strategy_weights.csv", float_format="%.8f")
    cash_validation.to_csv(OUT / "cash_product_validation.csv", index=False, float_format="%.8f")

    identity_text = identity.to_csv(index=False, float_format="%.8f")
    identity_sha = hashlib.sha256(identity_text.encode()).hexdigest()
    base_manifest = json.loads((BASE_OUT / "run_manifest.json").read_text())
    manifest = {
        "version": "core-satellite-v1",
        "completed_close_cutoff": "2026-07-21",
        "candidate_count": len(grid),
        "family_count": len(family_summary),
        "effective_trials": effective_trials,
        "trial_participation_ratio": participation_ratio,
        "identity_sha256": identity_sha,
        "base_engine_source_sha256": base_manifest.get("source_sha256"),
        "selection_policy": "fixed 20% satellite; family must be robust across 15%, 20% and 25% sleeves",
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2))
    inputs = {}
    for name, frame in {
        "SPY": data["SPY"], "QQQ": data["QQQ"], "SOXX": data["SOXX"],
        "USD": product_frames["USD"], "SOXL": product_frames["SOXL"], "BIL": product_frames["BIL"],
    }.items():
        inputs[name] = {
            "rows": int(len(frame)),
            "start": str(frame.index.min().date()),
            "end": str(frame.index.max().date()),
            "last_close": float(frame["Close"].dropna().iloc[-1]),
        }
    (OUT / "input_manifest.json").write_text(json.dumps(inputs, indent=2))

    lines = [
        "# SPY + QQQ core with SOXX risk-budget satellite",
        "",
        f"Identity SHA-256: `{identity_sha}`.",
        "",
        "## Identity",
        "",
        identity.to_markdown(index=False),
        "",
        "## Family summary",
        "",
        family_summary.to_markdown(index=False),
        "",
        "## Window comparison",
        "",
        window_frame.to_markdown(index=False),
        "",
        "## Cash-product validation",
        "",
        cash_validation.to_markdown(index=False),
        "",
        "The production satellite is fixed at 20%; sleeve size is not optimized after observing OOS results. A family must remain positive across neighbouring 15%, 20% and 25% sleeves, pass 3x-cost stress, DSR, bootstrap and CSCV/PBO, and beat both its matched static policy and the 40/40/20 drift Buy & Hold benchmark.",
    ]
    (OUT / "report.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
