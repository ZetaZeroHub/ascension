import sys,json
from pathlib import Path
import av
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];O=R/'outputs/Feisheng-MV/高清素材-v10';sid=sys.argv[1]
m=json.loads((O/'records'/f'{sid}-manifest.json').read_text(encoding='utf-8'))
source=O/m['smooth_file'];samples=[]
with av.open(str(source)) as c:
    for i,f in enumerate(c.decode(video=0)):
        if i%24==13:samples.append((i,f.to_image().resize((512,288))))
im=Image.new('RGB',(1536,((len(samples)+2)//3)*310),(15,16,18));d=ImageDraw.Draw(im)
for j,(n,img) in enumerate(samples):
    x=j%3*512;y=j//3*310;im.paste(img,(x,y));d.text((x+8,y+291),f'{sid} interpolated frame {n} {n/48:.3f}s',fill='white')
target=O/'审查'/f'{sid}-插帧奇数帧.jpg';im.save(target,quality=92);print(target)
