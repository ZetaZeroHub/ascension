import json, subprocess, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PUBLIC=ROOT/'remotion/public'
OUT=PUBLIC/'retimed'
OUT.mkdir(exist_ok=True)
plan=json.loads((ROOT/'src/data/storyboard.json').read_text(encoding='utf-8'))
for s in plan['scenes']:
    src=PUBLIC/s['native_video']
    target=OUT/(s['id']+'.mp4')
    marker=ROOT/'generation'/f"{s['id']}-manifest.json"
    while not marker.exists(): time.sleep(10)
    n=s['to']-s['from']
    if target.exists():
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=nb_frames','-of','json',str(target)]))
        if int(probe['streams'][0].get('nb_frames',0))==n: continue
    # Map the exact first and last source frames to the first and last edit frames.
    factor=(n-1)/123
    vf=f'tpad=stop_mode=clone:stop_duration=0.5,setpts={factor:.12f}*(PTS-STARTPTS),minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,tpad=stop_mode=clone:stop_duration=1,setsar=1'
    start=time.monotonic()
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-threads','2','-i',str(src),'-an','-vf',vf,'-filter_threads','2','-frames:v',str(n),'-c:v','libx264','-preset','slow','-crf','15','-pix_fmt','yuv420p','-threads','2','-movflags','+faststart',str(target)],check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=nb_frames','-of','json',str(target)]))
    assert int(probe['streams'][0]['nb_frames'])==n, 'Frame count does not match the timeline'
    print(json.dumps({'scene':s['id'],'edit_frames':n,'retime_factor':factor,'seconds':round(time.monotonic()-start,2)}),flush=True)
print('RETIME_COMPLETE',flush=True)
