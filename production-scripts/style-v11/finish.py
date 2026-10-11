"""Make synchronized LoRA comparisons and independently audit retained assets."""
import copy
import hashlib
import json
import statistics
from fractions import Fraction
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/Feisheng-MV/风格实验-v11"
FONT = ImageFont.truetype("<LOCAL_PATH>/msyh.ttc", 19)
EXPECTED = [f"{s}-{x}" for s in ["10", "16", "19"] for x in "ABCD"] + ["16-C-control", "19-D-control"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def frames(path):
    with av.open(str(path)) as c:
        return [f.to_image().convert("RGB") for f in c.decode(video=0)]


def comparison(eid):
    on = read(OUT / "workflows" / (eid + "-API.json"))
    off = read(OUT / "workflows" / (eid + "-control-API.json"))
    stripped = copy.deepcopy(on); stripped.pop("17")
    stripped["8"]["inputs"]["model"] = ["5", 0]
    stripped["9"]["inputs"]["model"] = ["5", 0]
    stripped["15"]["inputs"]["filename_prefix"] = off["15"]["inputs"]["filename_prefix"]
    assert stripped == off, "Comparison differs beyond style adapter / output filename"
    first, second = frames(OUT / "clips" / (eid + "-control.mp4")), frames(OUT / "clips" / (eid + ".mp4"))
    assert len(first) == len(second) == 73
    target = OUT / "comparison" / (eid + "-side-by-side.mp4")
    differences = []
    contact = Image.new("RGB", (1280, 4 * 408), (11, 16, 22))
    def canvas(a, b, i):
        im = Image.new("RGB", (1280, 408), (11, 16, 22)); d = ImageDraw.Draw(im)
        d.text((14, 9), f"{eid}  {i/24:.2f}s  ·  关闭风格 LoRA", font=FONT, fill="#c2ced8")
        d.text((654, 9), "开启风格 LoRA · 其余输入相同", font=FONT, fill="#c2ced8")
        im.paste(a.resize((640, 360), Image.Resampling.LANCZOS), (0, 48))
        im.paste(b.resize((640, 360), Image.Resampling.LANCZOS), (640, 48))
        return im
    with av.open(str(target), "w", options={"movflags": "+faststart"}) as c:
        v = c.add_stream("libx264", rate=24); v.width = 1280; v.height = 408; v.pix_fmt = "yuv420p"
        v.options = {"crf": "16", "preset": "medium", "threads": "2"}
        for i, (a, b) in enumerate(zip(first, second)):
            arr_a = np.asarray(a.resize((160, 90))).astype(np.float32)
            arr_b = np.asarray(b.resize((160, 90))).astype(np.float32)
            differences.append(float(np.abs(arr_a - arr_b).mean()))
            im = canvas(a, b, i)
            if i in [0, 12, 36, 60]: contact.paste(im, (0, [0, 12, 36, 60].index(i) * 408))
            f = av.VideoFrame.from_image(im); f.pts = i; f.time_base = Fraction(1, 24)
            for packet in v.encode(f): c.mux(packet)
        for packet in v.encode(): c.mux(packet)
    contact.save(OUT / "comparison" / (eid + "-contact.jpg"), quality=92)
    return {"eid": eid, "only_adapter_changed": True, "frames": 73, "mean_pixel_difference_0_255": statistics.mean(differences),
            "first_frame_difference": differences[0], "note": "Pixel difference measures change, not aesthetic quality.",
            "comparison_sha256": sha(target)}


def audit():
    reports = []; durations = []; errors = []
    for eid in EXPECTED:
        record = read(OUT / "records" / (eid + "-video.json"))
        api = read(OUT / "workflows" / (eid + "-API.json"))
        history = read(OUT / "records" / (eid + "-history.json"))
        assert history["prompt"][2] == api and history["status"]["status_str"] == "success"
        for directory, hash_key in [("clips", "sha256"), ("native", "native_sha256")]:
            p = OUT / directory / (eid + ".mp4"); assert sha(p) == record[hash_key]
            n = 0; black = []; pts = []
            with av.open(str(p)) as c:
                v = c.streams.video[0]
                dims = [v.width, v.height]; fps = float(v.average_rate)
                assert len(c.streams.audio) == 0
                for i, f in enumerate(c.decode(video=0)):
                    n += 1; pts.append(float(f.pts * f.time_base))
                    if np.asarray(f.to_image().resize((80, 45))).mean() < 1: black.append(i)
            assert dims == ([1280, 720] if directory == "clips" else [640, 384])
            assert fps == 24 and n == 73 and not black and all(abs(t - i/24) < 1e-6 for i, t in enumerate(pts))
        first_frame = OUT / "frames" / ("-".join(eid.split("-")[:2]) + ".png")
        assert sha(first_frame) == record["first_frame_sha256"]
        assert (OUT / "workflows" / (eid + ".json")).exists()
        log = (OUT / "records" / (eid + "-backend.log")).read_text(encoding="utf-8")
        bad = [line for line in log.splitlines() if any(t in line.lower() for t in ["lora key not loaded", "unexpected key", "size mismatch", "outofmemory", "execution_error"])]
        assert not bad, (eid, bad)
        durations.append(record["generation_seconds"])
        reports.append({"eid": eid, "history_success": True, "api_matches_executed": True, "full_decode_verified": True,
                        "frames": 73, "fps": 24, "native_size": [640, 384], "preview_size": [1280, 720],
                        "generation_seconds": record["generation_seconds"], "sha256": record["sha256"]})
    assert len(list((OUT / "frames").glob("*.png"))) == 12
    for p in (OUT / "frames").glob("*.png"):
        with Image.open(p) as im: im.verify()
    resources = [json.loads(line) for line in (ROOT / "work/feisheng/style-v11/resources.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    report = {"passed": True, "scope": "14 independent full decodes, exact executed API and file hashes; visual contact-sheet review of all 14",
              "browser_verified": False, "browser_note": "User requested file saving only; no further page interaction.",
              "still_count": 12, "style_video_count": 12, "control_video_count": 2, "reports": reports,
              "generation_seconds": {"min": min(durations), "median": statistics.median(durations), "max": max(durations), "total": sum(durations)},
              "resources": {"peak_gpu_celsius": max(r["temp"] for r in resources), "min_free_ram_mib": min(r["ram_free_mib"] for r in resources), "min_free_commit_mib": min(r["commit_free_mib"] for r in resources)},
              "visual_notes": {"A": "Matte paper/ceramic look holds through restrained motion; suitable for quiet passages.",
                               "B": "Mineral relief and contour texture persist; face reads as sculptural rather than natural skin.",
                               "C": "Most direct continuity with the original courier, terracotta architecture and dry studio floor.",
                               "D": "Cyanotype stays blue/cream, but 19-D deliberately retained as an exploration: dark background lifts to cream early in motion. Use as an insert or transition, not a seamless dark-studio replacement."},
              "resolution_note": "Native 640x384 cropped to 640x360 then Lanczos 1280x720. No interpolation. Silent audition clips."}
    (OUT / "review/technical-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    pairs = [comparison(eid) for eid in ["16-C", "19-D"]]
    (OUT / "comparison/paired-audit.json").write_text(json.dumps(pairs, ensure_ascii=False, indent=2), encoding="utf-8")
    report = audit()
    print(json.dumps({"generation_seconds": report["generation_seconds"], "resources": report["resources"], "paired": pairs}, ensure_ascii=False))
