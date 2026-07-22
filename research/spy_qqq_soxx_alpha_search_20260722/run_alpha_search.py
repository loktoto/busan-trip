from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
payload = ROOT / "source_v2.b64"
if not payload.exists():
    raise RuntimeError("missing anchored walk-forward source payload")
raw_bytes = gzip.decompress(base64.b64decode(payload.read_text().strip()))
raw_digest = hashlib.sha256(raw_bytes).hexdigest()
expected_raw = "d72007c2fded90ac5282e222b40f76a97f1619871d601c644fa018daff7e2e4a"
if raw_digest != expected_raw:
    raise RuntimeError(f"raw source SHA mismatch: {raw_digest} != {expected_raw}")
source = raw_bytes.decode("utf-8")

old_dsr = '''def deflated_sharpe_probability(returns: pd.Series, n_trials: int) -> float:
    x = returns.replace([np.inf, -np.inf], np.nan).dropna()
    if len(x) < 100:
        return np.nan
    m = metrics(x)
    sr = m["sharpe"]
    sr0 = math.sqrt(max(0.0, 2.0 * math.log(max(2, n_trials)))) / math.sqrt(len(x) / DAYS)
    denom = math.sqrt(max(1e-9, 1 - m["skew"] * sr + ((m["kurt"] - 1) / 4.0) * sr * sr))
    z = (sr - sr0) * math.sqrt(max(1, len(x) - 1)) / denom
    return float(norm.cdf(z))


'''
new_dsr = '''def effective_trial_count(
    raw_returns: dict[str, pd.Series],
    raw_families: dict[str, str],
    cash: pd.Series,
    development_end: pd.Timestamp = pd.Timestamp("2012-12-31"),
) -> tuple[int, float]:
    # Estimate independent trials from the development-period correlation
    # structure, with a floor at the number of economic strategy families.
    names = [name for name in sorted(raw_returns) if name != "buy_hold"]
    family_count = len({raw_families[name] for name in names if raw_families[name] != "baseline"})
    series = {}
    for name in names:
        ret = raw_returns[name].loc[:development_end]
        excess_cash = ret - cash.reindex(ret.index).fillna(0.0)
        if excess_cash.dropna().std(ddof=1) > 1e-12:
            series[name] = excess_cash
    if len(series) < 2:
        return max(2, family_count), float(max(1, family_count))
    frame = pd.concat(series, axis=1).dropna(how="all")
    corr = frame.corr(min_periods=252).replace([np.inf, -np.inf], np.nan)
    valid = corr.columns[corr.notna().sum(axis=0) >= max(2, int(0.8 * len(corr.columns)))]
    corr = corr.loc[valid, valid].fillna(0.0)
    if len(corr) < 2:
        return max(2, family_count), float(max(1, family_count))
    matrix = (corr.to_numpy(float) + corr.to_numpy(float).T) / 2.0
    np.fill_diagonal(matrix, 1.0)
    eigenvalues = np.linalg.eigvalsh(matrix)
    eigenvalues = np.clip(eigenvalues, 0.0, None)
    participation_ratio = float(eigenvalues.sum() ** 2 / max(1e-12, np.square(eigenvalues).sum()))
    effective = max(2, family_count, int(math.ceil(participation_ratio)))
    return effective, participation_ratio


def deflated_sharpe_probability(returns: pd.Series, n_trials: int) -> float:
    # metrics() reports annualised Sharpe, so the sampling horizon is years.
    x = returns.replace([np.inf, -np.inf], np.nan).dropna()
    if len(x) < 100:
        return np.nan
    m = metrics(x)
    sr = m["sharpe"]
    years = max(len(x) / DAYS, (x.index[-1] - x.index[0]).days / 365.25)
    sr0 = math.sqrt(max(0.0, 2.0 * math.log(max(2, n_trials)))) / math.sqrt(years)
    denom = math.sqrt(max(1e-9, 1 - m["skew"] * sr + ((m["kurt"] - 1) / 4.0) * sr * sr))
    z = (sr - sr0) * math.sqrt(years) / denom
    return float(norm.cdf(z))


'''
replacements = [
    (old_dsr, new_dsr),
    (
        '''    search_pbo, pbo_details = cscv_search_pbo(search_candidates, benchmark)\n    raw_trial_count = len(raw_returns) - 1\n''',
        '''    search_pbo, pbo_details = cscv_search_pbo(search_candidates, benchmark)\n    effective_trials, participation_ratio = effective_trial_count(raw_returns, raw_families, cash)\n''',
    ),
    (
        '''        p_positive = np.nan if name == "buy_hold" else moving_block_probability(excess)\n        dsr = np.nan if name == "buy_hold" else deflated_sharpe_probability(excess, raw_trial_count)\n''',
        '''        p_positive = np.nan if name == "buy_hold" else moving_block_probability(excess)\n        excess_cash = candidate_ret - cash.reindex(candidate_ret.index).fillna(0.0)\n        dsr = np.nan if name == "buy_hold" else deflated_sharpe_probability(excess_cash, effective_trials)\n''',
    ),
    (
        '''            "dsr_probability": dsr,\n            "search_pbo": search_pbo,\n''',
        '''            "dsr_probability": dsr,\n            "effective_trials": effective_trials,\n            "trial_participation_ratio": participation_ratio,\n            "search_pbo": search_pbo,\n''',
    ),
]
for old, new in replacements:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"deterministic patch expected one match, found {count}")
    source = source.replace(old, new)

patched_bytes = source.encode("utf-8")
patched_digest = hashlib.sha256(patched_bytes).hexdigest()
expected_patched = "2ee009cf9f0ccb6e0ad41e3f6327e90813d3327beb18204a5a34ab6cbf11c3aa"
if patched_digest != expected_patched:
    raise RuntimeError(f"patched source SHA mismatch: {patched_digest} != {expected_patched}")
compile(source, "alpha_search_engine.py", "exec")
print({"raw_source_sha256": raw_digest, "patched_source_sha256": patched_digest, "patched_bytes": len(patched_bytes)})
namespace = {"__name__": "__main__", "__file__": str(ROOT / "alpha_search_engine.py")}
exec(compile(source, "alpha_search_engine.py", "exec"), namespace)
manifest_path = Path("research_outputs/spy_qqq_soxx_alpha_search_20260722/run_manifest.json")
manifest = json.loads(manifest_path.read_text())
manifest["raw_source_sha256"] = raw_digest
manifest["source_sha256"] = patched_digest
manifest["dsr_method"] = "annualised Sharpe; sampling horizon in years; excess over cash; effective-trial floor equals eight economic families"
manifest_path.write_text(json.dumps(manifest, indent=2))
