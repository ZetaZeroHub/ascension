import json, time
from pathlib import Path
import av
import numpy as np
ROOT=Path(__file__).resolve().parent
PUB=ROOT/'remotion/public'
story=json.loads((ROOT/'src/data/storyboard.json').read_text(encoding='utf-8'))
report=[]
def endpoints(path):
    try:
        with av.open(str(path)) as c:
            first=None;last=None;count=0
            for f in c.decode(video=0):
                if first is None:first=f.to_ndarray(format='rgb24').astype(np.float32)
                last=f;count+=1
            return count,first,last.to_ndarray(format='rgb24').astype(np.float32)
    except (FileNotFoundError,av.error.InvalidDataError):return 0,None,None
for s in story['scenes']:
    n=s['to']-s['from'];p=PUB/'graded'/f"{s['id']}.mp4"
    while True:
        try:
            with av.open(str(p)) as c:ready=c.streams.video[0].frames==n
        except (FileNotFoundError,av.error.InvalidDataError):ready=False
        if ready:break
        time.sleep(10)
    native=endpoints(PUB/s['native_video']);retimed=endpoints(PUB/'retimed'/f"{s['id']}.mp4")
    assert native[0]==124 and retimed[0]==n
    first_mae=float(np.abs(native[1]-retimed[1]).mean())
    last_mae=float(np.abs(native[2]-retimed[2]).mean())
    assert first_mae<5 and last_mae<5, 'Endpoint drift after retiming'
    graded=endpoints(p);assert graded[0]==n and graded[1].shape==(1080,1920,3)
    row={'id':s['id'],'native_frames':124,'edit_frames':n,'first_endpoint_pixel_mae_255':first_mae,'last_endpoint_pixel_mae_255':last_mae,'graded_size':[1920,1080]}
    report.append(row)
    (ROOT/'analysis/edit-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(row),flush=True)
print('EDIT_QC_COMPLETE',flush=True)
