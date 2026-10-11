"""Install two public H3 safetensors adapters with pinned revision and LFS hash verification."""
import hashlib
import json
import struct
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/Feisheng-MV/风格实验-v11"
DEST = Path("<LOCAL_PATH>/FeishengStyleV11")
DEST.mkdir(parents=True, exist_ok=True)
MODELS = [("realism", "fal/MiniMax-H3-Realism-People-LoRA", "h3-realism-people-t2v-i2v-r2v.safetensors"), ("sketch", "Inner-Reflections/MiniMax-H3-Looping-Sketch-Anime", "minimax_h3_looping_sketch_anime_v1.safetensors")]

def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "FeishengStyleAudit/1.0"}), timeout=90)

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8*1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

records = []
for kind, repo, filename in MODELS:
    with fetch(f"https://huggingface.co/api/models/{repo}?blobs=true") as response:
        meta = json.load(response)
    revision = meta["sha"]
    info = next(x for x in meta["siblings"] if x["rfilename"] == filename)
    expected = info["lfs"]["sha256"]
    size = info["lfs"]["size"]
    target = DEST / filename
    if target.exists() and digest(target) != expected:
        raise RuntimeError(f"Different existing adapter; refusing overwrite: {target}")
    url = f"https://huggingface.co/{repo}/resolve/{revision}/{filename}"
    if not target.exists():
        partial = target.with_suffix(".download")
        print("DOWNLOAD", kind, revision, size, flush=True)
        started = time.monotonic()
        with fetch(url) as response, partial.open("wb") as f:
            for chunk in iter(lambda: response.read(4*1024*1024), b""):
                f.write(chunk)
        if partial.stat().st_size != size or digest(partial) != expected:
            raise RuntimeError(f"Size or LFS SHA256 mismatch for {kind}")
        partial.replace(target)
        print("VERIFIED", kind, round(time.monotonic()-started, 1), flush=True)
    with target.open("rb") as f:
        length = struct.unpack("<Q", f.read(8))[0]
        if not 0 < length < 16*1024*1024:
            raise RuntimeError("Invalid safetensors header length")
        header = json.loads(f.read(length))
    keys = [k for k in header if k != "__metadata__"]
    if not keys or not all(isinstance(header[k].get("shape"), list) for k in keys):
        raise RuntimeError("Invalid safetensors tensor table")
    records.append({"kind": kind, "repo": repo, "revision": revision, "filename": filename, "comfy_name": f"FeishengStyleV11/{filename}", "path": str(target), "size": size, "sha256": expected, "verified_lfs_hash": True, "tensor_count": len(keys), "tensor_examples": keys[:6], "header_metadata": header.get("__metadata__", {}), "source": f"https://huggingface.co/{repo}", "url": url})
    (OUT / "records" / f"{kind}-safetensors-header.json").write_text(json.dumps(header, ensure_ascii=False, indent=2), encoding="utf-8")
    with fetch(f"https://huggingface.co/{repo}/raw/{revision}/README.md") as response:
        (OUT / "records" / f"{kind}-model-card.md").write_bytes(response.read())
(OUT / "installed-loras.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(records, ensure_ascii=False), flush=True)
