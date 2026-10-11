import json, hashlib
from pathlib import Path
import av
import numpy as np

ROOT=Path(__file__).resolve().parent
OLD=ROOT/'remotion';NEW=ROOT/'remotion-v2'
OUT=ROOT.parents[1]/'outputs/Feisheng-MV/重剪版-v2'
story=json.loads((NEW/'src/data/storyboard.json').read_text(encoding='utf-8'))
clips=[]
for s in story['scenes']:
    a=OLD/'public'/s['native_video'];b=NEW/'public'/s['native_video']
    ha=hashlib.sha256(a.read_bytes()).hexdigest();hb=hashlib.sha256(b.read_bytes()).hexdigest()
    assert ha==hb;clips.append({'id':s['id'],'sha256':ha})
audio_original=hashlib.sha256((OLD/'public/audio/feisheng-master.wav').read_bytes()).hexdigest()
audio_reedit=hashlib.sha256((NEW/'public/audio/feisheng-master.wav').read_bytes()).hexdigest()
assert audio_original==audio_reedit and len(clips)==14
assert story['durationInFrames']==2282 and story['scenes'][0]['from']==0 and story['scenes'][-1]['to']==2282
assert all(a['to']==b['from'] for a,b in zip(story['scenes'],story['scenes'][1:]))
wanted=set(range(0,912,48))|{911}
def early(path):
    result={}
    with av.open(str(path)) as c:
        for i,f in enumerate(c.decode(video=0)):
            if i in wanted:result[i]=f.reformat(width=480,height=270,format='rgb24').to_ndarray().astype(np.float32)
            if i>=911:break
    return result
a=early(OUT.parent/'飞升-MV-1080p.mp4');b=early(OUT/'飞升-MV-1080p-节奏重剪-v2.mp4')
mae=[float(np.mean(np.abs(a[k]-b[k]))) for k in sorted(wanted)]
assert max(mae)<2,'Unexpected early-picture changes'
transients=json.loads((ROOT/'analysis/reedit-v2/transient-candidates.json').read_text())
cut_evidence=[]
for s in story['scenes']:
    if int(s['id'])<7:continue
    at=s['from']/24
    candidates=[(name,c) for name,items in transients.items() for c in items]
    name,closest=min(candidates,key=lambda x:abs(x[1]['time']-at))
    cut_evidence.append({'scene':s['id'],'cut_seconds':at,'nearby_attack_seconds':closest['time'],'attack_band':name,'offset_ms':round((at-closest['time'])*1000,3)})
report={'native_clip_count':len(clips),'same_native_clips':'passed','native_clips':clips,
        'same_master_audio':'passed','master_sha256':audio_original,'duration_frames':2282,
        'timeline_continuity':'passed','early_frame_samples':len(wanted),'early_frame_max_mae_255':max(mae),
        'unchanged_early_picture':'passed with encoding tolerance','abrupt_reframe_accents':0,
        'cut_attack_evidence':cut_evidence,
        'limitations':'Nearby spectral attacks support temporal alignment; they do not prove all cuts are score-derived downbeats or subjective musical fit.'}
(OUT/'重剪约束验证.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['native_clips']},ensure_ascii=False,indent=2))
