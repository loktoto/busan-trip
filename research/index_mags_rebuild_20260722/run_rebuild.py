from __future__ import annotations

import base64
import gzip
from pathlib import Path

ROOT = Path(__file__).resolve().parent
parts = sorted(ROOT.glob("source_v3.part??"))
if not parts:
    raise RuntimeError("Missing rebuilt V3 source payload")
encoded = "".join(part.read_text().strip() for part in parts)
source = gzip.decompress(base64.b64decode(encoded)).decode("utf-8")
compile(source, "index_mags_rebuild_v3.py", "exec")
namespace = {"__name__": "__main__", "__file__": str(ROOT / "index_mags_rebuild_v3.py")}
exec(compile(source, "index_mags_rebuild_v3.py", "exec"), namespace)
