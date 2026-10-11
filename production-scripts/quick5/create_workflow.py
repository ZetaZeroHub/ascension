"""Create a local MiniMax H3 quick-five-minute ComfyUI API workflow.

This only prepares the image and graph. It never submits a generation job.
"""

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

from PIL import Image


root = Path(__file__).resolve().parents[3]
fast = root / "outputs/Feisheng-MV/补充与舞蹈-v9"
base_file = fast / "workflows/20-API.json"
input_dir = Path("<LOCAL_PATH>/FeishengQuick5")
output_dir = root / "outputs/Feisheng-MV/快速档-5分钟"

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--image", type=Path, required=True, help="Approved first-frame image")
parser.add_argument("--slug", required=True, help="ASCII letters, numbers, dash or underscore")
parser.add_argument("--seed", type=int, required=True)
prompt_group = parser.add_mutually_exclusive_group(required=True)
prompt_group.add_argument("--prompt-file", type=Path)
prompt_group.add_argument("--v9-shot", choices=[str(i) for i in range(13, 23)])
args = parser.parse_args()

if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", args.slug):
    raise SystemExit("slug must use 1–64 ASCII letters, digits, dashes or underscores")
if args.seed < 0:
    raise SystemExit("seed must be nonnegative")
image = args.image.expanduser().resolve(strict=True)
with Image.open(image) as im:
    im.verify()
if args.prompt_file:
    prompt = args.prompt_file.expanduser().resolve(strict=True).read_text(encoding="utf-8").strip()
else:
    prompt = json.loads((fast / "视频提示词.json").read_text(encoding="utf-8"))[args.v9_shot]
if not prompt:
    raise SystemExit("prompt is empty")

graph = json.loads(base_file.read_text(encoding="utf-8"))
assert graph["8"]["inputs"]["steps"] == 8
assert graph["6"]["inputs"]["width"] == 640
assert graph["6"]["inputs"]["height"] == 384
assert graph["6"]["inputs"]["length"] == 124
assert graph["5"]["inputs"]["lora_name"] == "minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors"

input_dir.mkdir(parents=True, exist_ok=True)
output_dir.mkdir(parents=True, exist_ok=True)
target_image = input_dir / f"{args.slug}{image.suffix.lower()}"
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
if target_image.exists() and digest(target_image) != digest(image):
    raise SystemExit(f"refusing to replace different ComfyUI input: {target_image}")
if not target_image.exists():
    shutil.copy2(image, target_image)

graph["6"]["inputs"]["prompt"] = prompt
graph["10"]["inputs"]["noise_seed"] = args.seed
graph["16"]["inputs"]["image"] = f"FeishengQuick5/{target_image.name}"
graph["15"]["inputs"]["filename_prefix"] = f"video/FeishengQuick5_{args.slug}"
target_graph = output_dir / f"{args.slug}-API.json"
content = json.dumps(graph, ensure_ascii=False, indent=2)
if target_graph.exists() and target_graph.read_text(encoding="utf-8") != content:
    raise SystemExit(f"refusing to replace different workflow: {target_graph}")
target_graph.write_text(content, encoding="utf-8")
print(json.dumps({"workflow": str(target_graph), "first_frame": str(target_image), "seed": args.seed, "steps": 8, "size": [640, 384], "frames": 124, "submitted": False}, ensure_ascii=False))
