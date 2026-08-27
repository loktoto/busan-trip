"""Execute the auditable sequential source chunks for the v2 optimiser."""
from pathlib import Path

base = Path(__file__).resolve()
parts = sorted(base.parent.glob(base.name + ".part??"))
if not parts:
    raise RuntimeError("No optimiser source chunks found")
source = "".join(path.read_text(encoding="utf-8") for path in parts)
compiled = compile(source, str(base.with_suffix(".assembled.py")), "exec")
exec(compiled, {"__name__": "__main__", "__file__": str(base)})
