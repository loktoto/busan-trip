from __future__ import annotations

import base64
import gzip
from pathlib import Path

ROOT = Path(__file__).resolve().parent
parts = sorted(ROOT.glob("source.part??"))
if not parts:
    raise RuntimeError("missing source payload")
source = gzip.decompress(base64.b64decode("".join(p.read_text().strip() for p in parts))).decode("utf-8")
compile(source, "alpha_search_engine.py", "exec")
namespace = {"__name__": "__main__", "__file__": str(ROOT / "alpha_search_engine.py")}
exec(compile(source, "alpha_search_engine.py", "exec"), namespace)
