from pathlib import Path
import json,csv
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'outputs/Feisheng-MV/成片-v7'
timeline=json.loads((OUT/'timeline.json').read_text())
features=json.loads((ROOT/'work/feisheng/analysis/reedit-v2/transient-candidates.json').read_text())
events=[dict(**p,band=band) for band,values in features.items() for p in values]
rows=[]
for prev,s in zip(timeline,timeline[1:]):
    t=s['fromFrame']/24
    event=min(events,key=lambda p:abs(p['time']-t)) if 35<=t<=88 else None
    visible=(prev['source'],prev['view'])!=(s['source'],s['view']) or (s['source']=='08' and s['fromFrame']==1296 and (OUT/'选片记录.json').exists())
    rows.append(dict(frame=s['fromFrame'],seconds=round(t,6),source=s['source'],view=s['view'],visible_cut=visible,nearest_transient=event['time'] if event else '',band=event['band'] if event else '',offset_ms=round((t-event['time'])*1000,3) if event else ''))
with (OUT/'剪辑节拍核对.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('Visible cuts:',sum(r['visible_cut'] for r in rows),'Timeline segments:',len(timeline))
print('This measures distance to detected transients, not a manually transcribed score.')
