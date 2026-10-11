"""Technical acceptance plus dense visual evidence; never labels artistic review passed."""
from pathlib import Path
import hashlib,json,subprocess,re
import av
import numpy as np
from scipy.signal import correlate,correlation_lags
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'outputs/Feisheng-MV/成片-v7'
QA=OUT/'审查';QA.mkdir(exist_ok=True)
VIDEO=OUT/'飞升-MV-720p-v7-待视听复核.mp4'
MASTER=ROOT/'work/feisheng/v7/remotion/public/audio/feisheng-master.wav'
timeline=json.loads((OUT/'timeline.json').read_text())
assert timeline[0]['fromFrame']==0
for a,b in zip(timeline,timeline[1:]):assert a['fromFrame']+a['duration']==b['fromFrame']
assert timeline[-1]['fromFrame']+timeline[-1]['duration']==2282
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(VIDEO)]))
v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'],v['r_frame_rate'])==(1280,720,'24/1')
assert (a['sample_rate'],a['channels'])==('48000',2)
cuts={s['fromFrame'] for s in timeline[1:]}
boundary={f for c in cuts for f in (c-2,c-1,c,c+1,c+2)}
pages=[];tiles=[];boundary_tiles=[];pts=[];dark=[];blank=[];diff=[];prev=None
def write_page(items,name):
    canvas=Image.new('RGB',(1280,items.__len__()//4*202+(202 if len(items)%4 else 0)),(20,21,20))
    d=ImageDraw.Draw(canvas)
    for j,(n,img) in enumerate(items):
        x=(j%4)*320;y=(j//4)*202;canvas.paste(img,(x,y));d.text((x+8,y+181),f'{n/24:06.2f}s  frame {n}',fill=(235,227,213))
    canvas.save(QA/name)
with av.open(str(VIDEO)) as c:
    for n,frame in enumerate(c.decode(video=0)):
        pts.append(float(frame.pts*frame.time_base))
        gray=frame.reformat(width=96,height=54,format='gray').to_ndarray().astype(np.float32)
        if gray.mean()<2:dark.append(n)
        if gray.mean()<16 and gray.std()<1:blank.append(n)
        if prev is not None:diff.append(float(np.abs(gray-prev).mean()))
        prev=gray
        if n%12==0 or n in boundary:
            img=frame.to_image().resize((320,180),Image.Resampling.LANCZOS)
            if n%12==0:tiles.append((n,img))
            if n in boundary:boundary_tiles.append((n,img))
assert len(pts)==2282
assert all(abs(y-x-1/24)<1e-5 for x,y in zip(pts,pts[1:]))
assert not [n for n in dark if n<2246],f'Unexpected black frames: {dark}'
assert not [n for n in blank if n<2246],f'Unexpected flat empty frames: {blank}'
for kind,items in [('连续',tiles),('切点',boundary_tiles)]:
    for page,start in enumerate(range(0,len(items),24),1):write_page(items[start:start+24],f'{kind}-{page:02d}.jpg')
def pcm(p):return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-vn','-ac','1','-ar','8000','-f','f32le','pipe:1']),dtype='<f4')
x=pcm(MASTER);y=pcm(VIDEO);length=min(len(x),len(y));x=x[:length];y=y[:length]
corr=correlate(y,x,mode='full',method='fft');lags=correlation_lags(len(y),len(x));mask=np.abs(lags)<=2000
lag=int(lags[mask][np.argmax(corr[mask])]);similarity=float(np.corrcoef(x,y)[0,1])
assert abs(lag)<=8 and similarity>.995,(lag,similarity)
loud=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(VIDEO),'-af','ebur128=peak=true:framelog=verbose','-f','null','NUL'],capture_output=True,text=True,encoding='utf-8',errors='replace',check=True)
(QA/'响度.log').write_text(loud.stderr,encoding='utf-8')
summary=loud.stderr.rsplit('Summary:',1)[-1]
lufs=float(re.search(r'<LOCAL_PATH>/d.]+) LUFS',summary).group(1));peak=float(re.search(r'Peak:\s*([\-\d.]+) dBFS',summary).group(1))
assert -13<lufs<-11 and peak<=-1,(lufs,peak)
report=dict(file=VIDEO.name,sha256=hashlib.sha256(VIDEO.read_bytes()).hexdigest(),width=1280,height=720,fps=24,frames=len(pts),duration=len(pts)/24,audio_correlation=similarity,audio_offset_ms=lag/8,integrated_lufs=lufs,true_peak_dbfs=peak,dark_frames=dark,frame_motion_mean=diff,technical_pass=True,visual_review='pending',audio_method='Decoded waveform correlation, offset and loudness; no subjective listening claim.',source='Local H3 1280x736 cropped to 1280x720, 25 sampling steps; no AI upscale.')
report['flat_dark_frames']=blank
(QA/'验证结果.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='frame_motion_mean'},ensure_ascii=False,indent=2))
