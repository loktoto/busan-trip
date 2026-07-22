from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
parts = sorted(ROOT.glob("source_v3.part??"))
if len(parts) != 4:
    raise RuntimeError(f"expected four corrected source parts; found {parts}")
source_bytes = gzip.decompress(base64.b64decode("".join(part.read_text().strip() for part in parts)))
digest = hashlib.sha256(source_bytes).hexdigest()
expected = "f381e7642f1f61f05e8e5715878226395b779ebb6f7ab480789217d7c8cb41b3"
if digest != expected:
    raise RuntimeError(f"source SHA mismatch: {digest} != {expected}")
source = source_bytes.decode("utf-8")
compile(source, "alpha_search_engine.py", "exec")
print({"source_sha256": digest, "source_bytes": len(source_bytes), "parts": len(parts)})
namespace = {"__name__": "__main__", "__file__": str(ROOT / "alpha_search_engine.py")}
exec(compile(source, "alpha_search_engine.py", "exec"), namespace)
manifest_path = Path("research_outputs/spy_qqq_soxx_alpha_search_20260722/run_manifest.json")
manifest = json.loads(manifest_path.read_text())
manifest["source_sha256"] = digest
manifest["dsr_method"] = "annualised Sharpe; sampling horizon in years; excess over cash; effective-trial floor equals eight economic families"
manifest_path.write_text(json.dumps(manifest, indent=2))
