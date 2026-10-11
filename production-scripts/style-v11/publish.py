import argparse
import csv
import html
import json
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/Feisheng-MV/风格实验-v11"
PLAN = json.loads((OUT / "experiment-plan.json").read_text(encoding="utf-8"))
NAMES = {s["id"]: s["name"] for s in PLAN["shots"]}
LOOKS = {s["id"]: s for s in PLAN["styles"]}
DESCRIPTIONS = {"A": "米白纸感、陶土与留白，适合温柔而克制的段落。", "B": "地层、等高线与矿物浮雕，适合超现实空间和高潮意象。", "C": "赭石、深蓝阴影与胶片质感，适合人物和剧情主体。", "D": "普鲁士蓝与奶白摄影负片，适合记忆、幻象和抽象插镜。"}
CSS = '''body{margin:0;background:#0b1016;color:#e1e8ee;font:16px/1.65 system-ui,"Microsoft YaHei",sans-serif}main{max-width:1600px;margin:auto;padding:32px 24px}h1{font-size:34px;line-height:1.25}h2{font-size:23px}h3{font-size:18px;margin:0}p,small{color:#a7b7c5}a{color:#b9dfed;text-underline-offset:4px}a:focus-visible{outline:3px solid #b9dfed;outline-offset:5px}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin:20px 0 40px}.card{display:block;background:#141e28;color:inherit;text-decoration:none;border-radius:10px;overflow:hidden}.card img{display:block;width:100%;aspect-ratio:16/9;object-fit:cover}.caption{padding:14px}.caption p{font-size:14px;margin:4px 0}.source{display:flex;gap:20px;align-items:center;margin-top:40px}.source img{width:180px;aspect-ratio:16/9;object-fit:cover;border-radius:6px}.media{display:block;width:100%;max-height:78vh;object-fit:contain;background:#0b1016}.links{display:flex;flex-wrap:wrap;gap:16px;margin:18px 0}.split{display:grid;grid-template-columns:1fr 1fr;gap:18px}.split img{width:100%}.detail{max-width:1250px}details{margin:24px 0;padding:16px;background:#141e28;border-radius:8px}summary{cursor:pointer}table{border-collapse:collapse;width:100%}th,td{padding:10px;text-align:left;border-bottom:1px solid #2c3945}.ready{color:#b2dbc8}.pending{color:#dbc998}nav{margin-bottom:24px}@media(max-width:1100px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:650px){main{padding:24px 16px}.grid,.split{grid-template-columns:1fr}.source img{width:110px}h1{font-size:28px}}'''

def page(title, body, detail=False):
    return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>'+CSS+'</style></head><body><main'+(' class="detail"' if detail else '')+'>'+body+'</main></body></html>'

def publish():
    records = {x.stem[:-6]: json.loads(x.read_text(encoding="utf-8")) for x in (OUT / "records").glob("*-video.json")}
    styles_done = sum(not x.endswith("-control") for x in records)
    (OUT / "view").mkdir(exist_ok=True)
    body = '<h1>飞升 · 四种材质与运动</h1><p>同一主角，同一分镜，四种艺术表达。点击画面查看大图和短片。</p>'
    body += f'<p>首帧 {len(list((OUT / "frames").glob("*.png")))}/12 · 风格短片 {styles_done}/12 · LoRA 对照 {sum(x.endswith("-control") for x in records)}/2</p>'
    body += '<div class="links"><a href="使用说明.md">参数与风格说明</a><a href="素材索引.csv">剪辑素材索引</a><a href="review/四风格总览.jpg">全分镜对照大图</a><a href="../ComfyUI留存-v11/index.html">模型与全部工作流留存</a></div>'
    archive = OUT.parent / "飞升-四风格分镜与短片-v11.zip"
    if archive.exists(): body += '<p><a href="../飞升-四风格分镜与短片-v11.zip" download>下载完整素材包</a></p>'
    for shot in PLAN["shots"]:
        sid = shot["id"]
        body += f'<div class="source"><a href="originals/{sid}.png"><img src="originals/{sid}.png" alt="{html.escape(shot["name"])}的原始分镜"></a><div><h2>{sid} · {html.escape(shot["name"])}</h2><p>{html.escape(shot["category"])} · 原图与主角身份保持关联</p></div></div><div class="grid">'
        for style in PLAN["styles"]:
            look = style["id"]; eid = sid+'-'+look
            if not (OUT / "frames" / (eid+'.png')).exists(): continue
            data = records.get(eid)
            state = '短片已生成 · 3.04 秒' if data else '首帧已生成 · 短片制作中'
            body += f'<a class="card" href="view/{eid}.html"><img src="frames/{eid}.png" alt="{html.escape(shot["name"])}，{html.escape(style["name"])}风格"><div class="caption"><h3>{look} · {html.escape(style["name"])}</h3><p>{DESCRIPTIONS[look]}</p><small class="{ "ready" if data else "pending" }">{state}</small></div></a>'
            detail = f'<nav><a href="../index.html">返回四风格对照</a></nav><h1>{look} · {style["name"]} / {sid} {shot["name"]}</h1><p>{DESCRIPTIONS[look]}</p>'
            if data:
                detail += f'<video class="media" controls playsinline muted loop preload="metadata" poster="../frames/{eid}.png" src="../clips/{eid}.mp4"></video><p>无声风格试片 · 3.04 秒 · 24fps · 720p 精细缩放预览</p>'
            else:
                detail += f'<img class="media" src="../frames/{eid}.png" alt="风格分镜"><p>短片正在制作，重新打开本页可查看更新。</p>'
            detail += f'<div class="links"><a href="../frames/{eid}.png" download>下载首帧 PNG</a>'
            if data: detail += f'<a href="../clips/{eid}.mp4" download>下载短片 MP4</a><a href="../workflows/{eid}.json" download>下载 ComfyUI 节点工作流</a><a href="../workflows/{eid}-API.json" download>下载 API 工作流</a><a href="../review/{eid}-contact.jpg">逐时刻画面</a>'
            detail += f'</div><details><summary>原分镜与风格首帧</summary><div class="split"><figure><img src="../originals/{sid}.png" alt="原分镜"><figcaption>已采纳的原分镜</figcaption></figure><figure><img src="../frames/{eid}.png" alt="风格首帧"><figcaption>{style["name"]}</figcaption></figure></div></details>'
            if eid == '19-D':
                detail += '<p>本段约 0.4 秒后，深蓝摄影棚转为奶白留白。作为蓝晒材质转化试验保留，适合幻象或过渡；与深色摄影棚连续拼接时，请比较关闭 LoRA 的版本。</p>'
            detail += f'<details><summary>参数与生成来源</summary><p>首帧：内置 imagegen 参考重绘。视频：本机 MiniMax H3 FL2VA 剪枝 INT8 ConvRot，Turbo 8 步，640×384 原生生成后裁切并精细缩放至 1280×720。24fps，73 帧，未补帧。</p><p>风格适配器：{style["adapter"]}，强度 {style["strength"]}。'
            if data: detail += f'本段执行耗时 {data["generation_seconds"]:.1f} 秒，种子 {data["seed"]}。'
            detail += f'</p><a href="../prompts/{eid}-image.txt">图片提示词</a>'
            if data: detail += f' · <a href="../prompts/{eid}-video.txt">视频提示词</a> · <a href="../records/{eid}-video.json">本段记录</a>'
            detail += '</details>'
            (OUT / "view" / (eid+'.html')).write_text(page(style["name"]+' · '+shot["name"], detail, True), encoding="utf-8")
        body += '</div>'
    body += '<h2>LoRA 到底改变了什么</h2><p>两个对照保持首帧、提示词、种子和 Turbo 8 步一致，仅开关风格 LoRA。参考重绘负责四种具体材料设计；适配器参与运动生成，效果以对照为准。</p><div class="grid">'
    for eid, title in [("16-C","人物电影质感 / Realism People"),("19-D","线条与群像 / Looping Sketch")]:
        if eid+'-control' not in records: continue
        body += f'<a class="card" href="view/{eid}-compare.html"><img src="frames/{eid}.png" alt="{title}的 LoRA 开关对照"><div class="caption"><h3>{title}</h3><p>同种子开／关对照</p></div></a>'
        detail = f'<nav><a href="../index.html">返回四风格对照</a></nav><h1>{title}</h1><p>两边使用完全相同的首帧、提示词、随机种子与采样参数。左：关闭风格 LoRA；右：开启风格 LoRA。</p>'
        if (OUT / "comparison" / (eid+'-side-by-side.mp4')).exists(): detail += f'<video class="media" controls playsinline muted loop preload="metadata" src="../comparison/{eid}-side-by-side.mp4"></video>'
        else: detail += f'<div class="split"><video class="media" controls playsinline muted src="../clips/{eid}-control.mp4"></video><video class="media" controls playsinline muted src="../clips/{eid}.mp4"></video></div>'
        detail += f'<div class="links"><a href="../clips/{eid}-control.mp4" download>下载关闭版</a><a href="../clips/{eid}.mp4" download>下载开启版</a></div><p>LoRA 不保证每个镜头都更好。观察皮肤、线条、动态轮廓、舞步和时间稳定性，再决定保留或降低强度。</p>'
        if eid == '19-D':
            detail += '<p>这个种子的实测差异：开启 0.95 强度 Sketch 后，深蓝背景迅速转成奶白留白；关闭版保持深蓝摄影棚。两版都保留，便于选择连续性或材质转换。</p>'
        else:
            detail += '<p>这个种子的实测差异主要在表情、头部运动和阴影层次；没有发生新的艺术媒介转换。四种材质设计主要来自参考首帧重绘。</p>'
        (OUT / "view" / (eid+'-compare.html')).write_text(page(title, detail, True), encoding="utf-8")
    body += '</div>'
    audit = OUT / "review/final-audit.json"
    if audit.exists() and json.loads(audit.read_text())["passed"]: body += '<p class="ready">全部素材已完成技术检查与视觉复核。</p>'
    (OUT / "index.html").write_text(page('飞升 · 四风格分镜与短片', body), encoding="utf-8")
    rows = []
    for eid, data in sorted(records.items()):
        sid,look,*_=eid.split('-')
        rows.append({"编号":eid,"分镜":NAMES[sid],"风格":LOOKS[look]["name"],"类型":"LoRA关闭对照" if eid.endswith('-control') else "风格试片","时长秒":round(data["duration_seconds"],3),"帧率":data["fps"],"原生分辨率":"640x384","交付分辨率":"1280x720 精细缩放","步数":data["steps"],"生成秒":data["generation_seconds"],"LoRA强度":data["style_strength"],"文件":data["file"]})
    if rows:
        with (OUT / "素材索引.csv").open('w', encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    sheet = OUT / "review/四风格总览.jpg"
    if not sheet.exists() and len(list((OUT / "frames").glob('*.png'))) == 12:
        canvas = Image.new('RGB',(2048,3*334),(11,16,22)); draw=ImageDraw.Draw(canvas)
        font=ImageFont.truetype('<LOCAL_PATH>/msyh.ttc',21)
        for row,shot in enumerate(PLAN['shots']):
            for col,look in enumerate('ABCD'):
                eid=shot['id']+'-'+look
                with Image.open(OUT/'frames'/(eid+'.png')) as img: canvas.paste(img.convert('RGB').resize((512,288),Image.Resampling.LANCZOS),(col*512,row*334))
                draw.text((col*512+12,row*334+293),f"{eid}  {LOOKS[look]['name']} / {shot['name']}",font=font,fill=(225,232,238))
        canvas.save(sheet,quality=94)
    return len(records)

parser=argparse.ArgumentParser();parser.add_argument('--watch',action='store_true');args=parser.parse_args()
previous=None
while True:
    current=tuple((p.name,p.stat().st_mtime_ns) for p in sorted((OUT/'records').glob('*-video.json')))
    if current!=previous:
        count=publish(); print('PUBLISHED',count,flush=True);previous=current
    if not args.watch or count==14:break
    time.sleep(5)
