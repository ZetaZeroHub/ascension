"""Create matching-time visual sheets for direct v9/v10 review; does not modify the clips."""
import json,sys
from pathlib import Path
import av
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[3]
OLD=R/'outputs/Feisheng-MV/补充与舞蹈-v9';NEW=R/'outputs/Feisheng-MV/高清素材-v10'
items=json.loads((OLD/'素材清单.json').read_text(encoding='utf-8'))
times=[0,24,48,72,96,123]
def frames(path):
    result={}
    with av.open(str(path)) as c:
        for i,f in enumerate(c.decode(video=0)):
            if i in times:result[i]=f.to_image().resize((640,360),Image.Resampling.LANCZOS)
    return result
for item in items:
    sid=item['shot'];old=OLD/'独立视频'/f"{sid}-{item['name']}.mp4";new=NEW/'24fps母版'/f"{sid}-{item['name']}.mp4"
    if not new.exists():continue
    a,b=frames(old),frames(new)
    assert len(a)==len(b)==len(times)
    sheet=Image.new('RGB',(1280,390*len(times)),(12,15,20));draw=ImageDraw.Draw(sheet)
    for i,n in enumerate(times):
        y=i*390;sheet.paste(a[n],(0,y));sheet.paste(b[n],(640,y))
        draw.text((12,y+364),f'{sid} v9 FAST / {n/24:.3f}s',fill='white')
        draw.text((652,y+364),f'{sid} v10 NATIVE720 25 / {n/24:.3f}s',fill='white')
    target=NEW/'审查'/f'{sid}-v9-v10-对照.jpg';sheet.save(target,quality=91)
    print(sid,target)
