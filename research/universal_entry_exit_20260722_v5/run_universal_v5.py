from pathlib import Path
import base64
import gzip
import sys
import types

root = Path(__file__).parent
core_parts = sorted(root.parent.joinpath("universal_entry_exit_20260721").glob("optimize_universal_entry_exit.py.part??"))
v4_parts = sorted(root.parent.joinpath("universal_entry_exit_20260721").glob("robustness_patch_v3_2.py.part??"))
v5_parts = sorted(root.glob("challenger_patch_v5.py.gz.b64.part??"))
hotfix_path = root / "v5_hotfix.py"
if not core_parts or not v4_parts or not v5_parts or not hotfix_path.exists():
    raise RuntimeError("Missing core, V4.1, V5 source parts or V5 hotfix")

module_name = "universal_entry_exit_v5"
module = types.ModuleType(module_name)
module.__file__ = str(Path(__file__))
sys.modules[module_name] = module
namespace = module.__dict__
exec(compile("".join(path.read_text() for path in core_parts), "v4_core.py", "exec"), namespace)
exec(compile("".join(path.read_text() for path in v4_parts), "v4_robustness.py", "exec"), namespace)
v5_encoded = "".join(path.read_text() for path in v5_parts)
v5_source = gzip.decompress(base64.b64decode(v5_encoded.strip())).decode()
exec(compile(v5_source, "v5_challenger.py", "exec"), namespace)
exec(compile(hotfix_path.read_text(), "v5_hotfix.py", "exec"), namespace)
namespace["main"]()
