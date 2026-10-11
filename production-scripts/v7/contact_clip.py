import av,sys
from PIL import Image,ImageDraw
from pathlib import Path
source=Path(sys.argv[1]);target=Path(sys.argv[2]);stride=int(sys.argv[3]) if len(sys.argv)>3 else 6
items=[]
with av.open(str(source)) as c:
    for n,f in enumerate(c.decode(video=0)):
        if n%stride==0:items.append((n,f.to_image().resize((384,216),Image.Resampling.LANCZOS)))
canvas=Image.new('RGB',(1536,((len(items)+3)//4)*238),(18,19,18));d=ImageDraw.Draw(canvas)
for i,(n,img) in enumerate(items):
    x=i%4*384;y=i//4*238;canvas.paste(img,(x,y));d.text((x+8,y+219),f'frame {n} / {n/24:.3f}s',fill=(240,230,218))
canvas.save(target)
