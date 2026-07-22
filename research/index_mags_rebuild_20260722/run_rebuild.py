from __future__ import annotations

import base64
import gzip
from pathlib import Path

ROOT = Path(__file__).resolve().parent
parts = sorted(ROOT.glob("rebuild_v2.py.gz.b64.part??"))
if not parts:
    raise RuntimeError("Missing rebuilt V2 source payload")
encoded = "".join(part.read_text().strip() for part in parts)
source = gzip.decompress(base64.b64decode(encoded)).decode("utf-8")
compile(source, "index_mags_rebuild_v2.py", "exec")
namespace = {"__name__": "__main__", "__file__": str(ROOT / "index_mags_rebuild_v2.py")}
exec(compile(source, "index_mags_rebuild_v2.py", "exec"), namespace)
