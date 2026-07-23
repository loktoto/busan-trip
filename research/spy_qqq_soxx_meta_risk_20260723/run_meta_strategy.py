from __future__ import annotations

import base64
import gzip
import hashlib
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
payload = ROOT / 'source.b64'
raw = gzip.decompress(base64.b64decode(payload.read_text().strip()))
raw_digest = hashlib.sha256(raw).hexdigest()
expected_raw = 'ee1453d55a7b528e7084e575f283af60237b9b562883e02a322fdd68809d129d'
if raw_digest != expected_raw:
    raise RuntimeError(f'raw meta source SHA mismatch: {raw_digest} != {expected_raw}')
source = raw.decode('utf-8')

old_benchmark = '''def benchmark_return(data: dict[str, pd.DataFrame], budgets: dict[str, float], index: pd.DatetimeIndex) -> pd.Series:
    return sum(budgets[s] * open_to_open(data[s]).reindex(index) for s in budgets).dropna()
'''
new_benchmark = '''def benchmark_return(data: dict[str, pd.DataFrame], budgets: dict[str, float], index: pd.DatetimeIndex) -> pd.Series:
    # Literal Buy & Hold: invest the strategic capital weights once at the first
    # OOS open and allow weights to drift thereafter. Returns are indexed by the
    # signal date, matching the open-to-next-open convention used by the strategy.
    start = index.min()
    common = None
    for symbol in budgets:
        dates = data[symbol].index[data[symbol].index >= start]
        common = dates if common is None else common.intersection(dates)
    common = common[common <= CUTOFF]
    opens = pd.DataFrame({symbol: data[symbol]['Open'].reindex(common) for symbol in budgets}).dropna()
    first = opens.iloc[0]
    wealth = sum(budgets[symbol] * opens[symbol] / first[symbol] for symbol in budgets)
    returns = wealth.shift(-1) / wealth - 1.0
    return returns.reindex(index).dropna()
'''
if source.count(old_benchmark) != 1:
    raise RuntimeError(f'expected one benchmark function, found {source.count(old_benchmark)}')
source = source.replace(old_benchmark, new_benchmark)
old_label = "('same_weight_buy_hold', prod_bench)"
new_label = "('initial_weight_buy_hold', prod_bench)"
if source.count(old_label) != 1:
    raise RuntimeError(f'expected one benchmark label, found {source.count(old_label)}')
source = source.replace(old_label, new_label)

patched = source.encode('utf-8')
patched_digest = hashlib.sha256(patched).hexdigest()
expected_patched = 'e3e0cbb93947a9fe1546b4ef365d4f3723cd0ae7c59e6776b0634baf3873f0d1'
if patched_digest != expected_patched:
    raise RuntimeError(f'patched meta source SHA mismatch: {patched_digest} != {expected_patched}')
compile(source, 'meta_strategy_engine.py', 'exec')
engine_path = ROOT / 'meta_strategy_engine.py'
engine_path.write_bytes(patched)
print({'raw_meta_source_sha256': raw_digest, 'patched_meta_source_sha256': patched_digest, 'patched_bytes': len(patched)})
runpy.run_path(str(engine_path), run_name='__main__')
