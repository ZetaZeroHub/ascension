import json, subprocess, hashlib, re, sys
from pathlib import Path
import av
import numpy as np
from scipy.signal import correlate, correlation_lags
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parents[1]/'outputs/Feisheng-MV'
video=Path(sys.argv[1]) if len(sys.argv)>1 else OUT/'飞升-MV-1080p.mp4'
source=ROOT/'remotion/public/audio/feisheng-master.wav'
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
v=next(x for x in probe['streams'] if x['codec_type']=='video')
a=next(x for x in probe['streams'] if x['codec_type']=='audio')
assert (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'24/1')
assert a['sample_rate']=='48000' and a['channels']==2
frames=0;pts=[];black=[]
with av.open(str(video)) as c:
    for f in c.decode(video=0):
        pts.append(float(f.pts*f.time_base))
        gray=np.asarray(f.reformat(width=96,height=54,format='gray').to_ndarray())
        if gray.mean()<2:black.append(frames)
        frames+=1
assert frames==2282
assert all(abs((y-x)-1/24)<1e-5 for x,y in zip(pts,pts[1:]))
def pcm(path):
    return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-vn','-ac','1','-ar','8000','-f','f32le','pipe:1']),dtype='<f4')
x=pcm(source);y=pcm(video);n=min(len(x),len(y));x=x[:n];y=y[:n]
c=correlate(y,x,mode='full',method='fft');lags=correlation_lags(len(y),len(x),mode='full')
mask=np.abs(lags)<=2000;lag=int(lags[mask][np.argmax(c[mask])])
assert abs(lag)<=8, f'Audio offset exceeds 1 ms: {lag/8} ms'
corr=float(np.corrcoef(x,y)[0,1]);assert corr>.995
level_ratio=float(np.sqrt(np.mean(y*y)/np.mean(x*x)))
loud=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(video),'-af','ebur128=peak=true:framelog=verbose','-f','null','NUL'],capture_output=True,text=True,encoding='utf-8',errors='replace')
assert loud.returncode==0
(OUT/'成片响度检测.log').write_text(loud.stderr,encoding='utf-8')
summary=loud.stderr.rsplit('Summary:',1)[-1]
integrated=float(re.search(r'<LOCAL_PATH>/d.]+) LUFS',summary).group(1))
peak=float(re.search(r'Peak:\s*([\-\d.]+) dBFS',summary).group(1))
assert peak<=-1 and -13<integrated<-11
report={'file':video.name,'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'width':v['width'],'height':v['height'],'fps':24,'decoded_frames':frames,'duration_seconds':frames/24,'video_codec':v['codec_name'],'audio_codec':a['codec_name'],'audio_sample_rate':48000,'audio_channels':2,'integrated_lufs':integrated,'true_peak_dbfs':peak,'audio_vs_master_correlation':corr,'audio_offset_ms':lag/8,'audio_level_ratio_vs_master':level_ratio,'very_dark_frames_mean_under_2':black,'timeline_continuity':'passed','audio_preservation':'passed','limitations':['Automatic beat estimates are not a verified score transcription.','Native H3 resolution is 704x384; final output is upscaled 1080p.','Technical analysis and visual sampling do not substitute for subjective full headphone/speaker listening.']}
(OUT/'成片验证.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
