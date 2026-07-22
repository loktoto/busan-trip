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


def compare(name: str, keys: list[str], exact: list[str], tolerances: dict[str, float]) -> dict[str, float]:
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
        difference = (left - right).abs().mask(both_nan, 0.0)
        maximum = float(difference.max(skipna=True) or 0.0)
        maxima[column] = maximum
        if maximum > tolerance:
            raise RuntimeError(f'{name}: {column} difference {maximum} > {tolerance}')
    a.to_csv(OUT / name, index=False, float_format='%.8f')
    return maxima


identity_diff = compare(
    'strategy_identity.csv', ['candidate'],
    ['classification','description','return_alpha_gate','defensive_gate','start','end'],
    {'current_spy_weight':1e-12,'current_qqq_weight':1e-12,'current_soxx_weight':1e-12,'current_cash_weight':1e-12,
     'cagr_delta':0.0015,'sharpe_delta':0.015,'dd_delta':0.005,'annual_alpha':0.0015,'beta':0.015,
     'stress_3x_cagr_delta':0.002,'bootstrap_p_positive':0.06,'dsr_probability':0.08,'search_pbo':0.08},
)
grid_diff = compare(
    'candidate_grid.csv', ['candidate'],
    ['description','return_alpha_gate','defensive_gate','start','end'],
    {'cagr':0.002,'benchmark_cagr':0.001,'cagr_delta':0.002,'sharpe':0.02,'benchmark_sharpe':0.01,
     'sharpe_delta':0.02,'maxdd':0.006,'benchmark_maxdd':0.003,'dd_delta':0.006,
     'annual_alpha':0.002,'beta':0.02,'stress_3x_cagr_delta':0.003,'bootstrap_p_positive':0.07,
     'dsr_probability':0.08,'search_pbo':0.08,'selection_frequency':0.08,'conditional_pbo':0.08,
     'terminal':200.0,'benchmark_terminal':100.0,'spy_buy_hold_terminal':100.0,'qqq_buy_hold_terminal':150.0,
     'soxx_buy_hold_terminal':300.0,'average_turnover':0.002,'quality':0.004},
)
window_diff = compare(
    'window_comparison.csv', ['candidate','window'], ['start','end'],
    {'cagr':0.002,'sharpe':0.02,'maxdd':0.006,'terminal':150.0},
)
compare(
    'block_diagnostics.csv', ['candidate','block'], ['start','end'],
    {'cagr_delta':0.005,'sharpe_delta':0.05,'dd_delta':0.012},
)
manifest_a = json.loads(locate('a','run_manifest.json').read_text())
manifest_b = json.loads(locate('b','run_manifest.json').read_text())
if manifest_a['identity_sha256'] != manifest_b['identity_sha256']:
    raise RuntimeError('identity SHA mismatch')
for name in ['report.md','run_manifest.json','current_strategy_weights.csv']:
    shutil.copy2(locate('a', name), OUT / name)
identity_bytes = (OUT/'strategy_identity.csv').read_bytes()
result = {
    'status':'PASS',
    'canonical_identity_sha256':hashlib.sha256(identity_bytes).hexdigest(),
    'identity_metric_max_differences':identity_diff,
    'candidate_metric_max_differences':grid_diff,
    'window_metric_max_differences':window_diff,
    'policy':'candidate identity and classification must match exactly; numerical results within fixed tolerances',
}
(OUT/'repeatability.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
