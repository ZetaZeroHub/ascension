"""Build enlarged portrait timeline for identity and facial-motion review."""
import json
import sys
from pathlib import Path

import av
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[3]
out = root / 'outputs/Feisheng-MV/高清素材-v10'
sid = sys.argv[1]
box = tuple(map(int, sys.argv[2:6])) if len(sys.argv) == 6 else (380, 0, 900, 550)
manifest = json.loads((out / 'records' / f'{sid}-manifest.json').read_text(encoding='utf-8'))
video = out / manifest['master_file']
indices = set(range(0, 124, 12)) | {123}
samples = []
with av.open(str(video)) as container:
    for index, frame in enumerate(container.decode(video=0)):
        if index in indices:
            samples.append((index, frame.to_image().crop(box).resize((420, 420), Image.Resampling.LANCZOS)))
assert len(samples) == len(indices)
sheet = Image.new('RGB', (1680, 440 * ((len(samples) + 3) // 4)), (13, 16, 21))
draw = ImageDraw.Draw(sheet)
for position, (index, image) in enumerate(samples):
    x, y = position % 4 * 420, position // 4 * 440
    sheet.paste(image, (x, y))
    draw.text((x + 8, y + 423), f'{sid} frame {index} / {index / 24:.3f}s', fill='white')
target = out / '审查' / f'{sid}-面部连续性.jpg'
sheet.save(target, quality=93)
print(json.dumps({'shot': sid, 'image': str(target), 'frames': len(samples), 'crop': box}, ensure_ascii=False))
