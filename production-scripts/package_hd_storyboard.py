from pathlib import Path
import json, hashlib, shutil, html
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/Feisheng-MV/独立分镜-v6'
shots=json.loads((OUT/'shot-plan.json').read_text(encoding='utf-8'))
rows=[]
for sid,name,start,end,prompt in shots:
    path=OUT/'frames'/f'{sid}.png'
    if not path.exists():
        raise RuntimeError(f'Missing frame {sid}')
    with Image.open(path) as im:
        im.verify()
    with Image.open(path) as im:
        size=im.size
    if size[0] < 1500 or abs(size[0]/size[1]-16/9)>.02:
        raise RuntimeError(f'Unexpected frame size {sid}: {size}')
    rows.append(dict(id=sid,name=name,start=start,end=end,prompt=prompt,file=f'frames/{sid}.png',width=size[0],height=size[1],sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(OUT/'asset-manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copy2(ROOT/'work/feisheng/remotion/public/audio/feisheng-original.m4a',OUT/'music.m4a')
cards=''.join(f'<a class="card" href="{r["file"]}" target="_blank"><img loading="lazy" src="{r["file"]}" alt="{html.escape(r["name"])}"><b>{r["id"]} / {html.escape(r["name"])}</b><small>{r["start"]:.1f}–{r["end"]:.1f}s · {r["width"]}×{r["height"]}</small></a>' for r in rows)
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>飞升 / 独立高清分镜 V6</title><style>*{box-sizing:border-box}body{background:#191a19;color:#e8e2d7;font:16px/1.65 system-ui;margin:0}main{max-width:1500px;margin:auto;padding:30px 24px}h1{font-size:38px;margin:8px 0}p,small{color:#b8b7b0}.eyebrow{color:#d1b589;font-size:12px;letter-spacing:.16em}.player{display:flex;gap:20px;align-items:center;flex-wrap:wrap;margin:20px 0}audio{width:550px;max-width:100%}#hero{width:100%;display:block;aspect-ratio:16/9;object-fit:contain;background:#101010}nav{display:flex;gap:6px;flex-wrap:wrap;margin:14px 0}button{background:#292b28;color:#eee;border:1px solid #666;padding:9px 12px;cursor:pointer;font:inherit}button[aria-pressed=true]{border-color:#dabb82;background:#494237}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.card{color:#eee;text-decoration:none;background:#242623;padding-bottom:12px}.card img{width:100%;display:block}.card b,.card small{display:block;padding:5px 12px}a{color:#dfc698}.info{border-left:3px solid #ba985f;padding:14px 22px;margin:22px 0;background:#242623}.reference{max-height:430px;max-width:100%;display:block}#title{font-size:23px}button:focus-visible{outline:3px solid #f5d490}@media(max-width:750px){.grid{grid-template-columns:1fr 1fr}main{padding:20px 12px}h1{font-size:28px}}</style><main><div class="eyebrow">FEISHENG / THE FIRE COURIER · HD STORYBOARD V6</div><h1>飞升 · 独立高清分镜</h1><p>已选方向：B 暖灰柔和。每张独立生成，统一角色参考；本轮是关键帧设计，不是已经生成的视频。</p><div class="player"><audio id="music" src="music.m4a" controls preload="metadata"></audio><label><input type="checkbox" id="follow" checked> 随音乐定位关键帧</label><span id="time">0.00s</span></div><nav id="nav"></nav><a id="full" href="frames/01.png" target="_blank"><img id="hero" src="frames/01.png" alt="当前关键帧"></a><h2 id="title"></h2><p id="timing"></p><div class="info">点击编号定位音乐；点击画面查看原尺寸。音乐保持本地原文件。展示时段是情节区间，不是最终逐镜剪辑时长；最终会增加动作覆盖和短镜头。<br>色彩为生成时参考 B 方向，未对已经调色的图重复叠加同一曲线。角色与道具的一致性需结合实际视频继续验证。</div><h2>12 张独立画面</h2><div class="grid">CARDS</div><h2>统一角色参考</h2><a href="reference/character.png" target="_blank"><img class="reference" src="reference/character.png" alt="红衣信使角色参考"></a><p>短黑发、酒红长外套、黑色内搭、右腕金线。面部与服装来自已确认概念稿；此图作为跨镜参考，不能保证生成模型绝对不漂移。</p><p><a href="review-notes.md">视觉复核与下一步</a> · <a href="asset-manifest.json">尺寸与哈希清单</a> · <a href="generation-manifest.json">生成提示词与来源</a></p></main><script>const shots=DATA;const music=document.getElementById('music');music.volume=.5;let selected=-1;shots.forEach((s,i)=>{let b=document.createElement('button');b.textContent=s.id+' '+s.name;b.onclick=()=>{select(i);music.currentTime=s.start};document.getElementById('nav').append(b)});function select(i){if(selected===i)return;selected=i;let s=shots[i];document.getElementById('hero').src=s.file;document.getElementById('hero').alt=s.name;document.getElementById('full').href=s.file;document.getElementById('title').textContent=s.id+' / '+s.name;document.getElementById('timing').textContent=s.start.toFixed(1)+'–'+s.end.toFixed(1)+'s · '+s.width+'×'+s.height+' · 静态关键帧';[...document.getElementById('nav').children].forEach((b,n)=>b.setAttribute('aria-pressed',n===i?'true':'false'))}music.ontimeupdate=()=>{document.getElementById('time').textContent=music.currentTime.toFixed(2)+'s';if(document.getElementById('follow').checked){let i=0;shots.forEach((s,n)=>{if(music.currentTime>=s.start)i=n});select(i)}};select(0);</script></html>'''
page=page.replace('CARDS',cards).replace('DATA',json.dumps(rows,ensure_ascii=False))
(OUT/'index.html').write_text(page,encoding='utf-8')
print(json.dumps({'frames':len(rows),'sizes':sorted({(r['width'],r['height']) for r in rows}),'page':str(OUT/'index.html')},ensure_ascii=False))
