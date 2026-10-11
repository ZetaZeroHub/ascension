import json,hashlib,subprocess,shutil,csv,zipfile,html
from pathlib import Path
import av,numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];W=R/'work/feisheng/fast-v9';O=R/'outputs/Feisheng-MV/补充与舞蹈-v9'
names=['握紧种子','断桥脚步','核心涟漪','归来回望','正面群舞','低机位独舞','侧面行进','俯拍旋转','近景律动','后方收束']
uses=['取种子之后／跃下之前的决心插镜','断桥全景与起跳之间','放下种子之后／重力反转之前','恢复城市结尾的情绪回声','建立舞台与主角，适合乐句起点','下蹲至伸展，适合渐强段','横移与舒展，连接相邻景别','旋转与衣摆，适合高潮重拍','眼神与上身动作，打断连续全景','舞台空间与队形收束，适合段落结束']
for d in ['独立视频','原生视频','审查','工程']: (O/d).mkdir(exist_ok=True)
results=[];cards=[];sources=[]
sheet=Image.new('RGB',(1200,5*370),(12,15,20));draw=ImageDraw.Draw(sheet)
for n,sid in enumerate(range(13,23)):
    s=str(sid);p=O/'clips'/f'{s}-720p.mp4';native=O/'clips'/f'{s}-native.mp4'
    m=json.loads((O/'records'/f'{s}-manifest.json').read_text())
    label=f'{s}-{names[n]}.mp4';shutil.copy2(p,O/'独立视频'/label);shutil.copy2(native,O/'原生视频'/label)
    thumbs=[];changes=[];previous=None;count=0;black=[]
    with av.open(str(p)) as c:
        v=c.streams.video[0];size=[v.width,v.height];fps=float(v.average_rate)
        for i,f in enumerate(c.decode(video=0)):
            count+=1;a=np.asarray(f.to_image().resize((160,90))).astype(np.float32)
            if a.mean()<1:black.append(i)
            if previous is not None:changes.append(float(np.abs(a-previous).mean()))
            previous=a
            if i%6==0:thumbs.append((i,f.to_image().resize((384,216))))
    assert size==[1280,720] and count==124 and fps==24 and not black,(s,size,count,fps,black)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==m['sha256']
    contact=Image.new('RGB',(1536,((len(thumbs)+3)//4)*238),(16,18,22));d=ImageDraw.Draw(contact)
    for j,(fr,im) in enumerate(thumbs):
        x=j%4*384;y=j//4*238;contact.paste(im,(x,y));d.text((x+8,y+219),f'{s}  frame {fr}  {fr/24:.3f}s',fill='white')
    contact.save(O/'审查'/f'{s}-contact.jpg',quality=88)
    peak=sorted(range(len(changes)),key=lambda k:changes[k],reverse=True);selected=[]
    for k in peak:
        t=(k+1)/24
        if all(abs(t-z)>.45 for z in selected):selected.append(t)
        if len(selected)==3:break
    result={**m,'name':names[n],'file':f'独立视频/{label}','decoded_frames':count,'duration_seconds':count/fps,'fps':fps,'black_frames':black,'mean_frame_change':float(np.mean(changes)),'motion_peak_seconds':sorted(selected),'use':uses[n],'resolution_note':'640x384 generated; center crop to 640x360 then Lanczos resize to 1280x720; not native 720p'}
    results.append(result)
    frame=Image.open(O/'frames'/f'{s}.png').convert('RGB').resize((592,333));x=n%2*600;y=n//2*370;sheet.paste(frame,(x,y));draw.text((x+10,y+343),f'{s} | {"INSERT" if sid<17 else "DANCE"} | 5.167s',fill='white')
    sec=m['generation_seconds'];cards.append(f'<article data-group="{"insert" if sid<17 else "dance"}"><video controls playsinline preload="none" poster="frames/{s}.png" src="{html.escape(result["file"],quote=True)}"></video><div><h2>{s} · {names[n]}</h2><p>{uses[n]}</p><small>5.17 秒 · 24 fps · Turbo 8 步 · 生成 {sec/60:.2f} 分钟</small><p><a href="{result["file"]}" download>下载独立视频</a>　<a href="frames/{s}.png" download>首帧</a>　<a href="workflows/{s}-API.json" download>工作流</a></p></div></article>')
sheet.save(O/'镜头总览.jpg',quality=92)
(O/'素材清单.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
with (O/'剪辑提示.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['镜头','名称','时长秒','用途','运动变化峰值秒_机器候选非音乐重拍','生成耗时秒'])
    for r in results:w.writerow([r['shot'],r['name'],r['duration_seconds'],r['use'],' / '.join(f'{x:.3f}' for x in r['motion_peak_seconds']),r['generation_seconds']])
music=json.loads((R/'work/feisheng/analysis/music-analysis.json').read_text(encoding='utf-8'))
with (O/'飞升音乐拍点.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['拍序','原音乐时间秒','24fps就近帧_从0计'])
    for i,t in enumerate(music['beats']):w.writerow([i+1,f'{t:.6f}',round(t*24)])
prompts={s:json.loads((O/'workflows'/f'{s}-API.json').read_text(encoding='utf-8'))['6']['inputs']['prompt'] for s in map(str,range(13,23))}
(O/'视频提示词.json').write_text(json.dumps(prompts,ensure_ascii=False,indent=2),encoding='utf-8')
for p in ['setup.py','render_shots.py','dance-prompts.json']:shutil.copy2(W/p,O/'工程'/p)
secs=[r['generation_seconds'] for r in results]
note=f'''# 《飞升》补充与舞蹈素材 v9

交付：4 个剧情关联插镜 + 6 个黑棚舞蹈镜头，共 10 段，每段 124 帧 / 24fps = 5.1667 秒，总计 51.6667 秒。独立视频为无音轨、无字幕、无转场的剪辑素材。原版 MV 未覆盖。

## 参数与实测

- 本地 MiniMax H3 FL2VA INT8 ConvRot，Qwen3VL NVFP4 AWQ，Turbo 8-step LoRA，res_multistep / simple，8 步。
- 原生 640×384，中心裁切 640×360，Lanczos 放大输出 1280×720。720p 是交付尺寸，真实生成细节来自 640×360。
- 单段 ComfyUI 执行耗时：最短 {min(secs):.1f} 秒，最长 {max(secs):.1f} 秒，平均 {sum(secs)/len(secs):.1f} 秒；不含首帧制作、队列等待和最终打包。
- 全部 10 段实际生成耗时合计 {sum(secs)/60:.2f} 分钟。此前开始的 25 步任务按用户降档要求中止，未混入本交付。
- 首帧由内置 imagegen 按已定稿角色参考生成；视频全部由本地 ComfyUI 生成。黑棚使用冷青阴影、克制暖边光、白雕塑和微景观；没有使用参考图的文字或界面图形。

## 使用方式

1. 将“独立视频”导入剪辑软件，时间线设 24fps。每段 5.17 秒可自由截取，首尾保留动作余量。
2. “飞升音乐拍点.csv”沿用原音乐本地分析，按原曲起点计秒；不是新视频动作已逐拍对齐的证明。
3. “剪辑提示.csv”给出用途和机器测得的运动变化峰值候选。用刀点对齐音乐重拍，再微调动作顶点；生成式动作并未逐帧锁定音乐。
4. “原生视频”保留未裁切文件；“frames”保留首帧；“workflows”保存每段完整 ComfyUI API 图和种子。复现时将 frames 内图片放入 ComfyUI input/FeishengFastV9/，使用对应 API JSON。

## 验证与限制

全部交付文件完整解码，核对 124 帧、24fps、1280×720、SHA256、无全黑帧。连续抽帧接触表在“审查”。画面审查结论另见“审查/视觉检查.json”；没有把首帧通过等同于视频通过。

低分辨率快速档适合节奏剪辑与中远景；手指、面部微细节与背景雕塑在运动中会变软，背景可能有轻微生成形变。它不是原生 720p/25 步精度。舞蹈为 AI 现代舞短句，不是实拍编舞或动作捕捉。

本任务是供自行剪辑的静音素材包，因此不套用成片旁白、音频母带和字幕验收项；视频编码与连续画面仍独立检查。置信度：技术规格及耗时高；角色微细节和复杂舞蹈精确性中。
'''
(O/'使用说明.md').write_text(note,encoding='utf-8')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>飞升 · 补充与舞蹈素材</title><style>body{margin:0;background:#0b0f14;color:#e4e8eb;font:16px/1.65 system-ui,"Microsoft YaHei",sans-serif}main{max-width:1280px;margin:auto;padding:44px 24px}h1{font-size:38px;letter-spacing:2px;margin:0}p{color:#aab6c3}nav{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}button,a{color:#c5dfed}button{background:#172431;border:1px solid #344956;padding:10px 18px;border-radius:20px;cursor:pointer}section{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}article{overflow:hidden;border:1px solid #29313b;border-radius:12px;background:#10171e}article>div{padding:8px 20px 20px}video{width:100%;aspect-ratio:16/9;background:black}h2{font-size:21px}small{color:#91a0af}a{text-underline-offset:4px}@media(max-width:800px){section{grid-template-columns:1fr}h1{font-size:28px}}</style><main><small>FEISHENG / ADDITIONAL FOOTAGE</small><h1>飞升 · 补充与舞蹈素材</h1><p>4 段剧情插镜 · 6 段黑棚舞蹈 · 每段 5.17 秒 / 24 fps<br>640×384 原生生成，裁切放大至 720p；Turbo 8 步快速档。静音独立素材，可自由拼接。</p><p><a href="使用说明.md">使用说明</a>　<a href="剪辑提示.csv">剪辑提示</a>　<a href="飞升音乐拍点.csv">原曲拍点</a>　<a href="镜头总览.jpg">镜头总览</a></p><nav><button onclick="filter('all')">全部 10 段</button><button onclick="filter('dance')">舞蹈 6 段</button><button onclick="filter('insert')">关联插镜 4 段</button></nav><section>'''+''.join(cards)+'''</section></main><script>function filter(g){document.querySelectorAll('article').forEach(e=>e.hidden=g!=='all'&&e.dataset.group!==g)}document.querySelectorAll('video').forEach(v=>v.addEventListener('play',()=>document.querySelectorAll('video').forEach(o=>{if(o!==v)o.pause()})))</script></html>'''
(O/'index.html').write_text(page,encoding='utf-8')
(O/'审查/技术检查.json').write_text(json.dumps({'passed':True,'count':len(results),'total_frames':1240,'total_duration':1240/24,'all_under_300_seconds':max(secs)<300,'results':results},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'clips':len(results),'min_seconds':min(secs),'max_seconds':max(secs),'sum_seconds':sum(secs)},ensure_ascii=False))
