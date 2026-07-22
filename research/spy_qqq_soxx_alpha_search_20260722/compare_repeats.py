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
    maxima: dict[str, float] = {}
    for column, tolerance in tolerances.items():
        left = pd.to_numeric(a[column], errors='coerce')
        right = pd.to_numeric(b[column], errors='coerce')
        both_nan = left.isna() & right.isna()
        difference = (left - right).abs().mask(both_nan, 0.0)
        maximum = float(difference.max(skipna=True) or 0.0)
        maxima[column] = maximum
        if maximum > tolerance:
            raise RuntimeError(f'{name}: {column} max difference {maximum} > {tolerance}')
    a.to_csv(OUT / name, index=False, float_format='%.8f')
    return maxima


manifest_a = json.loads(locate('a', 'run_manifest.json').read_text())
manifest_b = json.loads(locate('b', 'run_manifest.json').read_text())
source_sha = manifest_a.get('source_sha256')
raw_source_sha = manifest_a.get('raw_source_sha256')
if source_sha != '2ee009cf9f0ccb6e0ad41e3f6327e90813d3327beb18204a5a34ab6cbf11c3aa':
    raise RuntimeError(f'unexpected patched source {source_sha}')
if raw_source_sha != 'd72007c2fded90ac5282e222b40f76a97f1619871d601c644fa018daff7e2e4a':
    raise RuntimeError(f'unexpected raw source {raw_source_sha}')
if source_sha != manifest_b.get('source_sha256') or raw_source_sha != manifest_b.get('raw_source_sha256'):
    raise RuntimeError('A/B source mismatch')
expected_method = 'annualised Sharpe; sampling horizon in years; excess over cash; effective-trial floor equals eight economic families'
if manifest_a.get('dsr_method') != expected_method or manifest_b.get('dsr_method') != expected_method:
    raise RuntimeError('corrected DSR method marker missing')

identity_diff = compare_frame(
    'strategy_identity.csv', ['symbol'],
    ['classification','candidate','family','description','return_alpha_gate','defensive_gate','oos_start','oos_end'],
    {'current_model_exposure':1e-12,'current_production_exposure':1e-12,'average_exposure':0.002,
     'cagr_delta':0.001,'sharpe_delta':0.01,'dd_delta':0.004,'annual_alpha':0.001,'beta':0.01,
     'stress_3x_cagr_delta':0.0015,'bootstrap_p_positive':0.06,'dsr_probability':0.08,
     'search_pbo':0.08,'selection_frequency':0.08,'conditional_pbo':0.08},
)
window_diff = compare_frame(
    'window_comparison.csv', ['symbol','candidate','window'], ['start','end'],
    {'cagr':0.0015,'sharpe':0.015,'maxdd':0.005,'terminal':75.0},
)
choice_diff = compare_frame(
    'walk_forward_choices.csv', ['symbol','family','year'], ['dev_end','selected_candidate','selected_description'],
    {'selection_score':0.01,'dev_cagr_delta':0.003,'dev_sharpe_delta':0.03,'dev_dd_delta':0.01,
     'dev_median_block_cagr_delta':0.006,'dev_median_block_sharpe_delta':0.05,'dev_worst_block_sharpe_delta':0.08},
)
grid_diff = compare_frame(
    'candidate_grid.csv', ['symbol','candidate'],
    ['family','description','return_alpha_gate','defensive_gate','oos_start','oos_end'],
    {'cagr':0.0015,'sharpe':0.015,'maxdd':0.005,'annual_alpha':0.0015,'beta':0.015,
     'stress_3x_cagr_delta':0.002,'bootstrap_p_positive':0.06,'dsr_probability':0.08,
     'effective_trials':0.0,'trial_participation_ratio':0.15,'search_pbo':0.08},
)
product_diff = compare_frame(
    'actual_product_validation.csv', ['implementation'], ['start','end','actual_product_gate'],
    {'cagr':0.003,'buy_hold_cagr':0.0015,'cagr_delta':0.003,'sharpe':0.025,
     'sharpe_delta':0.025,'maxdd':0.008,'dd_delta':0.008,'annual_alpha':0.003,'beta':0.02,
     'terminal':250.0,'stress_3x_cagr_delta':0.004,'bootstrap_p_positive':0.08,
     'dsr_probability':0.08,'inherited_search_pbo':0.08},
)
weights_diff = compare_frame(
    'actual_product_weights.csv', ['implementation'], [],
    {'average_effective_exposure':0.002,'current_effective_exposure':1e-12,
     'average_base_weight':0.003,'average_leveraged_weight':0.003,'average_cash_weight':0.003,
     'current_base_weight':1e-12,'current_leveraged_weight':1e-12,'current_cash_weight':1e-12,
     'annualised_one_way_turnover':0.05},
)
frozen_diff = compare_frame(
    'pre2013_frozen_diagnostics.csv', ['symbol'],
    ['selected_candidate','family','description','development_end','oos_start','oos_end'],
    {'cagr':0.002,'buy_hold_cagr':0.0015,'cagr_delta':0.002,'sharpe':0.02,
     'sharpe_delta':0.02,'maxdd':0.006,'dd_delta':0.006,'annual_alpha':0.002,'beta':0.015,
     'terminal':150.0},
)
compare_frame(
    'ibkr_close_parity.csv', ['symbol'], ['date'],
    {'model_close':0.05,'ibkr_close':0.0,'absolute_pct_diff':0.0002},
)

for rep in ['a','b']:
    parity = pd.read_csv(locate(rep, 'ibkr_close_parity.csv'))
    if (parity.absolute_pct_diff > 0.003).any():
        raise RuntimeError(f'{rep}: IBKR parity failed')

for name in ['report.md','implementation_report.md','run_manifest.json','input_manifest.json','block_diagnostics.csv']:
    shutil.copy2(locate('a', name), OUT / name)

identity_bytes = (OUT / 'strategy_identity.csv').read_bytes()
result = {
    'status':'PASS','raw_source_sha256':raw_source_sha,'source_sha256':source_sha,
    'canonical_identity_sha256':hashlib.sha256(identity_bytes).hexdigest(),
    'identity_metric_max_differences':identity_diff,
    'candidate_grid_metric_max_differences':grid_diff,
    'window_metric_max_differences':window_diff,
    'walk_forward_metric_max_differences':choice_diff,
    'actual_product_metric_max_differences':product_diff,
    'actual_product_weight_max_differences':weights_diff,
    'frozen_rule_metric_max_differences':frozen_diff,
    'policy':'exact annual choices, classification, actual-product gate and frozen-rule identity; fixed numerical tolerances; IBKR parity required',
}
(OUT/'repeatability.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
