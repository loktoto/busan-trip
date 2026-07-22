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
source = source_bytes.decode("utf-8")
required_markers = [
    "def effective_trial_count(",
    "years = max(len(x) / DAYS",
    "excess_cash = candidate_ret - cash.reindex(candidate_ret.index)",
    '"effective_trials": effective_trials',
    '"trial_participation_ratio": participation_ratio',
]
missing = [marker for marker in required_markers if marker not in source]
if missing:
    raise RuntimeError(f"corrected DSR source markers missing: {missing}")
forbidden = "math.sqrt(max(1, len(x) - 1))"
if forbidden in source:
    raise RuntimeError("obsolete daily-observation DSR formula is still present")
compile(source, "alpha_search_engine.py", "exec")
print({"source_sha256": digest, "source_bytes": len(source_bytes), "parts": len(parts), "corrected_dsr_markers": True})
namespace = {"__name__": "__main__", "__file__": str(ROOT / "alpha_search_engine.py")}
exec(compile(source, "alpha_search_engine.py", "exec"), namespace)
manifest_path = Path("research_outputs/spy_qqq_soxx_alpha_search_20260722/run_manifest.json")
manifest = json.loads(manifest_path.read_text())
manifest["source_sha256"] = digest
manifest["dsr_method"] = "annualised Sharpe; sampling horizon in years; excess over cash; effective-trial floor equals eight economic families"
manifest_path.write_text(json.dumps(manifest, indent=2))
