from __future__ import annotations

import hashlib
import json
from pathlib import Path

SOURCE = Path(__file__).with_name("run_core_satellite.py")
text = SOURCE.read_text()
old_pbo = '''    excess_returns = {
        name: candidate_returns[name] - candidate_benchmarks[name].reindex(candidate_returns[name].index)
        for name in candidate_returns
    }
    search_pbo, pbo_details = cscv_pbo(excess_returns)
    effective_trials, participation_ratio = effective_trial_count(excess_returns)
'''
new_pbo = '''    # Production sleeve is fixed ex ante at 20%; other sleeve sizes are robustness
    # diagnostics and are never searched. Therefore selection PBO is computed only
    # across the twelve economic families at the fixed production sleeve.
    selection_excess_returns = {
        name: candidate_returns[name] - candidate_benchmarks[name].reindex(candidate_returns[name].index)
        for name in candidate_returns
        if abs(float(candidate_metadata[name]["sleeve"]) - 0.20) < 1e-12
    }
    if len(selection_excess_returns) != TRIAL_FLOOR:
        raise RuntimeError(f"expected {TRIAL_FLOOR} fixed-sleeve families, found {len(selection_excess_returns)}")
    search_pbo, pbo_details = cscv_pbo(selection_excess_returns)
    effective_trials, participation_ratio = effective_trial_count(selection_excess_returns)
'''
replacements = [
    ('str(central.product)', 'str(central["product"])', 1),
    ('str(selected_row.product)', 'str(selected_row["product"])', 4),
    (old_pbo, new_pbo, 1),
]
for old, new, expected in replacements:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"deterministic core-satellite patch expected {expected} matches, found {count}")
    text = text.replace(old, new)

raw_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
patched_sha = hashlib.sha256(text.encode()).hexdigest()
compile(text, str(SOURCE), "exec")
namespace = {"__name__": "__main__", "__file__": str(SOURCE)}
exec(compile(text, str(SOURCE), "exec"), namespace)

manifest_path = Path("research_outputs/spy_qqq_soxx_core_satellite_20260723/run_manifest.json")
manifest = json.loads(manifest_path.read_text())
manifest["raw_core_satellite_source_sha256"] = raw_sha
manifest["patched_core_satellite_source_sha256"] = patched_sha
manifest["deterministic_hotfix"] = "bracket product-column access; compute PBO only across twelve fixed-20%-sleeve economic families"
manifest["pbo_universe"] = "twelve 20% production-sleeve families; 10/15/25/30% sleeves are robustness diagnostics only"
manifest_path.write_text(json.dumps(manifest, indent=2))
print({"raw_source_sha256": raw_sha, "patched_source_sha256": patched_sha, "hotfix": manifest["deterministic_hotfix"]})
