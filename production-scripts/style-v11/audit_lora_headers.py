"""Read safetensors headers only: verify target names and matrix dimensions without loading base weights."""
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/Feisheng-MV/风格实验-v11"

def header(path):
    with path.open("rb") as f:
        count = struct.unpack("<Q", f.read(8))[0]
        assert 0 < count < 16*1024*1024
        return json.loads(f.read(count))

base_path = Path("<LOCAL_PATH>/minimax_h3_fl2va_pruned_int8_convrot.safetensors")
base = header(base_path)
aliases = {}
for key, value in base.items():
    if key == "__metadata__" or not key.endswith(".weight"):
        continue
    name = key[:-7]
    for prefix in ["model.diffusion_model.", "diffusion_model."]:
        if name.startswith(prefix):
            name = name[len(prefix):]
    aliases[name] = (key, value["shape"])
    aliases["diffusion_model."+name] = (key, value["shape"])
    aliases["lora_unet_"+name.replace(".","_")] = (key, value["shape"])

records = []
for model in json.loads((OUT / "installed-loras.json").read_text(encoding="utf-8")):
    data = header(Path(model["path"]))
    checks = []; missing = []; mismatch = []
    for key, tensor in data.items():
        for suffix, partner in [(".lora_A.weight", ".lora_B.weight"), (".lora_down.weight", ".lora_up.weight")]:
            if not key.endswith(suffix):
                continue
            name = key[:-len(suffix)]
            if name not in aliases:
                missing.append(name); break
            target, shape = aliases[name]
            down = tensor["shape"]; up = data[name+partner]["shape"]
            valid = len(shape) == 2 and len(down) == 2 and len(up) == 2 and shape == [up[0], down[1]] and up[1] == down[0]
            checks.append({"adapter": name, "target": target, "base_shape": shape, "down": down, "up": up, "shape_matches": valid})
            if not valid: mismatch.append(name)
            break
    result = {"kind": model["kind"], "base_model": str(base_path), "matched_targets": len(checks), "missing_targets": missing, "shape_mismatch": mismatch, "passed": bool(checks) and not missing and not mismatch, "scope": "static name and dimension compatibility; runtime evidence is separately recorded", "checks": checks}
    records.append(result)
    print(json.dumps({k: v for k, v in result.items() if k != "checks"}), flush=True)
(OUT / "records" / "lora-static-compatibility.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
assert all(x["passed"] for x in records), "Adapter key/shape compatibility failed"
