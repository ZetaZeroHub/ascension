import json, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PUB=ROOT/'remotion/public'
OUT=PUB/'graded'
OUT.mkdir(exist_ok=True)
story=json.loads((ROOT/'src/data/storyboard.json').read_text(encoding='utf-8'))
def probe(path):
    try:
        r=subprocess.run(['ffprobe','-v','error','-show_entries','stream=nb_frames,width,height','-of','json',str(path)],capture_output=True,text=True)
        return json.loads(r.stdout)['streams'][0]
    except (KeyError,IndexError,ValueError): return {}
for s in story['scenes']:
    n=s['to']-s['from'];src=PUB/'retimed'/f"{s['id']}.mp4";target=OUT/f"{s['id']}.mp4"
    while int(probe(src).get('nb_frames',0))!=n: time.sleep(10)
    if int(probe(target).get('nb_frames',0))==n: continue
    begin=time.monotonic()
    vf='scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1920:1080,unsharp=5:5:0.35:3:3:0,setsar=1'
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-threads','2','-i',str(src),'-an','-vf',vf,'-filter_threads','2','-frames:v',str(n),'-c:v','libx264','-preset','slow','-crf','16','-pix_fmt','yuv420p','-threads','2','-color_primaries','bt709','-color_trc','iec61966-2-1','-colorspace','bt709','-movflags','+faststart',str(target)],check=True)
    print(json.dumps({'scene':s['id'],'seconds':round(time.monotonic()-begin,2),'size':[1920,1080]}),flush=True)
print('POLISH_COMPLETE',flush=True)
