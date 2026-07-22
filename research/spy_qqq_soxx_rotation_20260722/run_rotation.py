from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE_OUT = Path('research_outputs/spy_qqq_soxx_alpha_search_20260722')
OUT = Path('research_outputs/spy_qqq_soxx_rotation_20260722')
OUT.mkdir(parents=True, exist_ok=True)
ASSETS = ['SPY', 'QQQ', 'SOXX']
COST_BPS = pd.Series({'SPY': 4.0, 'QQQ': 5.0, 'SOXX': 9.0, 'CASH': 0.0})
OOS_START = pd.Timestamp('2013-01-01')
CAPITAL = 10_000.0


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
    return {name: load_input(name) for name in ASSETS}


def common_index(data: dict[str, pd.DataFrame]) -> pd.DatetimeIndex:
    index = data[ASSETS[0]].index
    for symbol in ASSETS[1:]:
        index = index.intersection(data[symbol].index)
    return index.sort_values()


def benchmark_buy_hold(engine, asset_returns: pd.DataFrame, start_weights: pd.Series) -> tuple[pd.Series, pd.DataFrame]:
    values = start_weights.astype(float).copy() * CAPITAL
    returns = []
    weights = []
    for date, row in asset_returns.iterrows():
        pre = float(values.sum())
        values = values * (1.0 + row.fillna(0.0))
        post = float(values.sum())
        returns.append(post / pre - 1.0 if pre > 0 else 0.0)
        weights.append(values / post if post > 0 else start_weights)
    return pd.Series(returns, index=asset_returns.index), pd.DataFrame(weights, index=asset_returns.index)


def managed_portfolio(asset_returns: pd.DataFrame, cash_returns: pd.Series, target: pd.DataFrame, cost_multiplier: float = 1.0) -> tuple[pd.Series, pd.DataFrame, pd.Series]:
    columns = ASSETS + ['CASH']
    target = target.reindex(asset_returns.index).ffill().fillna(0.0)[columns]
    desired = target.shift(1).fillna(pd.Series({'SPY': 1/3, 'QQQ': 1/3, 'SOXX': 1/3, 'CASH': 0.0}))
    current = pd.Series({'SPY': 1/3, 'QQQ': 1/3, 'SOXX': 1/3, 'CASH': 0.0}, dtype=float)
    out_returns, out_weights, out_turnover = [], [], []
    for date in asset_returns.index:
        new = desired.loc[date].astype(float)
        if abs(float(new.sum()) - 1.0) > 1e-8:
            new['CASH'] += 1.0 - float(new.sum())
        changes = (new - current).abs()
        cost = float((changes * COST_BPS).sum()) * cost_multiplier / 10_000.0
        component = pd.Series({symbol: asset_returns.loc[date, symbol] for symbol in ASSETS} | {'CASH': cash_returns.reindex(asset_returns.index).loc[date]})
        gross = float((new * component.fillna(0.0)).sum())
        net = gross - cost
        end_values = new * (1.0 + component.fillna(0.0))
        total = float(end_values.sum())
        current = end_values / total if total != 0 else new
        out_returns.append(net)
        out_weights.append(new)
        out_turnover.append(float(changes[ASSETS].sum()))
    return pd.Series(out_returns, index=asset_returns.index), pd.DataFrame(out_weights, index=asset_returns.index), pd.Series(out_turnover, index=asset_returns.index)


def top_weights(score: pd.DataFrame, eligible: pd.DataFrame, top_n: int) -> pd.DataFrame:
    result = pd.DataFrame(0.0, index=score.index, columns=ASSETS + ['CASH'])
    for date in score.index:
        valid = [symbol for symbol in ASSETS if bool(eligible.loc[date, symbol]) and pd.notna(score.loc[date, symbol])]
        if not valid:
            result.loc[date, 'CASH'] = 1.0
            continue
        ranked = sorted(valid, key=lambda symbol: (float(score.loc[date, symbol]), symbol), reverse=True)[:top_n]
        weight = 1.0 / len(ranked)
        for symbol in ranked:
            result.loc[date, symbol] = weight
    return result


def smooth_weights(weights: pd.DataFrame, span: int = 5) -> pd.DataFrame:
    smoothed = weights.ewm(span=span, adjust=False).mean()
    total = smoothed.sum(axis=1).replace(0.0, np.nan)
    return smoothed.div(total, axis=0).fillna({'SPY': 1/3, 'QQQ': 1/3, 'SOXX': 1/3, 'CASH': 0.0})


def build_candidates(engine, data: dict[str, pd.DataFrame], index: pd.DatetimeIndex) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    close = pd.concat({symbol: data[symbol].Close.reindex(index) for symbol in ASSETS}, axis=1)
    momentum63 = close.pct_change(63)
    momentum126 = close.pct_change(126)
    momentum252 = close.pct_change(252)
    combined = 0.45 * momentum63 + 0.35 * momentum126 + 0.20 * momentum252
    rv60 = close.pct_change().rolling(60).std(ddof=1) * math.sqrt(engine.DAYS)
    risk_adjusted = combined / rv60.replace(0.0, np.nan)
    ma200 = close.rolling(200).mean()
    eligible = (close > ma200) & (combined > 0.0)

    top1 = smooth_weights(top_weights(combined, eligible, 1))
    top2 = smooth_weights(top_weights(combined, eligible, 2))
    risk_top1 = smooth_weights(top_weights(risk_adjusted, eligible, 1))
    risk_top2 = smooth_weights(top_weights(risk_adjusted, eligible, 2))

    equal = pd.DataFrame({'SPY': 1/3, 'QQQ': 1/3, 'SOXX': 1/3, 'CASH': 0.0}, index=index)
    core_top1 = 0.5 * equal + 0.5 * top1
    core_top2 = 0.5 * equal + 0.5 * top2
    core_risk_top1 = 0.5 * equal + 0.5 * risk_top1
    core_risk_top2 = 0.5 * equal + 0.5 * risk_top2

    # Rebuild the already validated SOXX family stream without changing its rule.
    helper = load_module(Path('research/spy_qqq_soxx_alpha_search_20260722/validate_actual_products.py'), 'rotation_product_helper')
    expanded_data = {
        'SPY': data['SPY'], 'QQQ': data['QQQ'], 'SOXX': data['SOXX'],
        'RSP': load_input('RSP'), 'QQEW': load_input('QQEW'), 'XSD': load_input('XSD'),
        'HYG': load_input('HYG'), 'LQD': load_input('LQD'),
        '^VIX': load_input('VIX'), '^VIX3M': load_input('VIX3M'),
    }
    soxx_bundle = helper.reconstruct_family_stream(engine, 'SOXX', expanded_data)
    soxx_exposure = soxx_bundle['final_exposures']['wf_trend_vol'].reindex(index).ffill().fillna(1.0).clip(0.5, 1.5)
    soxx_sleeve = equal.copy()
    soxx_sleeve['SOXX'] = (1/3) * soxx_exposure
    soxx_sleeve['CASH'] = 1.0 - soxx_sleeve[ASSETS].sum(axis=1)
    core_rotation_soxx = 0.5 * core_risk_top1 + 0.5 * soxx_sleeve

    candidates = {
        'equal_weight_core': equal,
        'top1_momentum': top1,
        'top2_momentum': top2,
        'top1_risk_adjusted': risk_top1,
        'top2_risk_adjusted': risk_top2,
        'core50_top1': core_top1,
        'core50_top2': core_top2,
        'core50_risk_top1': core_risk_top1,
        'core50_risk_top2': core_risk_top2,
        'soxx_alpha_sleeve': soxx_sleeve,
        'core_rotation_soxx_alpha': core_rotation_soxx,
    }
    descriptions = {
        'equal_weight_core': 'Daily 1/3 SPY, 1/3 QQQ, 1/3 SOXX reference allocation',
        'top1_momentum': '100% strongest eligible composite-momentum index, otherwise cash',
        'top2_momentum': 'Equal weight top two eligible composite-momentum indices',
        'top1_risk_adjusted': '100% strongest eligible momentum/volatility score',
        'top2_risk_adjusted': 'Equal weight top two eligible momentum/volatility scores',
        'core50_top1': '50% equal-weight core plus 50% top-one momentum tilt',
        'core50_top2': '50% equal-weight core plus 50% top-two momentum tilt',
        'core50_risk_top1': '50% equal-weight core plus 50% top-one risk-adjusted tilt',
        'core50_risk_top2': '50% equal-weight core plus 50% top-two risk-adjusted tilt',
        'soxx_alpha_sleeve': 'Equal SPY and QQQ sleeves plus validated SOXX trend-vol sleeve',
        'core_rotation_soxx_alpha': 'Half core risk-adjusted rotation plus half SOXX-alpha sleeve',
    }
    return candidates, descriptions


def block_diagnostics(engine, strategy: pd.Series, benchmark: pd.Series) -> tuple[int, int, list[dict]]:
    common = strategy.dropna().index.intersection(benchmark.dropna().index)
    periods = engine.contiguous_periods(common, 4)
    positive_cagr = positive_sharpe = 0
    rows = []
    for block, (start, end) in enumerate(periods, 1):
        sm = engine.metrics(strategy.loc[start:end])
        bm = engine.metrics(benchmark.loc[start:end])
        cagr_delta = sm['cagr'] - bm['cagr']
        sharpe_delta = sm['sharpe'] - bm['sharpe']
        positive_cagr += int(cagr_delta > 0)
        positive_sharpe += int(sharpe_delta > 0)
        rows.append({'block': block, 'start': str(start.date()), 'end': str(end.date()), 'cagr_delta': cagr_delta, 'sharpe_delta': sharpe_delta, 'dd_delta': sm['maxdd'] - bm['maxdd']})
    return positive_cagr, positive_sharpe, rows


def main() -> None:
    engine = load_module(BASE_OUT / 'engine_patched.py', 'rotation_engine')
    data = load_data()
    index = common_index(data)
    asset_returns = pd.concat({symbol: engine.open_to_open(data[symbol]).reindex(index) for symbol in ASSETS}, axis=1)
    cash = engine.load_cash(index).reindex(index).ffill().fillna(0.0)
    index = index[index >= OOS_START]
    asset_returns, cash = asset_returns.reindex(index), cash.reindex(index)
    benchmark, benchmark_weights = benchmark_buy_hold(engine, asset_returns, pd.Series({'SPY': 1/3, 'QQQ': 1/3, 'SOXX': 1/3}))
    single_benchmarks = {symbol: asset_returns[symbol].dropna() for symbol in ASSETS}
    candidates, descriptions = build_candidates(engine, data, common_index(data))

    returns, weights, turnover = {}, {}, {}
    for name, target in candidates.items():
        if name == 'equal_weight_core':
            returns[name] = benchmark
            weights[name] = pd.concat([benchmark_weights, pd.Series(0.0, index=benchmark_weights.index, name='CASH')], axis=1)
            turnover[name] = pd.Series(0.0, index=benchmark.index)
        else:
            ret, held, turn = managed_portfolio(asset_returns, cash, target.reindex(index), 1.0)
            returns[name], weights[name], turnover[name] = ret, held, turn

    search_pbo, pbo_details = engine.cscv_search_pbo(returns, benchmark)
    rows, block_rows = [], []
    for name, ret in returns.items():
        common = ret.dropna().index.intersection(benchmark.dropna().index)
        strategy, bh = ret.reindex(common), benchmark.reindex(common)
        sm, bm = engine.metrics(strategy), engine.metrics(bh)
        alpha, beta = engine.regression_alpha(strategy, bh)
        p_positive = np.nan if name == 'equal_weight_core' else engine.moving_block_probability(strategy - bh)
        dsr = np.nan if name == 'equal_weight_core' else engine.deflated_sharpe_probability(strategy - cash.reindex(common), 10)
        if name == 'equal_weight_core':
            stress2 = stress3 = strategy
        else:
            stress2, _, _ = managed_portfolio(asset_returns, cash, candidates[name].reindex(index), 2.0)
            stress3, _, _ = managed_portfolio(asset_returns, cash, candidates[name].reindex(index), 3.0)
            stress2, stress3 = stress2.reindex(common), stress3.reindex(common)
        positive_cagr, positive_sharpe, blocks = block_diagnostics(engine, strategy, bh)
        for block in blocks:
            block_rows.append({'candidate': name, **block})
        cagr_delta = sm['cagr'] - bm['cagr']
        sharpe_delta = sm['sharpe'] - bm['sharpe']
        dd_delta = sm['maxdd'] - bm['maxdd']
        stress3_delta = engine.metrics(stress3)['cagr'] - bm['cagr']
        details = pbo_details.get(name, {'selection_frequency': np.nan, 'conditional_pbo': np.nan})
        return_gate = bool(name != 'equal_weight_core' and cagr_delta >= 0.01 and sharpe_delta >= 0.0 and dd_delta >= -0.03 and alpha >= 0.01 and positive_cagr >= 3 and stress3_delta > 0.0 and p_positive >= 0.80 and dsr >= 0.80 and search_pbo <= 0.30)
        defensive_gate = bool(name != 'equal_weight_core' and sharpe_delta >= 0.10 and dd_delta >= abs(bm['maxdd']) * 0.20 and cagr_delta >= -0.02 and positive_sharpe >= 3 and search_pbo <= 0.40)
        quality = 2.0 * alpha + cagr_delta + 0.5 * sharpe_delta + 0.25 * dd_delta + 0.25 * stress3_delta
        single_terminal = {f'{symbol.lower()}_buy_hold_terminal': engine.metrics(single_benchmarks[symbol].reindex(common))['terminal'] for symbol in ASSETS}
        rows.append({
            'candidate': name, 'description': descriptions[name], 'return_alpha_gate': return_gate, 'defensive_gate': defensive_gate,
            'cagr': sm['cagr'], 'benchmark_cagr': bm['cagr'], 'cagr_delta': cagr_delta,
            'sharpe': sm['sharpe'], 'benchmark_sharpe': bm['sharpe'], 'sharpe_delta': sharpe_delta,
            'maxdd': sm['maxdd'], 'benchmark_maxdd': bm['maxdd'], 'dd_delta': dd_delta,
            'annual_alpha': alpha, 'beta': beta, 'stress_2x_cagr_delta': engine.metrics(stress2)['cagr'] - bm['cagr'],
            'stress_3x_cagr_delta': stress3_delta, 'positive_cagr_blocks': positive_cagr,
            'positive_sharpe_blocks': positive_sharpe, 'bootstrap_p_positive': p_positive,
            'dsr_probability': dsr, 'search_pbo': search_pbo,
            'selection_frequency': details['selection_frequency'], 'conditional_pbo': details['conditional_pbo'],
            'terminal': sm['terminal'], 'benchmark_terminal': bm['terminal'], **single_terminal,
            'average_turnover': float(turnover[name].mean()), 'quality': quality,
            'start': str(common.min().date()), 'end': str(common.max().date()),
        })
    grid = pd.DataFrame(rows).sort_values(['return_alpha_gate','defensive_gate','quality','candidate'], ascending=[False,False,False,True]).reset_index(drop=True)
    winner = grid.iloc[0]
    classification = 'RETURN_ALPHA' if bool(winner.return_alpha_gate) else ('DEFENSIVE_ALPHA' if bool(winner.defensive_gate) else 'RESEARCH_ONLY')
    current = weights[str(winner.candidate)].iloc[-1]
    identity = pd.DataFrame([{
        'classification': classification, 'candidate': str(winner.candidate), 'description': str(winner.description),
        'return_alpha_gate': bool(winner.return_alpha_gate), 'defensive_gate': bool(winner.defensive_gate),
        'current_spy_weight': float(current['SPY']), 'current_qqq_weight': float(current['QQQ']),
        'current_soxx_weight': float(current['SOXX']), 'current_cash_weight': float(current['CASH']),
        'cagr_delta': float(winner.cagr_delta), 'sharpe_delta': float(winner.sharpe_delta),
        'dd_delta': float(winner.dd_delta), 'annual_alpha': float(winner.annual_alpha),
        'beta': float(winner.beta), 'stress_3x_cagr_delta': float(winner.stress_3x_cagr_delta),
        'bootstrap_p_positive': float(winner.bootstrap_p_positive), 'dsr_probability': float(winner.dsr_probability),
        'search_pbo': float(winner.search_pbo), 'start': str(winner.start), 'end': str(winner.end),
    }])

    windows = []
    winner_ret = returns[str(winner.candidate)]
    for candidate_name, ret in [('equal_weight_core', benchmark), (str(winner.candidate), winner_ret)]:
        for label, years in [('1Y',1),('3Y',3),('5Y',5),('10Y',10)]:
            start = ret.index[ret.index >= ret.index.max() - pd.DateOffset(years=years)].min()
            result = engine.metrics(ret.loc[start:])
            windows.append({'candidate': candidate_name, 'window': label, 'start': str(start.date()), 'end': str(ret.index.max().date()), **result})
        result = engine.metrics(ret)
        windows.append({'candidate': candidate_name, 'window': 'MAX', 'start': str(ret.index.min().date()), 'end': str(ret.index.max().date()), **result})
    window_frame = pd.DataFrame(windows)

    grid.to_csv(OUT / 'candidate_grid.csv', index=False, float_format='%.8f')
    identity.to_csv(OUT / 'strategy_identity.csv', index=False, float_format='%.8f')
    pd.DataFrame(block_rows).to_csv(OUT / 'block_diagnostics.csv', index=False, float_format='%.8f')
    window_frame.to_csv(OUT / 'window_comparison.csv', index=False, float_format='%.8f')
    weights[str(winner.candidate)].to_csv(OUT / 'current_strategy_weights.csv', float_format='%.8f')
    identity_sha = hashlib.sha256(identity.to_csv(index=False, float_format='%.8f').encode()).hexdigest()
    manifest = {'version': 'tri-index-rotation-v1', 'completed_close_cutoff': '2026-07-21', 'candidate_count': len(candidates), 'identity_sha256': identity_sha}
    (OUT / 'run_manifest.json').write_text(json.dumps(manifest, indent=2))
    lines = ['# SPY + QQQ + SOXX relative-strength rotation', '', f'Identity SHA-256: `{identity_sha}`.', '', '## Identity', '', identity.to_markdown(index=False), '', '## Candidate grid', '', grid.to_markdown(index=False), '', '## Window comparison', '', window_frame.to_markdown(index=False)]
    (OUT / 'report.md').write_text('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
