from pathlib import Path,PureWindowsPath
import json,html,time,csv,zipfile,hashlib
R=Path(__file__).resolve().parents[3];O=R/'outputs/Feisheng-MV/高清素材-v10';S=R/'outputs/Feisheng-MV/补充与舞蹈-v9'
items=json.loads((S/'素材清单.json').read_text(encoding='utf-8'));status=json.loads((O/'status.json').read_text(encoding='utf-8'))
review_path=O/'审查/视觉验收.json'
reviews=json.loads(review_path.read_text(encoding='utf-8')) if review_path.exists() else {}
cards=[];records=[]
for x in items:
    sid=x['shot'];p=O/'records'/f'{sid}-manifest.json';m=json.loads(p.read_text(encoding='utf-8')) if p.exists() else None
    if m and m.get('verified'):
        master_url=html.escape(PureWindowsPath(m['master_file']).as_posix(),quote=True)
        smooth_url=html.escape(PureWindowsPath(m['smooth_file']).as_posix(),quote=True)
        review_files=[('新旧对照',f'{sid}-v9-v10-对照.jpg'),('24fps 抽帧',f'{sid}-24fps-contact.jpg'),('48fps 抽帧',f'{sid}-48fps-contact.jpg'),('强运动插帧',f'{sid}-强运动插帧三联.jpg'),('面部连续性',f'{sid}-面部连续性.jpg')]
        review_links='　'.join(f'<a href="审查/{html.escape(filename,quote=True)}" target="_blank">{label}</a>' for label,filename in review_files if (O/'审查'/filename).exists())
        records.append(m);review_status='已通过' if reviews.get(sid,{}).get('accepted') is True else '待检查';content=f'<video controls preload="none" poster="frames/{sid}.png" src="{smooth_url}"></video><p><a href="{master_url}" download>24fps 母版</a>　<a href="{smooth_url}" download>48fps 剪辑版</a></p><p>{review_links}</p><small>生成 {m["generation_seconds"]/60:.1f} 分钟 · 插帧 {m["interpolation_seconds"]/60:.1f} 分钟 · 视觉检查 {review_status}</small>'
    else:content=f'<img src="frames/{sid}.png" alt="{x["name"]}首帧"><p>{"正在生成" if status.get("active_shot")==sid else "等待逐个生成"}</p>'
    cards.append(f'<article><h2>{sid} · {x["name"]}</h2>{content}</article>')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>飞升 · 高清升级进度</title><style>body{background:#0b1016;color:#e1e8ee;margin:0;font:16px/1.65 system-ui,"Microsoft YaHei",sans-serif}main{max-width:1260px;margin:auto;padding:32px 24px}h1{font-size:34px}p,small{color:#a7b7c5}a{color:#b9dfed}section{display:grid;grid-template-columns:1fr 1fr;gap:20px}article{background:#141e28;padding:18px;border-radius:12px}img,video{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:6px}h2{font-size:20px}@media(max-width:760px){section{grid-template-columns:1fr}}</style><main><h1>飞升 · 高清素材升级</h1><p>原生 1280×736 → 裁切 1280×720 · 原模型 25 步<br>24fps 母版 + 48fps 运动补偿插帧版 · 每段 5.17 秒</p>'''+f'<p>技术检查已完成 {len(records)}/10 段；当前阶段：{html.escape(status["phase"])}。<br>这是生成进度页面，全部完成并检查后才是最终交付。页面内容按发布时状态显示。</p><p><a href="使用说明.md">参数和使用说明</a>　<a href="档位与耗时实测.md">快速/高清档位实测</a>　<a href="审查/跨镜连续性-剧情.jpg">剧情跨镜总览</a>　<a href="审查/跨镜连续性-舞蹈.jpg">舞蹈跨镜总览</a>　<a href="审查/逐镜验收基准.md">逐镜验收基准</a>　<a href="审查/运行资源汇总.json">运行资源汇总</a>　<a href="status.json">最新任务状态</a></p><section>'+''.join(cards)+'</section></main></html>'
final_file=O/'审查/最终验收.json'
final_report=json.loads(final_file.read_text(encoding='utf-8')) if final_file.exists() else {}
final_pass=final_report.get('passed') is True and final_report.get('checked')==len(items)
if final_pass:
    page=page.replace('这是生成进度页面，全部完成并检查后才是最终交付。', '全部镜头已通过技术与逐镜视觉验收。')
    page=page.replace('</section></main></html>', '</section><p><a href="../飞升-高清10镜头-720p-25步-48fps.zip">下载完整素材包</a>　<a href="剪辑素材索引.csv">剪辑素材索引</a>　<a href="审查/最终验收.json">最终验收记录</a></p></main></html>')
(O/'index.html').write_text(page,encoding='utf-8')
(O/'升级素材清单.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
note='''# 《飞升》高清素材 v10

范围为 v9 的全部 10 段：13–16 剧情关联插镜、17–22 舞蹈。使用原首帧与对应种子重新生成，原始快速版保留。

## 提升规格

| 项目 | v9 快速档 | v10 高清档 |
|---|---|---|
| 生成分辨率 | 640×384 | 1280×736 |
| 有效画面 | 640×360 放大输出 | 1280×720 原生裁切 |
| 步数 | Turbo LoRA 8 | 原模型 25，无 Turbo |
| 原生帧率 | 24fps | 24fps |
| 可选剪辑帧率 | 24fps | 48fps 运动补偿插帧 |
| 每段时长 | 124帧 / 24fps = 5.1667s | 124帧 / 24fps = 5.1667s；48fps版248帧 |

原模型 25 步的算力成本明显高于 Turbo 8 步，步数不是可以直接跨模型比较的线性画质分数。高清档按此前同规格成功任务估计，单段约 30–35 分钟，10 段约 5–6 小时生成，插帧和检查另计；实际记录保存在 records。

48fps 为 FFmpeg 双向运动估计补偿插帧，不是模型原生生成 48fps。保留 24fps 母版以供你根据舞蹈快速转身、手臂交叉等部位的实际表现选择版本。原生重新生成的视频运动可能与快速版不同。

## 交付与复现

“24fps母版”是优先用于严肃剪辑的原生画面；“48fps剪辑版”提供更平滑运动；“原生视频”保留未裁切文件；“frames”保留同角色首帧；“workflows”保留完整 ComfyUI API 图。把首帧放入 input/FeishengHDV10/ 后使用对应 JSON。

生成器位于 work/feisheng/hd-v10/batch.py，按10段串行执行，逐段保存提交ID和历史。恢复前核对真实进程及 ComfyUI 队列，已提交且仍可查询的任务不会重新提交。每段技术验证完成后记录 SHA256、完整解码、尺寸、帧率、帧数和时间戳，视觉检查另行记录。

进度页面和 status.json 不代表整批已完成；以所有10段实际文件、技术验证与逐镜视觉审查为验收条件。素材保持静音，适合原曲自行剪辑。
'''
if final_pass:
    note+='\n## 最终交付\n\n十段已全部通过技术与逐镜视觉验收。完整文件见上级目录的“飞升-高清10镜头-720p-25步-48fps.zip”；本目录的“剪辑素材索引.csv”可供导入剪辑清单。验收细项见“审查/最终验收.json”。\n'
(O/'使用说明.md').write_text(note,encoding='utf-8')
print(json.dumps({'completed':len(records),'phase':status['phase'],'active':status.get('active_shot')},ensure_ascii=False))
