from pathlib import Path
import subprocess,sys,time,json,html,traceback
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'work/feisheng/v7';OUT=ROOT/'outputs/Feisheng-MV/成片-v7'
def status(stage,error=''):
    manifests=[]
    for p in sorted((OUT/'records').glob('*-manifest.json')):
        manifests.append(json.loads(p.read_text(encoding='utf-8')))
    active={}
    if (WORK/'active.json').exists():active=json.loads((WORK/'active.json').read_text())
    payload=dict(stage=stage,updated=datetime.now(timezone(timedelta(hours=8))).isoformat(),completed=len(manifests),total=12,active=active,error=error)
    (OUT/'status.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    clips=''.join(f'<section><h2>镜头 {m["shot"]}</h2><p>生成 {m["generation_seconds"]/60:.1f} 分钟 · 720p / 25 步</p><video src="clips/{m["shot"]}-720p.mp4" controls preload="metadata"></video></section>' for m in manifests)
    final=OUT/'飞升-MV-720p-v7-待视听复核.mp4'
    finalblock='<h2>整片候选</h2><video controls src="'+final.name+'"></video><p>完整视听复核未完成，不把技术检查等同于艺术质量验收。</p>' if final.exists() and (OUT/'technical-validation.json').exists() else ''
    page='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="60"><title>飞升 V7 制作进度</title><style>body{background:#191a19;color:#e9e3d8;font:16px/1.7 system-ui;max-width:1100px;margin:35px auto;padding:0 22px}p{color:#bab6ad}video{width:100%;max-height:620px}section{margin:35px 0}a{color:#dabb8d}strong{color:#e2c495}</style><h1>飞升 · 720p 制作</h1><p>生成画布 1280×736 → 裁切 1280×720 · 24 fps · 25 步 · 单段 124 帧</p><h2>'+html.escape(stage)+'</h2><p><strong>'+str(len(manifests))+' / 12</strong> 段完成。页面每分钟刷新；播放中可打开视频单独观看。</p><p>'+html.escape(error)+'</p><p>更新：'+payload['updated']+'</p>'+finalblock+clips+'<p><a href="../独立分镜-v6/index.html">定稿分镜</a> · <a href="status.json">机器可读状态</a></p></html>'
    (OUT/'制作进度.html').write_text(page,encoding='utf-8')
try:
    while not (OUT/'records/02-manifest.json').exists():
        if (WORK/'resource-stop.json').exists():raise RuntimeError('Resource guard stopped the first generation. See resource-stop.json.')
        h=OUT/'records/02-history.json'
        if h.exists() and json.loads(h.read_text(encoding='utf-8'))['status']['status_str']=='error':raise RuntimeError('First shot failed; batch was not started.')
        status('正在生成第 02 镜；完成后自动继续其余镜头')
        time.sleep(20)
    with (WORK/'batch.log').open('a',encoding='utf-8') as log:
        child=subprocess.Popen([sys.executable,str(WORK/'render_shots.py')],stdout=log,stderr=subprocess.STDOUT)
        while child.poll() is None:
            status('正在串行生成其余镜头');time.sleep(20)
        if child.returncode:raise RuntimeError('Generation stopped; inspect work/feisheng/v7/batch.log. Completed clips are retained.')
    with (WORK/'edit.log').open('w',encoding='utf-8') as log:
        child=subprocess.Popen([sys.executable,str(WORK/'build_edit.py')],stdout=log,stderr=subprocess.STDOUT)
        while child.poll() is None:
            status('镜头生成完成；正在剪辑、调色和渲染整片候选');time.sleep(20)
        if child.returncode:raise RuntimeError('Edit/render stopped; inspect work/feisheng/v7/edit.log.')
    status('整片候选已导出，通过技术检查，待完整视听复核')
except Exception:
    error=traceback.format_exc();(WORK/'pipeline-error.log').write_text(error,encoding='utf-8');status('制作已停止，保留已完成素材',error);raise
