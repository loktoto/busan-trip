from __future__ import annotations

import hashlib
import json
from pathlib import Path

SOURCE = Path(__file__).with_name("run_core_satellite.py")
text = SOURCE.read_text()
replacements = [
    ('str(central.product)', 'str(central["product"])', 1),
    ('str(selected_row.product)', 'str(selected_row["product"])', 4),
]
for old, new, expected in replacements:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"deterministic product-column fix expected {expected} matches for {old!r}, found {count}")
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
manifest["deterministic_hotfix"] = "use Series['product'] instead of Series.product at five output-only access sites"
manifest_path.write_text(json.dumps(manifest, indent=2))
print({"raw_source_sha256": raw_sha, "patched_source_sha256": patched_sha, "hotfix": manifest["deterministic_hotfix"]})
