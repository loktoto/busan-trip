from __future__ import annotations

import base64
import gzip
import hashlib
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
payload = ROOT / 'source.b64'
source = gzip.decompress(base64.b64decode(payload.read_text().strip()))
expected = '92ffdfbf11d8b756d3c1b137d6ff39b9646702e0d3ef99d33c0903f4a778c67a'
digest = hashlib.sha256(source).hexdigest()
if digest != expected:
    raise RuntimeError(f'meta source SHA mismatch: {digest} != {expected}')
compile(source.decode('utf-8'), 'meta_strategy_engine.py', 'exec')
engine_path = ROOT / 'meta_strategy_engine.py'
engine_path.write_bytes(source)
print({'meta_source_sha256': digest, 'source_bytes': len(source)})
runpy.run_path(str(engine_path), run_name='__main__')
