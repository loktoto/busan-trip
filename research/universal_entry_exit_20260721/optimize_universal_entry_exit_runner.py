from pathlib import Path

parts = sorted(Path(__file__).parent.glob("optimize_universal_entry_exit.py.part??"))
if not parts:
    raise RuntimeError("No universal optimiser source parts found")
source = "".join(path.read_text() for path in parts)
exec(compile(source, "optimize_universal_entry_exit.py", "exec"), {"__name__": "__main__", "__file__": str(Path(__file__))})
