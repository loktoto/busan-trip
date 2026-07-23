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

BASE_OUT = Path('research_outputs/spy_qqq_soxx_alpha_search_20260722')
OUT = Path('research_outputs/spy_qqq_soxx_portfolio_vol_20260723')
OUT.mkdir(parents=True, exist_ok=True)

OOS_START = pd.Timestamp('2013-01-01')
CAPITAL = 10_000.0
BASE_WEIGHTS = pd.Series({'SPY': 0.40, 'QQQ': 0.40, 'SOXX': 0.20})
TARGET_VOLS = [0.22, 0.25, 0.28]
PRODUCTION_TARGET_VOL = 0.25
FAMILY_NAMES = [
    'fixed_vol',
    'fixed_trend',
    'fixed_trend_corr',
    'fixed_trend_drawdown',
    'shrink_invvol_vol',
    'shrink_invvol_trend',
]
ROUTES = {
    '2X': {
        'multiple': 2.0,
        'products': {'SPY': 'SSO', 'QQQ': 'QLD', 'SOXX': 'USD'},
        'cost_bps': {'SSO': 8.0, 'QLD': 9.0, 'USD': 25.0},
    },
    '3X': {
        'multiple': 3.0,
        'products': {'SPY': 'UPRO', 'QQQ': 'TQQQ', 'SOXX': 'SOXL'},
        'cost_bps': {'UPRO': 12.0, 'TQQQ': 10.0, 'SOXL': 18.0},
    },
}
BASE_COST_BPS = {'SPY': 4.0, 'QQQ': 5.0, 'SOXX': 9.0, 'CASH': 2.0}
TRIAL_FLOOR = len(FAMILY_NAMES) * len(ROUTES)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def project_weights(row: pd.Series) -> pd.Series:
    lower = pd.Series({'SPY': 0.25, 'QQQ': 0.25, 'SOXX': 0.10})
    upper = pd.Series({'SPY': 0.55, 'QQQ': 0.55, 'SOXX': 0.30})
    w = row.reindex(BASE_WEIGHTS.index).astype(float).fillna(BASE_WEIGHTS)
    w = w.clip(lower=lower, upper=upper)
    for _ in range(12):
        total = float(w.sum())
        if total <= 0:
            return BASE_WEIGHTS.copy()
        w = w / total
        below = w < lower
        above = w > upper
        if not below.any() and not above.any():
            break
        w = w.clip(lower=lower, upper=upper)
        free = ~(below | above)
        locked = float(w[~free].sum())
        remaining = max(0.0, 1.0 - locked)
        if free.any():
            free_sum = float(w[free].sum())
            w.loc[free] = remaining * (w.loc[free] / free_sum if free_sum > 0 else 1.0 / free.sum())
    return w / float(w.sum())


def allocation_weights(close: pd.DataFrame, mode: str) -> pd.DataFrame:
    if mode == 'fixed':
        return pd.DataFrame(np.tile(BASE_WEIGHTS.to_numpy(), (len(close), 1)), index=close.index, columns=BASE_WEIGHTS.index)
    if mode != 'shrink_invvol':
        raise ValueError(mode)
    volatility = close.pct_change().rolling(60).std(ddof=1) * math.sqrt(252.0)
    inverse = 1.0 / volatility.replace(0.0, np.nan)
    inverse = inverse.div(inverse.sum(axis=1), axis=0)
    blended = 0.50 * pd.DataFrame(np.tile(BASE_WEIGHTS.to_numpy(), (len(close), 1)), index=close.index, columns=BASE_WEIGHTS.index) + 0.50 * inverse
    projected = pd.DataFrame([project_weights(row) for _, row in blended.iterrows()], index=close.index)
    month = projected.index.to_period('M')
    monthly = projected.where(pd.Series(month != month.shift(1), index=projected.index), np.nan).ffill()
    return monthly.fillna(BASE_WEIGHTS)


def weighted_close_return(close: pd.DataFrame, weights: pd.DataFrame) -> pd.Series:
    return (weights.shift(1).fillna(BASE_WEIGHTS) * close.pct_change().fillna(0.0)).sum(axis=1)


def base_vol_exposure(portfolio_return: pd.Series, target_vol: float) -> pd.Series:
    realised = portfolio_return.rolling(40).std(ddof=1) * math.sqrt(252.0)
    raw = (target_vol / realised.replace(0.0, np.nan)).clip(0.5, 1.5)
    return raw.ewm(span=5, adjust=False, min_periods=1).mean().fillna(1.0).clip(0.5, 1.5)


def breadth_cap(close: pd.DataFrame) -> pd.Series:
    above = close.gt(close.rolling(200).mean()).sum(axis=1)
    cap = pd.Series(0.5, index=close.index)
    cap.loc[above == 1] = 0.75
    cap.loc[above == 2] = 1.15
    cap.loc[above == 3] = 1.50
    return cap


def correlation_cap(close: pd.DataFrame, portfolio_return: pd.Series) -> pd.Series:
    returns = close.pct_change()
    corr1 = returns['SPY'].rolling(63).corr(returns['QQQ'])
    corr2 = returns['SPY'].rolling(63).corr(returns['SOXX'])
    corr3 = returns['QQQ'].rolling(63).corr(returns['SOXX'])
    average = (corr1 + corr2 + corr3) / 3.0
    realised = portfolio_return.rolling(40).std(ddof=1) * math.sqrt(252.0)
    cap = pd.Series(1.5, index=close.index)
    cap.loc[(average > 0.85) & (realised > 0.30)] = 0.90
    cap.loc[(average > 0.90) & (realised > 0.45)] = 0.65
    return cap


def drawdown_cap(portfolio_return: pd.Series) -> pd.Series:
    wealth = (1.0 + portfolio_return.fillna(0.0)).cumprod()
    drawdown = wealth / wealth.rolling(252, min_periods=60).max() - 1.0
    cap = pd.Series(1.5, index=portfolio_return.index)
    cap.loc[drawdown <= -0.10] = 1.00
    cap.loc[drawdown <= -0.20] = 0.75
    cap.loc[drawdown <= -0.30] = 0.50
    return cap


def family_state(close: pd.DataFrame, family: str, target_vol: float) -> tuple[pd.DataFrame, pd.Series]:
    allocation_mode = 'shrink_invvol' if family.startswith('shrink_invvol') else 'fixed'
    weights = allocation_weights(close, allocation_mode)
    portfolio_return = weighted_close_return(close, weights)
    exposure = base_vol_exposure(portfolio_return, target_vol)
    if 'trend' in family:
        exposure = np.minimum(exposure, breadth_cap(close))
    if 'corr' in family:
        exposure = np.minimum(exposure, correlation_cap(close, portfolio_return))
    if 'drawdown' in family:
        exposure = np.minimum(exposure, drawdown_cap(portfolio_return))
    return weights, pd.Series(exposure, index=close.index).clip(0.5, 1.5)


def rebalance_mask(weights: pd.DataFrame, exposure: pd.Series) -> pd.Series:
    output = pd.Series(False, index=weights.index)
    output.iloc[0] = True
    last_weights = weights.iloc[0].copy()
    last_exposure = float(exposure.iloc[0])
    last_month = weights.index[0].to_period('M')
    for i in range(1, len(weights)):
        current_month = weights.index[i].to_period('M')
        weight_change = float((weights.iloc[i] - last_weights).abs().sum())
        exposure_change = abs(float(exposure.iloc[i]) - last_exposure)
        if current_month != last_month or weight_change >= 0.10 or exposure_change >= 0.10:
            output.iloc[i] = True
            last_weights = weights.iloc[i].copy()
            last_exposure = float(exposure.iloc[i])
            last_month = current_month
    return output


def route_target(index: pd.DatetimeIndex, allocation: pd.DataFrame, exposure: pd.Series, route: dict) -> pd.DataFrame:
    products = route['products']
    multiple = float(route['multiple'])
    columns = ['SPY', 'QQQ', 'SOXX', *products.values(), 'CASH']
    result = pd.DataFrame(0.0, index=index, columns=columns)
    w = allocation.reindex(index).ffill().fillna(BASE_WEIGHTS)
    e = exposure.reindex(index).ffill().fillna(1.0).clip(0.5, 1.5)
    low = e <= 1.0
    for asset in BASE_WEIGHTS.index:
        result.loc[low, asset] = w.loc[low, asset] * e.loc[low]
    result.loc[low, 'CASH'] = 1.0 - e.loc[low]
    high = ~low
    for asset in BASE_WEIGHTS.index:
        leveraged_weight = w.loc[high, asset] * (e.loc[high] - 1.0) / (multiple - 1.0)
        result.loc[high, products[asset]] = leveraged_weight
        result.loc[high, asset] = w.loc[high, asset] - leveraged_weight
    result['CASH'] += 1.0 - result.sum(axis=1)
    return result


def benchmark_target(index: pd.DatetimeIndex, allocation: pd.DataFrame, route: dict) -> pd.DataFrame:
    return route_target(index, allocation, pd.Series(1.0, index=index), route)


def contiguous_blocks(engine, strategy: pd.Series, benchmark: pd.Series) -> tuple[int, int, list[dict]]:
    common = strategy.dropna().index.intersection(benchmark.dropna().index)
    rows = []
    positive_cagr = 0
    positive_sharpe = 0
    for block, (start, end) in enumerate(engine.contiguous_periods(common, 4), 1):
        sm = engine.metrics(strategy.loc[start:end])
        bm = engine.metrics(benchmark.loc[start:end])
        cagr_delta = sm['cagr'] - bm['cagr']
        sharpe_delta = sm['sharpe'] - bm['sharpe']
        positive_cagr += int(cagr_delta > 0.0)
        positive_sharpe += int(sharpe_delta > 0.0)
        rows.append({'block': block, 'start': str(start.date()), 'end': str(end.date()), 'cagr_delta': cagr_delta, 'sharpe_delta': sharpe_delta, 'dd_delta': sm['maxdd'] - bm['maxdd']})
    return positive_cagr, positive_sharpe, rows


def cscv_pbo(excess_returns: dict[str, pd.Series], blocks: int = 8) -> tuple[float, dict[str, dict[str, float]]]:
    frame = pd.concat(excess_returns, axis=1).dropna()
    if len(frame) < 1000 or len(frame.columns) < 2:
        return np.nan, {}
    block_indices = np.array_split(np.arange(len(frame)), blocks)
    failures = 0
    total = 0
    selected = {name: 0 for name in frame.columns}
    conditional = {name: 0 for name in frame.columns}
    for in_blocks in itertools.combinations(range(blocks), blocks // 2):
        in_idx = np.concatenate([block_indices[i] for i in in_blocks])
        out_idx = np.concatenate([block_indices[i] for i in range(blocks) if i not in set(in_blocks)])
        ins = frame.iloc[in_idx]
        outs = frame.iloc[out_idx]
        in_sharpe = ins.mean() / ins.std(ddof=1).replace(0.0, np.nan)
        if in_sharpe.dropna().empty:
            continue
        winner = str(in_sharpe.idxmax())
        out_sharpe = outs.mean() / outs.std(ddof=1).replace(0.0, np.nan)
        ranks = out_sharpe.rank(pct=True, method='average')
        fail = bool(float(ranks.get(winner, 0.0)) <= 0.5)
        total += 1
        selected[winner] += 1
        conditional[winner] += int(fail)
        failures += int(fail)
    details = {name: {'selection_frequency': selected[name] / total if total else np.nan, 'conditional_pbo': conditional[name] / selected[name] if selected[name] else np.nan} for name in frame.columns}
    return failures / total if total else np.nan, details


def effective_trials(excess_returns: dict[str, pd.Series]) -> tuple[int, float]:
    frame = pd.concat(excess_returns, axis=1).dropna(how='all')
    corr = frame.corr(min_periods=252).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    matrix = (corr.to_numpy(float) + corr.to_numpy(float).T) / 2.0
    np.fill_diagonal(matrix, 1.0)
    eigenvalues = np.clip(np.linalg.eigvalsh(matrix), 0.0, None)
    participation = float(eigenvalues.sum() ** 2 / max(1e-12, np.square(eigenvalues).sum()))
    return max(TRIAL_FLOOR, int(math.ceil(participation))), participation


def main() -> None:
    engine = load_module(BASE_OUT / 'engine_patched.py', 'portfolio_vol_engine')
    helper = load_module(Path('research/spy_qqq_soxx_core_satellite_20260723/run_core_satellite.py'), 'portfolio_vol_helper')
    base = {symbol: helper.load_input(symbol) for symbol in ['SPY', 'QQQ', 'SOXX']}
    products = {symbol: engine.download(symbol) for symbol in ['SSO', 'QLD', 'USD', 'UPRO', 'TQQQ', 'SOXL', 'BIL']}
    for symbol, frame in products.items():
        frame.to_csv(OUT / f'{symbol}.csv.gz', compression='gzip')

    index = helper.common_index([*base.values(), *products.values()])
    index = index[index >= OOS_START]
    close = pd.concat({symbol: base[symbol]['Close'].reindex(index) for symbol in BASE_WEIGHTS.index}, axis=1)
    base_returns = pd.concat({symbol: engine.open_to_open(base[symbol]).reindex(index) for symbol in BASE_WEIGHTS.index}, axis=1)
    bil = engine.open_to_open(products['BIL']).reindex(index)
    synthetic_cash = engine.load_cash(index).reindex(index).ffill().fillna(0.0)
    cash_return = bil.fillna(synthetic_cash)

    drift_returns = base_returns.copy()
    drift_returns['CASH'] = cash_return
    buy_hold, _ = helper.buy_hold_returns(drift_returns[['SPY', 'QQQ', 'SOXX', 'CASH']], pd.Series({'SPY': 0.40, 'QQQ': 0.40, 'SOXX': 0.20, 'CASH': 0.0}))

    candidate_returns = {}
    candidate_benchmarks = {}
    candidate_stress2 = {}
    candidate_stress3 = {}
    benchmark_stress3 = {}
    candidate_weights = {}
    candidate_turnover = {}
    metadata = {}

    for route_name, route in ROUTES.items():
        returns = base_returns.copy()
        for product in route['products'].values():
            returns[product] = engine.open_to_open(products[product]).reindex(index)
        returns['CASH'] = cash_return
        cost = pd.Series({**BASE_COST_BPS, **route['cost_bps']}).reindex(returns.columns)
        for family in FAMILY_NAMES:
            for target_vol in TARGET_VOLS:
                allocation, exposure = family_state(close, family, target_vol)
                mask = rebalance_mask(allocation, exposure)
                target = route_target(index, allocation, exposure, route)
                benchmark = benchmark_target(index, allocation, route)
                name = f'{route_name}_{family}_tv{int(round(target_vol * 100)):02d}'
                strategy, held, turnover = helper.matched_portfolio(returns, target, mask, cost, 1.0)
                matched, _, _ = helper.matched_portfolio(returns, benchmark, mask, cost, 1.0)
                stress2, _, _ = helper.matched_portfolio(returns, target, mask, cost, 2.0)
                stress3, _, _ = helper.matched_portfolio(returns, target, mask, cost, 3.0)
                matched3, _, _ = helper.matched_portfolio(returns, benchmark, mask, cost, 3.0)
                candidate_returns[name] = strategy
                candidate_benchmarks[name] = matched
                candidate_stress2[name] = stress2
                candidate_stress3[name] = stress3
                benchmark_stress3[name] = matched3
                candidate_weights[name] = held
                candidate_turnover[name] = turnover
                metadata[name] = {'route': route_name, 'family': family, 'target_vol': target_vol, 'allocation_mode': 'shrink_invvol' if family.startswith('shrink_invvol') else 'fixed'}

    selection_excess = {name: candidate_returns[name] - candidate_benchmarks[name].reindex(candidate_returns[name].index) for name in candidate_returns if abs(metadata[name]['target_vol'] - PRODUCTION_TARGET_VOL) < 1e-12}
    if len(selection_excess) != TRIAL_FLOOR:
        raise RuntimeError(f'expected {TRIAL_FLOOR} central candidates, found {len(selection_excess)}')
    search_pbo, pbo_details = cscv_pbo(selection_excess)
    trials, participation = effective_trials(selection_excess)

    rows = []
    block_rows = []
    for name, strategy in candidate_returns.items():
        benchmark = candidate_benchmarks[name].reindex(strategy.index)
        common = strategy.dropna().index.intersection(benchmark.dropna().index)
        strategy = strategy.reindex(common)
        benchmark = benchmark.reindex(common)
        stress2 = candidate_stress2[name].reindex(common)
        stress3 = candidate_stress3[name].reindex(common)
        matched3 = benchmark_stress3[name].reindex(common)
        sm = engine.metrics(strategy)
        bm = engine.metrics(benchmark)
        drift = buy_hold.reindex(common).dropna()
        strategy_drift = strategy.reindex(drift.index)
        alpha, beta = engine.regression_alpha(strategy, benchmark)
        p_positive = engine.moving_block_probability(strategy - benchmark)
        dsr = engine.deflated_sharpe_probability(strategy - cash_return.reindex(common).fillna(synthetic_cash.reindex(common)), trials)
        positive_cagr, positive_sharpe, blocks = contiguous_blocks(engine, strategy, benchmark)
        for block in blocks:
            block_rows.append({'candidate': name, **block})
        cagr_delta = sm['cagr'] - bm['cagr']
        cagr_vs_bh = engine.metrics(strategy_drift)['cagr'] - engine.metrics(drift)['cagr']
        sharpe_delta = sm['sharpe'] - bm['sharpe']
        dd_delta = sm['maxdd'] - bm['maxdd']
        stress2_delta = engine.metrics(stress2)['cagr'] - bm['cagr']
        stress3_delta = engine.metrics(stress3)['cagr'] - engine.metrics(matched3)['cagr']
        gate = bool(cagr_delta >= 0.005 and cagr_vs_bh >= 0.0 and sharpe_delta >= 0.0 and dd_delta >= -0.03 and alpha >= 0.005 and positive_cagr >= 3 and stress3_delta > 0.0 and p_positive >= 0.80 and dsr >= 0.80 and search_pbo <= 0.30)
        details = pbo_details.get(name, {'selection_frequency': np.nan, 'conditional_pbo': np.nan})
        meta = metadata[name]
        quality = 2.0 * alpha + cagr_delta + 0.5 * sharpe_delta + 0.25 * dd_delta + 0.25 * stress3_delta
        rows.append({'candidate': name, **meta, 'return_alpha_gate': gate, 'cagr': sm['cagr'], 'benchmark_cagr': bm['cagr'], 'cagr_delta': cagr_delta, 'cagr_delta_vs_402020_buy_hold': cagr_vs_bh, 'sharpe': sm['sharpe'], 'benchmark_sharpe': bm['sharpe'], 'sharpe_delta': sharpe_delta, 'maxdd': sm['maxdd'], 'benchmark_maxdd': bm['maxdd'], 'dd_delta': dd_delta, 'annual_alpha': alpha, 'beta': beta, 'stress_2x_cagr_delta': stress2_delta, 'stress_3x_cagr_delta': stress3_delta, 'positive_cagr_blocks': positive_cagr, 'positive_sharpe_blocks': positive_sharpe, 'bootstrap_p_positive': p_positive, 'dsr_probability': dsr, 'search_pbo': search_pbo, 'effective_trials': trials, 'trial_participation_ratio': participation, 'selection_frequency': details['selection_frequency'], 'conditional_pbo': details['conditional_pbo'], 'average_turnover': float(candidate_turnover[name].mean() * 252.0), 'terminal': sm['terminal'], 'benchmark_terminal': bm['terminal'], 'quality': quality, 'start': str(common.min().date()), 'end': str(common.max().date())})
    grid = pd.DataFrame(rows).sort_values(['return_alpha_gate', 'quality', 'candidate'], ascending=[False, False, True]).reset_index(drop=True)

    family_rows = []
    for key, group in grid.groupby(['route', 'family'], sort=True):
        group = group.sort_values('target_vol')
        central = group.loc[np.isclose(group['target_vol'], PRODUCTION_TARGET_VOL)].iloc[0]
        family_gate = bool(bool(central['return_alpha_gate']) and (group['cagr_delta'] > 0).all() and (group['stress_3x_cagr_delta'] > 0).all() and (group['sharpe_delta'] >= 0).all() and (group['annual_alpha'] > 0).all())
        family_rows.append({'route': key[0], 'family': key[1], 'family_key': f'{key[0]}_{key[1]}', 'family_gate': family_gate, 'strict_pass_count': int(group['return_alpha_gate'].sum()), 'central_candidate': str(central['candidate']), 'central_cagr_delta': float(central['cagr_delta']), 'central_cagr_vs_buy_hold': float(central['cagr_delta_vs_402020_buy_hold']), 'central_sharpe_delta': float(central['sharpe_delta']), 'central_dd_delta': float(central['dd_delta']), 'central_annual_alpha': float(central['annual_alpha']), 'central_stress3_delta': float(central['stress_3x_cagr_delta']), 'central_bootstrap': float(central['bootstrap_p_positive']), 'central_dsr': float(central['dsr_probability']), 'median_quality': float(group['quality'].median())})
    family_summary = pd.DataFrame(family_rows).sort_values(['family_gate', 'median_quality', 'family_key'], ascending=[False, False, True]).reset_index(drop=True)
    selected_family = family_summary.iloc[0]
    selected_name = str(selected_family['central_candidate'])
    selected = grid.set_index('candidate').loc[selected_name]
    classification = 'RETURN_ALPHA' if bool(selected_family['family_gate']) else 'RESEARCH_ONLY'
    current = candidate_weights[selected_name].iloc[-1]
    route = ROUTES[str(selected['route'])]
    effective = sum(float(current.get(asset, 0.0)) + float(route['multiple']) * float(current.get(product, 0.0)) for asset, product in route['products'].items())
    identity = pd.DataFrame([{'classification': classification, 'family_key': str(selected_family['family_key']), 'candidate': selected_name, 'route': str(selected['route']), 'family': str(selected['family']), 'production_target_vol': PRODUCTION_TARGET_VOL, 'family_gate': bool(selected_family['family_gate']), 'return_alpha_gate': bool(selected['return_alpha_gate']), 'current_spy_weight': float(current.get('SPY', 0.0)), 'current_qqq_weight': float(current.get('QQQ', 0.0)), 'current_soxx_weight': float(current.get('SOXX', 0.0)), 'current_sso_upro_weight': float(current.get(route['products']['SPY'], 0.0)), 'current_qld_tqqq_weight': float(current.get(route['products']['QQQ'], 0.0)), 'current_usd_soxl_weight': float(current.get(route['products']['SOXX'], 0.0)), 'current_cash_weight': float(current.get('CASH', 0.0)), 'current_total_effective_exposure': effective, 'cagr_delta': float(selected['cagr_delta']), 'cagr_delta_vs_402020_buy_hold': float(selected['cagr_delta_vs_402020_buy_hold']), 'sharpe_delta': float(selected['sharpe_delta']), 'dd_delta': float(selected['dd_delta']), 'annual_alpha': float(selected['annual_alpha']), 'stress_3x_cagr_delta': float(selected['stress_3x_cagr_delta']), 'bootstrap_p_positive': float(selected['bootstrap_p_positive']), 'dsr_probability': float(selected['dsr_probability']), 'search_pbo': float(selected['search_pbo']), 'start': str(selected['start']), 'end': str(selected['end'])}])

    windows = []
    selected_return = candidate_returns[selected_name]
    selected_benchmark = candidate_benchmarks[selected_name]
    for label_name, ret in [('matched_dynamic_1x', selected_benchmark), ('buy_hold_40_40_20', buy_hold.reindex(selected_return.index)), (selected_name, selected_return)]:
        ret = ret.dropna()
        for label, years in [('1Y', 1), ('3Y', 3), ('5Y', 5), ('10Y', 10)]:
            start = ret.index[ret.index >= ret.index.max() - pd.DateOffset(years=years)].min()
            windows.append({'candidate': label_name, 'window': label, 'start': str(start.date()), 'end': str(ret.index.max().date()), **engine.metrics(ret.loc[start:])})
        windows.append({'candidate': label_name, 'window': 'MAX', 'start': str(ret.index.min().date()), 'end': str(ret.index.max().date()), **engine.metrics(ret)})
    window_frame = pd.DataFrame(windows)

    cash_common = bil.dropna().index.intersection(synthetic_cash.dropna().index)
    cash_validation = pd.DataFrame([{'start': str(cash_common.min().date()), 'end': str(cash_common.max().date()), 'bil_cagr': engine.metrics(bil.reindex(cash_common))['cagr'], 'synthetic_cash_cagr': engine.metrics(synthetic_cash.reindex(cash_common))['cagr'], 'cagr_difference': engine.metrics(bil.reindex(cash_common))['cagr'] - engine.metrics(synthetic_cash.reindex(cash_common))['cagr'], 'daily_return_correlation': float(bil.reindex(cash_common).corr(synthetic_cash.reindex(cash_common)))}])

    grid.to_csv(OUT / 'candidate_grid.csv', index=False, float_format='%.8f')
    family_summary.to_csv(OUT / 'family_summary.csv', index=False, float_format='%.8f')
    identity.to_csv(OUT / 'strategy_identity.csv', index=False, float_format='%.8f')
    pd.DataFrame(block_rows).to_csv(OUT / 'block_diagnostics.csv', index=False, float_format='%.8f')
    window_frame.to_csv(OUT / 'window_comparison.csv', index=False, float_format='%.8f')
    candidate_weights[selected_name].to_csv(OUT / 'current_strategy_weights.csv', float_format='%.8f')
    cash_validation.to_csv(OUT / 'cash_product_validation.csv', index=False, float_format='%.8f')

    identity_sha = hashlib.sha256(identity.to_csv(index=False, float_format='%.8f').encode()).hexdigest()
    base_manifest = json.loads((BASE_OUT / 'run_manifest.json').read_text())
    manifest = {'version': 'portfolio-vol-v1', 'completed_close_cutoff': '2026-07-21', 'candidate_count': len(grid), 'family_count': len(family_summary), 'production_target_vol': PRODUCTION_TARGET_VOL, 'effective_trials': trials, 'trial_participation_ratio': participation, 'identity_sha256': identity_sha, 'base_engine_source_sha256': base_manifest.get('source_sha256'), 'selection_policy': 'fixed 25% portfolio volatility target; 22% and 28% are robustness diagnostics only; PBO across twelve central families'}
    (OUT / 'run_manifest.json').write_text(json.dumps(manifest, indent=2))
    input_manifest = {}
    for symbol, frame in {**base, **products}.items():
        input_manifest[symbol] = {'rows': int(len(frame)), 'start': str(frame.index.min().date()), 'end': str(frame.index.max().date()), 'last_close': float(frame['Close'].dropna().iloc[-1])}
    (OUT / 'input_manifest.json').write_text(json.dumps(input_manifest, indent=2))

    report = ['# SPY + QQQ + SOXX portfolio-level volatility management', '', f'Identity SHA-256: `{identity_sha}`.', '', '## Identity', '', identity.to_markdown(index=False), '', '## Family summary', '', family_summary.to_markdown(index=False), '', '## Window comparison', '', window_frame.to_markdown(index=False), '', 'The production target volatility is fixed at 25%. The 22% and 28% targets are robustness diagnostics and are excluded from the PBO selection universe. Actual SSO/QLD/USD or UPRO/TQQQ/SOXL adjusted prices are used.']
    (OUT / 'report.md').write_text('\n'.join(report))
    print('\n'.join(report))


if __name__ == '__main__':
    main()
