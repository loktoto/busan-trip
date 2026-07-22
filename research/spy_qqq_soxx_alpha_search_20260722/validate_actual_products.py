from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path('research_outputs/spy_qqq_soxx_alpha_search_20260722')
ENGINE_PATH = OUT / 'engine_patched.py'
OOS_START = pd.Timestamp('2013-01-01')


def load_engine():
    spec = importlib.util.spec_from_file_location('alpha_engine_patched', ENGINE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules['alpha_engine_patched'] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_input(name: str) -> pd.DataFrame:
    frame = pd.read_csv(OUT / 'inputs' / f'{name}.csv.gz', index_col=0, parse_dates=True)
    frame.index = pd.to_datetime(frame.index).normalize()
    frame.columns = [str(column).title() for column in frame.columns]
    return frame.sort_index()


def load_saved_data() -> dict[str, pd.DataFrame]:
    return {
        'SPY': load_input('SPY'), 'QQQ': load_input('QQQ'), 'SOXX': load_input('SOXX'),
        'RSP': load_input('RSP'), 'QQEW': load_input('QQEW'), 'XSD': load_input('XSD'),
        'HYG': load_input('HYG'), 'LQD': load_input('LQD'),
        '^VIX': load_input('VIX'), '^VIX3M': load_input('VIX3M'),
    }


def reconstruct_family_stream(engine, symbol: str, data: dict[str, pd.DataFrame]):
    frame = data[symbol]
    cash = engine.load_cash(frame.index)
    candidates = engine.candidate_exposure(frame, data, symbol) + engine.session_candidates(
        frame, symbol, engine.BASE_COST_BPS[symbol]
    )
    raw_returns, raw_exposures, raw_turnovers, raw_families, raw_descriptions = engine.raw_candidate_data(
        frame, cash, candidates, engine.BASE_COST_BPS[symbol]
    )
    oos_start = frame.index[frame.index >= OOS_START].min()
    final_returns, final_exposures, final_turnovers, final_families, final_descriptions, choices = engine.anchored_family_streams(
        symbol, frame, cash, candidates, raw_returns, raw_exposures, raw_turnovers,
        raw_families, raw_descriptions, oos_start,
    )
    return {
        'frame': frame, 'cash': cash, 'raw_returns': raw_returns,
        'raw_exposures': raw_exposures, 'raw_families': raw_families,
        'raw_descriptions': raw_descriptions, 'final_returns': final_returns,
        'final_exposures': final_exposures, 'choices': choices,
    }


def portfolio_path(engine, base: pd.DataFrame, leveraged: pd.DataFrame, cash: pd.Series,
                   signal_exposure: pd.Series, leverage_multiple: float,
                   base_cost_bps: float, leveraged_cost_bps: float,
                   cost_multiplier: float = 1.0) -> tuple[pd.Series, pd.DataFrame]:
    common = base.index.intersection(leveraged.index).intersection(signal_exposure.index)
    common = common[common >= OOS_START]
    base_ret = engine.open_to_open(base).reindex(common)
    lev_ret = engine.open_to_open(leveraged).reindex(common)
    cash_ret = cash.reindex(common).ffill().fillna(0.0)
    exposure = signal_exposure.reindex(common).ffill().fillna(1.0).clip(0.0, leverage_multiple)

    base_weight = pd.Series(index=common, dtype=float)
    lev_weight = pd.Series(0.0, index=common, dtype=float)
    cash_weight = pd.Series(0.0, index=common, dtype=float)
    low = exposure <= 1.0
    base_weight.loc[low] = exposure.loc[low]
    cash_weight.loc[low] = 1.0 - exposure.loc[low]
    high = ~low
    lev_weight.loc[high] = (exposure.loc[high] - 1.0) / (leverage_multiple - 1.0)
    base_weight.loc[high] = 1.0 - lev_weight.loc[high]

    held_base = base_weight.shift(1).ffill().fillna(1.0)
    held_lev = lev_weight.shift(1).ffill().fillna(0.0)
    held_cash = cash_weight.shift(1).ffill().fillna(0.0)
    cost = (
        held_base.diff().abs().fillna(0.0) * base_cost_bps
        + held_lev.diff().abs().fillna(0.0) * leveraged_cost_bps
    ) * cost_multiplier / 10_000.0
    returns = held_base * base_ret + held_lev * lev_ret + held_cash * cash_ret - cost
    returns = returns.iloc[:-1].dropna()
    weights = pd.DataFrame({
        'signal_exposure': exposure, 'held_base': held_base,
        'held_leveraged': held_lev, 'held_cash': held_cash, 'cost': cost,
    }).reindex(returns.index)
    return returns, weights


def frozen_pre2013(engine, symbol: str, bundle: dict) -> dict:
    benchmark = bundle['raw_returns']['buy_hold']
    rows = []
    for name, returns in bundle['raw_returns'].items():
        score, diagnostics = engine.development_score(
            returns.loc[:'2012-12-31'], benchmark.loc[:'2012-12-31']
        )
        rows.append({
            'candidate': name, 'family': bundle['raw_families'][name],
            'description': bundle['raw_descriptions'][name],
            'selection_score': score, **diagnostics,
        })
    ranking = pd.DataFrame(rows).sort_values(
        ['selection_score', 'candidate'], ascending=[False, False]
    ).reset_index(drop=True)
    winner = ranking.iloc[0]
    selected = str(winner.candidate)
    strategy = bundle['raw_returns'][selected].loc[OOS_START:].dropna()
    buy_hold = benchmark.reindex(strategy.index).dropna()
    common = strategy.index.intersection(buy_hold.index)
    strategy, buy_hold = strategy.reindex(common), buy_hold.reindex(common)
    sm, bm = engine.metrics(strategy), engine.metrics(buy_hold)
    alpha, beta = engine.regression_alpha(strategy, buy_hold)
    return {
        'symbol': symbol, 'selected_candidate': selected,
        'family': str(winner.family), 'description': str(winner.description),
        'development_end': '2012-12-31', 'oos_start': str(common.min().date()),
        'oos_end': str(common.max().date()), 'cagr': sm['cagr'],
        'buy_hold_cagr': bm['cagr'], 'cagr_delta': sm['cagr'] - bm['cagr'],
        'sharpe': sm['sharpe'], 'buy_hold_sharpe': bm['sharpe'],
        'sharpe_delta': sm['sharpe'] - bm['sharpe'], 'maxdd': sm['maxdd'],
        'buy_hold_maxdd': bm['maxdd'], 'dd_delta': sm['maxdd'] - bm['maxdd'],
        'annual_alpha': alpha, 'beta': beta, 'terminal': sm['terminal'],
        'buy_hold_terminal': bm['terminal'],
    }


def main() -> None:
    engine = load_engine()
    data = load_saved_data()
    bundles = {symbol: reconstruct_family_stream(engine, symbol, data) for symbol in engine.ASSETS}

    frozen_rows = [frozen_pre2013(engine, symbol, bundles[symbol]) for symbol in engine.ASSETS]
    frozen = pd.DataFrame(frozen_rows).sort_values('symbol')
    frozen.to_csv(OUT / 'pre2013_frozen_diagnostics.csv', index=False, float_format='%.8f')

    soxx = bundles['SOXX']
    exposure = soxx['final_exposures']['wf_trend_vol']
    if exposure is None:
        raise RuntimeError('SOXX trend-vol exposure missing')
    soxl = engine.download('SOXL')
    usd = engine.download('USD')
    soxl.to_csv(OUT / 'inputs' / 'SOXL.csv.gz', compression='gzip')
    usd.to_csv(OUT / 'inputs' / 'USD.csv.gz', compression='gzip')

    identity = pd.read_csv(OUT / 'strategy_identity.csv').set_index('symbol')
    inherited = identity.loc['SOXX']
    product_specs = [
        ('SOXX_USD_2X', usd, 2.0, 25.0),
        ('SOXX_SOXL_3X', soxl, 3.0, 18.0),
    ]
    result_rows, weight_summaries = [], []
    base, cash = soxx['frame'], soxx['cash']
    for implementation, product, multiple, lev_cost in product_specs:
        actual, weights = portfolio_path(engine, base, product, cash, exposure, multiple, 9.0, lev_cost, 1.0)
        stress2, _ = portfolio_path(engine, base, product, cash, exposure, multiple, 9.0, lev_cost, 2.0)
        stress3, _ = portfolio_path(engine, base, product, cash, exposure, multiple, 9.0, lev_cost, 3.0)
        benchmark = engine.open_to_open(base).reindex(actual.index).dropna()
        common = actual.index.intersection(benchmark.index)
        actual, stress2, stress3, benchmark = (
            actual.reindex(common), stress2.reindex(common),
            stress3.reindex(common), benchmark.reindex(common),
        )
        cash_common = cash.reindex(common).ffill().fillna(0.0)
        m, b, m2, m3 = (
            engine.metrics(actual), engine.metrics(benchmark),
            engine.metrics(stress2), engine.metrics(stress3),
        )
        alpha, beta = engine.regression_alpha(actual, benchmark)
        p_positive = engine.moving_block_probability(actual - benchmark)
        dsr = engine.deflated_sharpe_probability(actual - cash_common, 8)
        cagr_delta, sharpe_delta = m['cagr'] - b['cagr'], m['sharpe'] - b['sharpe']
        dd_delta, stress3_delta = m['maxdd'] - b['maxdd'], m3['cagr'] - b['cagr']
        gate = bool(
            cagr_delta >= 0.005 and sharpe_delta >= 0.0 and dd_delta >= -0.03
            and alpha >= 0.005 and stress3_delta > 0.0 and p_positive >= 0.80
            and dsr >= 0.80 and float(inherited.search_pbo) <= 0.30
        )
        result_rows.append({
            'implementation': implementation, 'start': str(common.min().date()),
            'end': str(common.max().date()), 'cagr': m['cagr'],
            'buy_hold_cagr': b['cagr'], 'cagr_delta': cagr_delta,
            'sharpe': m['sharpe'], 'buy_hold_sharpe': b['sharpe'],
            'sharpe_delta': sharpe_delta, 'maxdd': m['maxdd'],
            'buy_hold_maxdd': b['maxdd'], 'dd_delta': dd_delta,
            'annual_alpha': alpha, 'beta': beta, 'terminal': m['terminal'],
            'buy_hold_terminal': b['terminal'],
            'stress_2x_cagr_delta': m2['cagr'] - b['cagr'],
            'stress_3x_cagr_delta': stress3_delta,
            'bootstrap_p_positive': p_positive, 'dsr_probability': dsr,
            'inherited_search_pbo': float(inherited.search_pbo),
            'actual_product_gate': gate,
        })
        weight_summaries.append({
            'implementation': implementation,
            'average_effective_exposure': float(weights.signal_exposure.mean()),
            'current_effective_exposure': float(weights.signal_exposure.iloc[-1]),
            'average_base_weight': float(weights.held_base.mean()),
            'average_leveraged_weight': float(weights.held_leveraged.mean()),
            'average_cash_weight': float(weights.held_cash.mean()),
            'current_base_weight': float(weights.held_base.iloc[-1]),
            'current_leveraged_weight': float(weights.held_leveraged.iloc[-1]),
            'current_cash_weight': float(weights.held_cash.iloc[-1]),
            'annualised_one_way_turnover': float(
                (weights.held_base.diff().abs().fillna(0)
                 + weights.held_leveraged.diff().abs().fillna(0)).mean() * engine.DAYS
            ),
        })
    products = pd.DataFrame(result_rows).sort_values('implementation')
    products.to_csv(OUT / 'actual_product_validation.csv', index=False, float_format='%.8f')
    weights_frame = pd.DataFrame(weight_summaries).sort_values('implementation')
    weights_frame.to_csv(OUT / 'actual_product_weights.csv', index=False, float_format='%.8f')

    lines = [
        '# Actual-product and frozen-rule validation', '',
        '## SOXX actual-product paths', '', products.to_markdown(index=False), '',
        '## Actual-product weights', '', weights_frame.to_markdown(index=False), '',
        '## Pre-2013 single-selection frozen diagnostics', '', frozen.to_markdown(index=False), '',
        'The actual-product gate inherits the signal-family search PBO and independently re-tests CAGR, Sharpe, drawdown, beta-adjusted alpha, bootstrap probability, DSR and 3x transaction costs using adjusted SOXL or USD prices.',
    ]
    (OUT / 'implementation_report.md').write_text('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
