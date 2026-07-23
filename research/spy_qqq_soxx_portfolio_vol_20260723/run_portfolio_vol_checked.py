from __future__ import annotations

import hashlib
import json
from pathlib import Path

SOURCE = Path(__file__).with_name("run_portfolio_vol.py")
text = SOURCE.read_text()

old_month_block = '''    month = projected.index.to_period('M')
    monthly = projected.where(pd.Series(month != month.shift(1), index=projected.index), np.nan).ffill()
    return monthly.fillna(BASE_WEIGHTS)
'''
new_month_block = '''    # PeriodIndex.shift() changes calendar values rather than moving rows. Use a
    # position-aligned Series so monthly refresh is determined from the prior row.
    month = pd.Series(projected.index.to_period('M'), index=projected.index)
    monthly = projected.where(month.ne(month.shift(1)), np.nan).ffill()
    return monthly.fillna(BASE_WEIGHTS)
'''

replacements = [(old_month_block, new_month_block, 1)]
for old, new, expected in replacements:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(
            f"deterministic portfolio-vol patch expected {expected} matches, found {count}"
        )
    text = text.replace(old, new)

raw_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
patched_sha = hashlib.sha256(text.encode()).hexdigest()
compiled = compile(text, str(SOURCE), "exec")
namespace = {"__name__": "__main__", "__file__": str(SOURCE)}
exec(compiled, namespace)

manifest_path = Path("research_outputs/spy_qqq_soxx_portfolio_vol_20260723/run_manifest.json")
manifest = json.loads(manifest_path.read_text())
manifest["raw_portfolio_vol_source_sha256"] = raw_sha
manifest["patched_portfolio_vol_source_sha256"] = patched_sha
manifest["deterministic_hotfix"] = (
    "use position-aligned monthly Period Series for shrinkage inverse-volatility allocation refresh"
)
manifest_path.write_text(json.dumps(manifest, indent=2))
print(
    {
        "raw_source_sha256": raw_sha,
        "patched_source_sha256": patched_sha,
        "hotfix": manifest["deterministic_hotfix"],
    }
)
