import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PUB=ROOT/'remotion/public'
for p in sorted((PUB/'graded').glob('*.mp4')):
    meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=color_transfer','-of','json',str(p)]))
    if meta['streams'][0].get('color_transfer')=='iec61966-2-1':continue
    target=p.with_suffix('.colorfix.mp4')
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-i',str(p),'-map','0','-c','copy','-bsf:v','h264_metadata=transfer_characteristics=13','-color_trc','iec61966-2-1','-movflags','+faststart',str(target)],check=True)
    target.replace(p)
    print('Preserved source sRGB transfer metadata:',p.name)
