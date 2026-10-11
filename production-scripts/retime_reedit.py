import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PUB=ROOT/'remotion-v2/public'
story=json.loads((ROOT/'remotion-v2/src/data/storyboard.json').read_text(encoding='utf-8'))
for s in story['scenes']:
    if int(s['id'])<7:continue
    n=s['to']-s['from'];factor=(n-1)/123
    src=PUB/s['native_video'];retimed=PUB/'retimed'/f"{s['id']}.mp4";graded=PUB/'graded'/f"{s['id']}.mp4"
    vf=f'tpad=stop_mode=clone:stop_duration=0.5,setpts={factor}*(PTS-STARTPTS),minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,tpad=stop_mode=clone:stop_duration=1,setsar=1'
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-threads','2','-i',str(src),'-an','-vf',vf,'-filter_threads','2','-frames:v',str(n),'-c:v','libx264','-preset','slow','-crf','15','-threads','2',str(retimed)],check=True)
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-threads','2','-i',str(retimed),'-an','-vf','scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1920:1080,unsharp=5:5:0.35:3:3:0,setsar=1','-filter_threads','2','-frames:v',str(n),'-c:v','libx264','-preset','slow','-crf','16','-pix_fmt','yuv420p','-threads','2','-color_primaries','bt709','-color_trc','iec61966-2-1','-colorspace','bt709','-movflags','+faststart',str(graded)],check=True)
    p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=nb_frames','-of','json',str(graded)]))
    assert int(p['streams'][0]['nb_frames'])==n
    print(s['id'],n,'frames',flush=True)
print('REEDIT_ASSETS_COMPLETE',flush=True)
