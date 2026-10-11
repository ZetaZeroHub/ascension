"""Serial, resumable local H3 style auditions. Only interrupt this runner's own prompt."""
import argparse
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/Feisheng-MV/风格实验-v11"
WORK = ROOT / "work/feisheng/style-v11"
INPUT = Path("<LOCAL_PATH>/FeishengStyleV11")
BACKEND_OUTPUT = Path("<LOCAL_PATH>/output").resolve()
PLAN = json.loads((OUT / "experiment-plan.json").read_text(encoding="utf-8"))
LORAS = {x["kind"]: x for x in json.loads((OUT / "installed-loras.json").read_text(encoding="utf-8"))}
STYLES = {x["id"]: x for x in PLAN["styles"]}
BASE = json.loads((ROOT / "outputs/Feisheng-MV/补充与舞蹈-v9/workflows/19-API.json").read_text(encoding="utf-8"))
parser = argparse.ArgumentParser()
parser.add_argument("ids", nargs="*")
args = parser.parse_args()
all_ids = [f"{shot['id']}-{style['id']}" for style in PLAN["styles"] for shot in PLAN["shots"]] + ["16-C-control", "19-D-control"]
ids = args.ids or all_ids
if any(x not in all_ids for x in ids):
    raise SystemExit("Unknown experiment id")
INPUT.mkdir(parents=True, exist_ok=True)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)

def req(path, value=None):
    request = urllib.request.Request("http://127.0.0.1:8000" + path, data=None if value is None else json.dumps(value).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(error.read().decode())

class Memory(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong), ("free", ctypes.c_ulonglong), ("commit_total", ctypes.c_ulonglong), ("commit_free", ctypes.c_ulonglong), ("virtual_total", ctypes.c_ulonglong), ("virtual_free", ctypes.c_ulonglong), ("extended", ctypes.c_ulonglong)]

def resources():
    mem = Memory(); mem.length = ctypes.sizeof(mem)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
    gpu = subprocess.check_output(["nvidia-smi", "--query-gpu=temperature.gpu,memory.used,utilization.gpu", "--format=csv,noheader,nounits"], text=True).strip().split(",")
    return {"time": time.time(), "ram_free_mib": mem.free//1048576, "commit_free_mib": mem.commit_free//1048576, "temp": int(gpu[0]), "gpu_mib": int(gpu[1]), "gpu_util": int(gpu[2])}

def complete(eid):
    record = OUT / "records" / (eid + "-video.json")
    final = OUT / "clips" / (eid + ".mp4")
    if not record.exists() or not final.exists():
        return False
    value = json.loads(record.read_text(encoding="utf-8"))
    return value.get("verified") is True and value["sha256"] == sha(final)

def status(phase, eid=None, **extra):
    write(OUT / "status.json", dict(phase=phase, active=eid, updated=time.time(), runner_pid=os.getpid(), completed=[x for x in all_ids if complete(x)], total=len(all_ids), **extra))

COMMON = "One uninterrupted shot. Same adult East Asian female courier with short black bob, same recognizable face and belted long coat, coherent anatomy, stable exposure and art medium throughout. No new people, no scene cut, no text, no watermark, no glossy oily highlights. "
LOOK = {
    "A": "Preserve the first frame's tactile warm ivory rice-paper and unglazed ceramic editorial art direction, muted sage, ochre and charcoal, dusty burgundy cloth, soft diffuse light. Minimalist material shapes and fine paper grain remain stable. A hand-crafted matte gallery installation with restrained flat-colour accents and textured edges. ",
    "B": "Preserve the first frame's geological-relief fine-art medium: delicate contour lines, dry earth ochre and moss, bone and charcoal, rich stratified mineral surface and hand-coloured atlas textures. The world feels like an intricate sculptural landscape. Maintain tactile relief and fine hand-drawn textured contours, never turning into a glossy digital rendering. ",
    "C": "r34l1sm. Dry mineral cinematic analogue photography. Warm terracotta and dusty amber highlights against restrained ultramarine shadows. Natural skin texture, believable eyes and gestures, gentle grain, smooth highlight rolloff, low specular light and professional secondary colour separation. ",
    "D": "A cyanotype photographic contact print in Prussian blue and unbleached cream on cotton paper, fine fibre texture, photographic negative tonal logic, white organic details and delicate botanical photogram contours. Restrained hand-drawn 2D textured edges and flat blue fields. Keep the cyanotype print medium throughout the movement, no photorealistic colour restoration. "
}
ACTION = {
    "10": "Low-angle full-body view of the courier upright and floating in the monumental city shaft. She rises only a little while her EMPTY hands remain relaxed at her sides; the long coat hem and bob sway gently. Nearby massive floating blocks drift upward slowly while remaining rigid and separate. The camera makes a restrained slow push in. No spin, no falling, no seed appears, same city and scale.",
    "16": "Medium rear three-quarter portrait in the restored monumental city. She already looks over her shoulder toward camera; she holds her recognizable gaze, blinks once, makes a very small further head turn, and breathes with a faint relieved expression. Hair and coat move slightly. Tiny steady camera push. City arch and foliage remain rigid and stable; hands remain out of frame. No dialogue, no sudden face change.",
    "19": "Side-profile full-body studio dance shot with exactly the same lead dancer and two grey-costumed background dancers. The lead performs one restrained grounded side step, a crisp shoulder isolation and a short synchronized downward arm sweep, then holds an angular pose. The two backing dancers echo the same small phrase without overlapping. Approximately 100 BPM accents, controlled pause, a short smooth lateral camera slide. The white sculpture and bonsai remain rigid and in place; feet stay grounded, no spin, no new limbs."
}

def graph(eid):
    sid, look, *_ = eid.split("-")
    source = OUT / "frames" / f"{sid}-{look}.png"
    p = json.loads(json.dumps(BASE))
    p["6"]["inputs"].update(prompt=COMMON + LOOK[look] + ACTION[sid], width=640, height=384, length=73, first_frame=["16", 0])
    p["8"]["inputs"]["steps"] = 8
    p["10"]["inputs"]["noise_seed"] = 26101100 + int(sid)
    p["15"]["inputs"]["filename_prefix"] = "video/FeishengStyleV11_" + eid
    p["16"]["inputs"]["image"] = "FeishengStyleV11/" + source.name
    if not eid.endswith("-control"):
        style = STYLES[look]
        listed = req("/object_info/LoraLoaderModelOnly")["LoraLoaderModelOnly"]["input"]["required"]["lora_name"][0]
        expected = LORAS[style["adapter"]]["comfy_name"]
        actual = next((name for name in listed if name.replace("\\", "/") == expected), None)
        if actual is None:
            raise RuntimeError(f"Installed style LoRA not listed by backend: {expected}")
        p["17"] = {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["5", 0], "lora_name": actual, "strength_model": style["strength"]}}
        p["8"]["inputs"]["model"] = ["17", 0]
        p["9"]["inputs"]["model"] = ["17", 0]
    else:
        p["8"]["inputs"]["model"] = ["5", 0]
        p["9"]["inputs"]["model"] = ["5", 0]
    write(OUT / "workflows" / (eid + "-API.json"), p)
    (OUT / "prompts" / (eid + "-video.txt")).write_text(p["6"]["inputs"]["prompt"], encoding="utf-8")
    dest = INPUT / source.name
    if dest.exists() and sha(dest) != sha(source):
        raise RuntimeError("Different ComfyUI input already exists")
    shutil.copy2(source, dest)
    return p, source

def verify(final, eid):
    arrays = []; thumbs = []; pts = []; black = []
    with av.open(str(final)) as container:
        stream = container.streams.video[0]
        dimensions = [stream.width, stream.height]; fps = float(stream.average_rate)
        audio_streams = len(container.streams.audio)
        for i, frame in enumerate(container.decode(video=0)):
            pts.append(float(frame.pts * frame.time_base))
            image = frame.to_image()
            small = np.asarray(image.resize((160,90))).astype(np.float32)
            arrays.append(small)
            if small.mean() < 1: black.append(i)
            if i % 6 == 0 or i == 72: thumbs.append((i, image.resize((384,216))))
    assert dimensions == [1280,720] and fps == 24 and len(pts) == 73 and not black and not audio_streams, (eid, dimensions, fps, len(pts), black)
    assert all(abs(t-i/24) < 0.0001 for i,t in enumerate(pts))
    canvas = Image.new("RGB", (1536, ((len(thumbs)+3)//4)*238), (17,20,25)); draw = ImageDraw.Draw(canvas)
    for j,(i,image) in enumerate(thumbs):
        x = j%4*384; y = j//4*238; canvas.paste(image, (x,y)); draw.text((x+8,y+219), f"{eid}  {i/24:.2f}s", fill="white")
    canvas.save(OUT / "review" / (eid + "-contact.jpg"), quality=91)
    change = [float(np.abs(b-a).mean()) for a,b in zip(arrays,arrays[1:])]
    return dict(size=dimensions, fps=fps, frames=len(pts), duration_seconds=len(pts)/fps, audio_streams=audio_streams, black_frames=black, mean_frame_change=float(np.mean(change)), max_frame_change=max(change))

def run(eid):
    if complete(eid):
        print("REUSE", eid, flush=True); return
    source = OUT / "frames" / ("-".join(eid.split("-")[:2]) + ".png")
    until = time.monotonic()+1800
    while not source.exists():
        if time.monotonic() > until: raise RuntimeError(f"Missing first frame {eid}")
        status("waiting_first_frame", eid); time.sleep(10)
    p, source = graph(eid)
    submit_file = OUT / "records" / (eid + "-submitted.json")
    pid = None
    if submit_file.exists():
        old = json.loads(submit_file.read_text()); saved_id = old["prompt_id"]
        history = req("/history/" + saved_id); queue = req("/queue")
        if saved_id in history or any(x[1] == saved_id for x in queue["queue_running"]+queue["queue_pending"]): pid = saved_id
        else: raise RuntimeError("Uncertain prior submission; inspect before retry")
    log_start = (WORK / "backend.stderr.log").stat().st_size
    while pid is None:
        try: queue = req("/queue")
        except (ConnectionError, urllib.error.URLError):
            status("waiting_backend", eid); time.sleep(10); continue
        if queue["queue_running"] or queue["queue_pending"]:
            status("waiting_queue", eid); time.sleep(10); continue
        current = resources()
        if current["commit_free_mib"] < 2048 or current["ram_free_mib"] < 1024 or current["temp"] >= 83:
            raise RuntimeError(f"Insufficient starting resource headroom: {current}")
        result = req("/prompt", {"prompt": p, "client_id": "codex-feisheng-style-v11"})
        if result.get("node_errors"): raise RuntimeError(result)
        write(submit_file, result); pid = result["prompt_id"]
        print("SUBMITTED", eid, pid, flush=True)
    status("generating", eid, prompt_id=pid)
    while True:
        history = req("/history/" + pid)
        if pid in history and history[pid].get("status",{}).get("status_str") in ["success","error"]:
            record = history[pid]; break
        current = resources()
        with (WORK / "resources.jsonl").open("a", encoding="utf-8") as f: f.write(json.dumps(dict(eid=eid, **current)) + "\n")
        status("generating", eid, prompt_id=pid, resources=current)
        if current["ram_free_mib"] < 640 or current["commit_free_mib"] < 1536 or current["temp"] >= 84:
            queue = req("/queue")
            if any(x[1] == pid for x in queue["queue_running"]): req("/interrupt", {})
            raise RuntimeError(f"Own generation stopped at resource threshold: {current}")
        time.sleep(10)
    write(OUT / "records" / (eid + "-history.json"), record)
    with (WORK / "backend.stderr.log").open("rb") as f:
        f.seek(log_start); excerpt = f.read().decode("utf-8", errors="replace")
    (OUT / "records" / (eid + "-backend.log")).write_text(excerpt, encoding="utf-8")
    if record["status"]["status_str"] != "success": raise RuntimeError(record["status"])
    assert record["prompt"][2] == p, "Executed graph differs from frozen workflow"
    output = record["outputs"]["15"]["images"][0]
    generated = (BACKEND_OUTPUT / output.get("subfolder", "") / output["filename"]).resolve(strict=True)
    assert generated.is_relative_to(BACKEND_OUTPUT)
    native = OUT / "native" / (eid + ".mp4"); shutil.copy2(generated, native)
    final = OUT / "clips" / (eid + ".mp4")
    status("encoding", eid, prompt_id=pid)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(native), "-vf", "crop=640:360:0:12,scale=1280:720:flags=lanczos,setsar=1", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-threads", "2", "-color_primaries", "bt709", "-color_trc", "iec61966-2-1", "-colorspace", "bt709", "-movflags", "+faststart", str(final)], check=True)
    qa = verify(final, eid)
    timestamps = {kind: data.get("timestamp") for kind,data in record["status"]["messages"]}
    style = STYLES[eid.split("-")[1]]
    manifest = dict(eid=eid, prompt_id=pid, file=str(final.relative_to(OUT)), native_file=str(native.relative_to(OUT)), native_size=[640,384], resolution_note="Generated at 640x384, centre-cropped to 640x360 and Lanczos scaled to 1280x720", steps=8, turbo=True, seed=p["10"]["inputs"]["noise_seed"], style_adapter=None if eid.endswith("-control") else LORAS[style["adapter"]]["comfy_name"], style_strength=0 if eid.endswith("-control") else style["strength"], first_frame_sha256=sha(source), generation_seconds=(timestamps["execution_success"]-timestamps["execution_start"])/1000, sha256=sha(final), native_sha256=sha(native), verified=True, **qa)
    write(OUT / "records" / (eid + "-video.json"), manifest)
    print("COMPLETE", eid, manifest["generation_seconds"], flush=True)

try:
    for eid in ids: run(eid)
    status("complete" if all(complete(x) for x in all_ids) else "subset_complete")
    print("REQUESTED_AUDITIONS_COMPLETE", flush=True)
except Exception as error:
    write(WORK / "failure.json", {"error": str(error), "traceback": traceback.format_exc(), "time": time.time()})
    status("failed", locals().get("eid"), error=str(error))
    raise
