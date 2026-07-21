from pathlib import Path

root = Path(__file__).parent
parts = sorted(root.glob("optimize_universal_entry_exit.py.part??"))
patches = sorted(root.glob("robustness_patch_v3_2.py.part??"))
if not parts:
    raise RuntimeError("No universal optimiser source parts found")
if not patches:
    raise RuntimeError("No v3.2 robustness patches found")

namespace = {"__name__": "universal_entry_exit_core", "__file__": str(Path(__file__))}
source = "".join(path.read_text() for path in parts)
exec(compile(source, "optimize_universal_entry_exit.py", "exec"), namespace)
patch_source = "".join(path.read_text() for path in patches)
exec(compile(patch_source, "robustness_patch_v3_2.py", "exec"), namespace)
namespace["main"]()
