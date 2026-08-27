from __future__ import annotations

import base64
import gzip
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENCODED = HERE / "optimize_universal_entry_exit.py.gz.b64"
ASSEMBLED = HERE / "optimize_universal_entry_exit.py"
ASSEMBLED.write_bytes(gzip.decompress(base64.b64decode(ENCODED.read_text().strip())))
code = compile(ASSEMBLED.read_text(), str(ASSEMBLED), "exec")
namespace = {"__name__": "__main__", "__file__": str(ASSEMBLED)}
exec(code, namespace)
