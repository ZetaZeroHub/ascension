import csv, hashlib, json, shutil, statistics, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT/'remotion'
OUT=ROOT.parents[1]/'outputs/Feisheng-MV'
story=json.loads((ROOT/'src/data/storyboard.json').read_text(encoding='utf-8'))
manifests=[json.loads((ROOT/'generation'/f"{s['id']}-manifest.json").read_text()) for s in story['scenes']]
validation=json.loads((OUT/'成片验证.json').read_text(encoding='utf-8'))
render_stats=json.loads((OUT/'成片渲染实测.json').read_text(encoding='utf-8'))
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assets=[]
for p in sorted((PROJECT/'public').rglob('*')):
    if p.is_file():assets.append({'path':p.relative_to(PROJECT).as_posix(),'sha256':h(p),'bytes':p.stat().st_size})
(PROJECT/'src/data/asset-manifest.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2),encoding='utf-8')
timings=[]
for s,m in zip(story['scenes'],manifests):
    timings.append({'镜头':s['id'],'名称':s['title'],'原生分辨率':'704×384','原生秒数':124/24,'成片秒数':(s['to']-s['from'])/24,'步数':20,'生成耗时秒':m['generation_seconds'],'种子':s['seed']})
with (OUT/'逐镜头实测.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(timings[0]));w.writeheader();w.writerows(timings)
seconds=[m['generation_seconds'] for m in manifests]
resource_log=ROOT.parent/'resources.csv'
resource_rows=list(csv.DictReader(resource_log.open(encoding='utf-8-sig')))
resource_stats={'samples':len(resource_rows),'minimum_free_ram_mib':min(float(r['free_ram_mib']) for r in resource_rows),'minimum_free_commit_mib':min(float(r['free_commit_mib']) for r in resource_rows),'maximum_gpu_temperature_c':max(float(r['gpu_temp_c']) for r in resource_rows),'maximum_total_gpu_used_mib':max(float(r['gpu_used_mib']) for r in resource_rows)}
shutil.copy2(resource_log,OUT/'制作资源记录.csv')
(OUT/'资源统计.json').write_text(json.dumps(resource_stats,indent=2),encoding='utf-8')
shutil.copy2(ROOT/'analysis/clip-qc/native-validation.json',OUT/'原生视频验证.json')
shutil.copy2(ROOT/'analysis/edit-validation.json',OUT/'后处理验证.json')
for name in ['script','timeline','audio-manifest','asset-manifest','style-preset','captions']:
    shutil.copy2(PROJECT/'src/data'/f'{name}.json',OUT/f'{name}.json')
prov=json.loads((ROOT/'generation/image-provenance.json').read_text())
prov['note']='Original generated paths retained for provenance. Authored scene prompts are in storyboard.json; model requests also included continuity instructions.'
(OUT/'图像来源.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2),encoding='utf-8')
gen=OUT/'生成记录';gen.mkdir(exist_ok=True)
for p in (ROOT/'generation').glob('*manifest.json'):shutil.copy2(p,gen/p.name)
portable_generation=PROJECT/'generation';portable_generation.mkdir(exist_ok=True)
for p in (ROOT/'generation').glob('*manifest.json'):shutil.copy2(p,portable_generation/p.name)
portable_analysis=PROJECT/'analysis';portable_analysis.mkdir(exist_ok=True)
for name in ['music-mono.wav','music-analysis.json','music-analysis.png','features.npz']:
    shutil.copy2(ROOT/'analysis'/name,portable_analysis/name)
report=f'''# 飞升 · 完整 MV 交付说明

成片：1920×1080、24 fps、2282 帧、{2282/24:.3f} 秒；H.264 视频、48 kHz 双声道 AAC。使用完整原曲，未改变速度。

## 制作与叙事

14 段 MiniMax H3 视频，28 张独立生成的首尾帧原型。红绸贯穿重力之室、自缚、越界、试炼、归零、破茧、飞升与携光归返。开场与结尾复用同一建筑空间，通过光线和红绸姿态改变完成故事闭环。

每段用文字＋首帧＋尾帧驱动本机 H3。ComfyUI 工作流在“工作流”目录；`*-API.json` 用于接口，普通编号 JSON 用于界面导入。图像需放入 ComfyUI input/Feisheng/。最终由 Remotion 按音乐帧级剪辑、合成片名与原曲。

## 本地音乐分析与卡点

解码后的原曲约 95.081 秒；容器约 95.125 秒，差异主要来自 AAC 起始偏移/编码信息。统一使用解码音频的时间原点。平均脉冲估计约 100.23 BPM；增强主要来自音色、低频和事件密度，未验证持续加速。Dm–G/B–Dm–G/D 为用户提供，未独立逐和弦转录。

约 0–19 秒建立空间；19–48 秒推进试炼；48–57.6 秒积蓄；57.6 秒进入低频驱动的破茧；72–77 秒承接飞升；77.4 秒归返；86.7 秒起收束，保留原曲自然尾音。

19 个剪切/重构图点吸附至本地估计节拍，帧取整最大误差 19.161 毫秒。此数值说明“剪辑点与检测网格的一致性”，不等于所有真实强拍均已人工确认。原始估计和剪辑帧号见 `剪辑卡点.csv`。

## 效率与质量选择

| 档位 | 原生尺寸 | 原生时长 | 步数 | 本机时间 | 适用与限制 |
|---|---|---|---|---|---|
| 快速草稿 | 512×288 | 5.17 秒 | Turbo 8 | 此前实测约 2 分 36 秒 | 快速检查构图和动作，细节少；原生生成声音较弱。 |
| 本次 MV | 704×384 | 每段 5.17 秒 | 原模型 20 | 本次 {min(seconds)/60:.2f}–{max(seconds)/60:.2f} 分/段，中位数 {statistics.median(seconds)/60:.2f} 分 | 首尾帧使空间与布料身份可控；慢动作和抽象主体较合适。 |
| 高分辨率压力档 | 1344×768 | 目标 5.17 秒 | 原模型 32 | 此前超过 50 分钟仍未完成，已中止 | 无完整成片质量证据，不作为这台机器当前的常用配置。 |

14 段后端生成时间合计 {sum(seconds)/60:.2f} 分钟，不含前期图片、分析、后期与检查。这是本机测量，不是通用硬件保证。单段成片时长通过光流重定时适配乐句；没有假称原生生成了整段 9 秒视频。

最终 Remotion 整片合成耗时 {render_stats['render_seconds']/60:.2f} 分钟，文件约 {render_stats['bytes']/1024/1024:.1f} MiB。后处理与部分生成并行，因此不能把各步骤耗时简单相加作为完整制作墙钟时间。

本机配置：RTX 4060 Ti 8GB、32GB RAM；ComfyUI v0.37.4 / PyTorch 2.9.1+cu130；模型位于 H: NVMe。视频模型 `minimax_h3_fl2va_pruned_int8_convrot.safetensors`，文本编码器 `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`，视频 VAE `minimax_h3_video_vae_int8_convrot.safetensors`。采样 `res_multistep / simple`，20 步，不叠加 Turbo LoRA。每镜种子见 CSV。

启动参数：`--enable-dynamic-vram --fast-disk --disable-pinned-memory --vram-headroom 2.5 --cache-ram 6 8 --preview-method none`。串行生成，批量为 1；MV 使用原曲，所以工作流省略 H3 声音解码。资源监测会记录整机显存、可用 RAM/commit 与 GPU 温度；整机显存数字包含其他应用。

本轮制作记录：最低可用 RAM {resource_stats['minimum_free_ram_mib']:.0f} MiB，最低可用 commit {resource_stats['minimum_free_commit_mib']:.0f} MiB，最高 GPU 温度 {resource_stats['maximum_gpu_temperature_c']:.0f}°C，整机显存峰值 {resource_stats['maximum_total_gpu_used_mib']:.0f} MiB。

1080p 为后期 Lanczos 放大、中心裁切和轻微亮度锐化。画面尺寸达到 1080p，细节来源仍为 704×384；不宣称原生 1080p，也未使用生成式超分凭空补细节。质量判断：空间和配色统一、主体易辨认；动作偏克制，局部布料细节和低分辨率纹理仍有模型局限。

另做了 3 帧 4x-UltraSharp 对照：60% 超分与 40% 常规缩放混合，暖机后约 1.02 秒/帧；外推 2282 帧约额外 39 分钟，未作为全片实测值。单帧边缘更清楚，但不能据此证明整片无纹理闪烁。对照图与速度记录另附，本版选择适中耗时的常规缩放。

## 声音与验证

原曲为唯一音轨，整体降低 6 dB 后合成；没有额外生成配音、音效或替换音乐。未使用 ElevenLabs，也没有把用户密钥写入工程。
完整编码成片实测综合响度 {validation['integrated_lufs']:.1f} LUFS、真峰值 {validation['true_peak_dbfs']:.1f} dBTP；与本地主母带的波形相关系数 {validation['audio_vs_master_correlation']:.6f}，检测偏移 {validation['audio_offset_ms']:.3f} 毫秒。

每段原生视频的 124 帧均已解码；最终 2282 帧完整解码、时间戳连续。另核验素材哈希、无缺口时间轴、画幅、音轨和工程检查。视觉判断依据实际视频的多时点抽帧；本环境未完成耳机/手机外放的主观全曲试听，不把技术检测冒充听感验收。

置信度：成功生成、参数、耗时、帧数、编码、音频相关性为高；自动节拍、动作连贯性与艺术评价为中；历史关机/蓝屏的硬件根因仍未知。

## 后续修改

解压可编辑工程后按 README 运行。`src/data/storyboard.json` 保存分镜和提示词，`src/data/timeline.json` 保存时间轴，`src/Feisheng.tsx` 控制片名、重构图与尾部淡出。原始 AI 片段、首尾帧、重定时片段和原曲均保留，可以重新剪辑而不用重新生成。

公开技术依据：[ComfyUI H3](https://docs.comfy.org/tutorials/video/minimax/minimax-h3)、[librosa 节拍跟踪](https://librosa.org/doc/0.11.0/generated/librosa.beat.beat_track.html)、[Remotion 时间轴](https://www.remotion.dev/docs/timing)。
'''
(OUT/'制作说明与效率实测.md').write_text(report,encoding='utf-8')
(OUT/'发布文案.txt').write_text('《飞升》\n一条红绸穿过重力、秩序与自己的束缚。它把光带回出发的地方。\n纯音乐 × 抽象英雄之旅。',encoding='utf-8')
shutil.copy2(OUT/'制作说明与效率实测.md',PROJECT/'制作说明.md')
archive=OUT/'飞升-可编辑工程.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
    for p in PROJECT.rglob('*'):
        if not p.is_file() or any(x in {'node_modules','.git','out','dist','build'} for x in p.relative_to(PROJECT).parts):continue
        z.write(p,'Feisheng/'+p.relative_to(PROJECT).as_posix())
    for p in (OUT/'工作流').glob('*.json'):z.write(p,'Feisheng/ComfyUI-workflows/'+p.name)
    for name in ['retime.py','polish.py','analyze_music.py','check_clips.py']:
        script=(ROOT/name).read_text(encoding='utf-8')
        script=script.replace('ROOT=Path(__file__).resolve().parent','ROOT=Path(__file__).resolve().parents[1]').replace('root=Path(__file__).resolve().parent','root=Path(__file__).resolve().parents[1]')
        script=script.replace("ROOT/'remotion/public'","ROOT/'public'")
        z.writestr('Feisheng/production-scripts/'+name,script)
    z.writestr('Feisheng/production-scripts/README.md','分析脚本依赖 librosa 0.11、numpy、scipy、soundfile、matplotlib；视频脚本依赖 FFmpeg、PyAV、Pillow。已适配解压后的工程目录。原生模型推理由另附 ComfyUI 工作流重现。生成记录的旧绝对路径仅作来源记录，不影响素材相对路径。')
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'total_generation_minutes':sum(seconds)/60,'scenes':len(manifests)},ensure_ascii=False))
