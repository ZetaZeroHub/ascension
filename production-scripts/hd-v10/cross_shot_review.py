"""Make first/middle/last-frame sheets for the narrative and dance clips."""

import json
from pathlib import Path

import av
from PIL import Image, ImageDraw, ImageFont


root = Path(__file__).resolve().parents[3]
out = root / "outputs/Feisheng-MV/高清素材-v10"
source = root / "outputs/Feisheng-MV/补充与舞蹈-v9"
items = json.loads((source / "素材清单.json").read_text(encoding="utf-8"))
groups = {
    "剧情": [item for item in items if int(item["shot"]) <= 16],
    "舞蹈": [item for item in items if int(item["shot"]) >= 17],
}
font_path = Path("<LOCAL_PATH>/msyh.ttc")
font = ImageFont.truetype(str(font_path), 18) if font_path.exists() else ImageFont.load_default()
indices = (0, 60, 123)

for group, shots in groups.items():
    sheet = Image.new("RGB", (1152, 248 * len(shots)), (13, 17, 23))
    draw = ImageDraw.Draw(sheet)
    for row, item in enumerate(shots):
        sid = item["shot"]
        video = out / "24fps母版" / f"{sid}-{item['name']}.mp4"
        if not video.exists():
            draw.text((12, row * 248 + 15), f"{sid} {item['name']} · 生成中", font=font, fill="white")
            continue
        frames = {}
        with av.open(str(video)) as container:
            for index, frame in enumerate(container.decode(video=0)):
                if index in indices:
                    frames[index] = frame.to_image().resize((384, 216), Image.Resampling.LANCZOS)
        assert set(frames) == set(indices), (sid, sorted(frames))
        for col, index in enumerate(indices):
            x, y = col * 384, row * 248
            sheet.paste(frames[index], (x, y))
            draw.text((x + 8, y + 219), f"{sid} {item['name']} · {index / 24:.2f}s", font=font, fill="white")
    target = out / "审查" / f"跨镜连续性-{group}.jpg"
    sheet.save(target, quality=92)
    print(str(target))
