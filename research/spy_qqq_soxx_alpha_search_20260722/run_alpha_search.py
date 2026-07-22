from __future__ import annotations

import base64
import gzip
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
parts = sorted(ROOT.glob("source.part??"))
if len(parts) != 2:
    raise RuntimeError(f"expected two source payload parts; found {parts}")
source_bytes = gzip.decompress(base64.b64decode("".join(p.read_text().strip() for p in parts)))
digest = hashlib.sha256(source_bytes).hexdigest()
expected = "419857ef2492665d60f8bcd955aee4f85601d6d0de5854cff9fb5c6d0f678e7c"
if digest != expected:
    raise RuntimeError(f"source SHA mismatch: {digest} != {expected}")
source = source_bytes.decode("utf-8")
compile(source, "alpha_search_engine.py", "exec")
print({"source_sha256": digest, "source_bytes": len(source_bytes), "parts": len(parts)})
namespace = {"__name__": "__main__", "__file__": str(ROOT / "alpha_search_engine.py")}
exec(compile(source, "alpha_search_engine.py", "exec"), namespace)
