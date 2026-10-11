import json, hashlib, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
P=ROOT/'remotion-v2';OLD=ROOT/'remotion'
OUT=ROOT.parents[1]/'outputs/Feisheng-MV/重剪版-v2'
assets=[]
for f in sorted((P/'public').rglob('*')):
    if f.is_file():assets.append({'path':f.relative_to(P).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size})
(P/'src/data/asset-manifest.json').write_text(json.dumps(assets,indent=2),encoding='utf-8')
for f in (OLD/'public/clips').glob('*.mp4'):
    assert hashlib.sha256(f.read_bytes()).digest()==hashlib.sha256((P/'public/clips'/f.name).read_bytes()).digest()
assert hashlib.sha256((OLD/'public/audio/feisheng-master.wav').read_bytes()).digest()==hashlib.sha256((P/'public/audio/feisheng-master.wav').read_bytes()).digest()
note=(OUT/'重剪说明.md').read_text(encoding='utf-8')
(P/'制作说明.md').write_text(note,encoding='utf-8')
with (P/'README.md').open('a',encoding='utf-8') as f:f.write('\n## v2 节奏重剪\n\n详见 重剪说明.md；同一套 14 段素材。最新切点见 src/data/timeline.json；第 06 段由 Sequence 在新切点截出，其余后段素材已重新定时。\n')
old=ROOT/'validate_final.py'
code=old.read_text(encoding='utf-8').replace("OUT=ROOT.parents[1]/'outputs/Feisheng-MV'","OUT=ROOT.parents[1]/'outputs/Feisheng-MV/重剪版-v2'")
code=code.replace("OUT/'飞升-MV-1080p.mp4'","OUT/'飞升-MV-1080p-节奏重剪-v2.mp4'").replace("ROOT/'remotion/public/audio/feisheng-master.wav'","ROOT/'remotion-v2/public/audio/feisheng-master.wav'")
(ROOT/'validate_reedit.py').write_text(code,encoding='utf-8')
code=(ROOT/'contact_final.py').read_text(encoding='utf-8').replace("'outputs/Feisheng-MV'","'outputs/Feisheng-MV/重剪版-v2'")
code=code.replace("ROOT/'src/data/storyboard.json'","ROOT/'remotion-v2/src/data/storyboard.json'").replace("'飞升-MV-1080p.mp4'","'飞升-MV-1080p-节奏重剪-v2.mp4'")
code=code.replace("for f in [1441,1470,1642,1671,1786,1801]:frames.update([f-1,f])",'')
code=code.replace("ROOT/'analysis'/f'final-contact-{page}.jpg'","ROOT/'analysis/reedit-v2'/f'final-contact-{page}.jpg'")
(ROOT/'contact_reedit.py').write_text(code,encoding='utf-8')
print('Verified identical native clips and master audio; updated asset manifest',flush=True)
