from pathlib import Path
import av,numpy as np,json,hashlib
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'outputs/Feisheng-MV/成片-v7'
results=[]
for p in sorted((OUT/'records').glob('*-manifest.json')):
    m=json.loads(p.read_text(encoding='utf-8'));video=OUT/'clips'/f"{m['shot']}-720p.mp4"
    assert hashlib.sha256(video.read_bytes()).hexdigest()==m['sha256']
    changes=[];last=None;count=0;times=[]
    with av.open(str(video)) as c:
        s=c.streams.video[0];assert (s.width,s.height)==(1280,720)
        for f in c.decode(video=0):
            count+=1;times.append(float(f.pts*f.time_base));gray=f.reformat(width=96,height=54,format='gray').to_ndarray().astype(np.float32)
            if last is not None:changes.append(float(np.mean(np.abs(gray-last))))
            last=gray
    assert count==124
    assert all(abs(b-a-1/24)<1e-5 for a,b in zip(times,times[1:]))
    results.append(dict(shot=m['shot'],frames=count,sha256_matches=True,mean_frame_difference=float(np.mean(changes)),identical_adjacent_frames=sum(d==0 for d in changes),decode_pass=True))
(OUT/'素材技术检查.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False,indent=2))
