import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/Feisheng-MV/风格实验-v11"
SOURCE_ROOT = Path("<USER_HOME>/.codex/generated_images").resolve()
for record in sorted((OUT / "records").glob("imagegen-?.json")):
    for item in json.loads(record.read_text(encoding="utf-8")):
        source = Path(item["imagegen_file"]).resolve(strict=True)
        if not source.is_relative_to(SOURCE_ROOT):
            raise RuntimeError("Image source outside generated_images")
        dest = OUT / "frames" / (item["id"] + ".png")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Refusing overwrite of different still {dest}")
        if not dest.exists():
            shutil.copy2(source, dest)
        with Image.open(dest) as image:
            image.verify()
        with Image.open(dest) as image:
            size = image.size
        result = dict(item, engine="built-in image_gen", sha256=digest, size=size, delivered_file=str(dest.relative_to(OUT)))
        (OUT / "records" / (item["id"] + "-still.json")).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        (OUT / "prompts" / (item["id"] + "-image.txt")).write_text(item["prompt"], encoding="utf-8")
        print("IMPORTED", item["id"], size, digest[:12], flush=True)
