from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
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
    for col in exact:
        left = a[col].fillna('').astype(str)
        right = b[col].fillna('').astype(str)
        if not left.equals(right):
            diff = pd.DataFrame({'a': left, 'b': right})[left != right]
            raise RuntimeError(f'{name}: exact mismatch {col}: {diff.head().to_dict("records")}')
    maxima = {}
    for col, tol in tolerances.items():
        left = pd.to_numeric(a[col], errors='coerce')
        right = pd.to_numeric(b[col], errors='coerce')
        both_nan = left.isna() & right.isna()
        diff = (left - right).abs().mask(both_nan, 0.0)
        maximum = float(diff.max(skipna=True) or 0.0)
        maxima[col] = maximum
        if maximum > tol:
            raise RuntimeError(f'{name}: {col} max difference {maximum} > {tol}')
    a.to_csv(OUT / name, index=False, float_format='%.8f')
    return maxima


identity_diff = compare_frame(
    'strategy_identity.csv',
    keys=['symbol'],
    exact=['classification', 'candidate', 'family', 'description', 'return_alpha_gate', 'defensive_gate'],
    tolerances={
        'current_exposure': 1e-12,
        'cagr_delta': 0.001,
        'sharpe_delta': 0.01,
        'dd_delta': 0.004,
        'stress_3x_cagr_delta': 0.0015,
        'bootstrap_p_positive': 0.06,
        'dsr_probability': 0.08,
        'family_pbo': 0.08,
    },
)
window_diff = compare_frame(
    'window_comparison.csv',
    keys=['symbol', 'candidate', 'window'],
    exact=['start', 'end'],
    tolerances={'cagr': 0.0015, 'sharpe': 0.015, 'maxdd': 0.005, 'terminal': 75.0},
)
compare_frame(
    'ibkr_close_parity.csv',
    keys=['symbol'],
    exact=['date'],
    tolerances={'model_close': 0.05, 'ibkr_close': 0.0, 'absolute_pct_diff': 0.0002},
)

for rep in ['a', 'b']:
    parity = pd.read_csv(locate(rep, 'ibkr_close_parity.csv'))
    if (parity.absolute_pct_diff > 0.003).any():
        raise RuntimeError(f'{rep}: IBKR parity failed {parity.to_dict("records")}')

for name in ['report.md', 'run_manifest.json', 'input_manifest.json', 'candidate_grid.csv', 'block_diagnostics.csv']:
    shutil.copy2(locate('a', name), OUT / name)

identity_bytes = (OUT / 'strategy_identity.csv').read_bytes()
result = {
    'status': 'PASS',
    'canonical_identity_sha256': hashlib.sha256(identity_bytes).hexdigest(),
    'identity_metric_max_differences': identity_diff,
    'window_metric_max_differences': window_diff,
    'policy': 'exact strategy identity; numerical differences within fixed tolerances; IBKR completed-close parity required',
}
(OUT / 'repeatability.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
