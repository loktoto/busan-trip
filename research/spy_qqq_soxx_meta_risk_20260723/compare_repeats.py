from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path('repetitions')
OUT = Path('canonical')
OUT.mkdir(exist_ok=True)


def locate(rep: str, name: str) -> Path:
    matches = sorted(ROOT.glob(f'**/*-{rep}/**/{name}')) + sorted(ROOT.glob(f'**/{rep}/**/{name}'))
    matches = list(dict.fromkeys(matches))
    if len(matches) != 1:
        raise RuntimeError(f'expected one {name} for {rep}; found {matches}')
    return matches[0]


def compare_frame(name: str, keys: list[str], exact: list[str], tolerances: dict[str, float]) -> dict[str, float]:
    a = pd.read_csv(locate('a', name)).sort_values(keys).reset_index(drop=True)
    b = pd.read_csv(locate('b', name)).sort_values(keys).reset_index(drop=True)
    if a[keys].astype(str).to_dict('records') != b[keys].astype(str).to_dict('records'):
        raise RuntimeError(f'{name}: key mismatch')
    for column in exact:
        left = a[column].fillna('').astype(str)
        right = b[column].fillna('').astype(str)
        if not left.equals(right):
            diff = pd.DataFrame({'a': left, 'b': right})[left != right]
            raise RuntimeError(f'{name}: exact mismatch {column}: {diff.head().to_dict("records")}')
    maxima = {}
    for column, tolerance in tolerances.items():
        left = pd.to_numeric(a[column], errors='coerce')
        right = pd.to_numeric(b[column], errors='coerce')
        both_nan = left.isna() & right.isna()
        diff = (left - right).abs().mask(both_nan, 0.0)
        maximum = float(diff.max(skipna=True) or 0.0)
        maxima[column] = maximum
        if maximum > tolerance:
            raise RuntimeError(f'{name}: {column} max difference {maximum} > {tolerance}')
    a.to_csv(OUT / name, index=False, float_format='%.8f')
    return maxima


manifest_a = json.loads(locate('a', 'run_manifest.json').read_text())
manifest_b = json.loads(locate('b', 'run_manifest.json').read_text())
for field in ['cutoff', 'production_variant', 'target_vol', 'vol_lookback', 'scale_floor', 'scale_cap', 'gross_cap', 'classification', 'parent_source_sha256', 'meta_source_sha256']:
    if manifest_a.get(field) != manifest_b.get(field):
        raise RuntimeError(f'manifest mismatch {field}: {manifest_a.get(field)} != {manifest_b.get(field)}')

identity_diff = compare_frame(
    'strategy_identity.csv',
    keys=['production_variant'],
    exact=['classification', 'description', 'return_alpha_gate', 'dominates_soxx_buy_hold', 'start', 'end'],
    tolerances={
        'robust_variant_passes': 0.0, 'variant_count': 0.0,
        'current_portfolio_scale': 0.01, 'current_soxx_alpha_exposure': 0.01,
        'current_effective_gross_exposure': 0.01, 'cagr': 0.0015,
        'benchmark_cagr': 0.0015, 'cagr_delta': 0.0015,
        'sharpe_delta': 0.015, 'dd_delta': 0.005, 'annual_alpha': 0.0015,
        'stress_3x_cagr_delta': 0.002, 'bootstrap_p_positive': 0.06,
        'dsr_probability': 0.08, 'search_pbo': 0.08,
        'soxx_buy_hold_cagr': 0.0015, 'soxx_buy_hold_sharpe': 0.015,
        'soxx_buy_hold_maxdd': 0.005,
    },
)
grid_diff = compare_frame(
    'candidate_grid.csv',
    keys=['variant', 'route'],
    exact=['return_alpha_gate', 'start', 'end'],
    tolerances={
        'cagr': 0.0015, 'benchmark_cagr': 0.0015, 'cagr_delta': 0.0015,
        'sharpe': 0.015, 'benchmark_sharpe': 0.015, 'sharpe_delta': 0.015,
        'maxdd': 0.005, 'benchmark_maxdd': 0.005, 'dd_delta': 0.005,
        'vol': 0.005, 'annual_alpha': 0.0015, 'beta': 0.015,
        'stress_2x_cagr_delta': 0.002, 'stress_3x_cagr_delta': 0.002,
        'positive_cagr_blocks': 0.0, 'positive_sharpe_blocks': 0.0,
        'bootstrap_p_positive': 0.06, 'dsr_probability': 0.08,
        'search_pbo': 0.08, 'selection_frequency': 0.08, 'conditional_pbo': 0.08,
        'terminal': 100.0, 'benchmark_terminal': 100.0,
    },
)
weights_diff = compare_frame(
    'current_weights.csv',
    keys=['variant'],
    exact=['signal_date'],
    tolerances={column: 0.012 for column in [
        'portfolio_scale', 'soxx_alpha_exposure', 'effective_gross_exposure',
        'weight_spy', 'weight_qqq', 'weight_soxx', 'weight_sso', 'weight_qld', 'weight_usd', 'weight_cash',
    ]},
)
window_diff = compare_frame(
    'window_comparison.csv',
    keys=['candidate', 'window'],
    exact=['start', 'end'],
    tolerances={'cagr': 0.002, 'sharpe': 0.02, 'maxdd': 0.006, 'vol': 0.006, 'calmar': 0.03, 'terminal': 150.0, 'skew': 0.05, 'kurt': 0.15},
)
compare_frame(
    'ibkr_close_parity.csv',
    keys=['symbol'],
    exact=['date'],
    tolerances={'model_close': 0.08, 'ibkr_close': 0.0, 'absolute_pct_diff': 0.0003},
)
compare_frame(
    'inherited_soxx_choices.csv',
    keys=['year'],
    exact=['selected_candidate', 'development_end'],
    tolerances={},
)

for rep in ['a', 'b']:
    parity = pd.read_csv(locate(rep, 'ibkr_close_parity.csv'))
    if (parity.absolute_pct_diff > 0.003).any():
        raise RuntimeError(f'{rep}: IBKR parity failed')

for name in ['report.md', 'run_manifest.json', 'input_manifest.json', 'block_diagnostics.csv']:
    shutil.copy2(locate('a', name), OUT / name)

identity_bytes = (OUT / 'strategy_identity.csv').read_bytes()
result = {
    'status': 'PASS',
    'canonical_identity_sha256': hashlib.sha256(identity_bytes).hexdigest(),
    'identity_metric_max_differences': identity_diff,
    'candidate_metric_max_differences': grid_diff,
    'weight_metric_max_differences': weights_diff,
    'window_metric_max_differences': window_diff,
    'policy': 'fixed production variant; at least three of four strategic-weight variants must pass; exact classification and product-weight identity; numerical tolerances; IBKR completed-close parity',
}
(OUT / 'repeatability.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
