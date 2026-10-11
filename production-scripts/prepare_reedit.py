import json, shutil, csv, os, hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OLD=ROOT/'remotion'
NEW=ROOT/'remotion-v2'
OUT=ROOT.parents[1]/'outputs/Feisheng-MV/重剪版-v2'
OUT.mkdir(exist_ok=True)
if not NEW.exists():
    shutil.copytree(OLD,NEW,ignore=shutil.ignore_patterns('node_modules','.git','out','dist','build','analysis','generation'))
    os.symlink(OLD/'node_modules',NEW/'node_modules',target_is_directory=True)
story=json.loads((OLD/'src/data/storyboard.json').read_text(encoding='utf-8'))
old_timeline=json.loads((OLD/'src/data/timeline.json').read_text(encoding='utf-8'))
new_starts={'07':922,'08':1037,'09':1210,'10':1382,'11':1498,'12':1613,'13':1843,'14':2074}
why={'07':'38.4s low-frequency attack; begin mirror trial at the requested revision range',
     '08':'43.2s phrase pulse; move from mirror corridor into bridge tension',
     '09':'50.4s spectral attack and harmonic-change neighborhood; extend anticipation',
     '10':'57.6s sustained bass entry; retain the main release',
     '11':'62.4s bass attack after two 2.4-second bar units; tighten the opening action',
     '12':'67.2s strongest late bass transient; reveal the ascension at the phrase reset',
     '13':'76.8s onset before the bass texture falls away; transition into return',
     '14':'86.4s last active attack before decay; begin resolution before the tail'}
for i,s in enumerate(story['scenes']):
    if s['id'] in new_starts:s['from']=new_starts[s['id']]
    s['to']=new_starts.get(story['scenes'][i+1]['id'],story['scenes'][i+1]['from']) if i+1<len(story['scenes']) else 2282
    s['start']=s['from']/24;s['end']=s['to']/24
story['revision']='v2 rhythm reedit, existing 14 clips only, unchanged song and total length'
assert len(story['scenes'])==14 and story['scenes'][0]['from']==0 and story['scenes'][-1]['to']==2282
assert all(a['to']==b['from'] for a,b in zip(story['scenes'],story['scenes'][1:]))
cuts=[];changes=[]
for s,old in zip(story['scenes'][1:],old_timeline['scenes'][1:]):
    cuts.append({'kind':'scene_cut','scene':s['id'],'frame':s['from'],'seconds':s['from']/24,
                 'basis':why.get(s['id'],'unchanged opening edit'),'confidence':'medium'})
    if s['from']!=old['from']:
        changes.append({'镜头':s['id'],'名称':s['title'],'旧切点秒':old['from']/24,'新切点秒':s['from']/24,'调整秒':(s['from']-old['from'])/24})
timeline={'fps':24,'durationInFrames':2282,'audioOffsetFrames':0,
          'scenes':[{k:s[k] for k in ['id','from','to','title']} for s in story['scenes']],
          'cuts':cuts,'reframeAccents':[],
          'note':'V2 uses local multiband attacks and phrase grouping; inferred bar grouping is not a verified score transcription. Removes all six abrupt reframe accents.'}
(NEW/'src/data/storyboard.json').write_text(json.dumps(story,ensure_ascii=False,indent=2),encoding='utf-8')
(NEW/'src/data/timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copy2(NEW/'src/data/timeline.json',OUT/'重剪时间轴.json')
with (OUT/'切点调整对照.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(changes[0]));w.writeheader();w.writerows(changes)
code=(NEW/'src/Feisheng.tsx').read_text(encoding='utf-8')
start=code.index('const accents:');end=code.index('const pushEnds:')
code=code[:start]+code[end:]
start=code.index('  let scale = 1;');end=code.index('  const push =',start)
code=code[:start]+code[end:]
code=code.replace('scale(${scale * push})','scale(${push})')
(NEW/'src/Feisheng.tsx').write_text(code,encoding='utf-8')
note='''# 飞升 · 38 秒后节奏重剪 v2

使用同一套 14 段 AI 视频与同一条母带，仍为 2282 帧 / 24 fps / 95.083 秒 / 1080p。
38 秒前的剪辑区间与画面保留。第 06 段按原播放进度在 38.417 秒切出，第 07–14 段按新乐句区间重新定时。
取消原版六个突然放大／缩回的重构图点，保留平滑镜头推进。主要切点见 CSV。

音乐分析完全在本地完成：区分低频起音、宽频起音、低频进入/退出与尾音衰减，再结合现有故事顺序安排切换。
乐句分组是编辑推断，未声称进行了人工乐谱转录或主观全曲试听。
原版成片和原版工程继续保留。
'''
(OUT/'重剪说明.md').write_text(note,encoding='utf-8')
(NEW/'重剪说明.md').write_text(note,encoding='utf-8')
print(json.dumps(changes,ensure_ascii=False,indent=2))
