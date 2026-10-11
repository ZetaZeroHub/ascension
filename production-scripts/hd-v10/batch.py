import json,time,urllib.request,urllib.error,shutil,subprocess,ctypes,hashlib,os,sys,traceback
from pathlib import Path
import av,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'work/feisheng/hd-v10';OUT=ROOT/'outputs/Feisheng-MV/高清素材-v10';OLD=ROOT/'outputs/Feisheng-MV/补充与舞蹈-v9'
INPUT=Path('<LOCAL_PATH>/FeishengHDV10')
for d in [WORK,OUT,INPUT,*[OUT/x for x in ['frames','workflows','records','24fps母版','48fps剪辑版','原生视频','审查']]]:d.mkdir(parents=True,exist_ok=True)
SOURCE=json.loads((OLD/'素材清单.json').read_text(encoding='utf-8'))
PROMPTS=json.loads((OLD/'视频提示词.json').read_text(encoding='utf-8'))
BASE=json.loads((ROOT/'outputs/H3-Quality-768p-32step-API.json').read_text(encoding='utf-8'))
def write(p,x):
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(p)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def req(path,data=None):
    q=urllib.request.Request('http://127.0.0.1:8000'+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(q,timeout=45) as r:return json.load(r)
    except urllib.error.HTTPError as e:raise RuntimeError(e.read().decode())
class Memory(ctypes.Structure):
    _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong),('total',ctypes.c_ulonglong),('free',ctypes.c_ulonglong),('commit_total',ctypes.c_ulonglong),('commit_free',ctypes.c_ulonglong),('virtual_total',ctypes.c_ulonglong),('virtual_free',ctypes.c_ulonglong),('extended',ctypes.c_ulonglong)]
def resources():
    m=Memory();m.length=ctypes.sizeof(m);ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    g=subprocess.check_output(['nvidia-smi','--query-gpu=temperature.gpu,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip().split(',')
    return dict(time=time.time(),ram_free_mib=m.free//1048576,commit_free_mib=m.commit_free//1048576,temp=int(g[0]),gpu_mib=int(g[1]),gpu_util=int(g[2]))
def paths(item):
    label=f"{item['shot']}-{item['name']}.mp4"
    return OUT/'24fps母版'/label,OUT/'48fps剪辑版'/label,OUT/'records'/f"{item['shot']}-manifest.json"
def finished(item):
    master,smooth,m=paths(item)
    if not (m.exists() and master.exists() and smooth.exists()):return False
    x=json.loads(m.read_text(encoding='utf-8'))
    return x.get('verified') is True and x['master_sha256']==sha(master) and x['smooth_sha256']==sha(smooth)
def status(phase,item=None,pid=None,stat=None,**kw):
    write(OUT/'status.json',dict(phase=phase,runner_pid=os.getpid(),updated=time.time(),completed=[x['shot'] for x in SOURCE if finished(x)],total=len(SOURCE),active_shot=item['shot'] if item else None,active_name=item['name'] if item else None,prompt_id=pid,resources=stat,**kw))
def graph(item):
    sid=item['shot'];shutil.copy2(OLD/'frames'/f'{sid}.png',OUT/'frames'/f'{sid}.png');shutil.copy2(OUT/'frames'/f'{sid}.png',INPUT/f'{sid}.png')
    p=json.loads(json.dumps(BASE));p.pop('4');p.pop('13');p['14']['inputs'].pop('audio',None)
    p['6']['inputs'].update(prompt=PROMPTS[sid],width=1280,height=736,length=124,first_frame=['16',0])
    p['8']['inputs']['steps']=25;p['10']['inputs']['noise_seed']=item['seed']
    p['15']['inputs']['filename_prefix']=f'video/FeishengHDV10_{sid}_native720_25step'
    p['16']={'class_type':'LoadImage','inputs':{'image':f'FeishengHDV10/{sid}.png'}}
    write(OUT/'workflows'/f'{sid}-API.json',p);return p
def runff(args,log):
    with log.open('w',encoding='utf-8') as f:subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*args],stdout=f,stderr=f,check=True)
def validate(p,count,fps,contact=None):
    n=0;black=[];previous=None;deltas=[];thumbs=[];timestamps=[]
    with av.open(str(p)) as c:
        v=c.streams.video[0];dims=[v.width,v.height];rate=float(v.average_rate)
        for i,f in enumerate(c.decode(video=0)):
            n+=1;timestamps.append(float(f.pts*f.time_base));a=np.asarray(f.to_image().resize((160,90))).astype(np.float32)
            if a.mean()<1:black.append(i)
            if previous is not None:deltas.append(float(np.abs(a-previous).mean()))
            previous=a
            if contact and i%max(1,fps//4)==0:thumbs.append((i,f.to_image().resize((384,216))))
    assert dims==[1280,720] and rate==fps and n==count and not black,(p,dims,rate,n,black)
    assert all(abs(t-i/fps)<1e-5 for i,t in enumerate(timestamps)),(p,'timestamps')
    if contact:
        img=Image.new('RGB',(1536,((len(thumbs)+3)//4)*238),(16,18,22));d=ImageDraw.Draw(img)
        for j,(fr,im) in enumerate(thumbs):
            x=j%4*384;y=j//4*238;img.paste(im,(x,y));d.text((x+8,y+219),f'frame {fr} / {fr/fps:.3f}s',fill='white')
        img.save(contact,quality=90)
    return dict(file=str(p.relative_to(OUT)),frames=n,fps=rate,size=dims,duration=n/rate,black_frames=black,mean_frame_change=float(np.mean(deltas)),max_frame_change=max(deltas),sha256=sha(p))
def submit_or_resume(item,p):
    sid=item['shot'];sp=OUT/'records'/f'{sid}-submitted.json'
    if sp.exists():
        old=json.loads(sp.read_text());pid=old['prompt_id'];h=req('/history/'+pid);q=req('/queue')
        if pid in h:
            if h[pid].get('status',{}).get('status_str')=='error':raise RuntimeError(f'Previous shot {sid} failed; inspect history before retry')
            return pid
        if any(x[1]==pid for x in q['queue_running']+q['queue_pending']):return pid
        raise RuntimeError(f'Previously submitted prompt {pid} no longer visible; inspect backend before retry')
    while True:
        q=req('/queue')
        if not q['queue_running'] and not q['queue_pending']:break
        status('waiting_queue',item);time.sleep(15)
    submission=req('/prompt',{'prompt':p,'client_id':'codex-feisheng-hd-v10'})
    if submission.get('node_errors'):raise RuntimeError(submission)
    write(sp,submission);print('SUBMITTED',sid,submission['prompt_id'],flush=True);return submission['prompt_id']
def generate(item,p):
    pid=submit_or_resume(item,p);started=time.time();errors=0
    while True:
        try:
            h=req('/history/'+pid);errors=0
        except (urllib.error.URLError,TimeoutError):
            errors+=1;status('observation_retry',item,pid,observation_errors=errors);time.sleep(15);continue
        if pid in h and (h[pid].get('status',{}).get('completed') or h[pid].get('status',{}).get('status_str')=='error'):
            record=h[pid];break
        st=resources();status('generating',item,pid,st,observed_elapsed=time.time()-started)
        with (WORK/'resources.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(dict(shot=item['shot'],prompt_id=pid,**st))+'\n')
        if st['ram_free_mib']<768 or st['commit_free_mib']<1536 or st['temp']>=84:
            if any(x[1]==pid for x in req('/queue')['queue_running']):req('/interrupt',{})
            write(WORK/'resource-stop.json',st);raise RuntimeError('Own generation stopped at resource threshold')
        time.sleep(15)
    write(OUT/'records'/f"{item['shot']}-history.json",record)
    if record['status']['status_str']!='success':raise RuntimeError(record['status'])
    f=record['outputs']['15']['images'][0];generated=Path('<LOCAL_PATH>/output')/f.get('subfolder','')/f['filename']
    native=OUT/'原生视频'/f"{item['shot']}-{item['name']}.mp4";shutil.copy2(generated,native)
    ts={a:b.get('timestamp') for a,b in record['status']['messages']};return pid,native,(ts['execution_success']-ts['execution_start'])/1000
def postprocess(item,pid,native,seconds):
    master,smooth,mp=paths(item);sid=item['shot'];status('cropping',item,pid)
    tags=['-color_primaries','bt709','-color_trc','iec61966-2-1','-colorspace','bt709','-movflags','+faststart']
    runff(['-i',str(native),'-vf','crop=1280:720:0:8,setsar=1','-an','-c:v','libx264','-preset','slow','-crf','15','-threads','2',*tags,str(master)],WORK/f'{sid}-crop.log')
    qa1=validate(master,124,24,OUT/'审查'/f'{sid}-24fps-contact.jpg');status('interpolating',item,pid)
    start=time.time()
    vf='tpad=stop_mode=clone:stop_duration=0.2,minterpolate=fps=48:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:me=epzs:vsbmc=1,trim=end_frame=248,settb=AVTB,setpts=N/(48*TB),setsar=1'
    runff(['-filter_threads','2','-i',str(master),'-vf',vf,'-an','-c:v','libx264','-preset','slow','-crf','15','-threads','2','-r','48',*tags,str(smooth)],WORK/f'{sid}-interpolate.log')
    qa2=validate(smooth,248,48,OUT/'审查'/f'{sid}-48fps-contact.jpg')
    # Original frame cadence is preserved; odd frames add estimated motion rather than extend the story.
    manifest=dict(shot=sid,name=item['name'],prompt_id=pid,steps=25,turbo_lora=False,native_size=[1280,736],output_size=[1280,720],source_frames=124,source_fps=24,output_frames=248,output_fps=48,duration=124/24,interpolation='FFmpeg motion compensated interpolation, bidirectional EPZS, adaptive OBMC, VSBMC',generation_seconds=seconds,interpolation_seconds=time.time()-start,seed=item['seed'],source_reference_sha256=sha(OUT/'frames'/f'{sid}.png'),native_sha256=sha(native),master_sha256=sha(master),smooth_sha256=sha(smooth),master_file=str(master.relative_to(OUT)),smooth_file=str(smooth.relative_to(OUT)),verified=True,qa_master=qa1,qa_smooth=qa2,visual_review='pending')
    write(mp,manifest);print('COMPLETE',sid,seconds,manifest['interpolation_seconds'],flush=True);status('clip_completed',item,pid)
def main():
    graphs={x['shot']:graph(x) for x in SOURCE}
    write(OUT/'batch-spec.json',dict(objective='逐个把这些素材高清化，增强步数、增强分辨率和帧率或扩时长',shots=[x['shot'] for x in SOURCE],total=10,native_size=[1280,736],delivery_size=[1280,720],steps=25,turbo=False,native_fps=24,interpolated_fps=48,duration=124/24,source_batch=str(OLD),started=time.time(),runner_pid=os.getpid()))
    if '--prepare-only' in sys.argv:print('ALL_GRAPHS_PREPARED');return
    for item in SOURCE:
        if finished(item):print('REUSE_VERIFIED',item['shot'],flush=True);continue
        pid,native,seconds=generate(item,graphs[item['shot']]);postprocess(item,pid,native,seconds)
    status('generation_and_technical_validation_complete');print('ALL_TEN_HD_CLIPS_TECHNICALLY_VERIFIED',flush=True)
if __name__=='__main__':
    try:main()
    except Exception as e:
        current=json.loads((OUT/'status.json').read_text(encoding='utf-8')) if (OUT/'status.json').exists() else {}
        write(OUT/'failure.json',dict(time=time.time(),error=str(e),traceback=traceback.format_exc(),previous_status=current));print(traceback.format_exc(),flush=True);raise
