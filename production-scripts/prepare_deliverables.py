import csv, hashlib, json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT/'remotion'
DATA=PROJECT/'src/data'
OUT=ROOT.parents[1]/'outputs/Feisheng-MV'
OUT.mkdir(exist_ok=True)
analysis=json.loads((ROOT/'analysis/music-analysis.json').read_text(encoding='utf-8'))
story=json.loads((ROOT/'src/data/storyboard.json').read_text(encoding='utf-8'))
def save(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
source=Path('<USER_HOME>/Downloads/《飞升》hahaha(brighter) - 2025_7_12 06.32.m4a')
original=PROJECT/'public/audio/feisheng-original.m4a'
shutil.copy2(source,original)
master=PROJECT/'public/audio/feisheng-master.wav'
save(DATA/'audio-manifest.json',{'routing_profile':'user-provided-original-instrumental','provider':'local user file','service':'offline FFmpeg','model':None,'voice_id':None,'duration_seconds':analysis['duration'],'processing':'Decode AAC priming, retain original speed and full song; static -6 dB gain; 48 kHz stereo PCM24 master. No added voice, music or SFX.','assets':[{'path':str(p.relative_to(PROJECT)).replace('\\','/'),'sha256':digest(p)} for p in [original,master]]})
save(DATA/'captions.json',{'items':[],'reason':'Instrumental music video. No lyrics, speech, CTA or explanatory captions requested.'})
save(DATA/'script.json',{'logline':story['story_logline'],'scenes':[{'id':s['id'],'title':s['title'],'hero_stage':s['hero_stage'],'visual_action':s['motion_prompt']} for s in story['scenes']]})
cuts=[]
for s in story['scenes'][1:]:
    time=s['from']/24
    beat=min(analysis['beats'],key=lambda x:abs(x-time))
    cuts.append({'kind':'scene_cut','scene':s['id'],'frame':s['from'],'seconds':time,'measured_beat_seconds':beat,'error_ms':round((time-beat)*1000,3),'confidence':'medium' if time<19.2 else 'medium-high'})
for f in [1441,1470,1642,1671,1786,1801]:
    time=f/24;beat=min(analysis['beats'],key=lambda x:abs(x-time))
    cuts.append({'kind':'reframe_accent','scene':'','frame':f,'seconds':time,'measured_beat_seconds':beat,'error_ms':round((time-beat)*1000,3),'confidence':'medium-high'})
cuts.sort(key=lambda x:x['frame'])
assert story['scenes'][0]['from']==0 and story['scenes'][-1]['to']==2282
assert all(a['to']==b['from'] for a,b in zip(story['scenes'],story['scenes'][1:]))
assert max(abs(c['error_ms']) for c in cuts)<=1000/48
save(DATA/'timeline.json',{'fps':24,'durationInFrames':2282,'audioOffsetFrames':0,'scenes':[{k:s[k] for k in ['id','from','to','title']} for s in story['scenes']],'cuts':cuts,'note':'Beat tracking is an estimate, not a verified score transcription. Early quiet introduction has lower confidence.'})
with (OUT/'剪辑卡点.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(cuts[0]));w.writeheader();w.writerows(cuts)
shutil.copy2(ROOT/'analysis/music-analysis.png',OUT/'音乐结构分析.png')
shutil.copy2(ROOT/'analysis/music-analysis.json',OUT/'音乐分析数据.json')
save(DATA/'style-preset.json',{'palette':['#080909','#6d0611','#cfb378'],'subject':'one continuous crimson silk ribbon','cinematography':'monumental architecture, restrained motion, abstract hero journey','frame':'16:9','typography':'Microsoft YaHei, restrained title only','motion':'frame-driven, locked beat cuts, optical-flow retime; no generic transition pack'})
(PROJECT/'brief.md').write_text('''# 飞升 · 制作简报

完整纯音乐 MV，横屏 1920×1080、24 fps、2282 帧。原曲约 95.081 秒；时间轴 95.083 秒。
红绸作为唯一主人公：重力与秩序 → 召唤 → 自缚 → 指引 → 越界 → 试炼 → 深渊 → 归零 → 破茧 → 飞升 → 携光归来。
视觉语言：巨构混凝土、黑色镜面水、深红丝绸、逐渐增强的金色光线。结尾回到开场空间，完成英雄之旅的归返。

原曲由用户提供，本地分析，不上传音频。Dm–G/B–Dm–G/D 来自用户描述，未独立完成和弦转录。脉冲估计约 100.23 BPM，节拍不是人工核准乐谱；弱起前奏置信度中等，高潮由能量、频带与事件变化共同选取。
每段 H3 原生 704×384、124 帧、20 步，首尾帧条件。输出 1080p 是后期缩放，不宣称原生 1080p 细节。光流重定时使镜头严格落在音乐切点。
本片为艺术音乐作品：不适用营销 CTA、旁白、字幕和产品演示占比要求。原曲是唯一音轨，不添加 ElevenLabs 内容。用户凭据不进入工程。
''',encoding='utf-8')
print(json.dumps({'cuts':len(cuts),'maximum_snap_error_ms':max(abs(c['error_ms']) for c in cuts)},ensure_ascii=False))
