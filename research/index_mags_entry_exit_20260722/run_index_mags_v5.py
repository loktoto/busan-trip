from pathlib import Path
import base64
import gzip
import sys
import types

root = Path(__file__).parent
research_root = root.parent
core_parts = sorted(research_root.joinpath("universal_entry_exit_20260721").glob("optimize_universal_entry_exit.py.part??"))
v4_parts = sorted(research_root.joinpath("universal_entry_exit_20260721").glob("robustness_patch_v3_2.py.part??"))
v5_root = research_root / "universal_entry_exit_20260722_v5"
v5_parts = sorted(v5_root.glob("challenger_patch_v5.py.gz.b64.part??"))
hotfix_path = v5_root / "v5_hotfix.py"
focused_patch = root / "focused_basket_patch.py"
config_path = root / "universe_index_mags.json"

if not core_parts or not v4_parts or not v5_parts:
    raise RuntimeError("Missing frozen V4/V5 source parts")
for required in [hotfix_path, focused_patch, config_path]:
    if not required.exists():
        raise RuntimeError(f"Missing required focused research file: {required}")

module_name = "index_mags_entry_exit_v5"
module = types.ModuleType(module_name)
module.__file__ = str(Path(__file__))
sys.modules[module_name] = module
namespace = module.__dict__

exec(compile("".join(path.read_text() for path in core_parts), "v4_core.py", "exec"), namespace)
exec(compile("".join(path.read_text() for path in v4_parts), "v4_robustness.py", "exec"), namespace)
encoded = "".join(path.read_text() for path in v5_parts)
v5_source = gzip.decompress(base64.b64decode(encoded.strip())).decode()
exec(compile(v5_source, "v5_challenger.py", "exec"), namespace)
exec(compile(hotfix_path.read_text(), "v5_hotfix.py", "exec"), namespace)

output = Path("research_outputs/index_mags_entry_exit_20260722")
input_dir = output / "inputs"
output.mkdir(parents=True, exist_ok=True)
input_dir.mkdir(parents=True, exist_ok=True)
namespace["CONFIG_PATH"] = config_path
namespace["OUT"] = output
namespace["INPUT_DIR"] = input_dir
namespace["END_DATE"] = "2026-07-22"
namespace["START_DATE"] = "2005-01-01"

exec(compile(focused_patch.read_text(), "focused_basket_patch.py", "exec"), namespace)
namespace["main"]()
