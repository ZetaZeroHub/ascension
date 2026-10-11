"""Freeze a stratified random sample and a four-look storyboard experiment."""
import hashlib
import json
import random
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/Feisheng-MV/风格实验-v11"
for name in ["originals", "references", "frames", "clips", "native", "workflows", "records", "review", "comparison", "prompts"]:
    (OUT / name).mkdir(parents=True, exist_ok=True)

rng = random.Random(20261011)
selected = [
    ("空间与高潮", rng.choice(["01", "06", "08", "10", "11", "12"])),
    ("人物情绪", rng.choice(["02", "16", "21"])),
    ("动作与群像", rng.choice(["05", "17", "18", "19", "20", "22"])),
]
v6 = ROOT / "outputs/Feisheng-MV/独立分镜-v6"
v10 = ROOT / "outputs/Feisheng-MV/高清素材-v10"
v9 = ROOT / "outputs/Feisheng-MV/补充与舞蹈-v9"
names = {x["id"]: x["name"] for x in json.loads((v6 / "asset-manifest.json").read_text(encoding="utf-8"))}
names.update({x["shot"]: x["name"] for x in json.loads((v9 / "素材清单.json").read_text(encoding="utf-8"))})
shots = []
for category, sid in selected:
    source = (v6 if int(sid) <= 12 else v10) / "frames" / f"{sid}.png"
    target = OUT / "originals" / f"{sid}.png"
    shutil.copy2(source, target)
    shots.append({"id": sid, "name": names[sid], "category": category, "source": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})

refs = [
    ("A", "codex-clipboard-44e59b84-ddbe-4307-9d9b-f5b1e330757f.png"),
    ("B", "codex-clipboard-f6a2387f-6b17-4a33-a198-ee7f786c4599.png"),
    ("C", "codex-clipboard-dfe97fe3-e82b-41e4-9c3e-da139ef34058.png"),
    ("D", "codex-clipboard-87d5822d-3ce4-4bfc-b630-ea4e502fdd61.png"),
]
for letter, name in refs:
    shutil.copy2(Path("<USER_HOME>/AppData/Local/Temp") / name, OUT / "references" / f"{letter}.png")

styles = [
    {"id": "A", "name": "米纸陶土", "medium": "matte tactile editorial minimalism", "palette": ["ivory", "sage", "charcoal", "ochre", "muted burgundy"], "adapter": "sketch", "strength": 0.85},
    {"id": "B", "name": "地貌织绘", "medium": "hand-coloured geological relief and fine contour drawing", "palette": ["moss", "earth ochre", "umber", "bone", "burgundy"], "adapter": "sketch", "strength": 0.8},
    {"id": "C", "name": "赭石胶片", "medium": "dry mineral cinematic analogue photography", "palette": ["ultramarine", "terracotta", "dusty amber", "burgundy"], "adapter": "realism", "strength": 0.7},
    {"id": "D", "name": "普鲁士蓝晒", "medium": "cyanotype photographic contact print on cotton paper", "palette": ["Prussian blue", "cream"], "adapter": "sketch", "strength": 0.95},
]
plan = {"sampling": {"seed": 20261011, "method": "one random draw within each of three predeclared representative shot categories", "universe": "adopted storyboards 01-22, latest approved stills"}, "shots": shots, "styles": styles, "target": {"stills": 12, "style_videos": 12, "native_video": [640, 384], "delivery_video": [1280, 720], "fps": 24, "frames": 73, "duration_seconds": 73/24, "steps": 8, "turbo": True, "audio": "silent style auditions"}, "comparison": "same first frame, same prompt, same seed, same Turbo schedule; change only style adapter", "invariants": ["same adopted protagonist and bob haircut", "same composition, lens direction and story action", "no additional characters", "dry matte surfaces, no oily highlights", "separate experimental output, no overwrite of accepted film"], "exceptions": ["These are silent style auditions rather than a newly edited MV.", "720p audition files are Lanczos-scaled from 640x384 generation.", "Four visual systems are intentionally separate alternatives.", "Image generation uses built-in imagegen; video generation and LoRA evaluation run locally."]}
(OUT / "experiment-plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"output": str(OUT), "shots": shots, "variants": 12, "video_seconds": 73/24}, ensure_ascii=False))
