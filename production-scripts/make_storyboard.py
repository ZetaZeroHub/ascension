import json, html
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parents[1]/'outputs/Feisheng-MV'
story=json.loads((ROOT/'src/data/storyboard.json').read_text(encoding='utf-8'))
font=ImageFont.truetype('<LOCAL_PATH>/msyh.ttc',22)
small=ImageFont.truetype('<LOCAL_PATH>/msyh.ttc',16)
for page in range(2):
    canvas=Image.new('RGB',(1440,1670),'#101112');draw=ImageDraw.Draw(canvas)
    draw.text((24,15),f"飞升 · 首尾帧分镜 {page+1}/2",font=font,fill='#ead8bb')
    for row,s in enumerate(story['scenes'][page*7:(page+1)*7]):
        y=58+row*228
        draw.text((24,y),f"{s['id']}  {s['title']}  /  {s['hero_stage']}   {s['from']/24:.2f}–{s['to']/24:.2f}s",font=small,fill='#eee8de')
        for j,kind in enumerate(['first','last']):
            image=Image.open(ROOT/'remotion/public'/s[kind+'_image']).convert('RGB')
            image.thumbnail((690,190),Image.Resampling.LANCZOS)
            x=24+j*708+(690-image.width)//2
            canvas.paste(image,(x,y+29))
            draw.text((24+j*708,y+31),'首帧' if j==0 else '尾帧',font=small,fill='white')
    canvas.save(OUT/f'分镜总览-{page+1}.jpg',quality=94)
cards=[]
for s in story['scenes']:
    cards.append(f'''<article><header><span>{s['id']} / {html.escape(s['hero_stage'])}</span><h2>{html.escape(s['title'])}</h2><p>{s['from']/24:.3f}–{s['to']/24:.3f} 秒 · {(s['to']-s['from'])} 帧</p></header><div class="pair"><figure><img src="首尾帧/{s['id']}-first.png"><figcaption>首帧</figcaption></figure><figure><img src="首尾帧/{s['id']}-last.png"><figcaption>尾帧</figcaption></figure></div><details><summary>分镜与运动提示词</summary><p>{html.escape(s['motion_prompt'])}</p><h3>首帧</h3><p>{html.escape(s['first_prompt'])}</p><h3>尾帧</h3><p>{html.escape(s['last_prompt'])}</p></details></article>''')
(OUT/'分镜总览.html').write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>飞升 · 分镜</title><style>body{margin:0;background:#101112;color:#eee9de;font:16px/1.7 "Microsoft YaHei",sans-serif}main{max-width:1420px;margin:auto;padding:48px 28px}h1{font-size:48px;letter-spacing:16px;margin-bottom:8px}header span,figcaption{color:#c9b287}article{margin-top:44px;border-top:1px solid #37322c;padding-top:24px}h2{margin:4px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}figure{margin:0}img{width:100%;display:block}details{font-size:13px;color:#bbb4a9;margin-top:18px}summary{cursor:pointer;color:#ead4b2}@media(max-width:700px){.pair{grid-template-columns:1fr}} </style><main><h1>飞升</h1><p>一条红绸的英雄之旅。重力 → 试炼 → 飞升 → 携光归来。</p><p>95.083 秒 / 24 fps / 14 段文＋首尾帧生成视频 / 最终输出 1920×1080</p><p>卡点来自原曲本地分析。以下为生成原型图；最终动态画面由本机 H3 生成。</p>'''+''.join(cards)+'</main></html>',encoding='utf-8')
print('Storyboard contact sheets and HTML saved.')
