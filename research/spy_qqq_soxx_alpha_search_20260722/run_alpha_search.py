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
source_bytes = gzip.decompress(base64.b64decode(payload.read_text().strip()))
digest = hashlib.sha256(source_bytes).hexdigest()
expected = "d72007c2fded90ac5282e222b40f76a97f1619871d601c644fa018daff7e2e4a"
if digest != expected:
    raise RuntimeError(f"source SHA mismatch: {digest} != {expected}")
source = source_bytes.decode("utf-8")
compile(source, "alpha_search_engine.py", "exec")
print({"source_sha256": digest, "source_bytes": len(source_bytes)})
namespace = {"__name__": "__main__", "__file__": str(ROOT / "alpha_search_engine.py")}
exec(compile(source, "alpha_search_engine.py", "exec"), namespace)
manifest_path = Path("research_outputs/spy_qqq_soxx_alpha_search_20260722/run_manifest.json")
manifest = json.loads(manifest_path.read_text())
manifest["source_sha256"] = digest
manifest_path.write_text(json.dumps(manifest, indent=2))
