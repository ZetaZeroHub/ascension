import json, hashlib, time
from pathlib import Path
import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parent
PUB=ROOT/'remotion/public'
OUT=ROOT/'analysis/clip-qc'
OUT.mkdir(exist_ok=True)
font=ImageFont.truetype('<LOCAL_PATH>/msyh.ttc',16)
story=json.loads((ROOT/'src/data/storyboard.json').read_text(encoding='utf-8'))
results=[]
for s in story['scenes']:
    src=PUB/s['native_video']; marker=ROOT/'generation'/f"{s['id']}-manifest.json"
    while not marker.exists():time.sleep(10)
    manifest=json.loads(marker.read_text())
    assert hashlib.sha256(src.read_bytes()).hexdigest()==manifest['sha256']
    frames=[];tiny=[];timestamps=[]
    with av.open(str(src)) as c:
        assert not c.streams.audio
        for f in c.decode(video=0):
            assert (f.width,f.height)==(704,384)
            timestamps.append(float(f.pts*f.time_base))
            tiny.append(np.asarray(f.to_image().resize((176,96)),dtype=np.float32))
            if len(tiny)-1 in [0,17,35,52,70,87,105,123]:frames.append((len(tiny)-1,f.to_image()))
    assert len(tiny)==124
    assert all(abs((b-a)-1/24)<1e-5 for a,b in zip(timestamps,timestamps[1:]))
    diff=[float(np.abs(b-a).mean()) for a,b in zip(tiny,tiny[1:])]
    result={'id':s['id'],'decoded_frames':len(tiny),'black_frames_under_mean_1':[i for i,x in enumerate(tiny) if x.mean()<1], 'mean_adjacent_pixel_change':float(np.mean(diff)),'max_adjacent_pixel_change':max(diff),'identical_frame_pairs_under_0_01':sum(d<.01 for d in diff),'generation_seconds':manifest['generation_seconds']}
    results.append(result)
    sheet=Image.new('RGB',(1408,832),'#101112');d=ImageDraw.Draw(sheet)
    for i,(idx,im) in enumerate(frames):
        x=(i%2)*704;y=(i//2)*208
        im=im.resize((352,192),Image.Resampling.LANCZOS)
        # Wide columns leave annotations readable while preserving native aspect.
        sheet.paste(im,(x+176,y+16));d.text((x+12,y+18),f"{s['id']} / {idx:03d}",font=font,fill='white')
    sheet.save(OUT/f"{s['id']}-motion.jpg",quality=92)
    (OUT/'native-validation.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)
print('NATIVE_QC_COMPLETE',flush=True)
