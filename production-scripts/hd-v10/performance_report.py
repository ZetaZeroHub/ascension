"""Publish measured fast/HD timing from the paired Feisheng clips."""

import json
import statistics
from pathlib import Path


root = Path(__file__).resolve().parents[3]
fast_dir = root / "outputs/Feisheng-MV/补充与舞蹈-v9"
hd_dir = root / "outputs/Feisheng-MV/高清素材-v10"
items = json.loads((fast_dir / "素材清单.json").read_text(encoding="utf-8"))

rows = []
for item in items:
    sid = item["shot"]
    manifest_file = hd_dir / "records" / f"{sid}-manifest.json"
    if not manifest_file.exists():
        continue
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    rows.append(
        {
            "shot": sid,
            "name": item["name"],
            "fast_seconds": float(item["generation_seconds"]),
            "hd_seconds": float(manifest["generation_seconds"]),
            "interpolation_seconds": float(manifest["interpolation_seconds"]),
        }
    )

fast = [row["fast_seconds"] for row in rows]
hd = [row["hd_seconds"] for row in rows]
interp = [row["interpolation_seconds"] for row in rows]
summary = {
    "paired_shots": len(rows),
    "total_shots": len(items),
    "fast_generation_seconds": {
        "min": min(fast),
        "median": statistics.median(fast),
        "max": max(fast),
    },
    "hd_generation_seconds": {
        "min": min(hd),
        "median": statistics.median(hd),
        "max": max(hd),
    },
    "hd_interpolation_seconds": {
        "median": statistics.median(interp),
    },
    "median_hd_to_fast_generation_ratio": statistics.median(hd) / statistics.median(fast),
    "rows": rows,
}
(hd_dir / "审查/档位与耗时实测.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)

lines = [
    "# 《飞升》两档生成规格与本机实测",
    "",
    f"现有 {len(rows)}/10 段已有成对实测。以下为 ComfyUI **模型执行**耗时，不含首帧制作、排队、人工验收和整包打包。",
    "",
    "| 档位 | 原生生成 | 采样 | 交付 | 已完成镜头耗时中位数 | 本机实测范围 |",
    "| --- | --- | --- | --- | ---: | ---: |",
    f"| 快速 v9 | 640×384、124 帧 / 24fps | Turbo LoRA 8 步 | 裁切放大至 1280×720 / 24fps | {statistics.median(fast)/60:.2f} 分钟 | {min(fast)/60:.2f}–{max(fast)/60:.2f} 分钟 |",
    f"| 高清 v10 | 1280×736、124 帧 / 24fps | 原模型 25 步 | 原生裁切 1280×720 / 24fps；可选 48fps 插帧 | {statistics.median(hd)/60:.2f} 分钟 | {min(hd)/60:.2f}–{max(hd)/60:.2f} 分钟 |",
    "",
    f"高清档生成耗时中位数约为快速档的 {summary['median_hd_to_fast_generation_ratio']:.1f} 倍；48fps 后处理额外中位耗时 {statistics.median(interp):.1f} 秒。两档均为 124/24 = 5.167 秒的视频。48fps 是运动补偿插帧，不是 H3 原生 48fps；快速档的 720p 是放大文件尺寸，不是原生细节。",
    "",
    "| 镜头 | 快速生成 | 高清生成 | 高清插帧后处理 |",
    "| --- | ---: | ---: | ---: |",
]
for row in rows:
    lines.append(
        f"| {row['shot']} {row['name']} | {row['fast_seconds']/60:.2f} 分钟 | {row['hd_seconds']/60:.2f} 分钟 | {row['interpolation_seconds']:.1f} 秒 |"
    )
lines.extend(
    [
        "",
        "画面效果以逐镜视觉验收为准。高清版增加衣料、皮肤和雕塑细节；快速动作处仍可能有模型原生运动模糊，插帧也不能恢复不存在的细节。近景脸部和高速肢体镜头优先检查高清母版；过门、中远景与构图试错可先用快速档。",
        "",
    ]
)
(hd_dir / "档位与耗时实测.md").write_text("\n".join(lines), encoding="utf-8")
print(json.dumps({key: value for key, value in summary.items() if key != "rows"}, ensure_ascii=False))
