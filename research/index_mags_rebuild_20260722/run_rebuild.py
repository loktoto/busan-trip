from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
parts = sorted(ROOT.glob("source_v2.part??"))
if len(parts) != 6:
    raise RuntimeError(f"Expected six rebuilt V2 source parts; found {parts}")
encoded = "".join(part.read_text().strip() for part in parts)
source_bytes = gzip.decompress(base64.b64decode(encoded))
source_sha = hashlib.sha256(source_bytes).hexdigest()
source = source_bytes.decode("utf-8")
compiled = compile(source, "index_mags_rebuild_v2.py", "exec")
print({"research_source_sha256": source_sha, "source_bytes": len(source_bytes), "parts": len(parts)})
namespace = {"__name__": "__main__", "__file__": str(ROOT / "index_mags_rebuild_v2.py")}
exec(compiled, namespace)
manifest_path = Path("research_outputs/index_mags_rebuild_20260722/run_manifest.json")
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text())
    manifest["research_source_sha256"] = source_sha
    manifest_path.write_text(json.dumps(manifest, indent=2))
