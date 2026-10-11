import av, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parents[1]/'outputs/Feisheng-MV'
story=json.loads((ROOT/'src/data/storyboard.json').read_text(encoding='utf-8'))
frames=set(range(0,2282,48))|{2281}
for scene in story['scenes'][1:]:frames.update([scene['from']-1,scene['from']])
for f in [1441,1470,1642,1671,1786,1801]:frames.update([f-1,f])
images=[]
with av.open(str(OUT/'飞升-MV-1080p.mp4')) as c:
    for i,f in enumerate(c.decode(video=0)):
        if i in frames:
            thumb=f.to_image();thumb.thumbnail((384,216))
            images.append((i,thumb))
font=ImageFont.truetype('<LOCAL_PATH>/arial.ttf',16)
for page,start in enumerate(range(0,len(images),16),1):
    canvas=Image.new('RGB',(1536,984),'#171919');draw=ImageDraw.Draw(canvas)
    for j,(frame,im) in enumerate(images[start:start+16]):
        x=(j%4)*384;y=(j//4)*246
        canvas.paste(im,(x,y+26));draw.text((x+6,y+4),f'{frame/24:06.2f}s | frame {frame}',font=font,fill='white')
    canvas.save(ROOT/'analysis'/f'final-contact-{page}.jpg',quality=93)
print(json.dumps({'sampled_frames':len(images),'pages':page}))
