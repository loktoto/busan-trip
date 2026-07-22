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
    left = pd.read_csv(locate('a', name)).sort_values(keys).reset_index(drop=True)
    right = pd.read_csv(locate('b', name)).sort_values(keys).reset_index(drop=True)
    if left[keys].astype(str).to_dict('records') != right[keys].astype(str).to_dict('records'):
        raise RuntimeError(f'{name}: key mismatch')
    for column in exact:
        a = left[column].fillna('').astype(str)
        b = right[column].fillna('').astype(str)
        if not a.equals(b):
            diff = pd.DataFrame({'a': a, 'b': b})[a != b]
            raise RuntimeError(f'{name}: exact mismatch in {column}: {diff.head().to_dict("records")}')
    maxima = {}
    for column, tolerance in tolerances.items():
        a = pd.to_numeric(left[column], errors='coerce')
        b = pd.to_numeric(right[column], errors='coerce')
        both_nan = a.isna() & b.isna()
        difference = (a - b).abs().mask(both_nan, 0.0)
        maximum = float(difference.max(skipna=True) or 0.0)
        maxima[column] = maximum
        if maximum > tolerance:
            raise RuntimeError(f'{name}: {column} difference {maximum} > {tolerance}')
    left.to_csv(OUT / name, index=False, float_format='%.8f')
    return maxima


identity_diff = compare(
    'strategy_identity.csv', ['symbol'],
    ['classification','candidate','family','description','signal_return_alpha_gate','signal_defensive_gate','actual_product_pass','oos_start','oos_end'],
    {'current_model_exposure':1e-12,'current_production_exposure':1e-12,'cagr_delta':0.001,
     'sharpe_delta':0.01,'dd_delta':0.004,'annual_alpha':0.001,'beta':0.01,
     'stress_3x_cagr_delta':0.0015,'bootstrap_p_positive':0.06,'dsr_probability':0.08,'search_pbo':0.08},
)
grid_diff = compare(
    'fixed_candidate_grid.csv', ['symbol','candidate'],
    ['family','description','return_alpha_gate','defensive_gate','oos_start','oos_end'],
    {'current_exposure':1e-12,'average_exposure':0.003,'cagr':0.0015,'cagr_delta':0.0015,
     'sharpe':0.015,'sharpe_delta':0.015,'maxdd':0.005,'dd_delta':0.005,
     'annual_alpha':0.0015,'beta':0.015,'stress_3x_cagr_delta':0.002,
     'bootstrap_p_positive':0.06,'dsr_probability':0.08,'search_pbo':0.08,
     'selection_frequency':0.08,'conditional_pbo':0.08,'terminal':100.0},
)
product_diff = compare(
    'actual_product_validation.csv', ['symbol','implementation'],
    ['ticker','candidate','start','end','actual_product_gate'],
    {'multiple':0.0,'cagr':0.003,'buy_hold_cagr':0.0015,'cagr_delta':0.003,
     'sharpe':0.025,'sharpe_delta':0.025,'maxdd':0.008,'dd_delta':0.008,
     'annual_alpha':0.003,'beta':0.02,'stress_3x_cagr_delta':0.004,
     'bootstrap_p_positive':0.08,'dsr_probability':0.08,'search_pbo':0.08,'terminal':300.0},
)
weight_diff = compare(
    'actual_product_weights.csv', ['symbol','implementation'], [],
    {'current_effective_exposure':1e-12,'current_base_weight':1e-12,'current_product_weight':1e-12,
     'current_cash_weight':1e-12,'average_effective_exposure':0.003,'average_product_weight':0.003},
)
compare(
    'block_diagnostics.csv', ['symbol','candidate','block'], ['start','end'],
    {'cagr_delta':0.004,'sharpe_delta':0.04,'dd_delta':0.01},
)

manifest_a = json.loads(locate('a', 'run_manifest.json').read_text())
manifest_b = json.loads(locate('b', 'run_manifest.json').read_text())
if manifest_a['identity_sha256'] != manifest_b['identity_sha256']:
    raise RuntimeError('identity hash mismatch')
for name in ['report.md','run_manifest.json']:
    shutil.copy2(locate('a', name), OUT / name)
identity_bytes = (OUT / 'strategy_identity.csv').read_bytes()
result = {
    'status':'PASS',
    'canonical_identity_sha256':hashlib.sha256(identity_bytes).hexdigest(),
    'identity_metric_max_differences':identity_diff,
    'candidate_metric_max_differences':grid_diff,
    'product_metric_max_differences':product_diff,
    'weight_metric_max_differences':weight_diff,
    'policy':'fixed candidate identity and product gate must match exactly; numerical results within fixed tolerances',
}
(OUT / 'repeatability.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
