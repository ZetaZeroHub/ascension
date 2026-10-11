"""Run only after reviewing generated QA evidence and writing visual-review.json."""
from pathlib import Path
import json,shutil,hashlib,statistics,zipfile
from datetime import datetime
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'outputs/Feisheng-MV/成片-v7';WORK=ROOT/'work/feisheng/v7'
PROJECT=WORK/'remotion'
validation=json.loads((OUT/'审查/验证结果.json').read_text(encoding='utf-8'))
review=json.loads((OUT/'审查/visual-review.json').read_text(encoding='utf-8'))
assert validation['technical_pass'] and review['status']=='reviewed'
assert review['open_high_severity_issues']==0
candidate=OUT/validation['file']
assert hashlib.sha256(candidate.read_bytes()).hexdigest()==validation['sha256']
assert review['reviewed_sha256']==validation['sha256']
manifests=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((OUT/'records').glob('*-manifest.json'))]
assert len(manifests)==12
final=OUT/'飞升-MV-720p-定稿.mp4';shutil.copy2(candidate,final)
times=[m['generation_seconds']/60 for m in manifests]
resources=[json.loads(line) for line in (WORK/'resources.jsonl').read_text().splitlines() if line.strip()]
timeline=json.loads((OUT/'timeline.json').read_text())
cut_count=sum((a['source'],a['view'])!=(b['source'],b['view']) or (b['source']=='08' and b['fromFrame']==1296) for a,b in zip(timeline,timeline[1:]))
def reference_mode(m):
    workflow=json.loads((OUT/'workflows'/f"{m['shot']}-API.json").read_text(encoding='utf-8'))
    inputs=workflow['6']['inputs']
    if 'ref_videos.ref_video_0' in inputs:return '人物、场景与视频参考＋首帧'
    if 'ref_images.ref_image_0' in inputs:return '人物、场景双参考＋首帧'
    if 'last_frame' in inputs and 'first_frame' not in inputs:return '文案＋尾帧约束'
    return '文案＋首帧图像'
table='\n'.join(f"| {m['shot']} | {reference_mode(m)} | {m['generation_seconds']/60:.2f} 分钟 |" for m in manifests)
report=f'''# 《飞升》720p 定稿

最终文件：{final.name}。1280×720、24 fps、2282 帧、95.083 秒；完整原音乐，48 kHz 双声道 AAC。

## 剧情与剪辑

红衣信使进入停滞之城，取走核心种子，奔跑抵达断桥，选择跃入深井，将种子放回核心；重力倒转、天幕打开，城市恢复生机，她带着空手返回。

12 段本机 H3 素材组成全片。{len(timeline)} 个编辑段包含 {cut_count} 处素材或构图变化；细节画面来自原素材裁切，不冒充额外生成机位。后半段逐渐收紧到 1.2 秒的交叉剪辑，74.4 秒打开天幕，76.8 秒起恢复长镜头呼吸。

后期包括光流变速、核心触地的透视冲击波与遮挡、67.2 秒上升碎屑、74.4 秒柔化天光与扩散粒子、轻微冲击回弹、B 暖灰调色收尾、片名和尾部淡出。所有合成特效由帧号驱动，可在工程内修改。没有添加旁白或覆盖原曲的音效。

08 号原始生成片段中间插入了不合叙事的桥面奔跑画面，后期已删除原生第 26–95 帧，仅保留第 0–25 帧与第 96–123 帧的离桥和下降动作，分别光流变速，在 54 秒衔接。原始素材保留作记录；成片与工程中的 graded/08.mp4 使用修正后的选片。参考视频条件不能保证模型严格延续单一动作，这次通过实际选片和剪辑修复。

## 画质与实际耗时

每段生成 1280×736、124 帧、24 fps、25 步，上下各裁 8 像素得到 720p，没有从低分辨率放大。使用 INT8 H3 与 NVFP4 文本编码器、动态显存卸载、逐段串行。

本次单段实测 {min(times):.2f}–{max(times):.2f} 分钟，中位数 {statistics.median(times):.2f} 分钟；后端生成累计 {sum(times):.2f} 分钟。后期与部分生成并行，不把累计耗时当成墙钟耗时。

本轮资源记录：最低可用 RAM {min(r['ram_free_mib'] for r in resources)} MiB，最低可用提交额度 {min(r['commit_free_mib'] for r in resources)} MiB，最高 GPU 温度 {max(r['temp'] for r in resources)}°C，整机 GPU 显存峰值 {max(r['gpu_mib'] for r in resources)} MiB。数据含同时运行的桌面和后期进程。

| 镜头 | 参考方式 | 本次生成耗时 |
|---|---|---|
{table}

| 可选档位 | 原生画布 / 步数 | 5.17 秒素材耗时 | 评价与证据 |
|---|---|---|---|
| 草稿 | 512×288 / Turbo 8 | 历史记录约 2 分 36 秒 | 用于构图试错；本次未复测 |
| 快速创作 | 704×384 / 原模型 20 | 历史三段实测 6.19–7.46 分钟 | 速度更快、细节更少；不同素材，不能严格归因于单项参数 |
| 本次定稿 | 1280×736 裁切 720p / 原模型 25 | 本次中位 {statistics.median(times):.2f} 分钟 | 人物、衣料和建筑细节较完整；复杂动作与跨镜道具比例仍受模型限制 |
| 压力档 | 1344×768 / 原模型 32 | 历史超过 50 分钟仍未完成后中止 | 无完整成功样本，不作常用档位推荐 |

## 音乐与验收

原曲未上传外部服务，未使用 ElevenLabs。音乐速度不变，母带整体降低 6 dB；成片实测 {validation['integrated_lufs']:.1f} LUFS、真峰值 {validation['true_peak_dbfs']:.1f} dBTP。与母带波形相关系数 {validation['audio_correlation']:.6f}，检测偏移 {validation['audio_offset_ms']:.3f} 毫秒。

全部 2282 帧解码、时间戳连续、时间轴无缺口、内部无意外黑帧。视觉审查采用全片每半秒抽帧与切点邻帧，具体发现与处理见“审查/visual-review.json”；音频采用波形和响度检测。本环境没有进行耳机或扬声器的主观全曲试听，不能把自动检测称作听感验收。

置信度：分辨率、耗时、帧数、音频同步为高；叙事连贯性、视觉审查与艺术效果为中。自动节拍检测不等于人工乐谱转录。

## 可编辑工程

“飞升-720p-可编辑工程.zip”包含 Remotion 源码、重定时素材、音频、参考图和 ComfyUI API 工作流，不含模型权重与 node_modules。解压后按工程 README 安装依赖和重新渲染。原始生成视频继续保存在本目录 clips/。
'''
(OUT/'交付说明.md').write_text(report,encoding='utf-8')
readme='''# 飞升 Remotion 编辑工程

打开 remotion 目录，安装与 package.json / pnpm-lock.yaml 对应的依赖。运行：

    pnpm install --frozen-lockfile
    pnpm exec remotion studio src/index.ts
    pnpm exec remotion render src/index.ts FeishengV7 feisheng-720p.mp4 --concurrency=1 --gl=swangle --crf=16 --audio-codec=aac --audio-bitrate=320k

src/Root.tsx 控制构图、合成特效、片名与尾部淡出；src/timeline.json 保存逐帧剪辑。public/graded 是已经变速和调色的素材，修改时长需同步重定时。

workflows 是 ComfyUI API 格式；输入图和参考视频放到 ComfyUI input/FeishengV7。生成依赖 H3 与对应量化模型、本地节点版本；未打包模型权重。此包可直接用于重剪已有素材，生成配置按工作流内模型名称准备。
'''
with zipfile.ZipFile(OUT/'飞升-720p-可编辑工程.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
    z.writestr('README.md',readme)
    for rel in ['package.json','pnpm-lock.yaml','pnpm-workspace.yaml','tsconfig.json','remotion.config.ts']:
        p=PROJECT/rel
        if p.exists():z.write(p,'remotion/'+rel)
    for folder in ['src','public']:
        for p in (PROJECT/folder).rglob('*'):
            if p.is_file():z.write(p,'remotion/'+p.relative_to(PROJECT).as_posix())
    for p in (OUT/'workflows').glob('*.json'):z.write(p,'workflows/'+p.name)
    z.write(OUT/'选片记录.json','选片记录.json')
    for p in Path('<LOCAL_PATH>/FeishengV7').iterdir():
        if p.is_file():z.write(p,'input/FeishengV7/'+p.name)
(OUT/'定稿索引.json').write_text(json.dumps(dict(file=final.name,sha256=validation['sha256'],technical_validation='审查/验证结果.json',visual_review='审查/visual-review.json',review_method=review.get('method')),ensure_ascii=False,indent=2),encoding='utf-8')
validation['visual_review']='reviewed; see visual-review.json for scope and limitations'
validation['delivery_file']=final.name
(OUT/'审查/验证结果.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
page=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>飞升 · 720p 定稿</title><style>body{{margin:0;background:#171918;color:#e8e2d7;font:16px/1.7 system-ui}}main{{max-width:1160px;margin:48px auto;padding:0 24px}}h1{{font-size:40px;font-weight:400;letter-spacing:.3em}}p{{color:#b9b6ab}}video{{width:100%;display:block;background:#090a09}}nav{{display:flex;gap:12px;flex-wrap:wrap;margin-top:24px}}a{{color:#e3c795;border:1px solid #4f4c43;border-radius:4px;padding:9px 15px;text-decoration:none}}small{{color:#a4a298}}</style><main><small>音乐短片 · 暖灰 B · 角色叙事版</small><h1>飞升</h1><p>1280 × 720 · 24 fps · 95 秒 · 原曲完整保留</p><video controls preload="metadata" src="{final.name}"></video><nav><a href="{final.name}" download>保存成片</a><a href="飞升-720p-可编辑工程.zip">可编辑工程</a><a href="交付说明.md">制作与效率说明</a><a href="审查/验证结果.json">技术验证</a></nav><p>取走种子，跃入深井，唤醒停滞之城。</p><small>审查方式：连续抽帧与切点邻帧、全片解码、音乐波形同步及响度检测。未进行主观耳机试听。</small></main></html>'''
(OUT/'index.html').write_text(page,encoding='utf-8')
(OUT/'制作进度.html').write_text(page,encoding='utf-8')
(OUT/'status.json').write_text(json.dumps(dict(stage='定稿已导出；技术验证与视觉抽帧审查完成',completed=12,total=12,active={},updated=datetime.now().astimezone().isoformat(),file=final.name,error=''),ensure_ascii=False,indent=2),encoding='utf-8')
print('PACKAGED',final)
