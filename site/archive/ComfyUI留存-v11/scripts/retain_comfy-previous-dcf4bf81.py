"""Retain project workflows, inputs, model locations and execution records.

Never enqueue or change the browser. Native graphs use the installed node schema.
Original API files remain byte-for-byte copies, including historical attempts.
"""
import copy
import hashlib
import json
import shutil
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "outputs/Feisheng-MV"
OUT = PROJECT / "ComfyUI留存-v11"
USER = Path("<LOCAL_PATH>/Feisheng-MV")
INPUT = Path("<LOCAL_PATH>/input")
WORK = ROOT / "work/feisheng/style-v11"
INFO = json.loads((WORK / "object-info.json").read_text(encoding="utf-8"))
CONFIG = Path("<USER_HOME>/AppData/Roaming/Comfy Desktop/instance-model-paths/inst-1786180594835.yaml")
LORAS = json.loads((PROJECT / "风格实验-v11/installed-loras.json").read_text(encoding="utf-8"))


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    if path.exists():
        backup = path.with_name(path.stem + "-previous-" + digest(path)[:8] + path.suffix)
        if not backup.exists():
            shutil.copy2(path, backup)
    path.write_text(text, encoding="utf-8")


def retain(source, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if digest(dest) == digest(source):
            return
        raise RuntimeError(f"Preserved file conflict: {dest}")
    shutil.copy2(source, dest)


def stage(path):
    rel = path.relative_to(ROOT / "outputs")
    if len(rel.parts) == 1:
        return "基础试验"
    names = {"工作流": "早期红绸", "成片-v7": "剧情-v7", "补充镜头-v8": "补充-v8",
             "补充与舞蹈-v9": "快速-v9", "高清素材-v10": "高清-v10",
             "风格实验-v11": "风格-v11", "快速档-5分钟": "快速档示例"}
    return names[rel.parts[1]]


PRIMITIVES = {"INT", "FLOAT", "STRING", "BOOLEAN", "COMBO", "COMFY_DYNAMICCOMBO_V3"}


def is_link(value):
    return isinstance(value, list) and len(value) == 2 and isinstance(value[1], int)


def input_type(spec):
    return "COMBO" if isinstance(spec[0], list) else spec[0]


def default_value(spec):
    opts = spec[1] if len(spec) > 1 else {}
    if "default" in opts:
        return opts["default"]
    if isinstance(spec[0], list):
        return spec[0][0] if spec[0] else ""
    if spec[0] == "COMBO":
        return opts["options"][0] if opts.get("options") else ""
    return {"INT": 0, "FLOAT": 0.0, "STRING": "", "BOOLEAN": False}.get(spec[0])


def native_graph(api, title):
    """Flatten v3 dynamic widgets and autogrow names exactly as the frontend does."""
    nodes = []; edges = []
    by_id = {}
    seen = set()
    order = []

    def visit(key):
        if key in seen: return
        seen.add(key)
        for value in api[key]["inputs"].values():
            if is_link(value): visit(str(value[0]))
        order.append(key)

    for key in api: visit(key)
    layers = {}
    columns = {}
    for key in order:
        parents = [str(v[0]) for v in api[key]["inputs"].values() if is_link(v)]
        layers[key] = max((layers[k] + 1 for k in parents), default=0)
    for key in order:
        item = api[key]; typ = item["class_type"]; schema = INFO[typ]
        all_specs = {**schema["input"].get("required", {}), **schema["input"].get("optional", {})}
        values = copy.deepcopy(item["inputs"])
        # Current SaveVideo format owns codec settings; retain the hidden legacy
        # codec widget as well, so both schema representations agree.
        if typ == "SaveVideo" and isinstance(values.get("format"), str):
            fmt = values["format"]
            codec = values.get("codec", {"codec": "auto"})
            if isinstance(codec, str): codec = {"codec": codec}
            values["codec"] = codec
            values["format"] = {"format": fmt, "codec": copy.deepcopy(codec)}
        sockets = []; widgets = {}; widget_specs = []
        def socket(name, datatype, value=None, widget=False):
            entry = {"name": name, "type": datatype, "link": None}
            if widget: entry["widget"] = {"name": name}
            sockets.append(entry)
        # Normal sockets precede widget sockets in the current frontend.
        for name, spec in all_specs.items():
            typ_in = input_type(spec)
            if typ_in == "COMFY_AUTOGROW_V3":
                conf = spec[1]["template"]
                base_spec = next(iter(conf["input"]["required"].values()))
                existing = [n for n in values if n.startswith(name + ".")]
                for n in existing: socket(n, input_type(base_spec), values[n])
                next_idx = max((int(n.rsplit("_", 1)[-1]) for n in existing), default=-1) + 1
                socket(name + "." + conf["prefix"] + str(next_idx), input_type(base_spec))
            elif typ_in not in PRIMITIVES:
                socket(name, typ_in, values.get(name))
            else:
                widget_specs.append((name, spec))
        def widget(name, spec, value):
            typ_in = input_type(spec)
            if typ_in == "COMFY_DYNAMICCOMBO_V3":
                short_name = name.rsplit(".", 1)[-1]
                options = spec[1]["options"]
                chosen = value.get(short_name) if isinstance(value, dict) else value
                if chosen is None: chosen = spec[1].get("default", options[0]["key"])
                widgets[name] = chosen
                socket(name, typ_in, widget=True)
                selected = next(x for x in options if x["key"] == chosen)
                nested = value if isinstance(value, dict) else {}
                for subgroup in ["required", "optional"]:
                    for child, child_spec in selected["inputs"].get(subgroup, {}).items():
                        child_value = nested.get(child, default_value(child_spec))
                        widget(name + "." + child, child_spec, child_value)
            else:
                widgets[name] = default_value(spec) if value is None or is_link(value) else value
                socket(name, typ_in, value, widget=True)
                opts = spec[1] if len(spec) > 1 else {}
                if opts.get("control_after_generate"):
                    widgets["control_after_generate"] = "fixed"
        for name, spec in widget_specs:
            widget(name, spec, values.get(name))
        if typ == "RandomNoise" and "control_after_generate" not in widgets:
            widgets["control_after_generate"] = "fixed"
        if typ in ["LoadImage", "LoadVideo"]:
            widgets["upload"] = "image" if typ == "LoadImage" else "video"
        outs = [{"name": name, "type": t, "links": [], "slot_index": i}
                for i, (name, t) in enumerate(zip(schema.get("output_name", schema["output"]), schema["output"]))]
        col = layers[key]; row = columns.get(col, 0); columns[col] = row + 1
        size = [420, 550] if typ.startswith("MiniMaxH3") and "ToVideo" in typ else [355, 170 + 24 * len(widgets)]
        if typ in ["LoadImage", "LoadVideo", "SaveVideo"]: size = [355, 380]
        node = {"id": int(key), "type": typ, "pos": [col * 490, row * 540], "size": size,
                "flags": {}, "order": order.index(key), "mode": 0, "inputs": sockets, "outputs": outs,
                "properties": {"cnr_id": "comfy-core", "ver": "0.37.4", "Node name for S&R": typ},
                "widgets_values": list(widgets.values()), "widgets_values_named": widgets}
        if typ == "MiniMaxH3ImageToVideo":
            node["title"] = f"{title} · {values['width']}×{values['height']} / {values['length']}帧"
        if typ == "LoraLoaderModelOnly":
            node["title"] = "风格 LoRA" if "FeishengStyleV11" in values["lora_name"] else "Turbo 8 步 LoRA"
        nodes.append(node); by_id[key] = node
    for key, item in api.items():
        node = by_id[key]
        for name, value in item["inputs"].items():
            if not is_link(value): continue
            parent, out_slot = str(value[0]), value[1]
            in_slot = next(i for i, x in enumerate(node["inputs"]) if x["name"] == name)
            datatype = node["inputs"][in_slot]["type"]
            assert by_id[parent]["outputs"][out_slot]["type"] == datatype
            lid = len(edges) + 1
            edges.append([lid, int(parent), out_slot, int(key), in_slot, datatype])
            node["inputs"][in_slot]["link"] = lid
            by_id[parent]["outputs"][out_slot]["links"].append(lid)
    graph = {"last_node_id": max(n["id"] for n in nodes), "last_link_id": len(edges), "nodes": nodes,
             "links": edges, "groups": [], "config": {}, "extra": {"ds": {"scale": 0.34, "offset": [40, 40]},
             "feisheng": {"title": title, "frozen_api_sha256": hashlib.sha256(json.dumps(api, sort_keys=True).encode()).hexdigest(),
                          "conversion": "installed 0.37.4 node schema / 1.52.7 native widget names"}}, "version": 0.4}
    # Verify every API connection and scalar against the saved graph.
    for key, item in api.items():
        node = by_id[key]
        for name, value in item["inputs"].items():
            if is_link(value):
                sock = next(s for s in node["inputs"] if s["name"] == name)
                edge = next(e for e in edges if e[0] == sock["link"])
                assert edge[1:3] == [int(value[0]), value[1]]
            elif item["class_type"] != "SaveVideo":
                assert node["widgets_values_named"][name] == value, (key, name)
    return graph


def input_dependencies(api):
    result = []
    for node in api.values():
        if node["class_type"] not in ["LoadImage", "LoadVideo"]: continue
        for key in ["image", "file"]:
            name = node["inputs"].get(key)
            if not isinstance(name, str): continue
            source = (INPUT / name).resolve()
            assert source.is_relative_to(INPUT.resolve())
            entry = {"comfy_input": name, "path": str(source), "exists": source.exists()}
            if source.exists():
                dest = OUT / "inputs" / name
                retain(source, dest)
                entry.update(sha256=digest(source), bytes=source.stat().st_size, archived_path=dest.relative_to(OUT).as_posix())
            result.append(entry)
    return result


def model_inventory(apis):
    selectors = {"UNETLoader": {"unet_name": "diffusion_models"}, "CLIPLoader": {"clip_name": "text_encoders"},
                 "VAELoader": {"vae_name": "vae"}, "LoraLoaderModelOnly": {"lora_name": "loras"},
                 "H3StudioModels": {"diffusion_model": "diffusion_models", "text_encoder": "text_encoders", "video_vae": "vae", "turbo_lora": "loras"}}
    used = {}
    for source, api in apis:
        for node in api.values():
            for key, category in selectors.get(node["class_type"], {}).items():
                name = node["inputs"].get(key)
                if name and name != "None": used.setdefault((category, name.replace("\\", "/")), set()).add(source.relative_to(ROOT).as_posix())
    result = []
    for (category, name), workflows in used.items():
        candidates = [Path("<LOCAL_PATH>/COMFY") / category / name,
                      Path("<LOCAL_PATH>/models") / category / name,
                      Path("<LOCAL_PATH>/models") / category / name]
        if category == "text_encoders":
            candidates += [p.parent.parent / "clip" / name for p in candidates]
        source = next((p for p in candidates if p.exists()), None)
        assert source, f"Used model missing: {name}"
        with source.open("rb") as f:
            header_bytes = int.from_bytes(f.read(8), "little")
            assert 0 < header_bytes < 64 * 1024 * 1024
            header = json.loads(f.read(header_bytes))
        metadata = {"name": name, "category": category, "path": str(source), "bytes": source.stat().st_size,
                    "exists": True, "header_sha256": hashlib.sha256(json.dumps(header, sort_keys=True).encode()).hexdigest(),
                    "file_sha256": None, "integrity_scope": "safetensors header and physical size; full hash not recomputed for large existing weights",
                    "used_by": sorted(workflows), "retention": "original installed weights retained in global model directory"}
        for lora in LORAS:
            if name == lora["comfy_name"]:
                assert digest(source) == lora["sha256"]
                metadata.update(file_sha256=lora["sha256"], revision=lora["revision"], source=lora["source"],
                                integrity_scope="full file SHA256 matches pinned Hugging Face LFS digest")
        result.append(metadata)
    sr = Path("<LOCAL_PATH>/4x-UltraSharp.pth")
    if sr.exists():
        result.append({"name": sr.name, "category": "upscale_models", "path": str(sr), "bytes": sr.stat().st_size,
                       "exists": True, "file_sha256": digest(sr), "used_by": ["work/feisheng/bench_sr.py"],
                       "purpose": "three-frame 1080p comparison only; not used in chosen final MV or v11 clips", "retention": "existing installed model retained"})
    return result


def main():
    for p in [OUT, USER]: p.mkdir(parents=True, exist_ok=True)
    files = [p for p in (ROOT / "outputs").rglob("*API.json") if OUT not in p.parents]
    apis = [(p, json.loads(p.read_text(encoding="utf-8-sig"))) for p in sorted(files)]
    rows = []
    for source, api in apis:
        group = stage(source); stem = source.stem.removesuffix("-API")
        native_name = stem + ".json"
        unknown = sorted({n["class_type"] for n in api.values()} - INFO.keys())
        retain(source, OUT / "API" / group / source.name)
        if unknown:
            existing = ROOT / "outputs/H3-4060Ti-8GB-TextToImage.json"
            native_name = "历史-H3Studio-文生图.json"
            retain(existing, OUT / "工作流" / group / native_name)
            retain(existing, USER / group / native_name)
        else:
            graph = native_graph(api, group + " / " + stem)
            save(OUT / "工作流" / group / native_name, graph)
            save(USER / group / native_name, graph)
            if group == "风格-v11":
                save(source.with_name(stem + ".json"), graph)
        deps = input_dependencies(api)
        frozen_hash = digest(source)
        row = {"group": group, "name": native_name, "original_api": source.relative_to(ROOT).as_posix(),
               "api_sha256": frozen_hash, "retained_api": "API/" + group + "/" + source.name,
               "retained_native": "工作流/" + group + "/" + native_name,
               "comfy_native": str(USER / group / native_name),
               "comfy_userdata": "workflows/Feisheng-MV/" + group + "/" + native_name,
               "unavailable_nodes_in_current_backend": unknown, "input_dependencies": deps,
               "static_graph_verified": not unknown, "browser_verified": False,
               "note": "历史自定义节点试验；当前原生后端禁用了自定义节点" if unknown else "参数与连接已按冻结 API 核对；本轮按用户要求未操作网页"}
        # Copy already existing execution records; no claims about absent history.
        candidates = [source.parent.parent / "records"]
        if group == "早期红绸": candidates.append(ROOT / "work/feisheng/generation")
        if group == "基础试验": candidates.append(ROOT / "work")
        histories = []
        for directory in candidates:
            for suffix in ["history", "submitted", "manifest", "video"]:
                p = directory / (stem + "-" + suffix + ".json")
                if p.exists():
                    dest = OUT / "records" / group / p.name;retain(p, dest)
                    histories.append(dest.relative_to(OUT).as_posix())
        row["records"] = histories
        rows.append(row)
    save(OUT / "模型清单.json", model_inventory(apis))
    retain(CONFIG, OUT / "configs/instance-model-paths.yaml")
    for name in ["start_backend.ps1", "render.py", "install_loras.py", "audit_lora_headers.py", "prepare.py", "import_stills.py", "publish.py", "retain_comfy.py"]:
        retain(WORK / name, OUT / "scripts" / name)
    retain(WORK / "object-info.json", OUT / "configs/object-info.json")
    # All project histories survive ComfyUI process restarts as file snapshots.
    for p in PROJECT.rglob("*-history.json"):
        if OUT in p.parents: continue
        dest = OUT / "history" / p.relative_to(PROJECT);retain(p, dest)
    for p in (ROOT / "work/feisheng/generation").glob("*-history.json"):
        retain(p, OUT / "history/早期红绸" / p.name)
    history = json.load(urllib.request.urlopen("http://127.0.0.1:8000/history", timeout=30))
    queue = json.load(urllib.request.urlopen("http://127.0.0.1:8000/queue", timeout=30))
    save(OUT / "records/本轮ComfyUI完整历史.json", history)
    save(OUT / "records/留存时队列状态.json", queue)
    # Verify the public file-listing API sees each saved workflow. Do not load UI.
    names = json.load(urllib.request.urlopen("http://127.0.0.1:8000/userdata?dir=workflows&recurse=true", timeout=30))
    normalized = {x.replace("\\", "/") for x in names}
    for row in rows:
        expected = row["comfy_userdata"].removeprefix("workflows/")
        assert expected in normalized, expected
        assert digest(Path(row["comfy_native"])) == digest(OUT / row["retained_native"])
    save(OUT / "工作流索引.json", rows)
    counts = {group: sum(x["group"] == group for x in rows) for group in sorted({x["group"] for x in rows})}
    save(OUT / "留存检查.json", {"api_count": len(rows), "native_count": len(rows), "counts": counts,
                                "native_backend_supported": sum(not x["unavailable_nodes_in_current_backend"] for x in rows),
                                "missing_inputs": [d for x in rows for d in x["input_dependencies"] if not d["exists"]],
                                "userdata_listing_verified": True, "browser_interaction_performed": False,
                                "current_history_count": len(history), "queued": len(queue["queue_pending"]), "running": len(queue["queue_running"]),
                                "model_count": len(json.loads((OUT / "模型清单.json").read_text(encoding="utf-8")))})
    print(json.dumps({"api_count": len(rows), "counts": counts, "model_count": len(json.loads((OUT / "模型清单.json").read_text(encoding="utf-8"))),
                      "missing_inputs": sum(not d["exists"] for x in rows for d in x["input_dependencies"])}, ensure_ascii=False))


if __name__ == "__main__": main()
