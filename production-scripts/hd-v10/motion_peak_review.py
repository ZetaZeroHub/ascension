"""Make even/odd/even triptychs at the strongest motion for 48fps artifact review."""
import json
import sys
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[3]
out = root / 'outputs/Feisheng-MV/高清素材-v10'
sid = sys.argv[1]
manifest = json.loads((out / 'records' / f'{sid}-manifest.json').read_text(encoding='utf-8'))
video = out / manifest['smooth_file']

small = []
with av.open(str(video)) as container:
    for frame in container.decode(video=0):
        small.append(np.asarray(frame.to_image().resize((160, 90))).astype(np.int16))
assert len(small) == 248
scores = []
for center in range(1, 247, 2):
    a, b, c = small[center - 1:center + 2]
    score = float(np.abs(b - a).mean() + np.abs(c - b).mean())
    scores.append((score, center))

selected = []
for score, center in sorted(scores, reverse=True):
    if all(abs(center - prior) >= 14 for _, prior in selected):
        selected.append((score, center))
    if len(selected) == 6:
        break
selected.sort(key=lambda entry: entry[1])
indices = {frame for _, center in selected for frame in (center - 1, center, center + 1)}
images = {}
with av.open(str(video)) as container:
    for index, frame in enumerate(container.decode(video=0)):
        if index in indices:
            images[index] = frame.to_image().resize((512, 288), Image.Resampling.LANCZOS)

sheet = Image.new('RGB', (1536, 310 * len(selected)), (12, 15, 20))
draw = ImageDraw.Draw(sheet)
for row, (score, center) in enumerate(selected):
    for column, index in enumerate((center - 1, center, center + 1)):
        x, y = column * 512, row * 310
        sheet.paste(images[index], (x, y))
        label = 'interpolated' if column == 1 else 'native cadence'
        draw.text((x + 8, y + 291), f'{sid}  frame {index}  {index / 48:.3f}s  {label}', fill='white')
target = out / '审查' / f'{sid}-强运动插帧三联.jpg'
sheet.save(target, quality=92)
print(json.dumps({'shot': sid, 'image': str(target), 'peak_frames': [center for _, center in selected]}, ensure_ascii=False))
