from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
BASE_RESEARCH = Path('research/spy_qqq_soxx_alpha_search_20260722')
OUT = Path('research_outputs/spy_qqq_fixed_ensemble_20260722')
BASE_OUT = Path('research_outputs/spy_qqq_soxx_alpha_search_20260722')
OUT.mkdir(parents=True, exist_ok=True)
OOS_START = pd.Timestamp('2013-01-01')
ASSETS = ['SPY', 'QQQ']
BASE_COST = {'SPY': 4.0, 'QQQ': 5.0}
PRODUCTS = {
    'SPY': [('SSO_2X', 'SSO', 2.0, 8.0), ('UPRO_3X', 'UPRO', 3.0, 12.0)],
    'QQQ': [('QLD_2X', 'QLD', 2.0, 10.0), ('TQQQ_3X', 'TQQQ', 3.0, 14.0)],
}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_input(name: str) -> pd.DataFrame:
    frame = pd.read_csv(BASE_OUT / 'inputs' / f'{name}.csv.gz', index_col=0, parse_dates=True)
    frame.index = pd.to_datetime(frame.index).normalize()
    frame.columns = [str(column).title() for column in frame.columns]
    return frame.sort_index()


def load_data() -> dict[str, pd.DataFrame]:
    return {
        'SPY': load_input('SPY'), 'QQQ': load_input('QQQ'), 'SOXX': load_input('SOXX'),
        'RSP': load_input('RSP'), 'QQEW': load_input('QQEW'), 'XSD': load_input('XSD'),
        'HYG': load_input('HYG'), 'LQD': load_input('LQD'),
        '^VIX': load_input('VIX'), '^VIX3M': load_input('VIX3M'),
    }


def median_exposure(raw_exposures: dict[str, pd.Series | None], raw_families: dict[str, str], family: str, index: pd.DatetimeIndex) -> pd.Series:
    names = sorted(name for name, fam in raw_families.items() if fam == family and raw_exposures.get(name) is not None)
    if not names:
        raise RuntimeError(f'no exposure candidates for {family}')
    frame = pd.concat({name: raw_exposures[name].reindex(index).ffill() for name in names}, axis=1)
    return frame.median(axis=1, skipna=True).ffill().fillna(1.0).clip(0.5, 2.0)


def frozen_pre2013(engine, raw_returns: dict[str, pd.Series], raw_exposures: dict[str, pd.Series | None], raw_families: dict[str, str], benchmark: pd.Series) -> tuple[str, pd.Series]:
    rows = []
    for name, exposure in raw_exposures.items():
        if exposure is None:
            continue
        score, diagnostics = engine.development_score(raw_returns[name].loc[:'2012-12-31'], benchmark.loc[:'2012-12-31'])
        rows.append({'name': name, 'score': score, 'family': raw_families[name], **diagnostics})
    ranking = pd.DataFrame(rows).sort_values(['score', 'name'], ascending=[False, False]).reset_index(drop=True)
    selected = str(ranking.iloc[0]['name'])
    return selected, raw_exposures[selected]


def fixed_exposures(engine, symbol: str, frame: pd.DataFrame, data: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.Series], dict[str, str], dict[str, str]]:
    cash = engine.load_cash(frame.index)
    candidates = engine.candidate_exposure(frame, data, symbol)
    raw_returns, raw_exposures, _, raw_families, raw_descriptions = engine.raw_candidate_data(frame, cash, candidates, BASE_COST[symbol])
    benchmark = raw_returns['buy_hold']
    selected_name, frozen = frozen_pre2013(engine, raw_returns, raw_exposures, raw_families, benchmark)
    vol = median_exposure(raw_exposures, raw_families, 'vol_target', frame.index)
    trend_vol = median_exposure(raw_exposures, raw_families, 'trend_vol', frame.index)
    damped_vol = (0.5 + 0.5 * vol).clip(0.5, 1.5)
    damped_trend_vol = (0.5 + 0.5 * trend_vol).clip(0.5, 1.5)
    damped_blend = (0.5 * damped_vol + 0.5 * damped_trend_vol).clip(0.5, 1.5)

    close = frame.Close
    ma50, ma200 = close.rolling(50).mean(), close.rolling(200).mean()
    rv20 = close.pct_change().rolling(20).std(ddof=1) * math.sqrt(engine.DAYS)
    rv100 = close.pct_change().rolling(100).std(ddof=1) * math.sqrt(engine.DAYS)
    crash = (close < ma200) & (rv20 > rv100)
    crash_guard = damped_blend.where(~crash, np.minimum(damped_blend, 0.5)).clip(0.5, 1.5)
    lowvol_trend = pd.Series(1.0, index=frame.index)
    lowvol_trend[(ma50 > ma200) & (rv20 < rv100)] = 1.25
    lowvol_trend[(close < ma200) & (rv20 > rv100)] = 0.75

    exposures = {
        'buy_hold': pd.Series(1.0, index=frame.index),
        'frozen_pre2013': frozen.clip(0.5, 2.0),
        'median_vol': vol,
        'damped_median_vol': damped_vol,
        'median_trend_vol': trend_vol,
        'damped_median_trend_vol': damped_trend_vol,
        'damped_blend': damped_blend,
        'crash_guard_blend': crash_guard,
        'lowvol_trend_fixed': lowvol_trend,
    }
    families = {
        'buy_hold': 'baseline', 'frozen_pre2013': 'frozen_once',
        'median_vol': 'fixed_ensemble', 'damped_median_vol': 'fixed_ensemble',
        'median_trend_vol': 'fixed_ensemble', 'damped_median_trend_vol': 'fixed_ensemble',
        'damped_blend': 'fixed_ensemble', 'crash_guard_blend': 'fixed_ensemble',
        'lowvol_trend_fixed': 'fixed_rule',
    }
    descriptions = {
        'buy_hold': '1.0x Buy & Hold',
        'frozen_pre2013': f'Raw rule selected once through 2012-12-31 and frozen: {selected_name} — {raw_descriptions[selected_name]}',
        'median_vol': 'Cross-parameter median of all fixed volatility-target exposure rules',
        'damped_median_vol': '50% Buy & Hold plus 50% median volatility-target exposure',
        'median_trend_vol': 'Cross-parameter median of all fixed trend-gated volatility-target rules',
        'damped_median_trend_vol': '50% Buy & Hold plus 50% median trend-vol exposure',
        'damped_blend': 'Equal blend of damped median vol-target and damped median trend-vol',
        'crash_guard_blend': 'Damped blend capped at 0.5x when below SMA200 with RV20 above RV100',
        'lowvol_trend_fixed': '1.25x in low-vol uptrend, 0.75x in high-vol downtrend, otherwise 1.0x',
    }
    return exposures, families, descriptions


def block_deltas(engine, candidate: pd.Series, benchmark: pd.Series) -> tuple[int, int, list[dict]]:
    common = candidate.dropna().index.intersection(benchmark.dropna().index)
    periods = engine.contiguous_periods(common, 4)
    positive_cagr = 0
    positive_sharpe = 0
    rows = []
    for block, (start, end) in enumerate(periods, 1):
        cm = engine.metrics(candidate.loc[start:end])
        bm = engine.metrics(benchmark.loc[start:end])
        cagr_delta = cm['cagr'] - bm['cagr']
        sharpe_delta = cm['sharpe'] - bm['sharpe']
        positive_cagr += int(cagr_delta > 0)
        positive_sharpe += int(sharpe_delta > 0)
        rows.append({'block': block, 'start': str(start.date()), 'end': str(end.date()), 'cagr_delta': cagr_delta, 'sharpe_delta': sharpe_delta, 'dd_delta': cm['maxdd'] - bm['maxdd']})
    return positive_cagr, positive_sharpe, rows


def evaluate_signal(engine, symbol: str, frame: pd.DataFrame, cash: pd.Series, exposures: dict[str, pd.Series], families: dict[str, str], descriptions: dict[str, str]):
    returns, held, turnover = {}, {}, {}
    for name, exposure in exposures.items():
        ret, h, t = engine.returns_from_exposure(frame, cash, exposure, BASE_COST[symbol])
        returns[name], held[name], turnover[name] = ret.loc[OOS_START:], h.loc[OOS_START:], t.loc[OOS_START:]
    benchmark = returns['buy_hold']
    search_pbo, pbo_details = engine.cscv_search_pbo(returns, benchmark)
    rows, blocks = [], []
    for name, ret in returns.items():
        common = ret.dropna().index.intersection(benchmark.dropna().index)
        candidate = ret.reindex(common)
        bh = benchmark.reindex(common)
        cm, bm = engine.metrics(candidate), engine.metrics(bh)
        excess = candidate - bh
        alpha, beta = engine.regression_alpha(candidate, bh)
        stress2, _, _ = engine.returns_from_exposure(frame, cash, exposures[name], BASE_COST[symbol] * 2.0)
        stress3, _, _ = engine.returns_from_exposure(frame, cash, exposures[name], BASE_COST[symbol] * 3.0)
        stress2 = stress2.reindex(common)
        stress3 = stress3.reindex(common)
        positive_cagr, positive_sharpe, block_rows = block_deltas(engine, candidate, bh)
        for row in block_rows:
            blocks.append({'symbol': symbol, 'candidate': name, **row})
        cagr_delta = cm['cagr'] - bm['cagr']
        sharpe_delta = cm['sharpe'] - bm['sharpe']
        dd_delta = cm['maxdd'] - bm['maxdd']
        p_positive = np.nan if name == 'buy_hold' else engine.moving_block_probability(excess)
        dsr = np.nan if name == 'buy_hold' else engine.deflated_sharpe_probability(candidate - cash.reindex(common).ffill().fillna(0.0), 8)
        stress3_delta = engine.metrics(stress3)['cagr'] - bm['cagr']
        return_gate = bool(name != 'buy_hold' and cagr_delta >= 0.005 and sharpe_delta >= 0.0 and dd_delta >= -0.03 and alpha >= 0.005 and positive_cagr >= 3 and stress3_delta > 0.0 and p_positive >= 0.80 and dsr >= 0.80 and search_pbo <= 0.30)
        defensive_gate = bool(name != 'buy_hold' and sharpe_delta >= 0.10 and dd_delta >= abs(bm['maxdd']) * 0.20 and cagr_delta >= -0.02 and positive_sharpe >= 3 and search_pbo <= 0.40)
        detail = pbo_details.get(name, {'selection_frequency': np.nan, 'conditional_pbo': np.nan})
        quality = 2.0 * alpha + cagr_delta + 0.5 * sharpe_delta + 0.25 * dd_delta + 0.25 * stress3_delta
        rows.append({
            'symbol': symbol, 'candidate': name, 'family': families[name], 'description': descriptions[name],
            'return_alpha_gate': return_gate, 'defensive_gate': defensive_gate,
            'current_exposure': float(exposures[name].iloc[-1]), 'average_exposure': float(held[name].mean()),
            'cagr': cm['cagr'], 'buy_hold_cagr': bm['cagr'], 'cagr_delta': cagr_delta,
            'sharpe': cm['sharpe'], 'buy_hold_sharpe': bm['sharpe'], 'sharpe_delta': sharpe_delta,
            'maxdd': cm['maxdd'], 'buy_hold_maxdd': bm['maxdd'], 'dd_delta': dd_delta,
            'annual_alpha': alpha, 'beta': beta, 'stress_2x_cagr_delta': engine.metrics(stress2)['cagr'] - bm['cagr'],
            'stress_3x_cagr_delta': stress3_delta, 'positive_cagr_blocks': positive_cagr,
            'positive_sharpe_blocks': positive_sharpe, 'bootstrap_p_positive': p_positive,
            'dsr_probability': dsr, 'search_pbo': search_pbo,
            'selection_frequency': detail['selection_frequency'], 'conditional_pbo': detail['conditional_pbo'],
            'terminal': cm['terminal'], 'buy_hold_terminal': bm['terminal'], 'quality': quality,
            'oos_start': str(common.min().date()), 'oos_end': str(common.max().date()),
        })
    grid = pd.DataFrame(rows).sort_values(['return_alpha_gate','defensive_gate','quality','candidate'], ascending=[False,False,False,True]).reset_index(drop=True)
    winner = grid.iloc[0]
    return grid, winner, returns, exposures, pd.DataFrame(blocks)


def product_path(engine, base: pd.DataFrame, product: pd.DataFrame, cash: pd.Series, exposure: pd.Series, multiple: float, base_cost: float, product_cost: float, cost_multiplier: float = 1.0):
    common = base.index.intersection(product.index).intersection(exposure.index)
    common = common[common >= OOS_START]
    target = exposure.reindex(common).ffill().fillna(1.0).clip(0.0, multiple)
    base_weight = pd.Series(index=common, dtype=float)
    product_weight = pd.Series(0.0, index=common, dtype=float)
    cash_weight = pd.Series(0.0, index=common, dtype=float)
    low = target <= 1.0
    base_weight.loc[low] = target.loc[low]
    cash_weight.loc[low] = 1.0 - target.loc[low]
    high = ~low
    product_weight.loc[high] = (target.loc[high] - 1.0) / (multiple - 1.0)
    base_weight.loc[high] = 1.0 - product_weight.loc[high]
    held_base = base_weight.shift(1).ffill().fillna(1.0)
    held_product = product_weight.shift(1).ffill().fillna(0.0)
    held_cash = cash_weight.shift(1).ffill().fillna(0.0)
    cost = (held_base.diff().abs().fillna(0.0) * base_cost + held_product.diff().abs().fillna(0.0) * product_cost) * cost_multiplier / 10_000.0
    ret = held_base * engine.open_to_open(base).reindex(common) + held_product * engine.open_to_open(product).reindex(common) + held_cash * cash.reindex(common).ffill().fillna(0.0) - cost
    ret = ret.iloc[:-1].dropna()
    weights = pd.DataFrame({'target_exposure': target, 'held_base': held_base, 'held_product': held_product, 'held_cash': held_cash}).reindex(ret.index)
    return ret, weights


def evaluate_products(engine, symbol: str, winner: pd.Series, frame: pd.DataFrame, cash: pd.Series, exposure: pd.Series):
    rows, weight_rows = [], []
    products = {}
    for label, ticker, multiple, product_cost in PRODUCTS[symbol]:
        product = engine.download(ticker)
        products[ticker] = product
        actual, weights = product_path(engine, frame, product, cash, exposure, multiple, BASE_COST[symbol], product_cost, 1.0)
        stress2, _ = product_path(engine, frame, product, cash, exposure, multiple, BASE_COST[symbol], product_cost, 2.0)
        stress3, _ = product_path(engine, frame, product, cash, exposure, multiple, BASE_COST[symbol], product_cost, 3.0)
        benchmark = engine.open_to_open(frame).reindex(actual.index).dropna()
        common = actual.index.intersection(benchmark.index)
        actual, stress2, stress3, benchmark = actual.reindex(common), stress2.reindex(common), stress3.reindex(common), benchmark.reindex(common)
        cm, bm = engine.metrics(actual), engine.metrics(benchmark)
        alpha, beta = engine.regression_alpha(actual, benchmark)
        cagr_delta = cm['cagr'] - bm['cagr']
        sharpe_delta = cm['sharpe'] - bm['sharpe']
        dd_delta = cm['maxdd'] - bm['maxdd']
        p_positive = engine.moving_block_probability(actual - benchmark)
        dsr = engine.deflated_sharpe_probability(actual - cash.reindex(common).ffill().fillna(0.0), 8)
        stress3_delta = engine.metrics(stress3)['cagr'] - bm['cagr']
        gate = bool(winner.return_alpha_gate and cagr_delta >= 0.005 and sharpe_delta >= 0.0 and dd_delta >= -0.03 and alpha >= 0.005 and stress3_delta > 0.0 and p_positive >= 0.80 and dsr >= 0.80 and float(winner.search_pbo) <= 0.30)
        rows.append({
            'symbol': symbol, 'implementation': label, 'ticker': ticker, 'multiple': multiple,
            'candidate': str(winner.candidate), 'start': str(common.min().date()), 'end': str(common.max().date()),
            'cagr': cm['cagr'], 'buy_hold_cagr': bm['cagr'], 'cagr_delta': cagr_delta,
            'sharpe': cm['sharpe'], 'buy_hold_sharpe': bm['sharpe'], 'sharpe_delta': sharpe_delta,
            'maxdd': cm['maxdd'], 'buy_hold_maxdd': bm['maxdd'], 'dd_delta': dd_delta,
            'annual_alpha': alpha, 'beta': beta, 'stress_2x_cagr_delta': engine.metrics(stress2)['cagr'] - bm['cagr'],
            'stress_3x_cagr_delta': stress3_delta, 'bootstrap_p_positive': p_positive,
            'dsr_probability': dsr, 'search_pbo': float(winner.search_pbo), 'actual_product_gate': gate,
            'terminal': cm['terminal'], 'buy_hold_terminal': bm['terminal'],
        })
        weight_rows.append({
            'symbol': symbol, 'implementation': label,
            'current_effective_exposure': float(weights.target_exposure.iloc[-1]),
            'current_base_weight': float(weights.held_base.iloc[-1]),
            'current_product_weight': float(weights.held_product.iloc[-1]),
            'current_cash_weight': float(weights.held_cash.iloc[-1]),
            'average_effective_exposure': float(weights.target_exposure.mean()),
            'average_product_weight': float(weights.held_product.mean()),
        })
    return pd.DataFrame(rows), pd.DataFrame(weight_rows), products


def main() -> None:
    engine = load_module(BASE_OUT / 'engine_patched.py', 'fixed_ensemble_engine')
    data = load_data()
    grids, identities, product_results, product_weights, block_frames = [], [], [], [], []
    input_manifest = {}
    for symbol in ASSETS:
        frame = data[symbol]
        cash = engine.load_cash(frame.index)
        exposures, families, descriptions = fixed_exposures(engine, symbol, frame, data)
        grid, winner, returns, exposure_map, blocks = evaluate_signal(engine, symbol, frame, cash, exposures, families, descriptions)
        grids.append(grid)
        block_frames.append(blocks)
        products, weights, downloaded = evaluate_products(engine, symbol, winner, frame, cash, exposure_map[str(winner.candidate)])
        product_results.append(products)
        product_weights.append(weights)
        product_pass = bool(products.actual_product_gate.any())
        classification = 'RETURN_ALPHA' if bool(winner.return_alpha_gate) and product_pass else ('DEFENSIVE_ALPHA' if bool(winner.defensive_gate) and product_pass else 'RESEARCH_ONLY')
        production_exposure = float(winner.current_exposure) if classification != 'RESEARCH_ONLY' else 1.0
        identities.append({
            'symbol': symbol, 'classification': classification, 'candidate': str(winner.candidate),
            'family': str(winner.family), 'description': str(winner.description),
            'signal_return_alpha_gate': bool(winner.return_alpha_gate), 'signal_defensive_gate': bool(winner.defensive_gate),
            'actual_product_pass': product_pass, 'current_model_exposure': float(winner.current_exposure),
            'current_production_exposure': production_exposure, 'cagr_delta': float(winner.cagr_delta),
            'sharpe_delta': float(winner.sharpe_delta), 'dd_delta': float(winner.dd_delta),
            'annual_alpha': float(winner.annual_alpha), 'beta': float(winner.beta),
            'stress_3x_cagr_delta': float(winner.stress_3x_cagr_delta),
            'bootstrap_p_positive': float(winner.bootstrap_p_positive), 'dsr_probability': float(winner.dsr_probability),
            'search_pbo': float(winner.search_pbo), 'oos_start': str(winner.oos_start), 'oos_end': str(winner.oos_end),
        })
        input_manifest[symbol] = {'rows': len(frame), 'start': str(frame.index.min().date()), 'end': str(frame.index.max().date())}
        for ticker, product in downloaded.items():
            input_manifest[ticker] = {'rows': len(product), 'start': str(product.index.min().date()), 'end': str(product.index.max().date())}
    grid_frame = pd.concat(grids, ignore_index=True)
    identity = pd.DataFrame(identities).sort_values('symbol')
    product_frame = pd.concat(product_results, ignore_index=True).sort_values(['symbol','implementation'])
    weight_frame = pd.concat(product_weights, ignore_index=True).sort_values(['symbol','implementation'])
    blocks = pd.concat(block_frames, ignore_index=True)
    grid_frame.to_csv(OUT / 'fixed_candidate_grid.csv', index=False, float_format='%.8f')
    identity.to_csv(OUT / 'strategy_identity.csv', index=False, float_format='%.8f')
    product_frame.to_csv(OUT / 'actual_product_validation.csv', index=False, float_format='%.8f')
    weight_frame.to_csv(OUT / 'actual_product_weights.csv', index=False, float_format='%.8f')
    blocks.to_csv(OUT / 'block_diagnostics.csv', index=False, float_format='%.8f')
    identity_sha = hashlib.sha256(identity.to_csv(index=False, float_format='%.8f').encode()).hexdigest()
    manifest = {'version': 'fixed-ensemble-v1', 'completed_close_cutoff': '2026-07-21', 'candidate_count_per_asset': 9, 'identity_sha256': identity_sha, 'inputs': input_manifest}
    (OUT / 'run_manifest.json').write_text(json.dumps(manifest, indent=2))
    lines = ['# SPY + QQQ fixed-ensemble challenger', '', f'Identity SHA-256: `{identity_sha}`.', '', '## Final identity', '', identity.to_markdown(index=False), '', '## Actual product paths', '', product_frame.to_markdown(index=False), '', '## Current implementation weights', '', weight_frame.to_markdown(index=False)]
    (OUT / 'report.md').write_text('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
