import json,time,urllib.request,urllib.error,shutil,sys,subprocess,ctypes,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'work/feisheng/v7'
OUT=ROOT/'outputs/Feisheng-MV/成片-v7'
ASSETS=ROOT/'outputs/Feisheng-MV/独立分镜-v6'
INPUT=Path('<LOCAL_PATH>/FeishengV7')
for p in [OUT/'clips',OUT/'workflows',OUT/'records',INPUT]:p.mkdir(parents=True,exist_ok=True)
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
COMMON='One continuous cinematic shot, warm grey soft film palette, burgundy matte coat, natural skin, stable exposure. Same short black bob woman, same face, clothing and body proportions throughout. Physically coherent motion, no extra limbs, no morphing, no cuts, no captions, no logo. '
PROMPTS={
'01':'Wide rear view of the burgundy-coated courier walking three slow steps toward the massive ring in the frozen brutalist city. Sparse raindrops remain suspended motionless while her coat gently moves. Slow forward dolly, the architecture stays rigid.',
'02':'Intimate side profile portrait. The courier subtly shifts her eyes toward a warm light offscreen right, takes a quiet breath, then slightly raises her chin with determination. Camera makes a very slow short push in. One raindrop remains suspended by her face. Keep face and skin natural and consistent.',
'03':'Over shoulder view. The courier slowly approaches the small cracked golden seed suspended inside the membrane at shoulder height. Her right hand begins to rise toward it. Seed remains palm-sized and stationary. Slow subtle dolly in; black arch and city remain rigid.',
'04':'Closeup of the right hand gripping the single palm-sized cracked golden seed. The fingers close securely, then the hand slowly pulls the seed toward the camera through the membrane. The thin membrane stretches, separates and retracts. Only one seed, stable five-finger hand, empty arch behind.',
'05':'Side tracking shot. The courier runs urgently left to right along the bridge, taking several grounded strides while protecting the single small golden seed with both hands against her chest. Her coat trails behind. The black ring searchlights sweep behind her, not across her face. Keep seed in her hands.',
'06':'The courier brakes and stops at the broken bridge edge, still holding the seed in her right hand. Small pieces break off the jagged stone and fall into the shaft. She leans forward slightly to look down but does not jump yet. The gap remains wide and clearly visible. Camera slowly tilts down.',
'07':'Medium close profile. She looks down into the shaft, glances at the small seed in her right hand, then closes her grip and looks down again with resolve. Minimal camera motion, natural blinking and breathing. Clear deliberate decision, she remains safely standing.',
'08':'The courier travels forward and downward from the left ledge into the open shaft on the right. Starting in the shown leap, she descends naturally under gravity, both hands holding the seed against her chest, knees bending slightly, coat trailing upward. Camera tracks downward alongside her. No flying upward, no somersault, no extra limbs.',
'09':'Low close shot. The crouching courier releases the small cracked golden seed onto the dark core surface; her right fingers draw back slowly. A thin amber ripple spreads outward from the exact contact point across the stone. She watches the seed, then looks upward as soft light rises. Only one seed.',
'10':'Low-angle shot of the same courier rising gently upward, her feet lift higher and her coat hangs below her. Both hands are empty. Massive stone blocks slowly rise around her at different depths, no collisions. Camera tilts upward with her. Stable anatomy and face, smooth gravity reversal.',
'11':'Extreme wide climax. The tiny burgundy courier rises at center while the enormous dark sky shell breaks further open. Colossal slabs peel outward slowly, smaller fragments move away from the central opening, broad pale daylight expands through the gap. Camera pulls back smoothly to reveal scale. No fireball, no strobe, keep heroine tiny.',
'12':'Rear medium-wide shot. The courier walks calmly away through the restored city, both hands empty, coat swaying naturally. Gentle rain falls downward, water flows in the fountains, pale green leaves move softly, warm windows glow steadily. Camera follows at walking speed, hopeful restrained ending.'}
base=json.loads((ROOT/'outputs/H3-Quality-768p-32step-API.json').read_text(encoding='utf-8'))
prepare='--prepare-only' in sys.argv
for sid in [a for a in sys.argv[1:] if not a.startswith('--')] or ['02','11','01','03','04','06','07','09','10','12','05','08']:
    final=OUT/'clips'/f'{sid}-720p.mp4'
    recordpath=OUT/'records'/f'{sid}-history.json'
    if not prepare and final.exists() and recordpath.exists():print('REUSE',sid,flush=True);continue
    q={'queue_running':[],'queue_pending':[]} if prepare else req('/queue')
    while q['queue_running'] or q['queue_pending']:
        print('WAIT_QUEUE',sid,flush=True);time.sleep(30);q=req('/queue')
    if not prepare and final.exists() and recordpath.exists():print('REUSE',sid,flush=True);continue
    source=ASSETS/'frames'/f'{sid}.png';shutil.copy2(source,INPUT/f'{sid}.png')
    p=json.loads(json.dumps(base));p.pop('4');p.pop('13');p['14']['inputs'].pop('audio',None)
    p['6']['inputs'].update(prompt=COMMON+PROMPTS[sid],width=1280,height=736,length=124,first_frame=['16',0])
    p['8']['inputs']['steps']=25;p['10']['inputs']['noise_seed']=26100800+int(sid)
    p['15']['inputs']['filename_prefix']=f'video/FeishengV7_{sid}_720p25'
    p['16']={'class_type':'LoadImage','inputs':{'image':f'FeishengV7/{sid}.png'}}
    if sid in ('05','08'):
        shutil.copy2(ASSETS/'reference/character.png',INPUT/'character.png')
        p['1']['inputs']['unet_name']='minimax_h3_ref2va_pruned_int8_convrot.safetensors'
        p['17']={'class_type':'LoadImage','inputs':{'image':'FeishengV7/character.png'}}
        p['18']={'class_type':'ImageScale','inputs':{'image':['17',0],'upscale_method':'lanczos','width':384,'height':576,'crop':'center'}}
        p['19']={'class_type':'ImageScale','inputs':{'image':['16',0],'upscale_method':'lanczos','width':704,'height':384,'crop':'center'}}
        p['6']={'class_type':'MiniMaxH3ReferenceToVideo','inputs':{'clip':['2',0],'vae':['3',0],'prompt':'<Picture 1> defines the exact courier identity and costume. <Picture 2> defines scene, composition and action direction. '+COMMON+PROMPTS[sid],'width':1280,'height':736,'length':124,'ref_image_size':'match','ref_images.ref_image_0':['18',0],'ref_images.ref_image_1':['19',0]}}
        p['20']={'class_type':'MiniMaxH3AddGuide','inputs':{'positive':['6',0],'latent':['6',1],'vae':['3',0],'image':['16',0],'frame_idx':0}}
        p['9']['inputs']['conditioning']=['20',0]
        if sid=='08':
            if not prepare:shutil.copy2(OUT/'clips/05-720p.mp4',INPUT/'05-motion.mp4')
            p['21']={'class_type':'LoadVideo','inputs':{'file':'FeishengV7/05-motion.mp4'}}
            p['22']={'class_type':'GetVideoComponents','inputs':{'video':['21',0]}}
            p['23']={'class_type':'ImageFromBatch','inputs':{'image':['22',0],'batch_index':68,'length':56}}
            p['24']={'class_type':'ImageScale','inputs':{'image':['23',0],'upscale_method':'lanczos','width':448,'height':256,'crop':'center'}}
            p['6']['inputs']['ref_videos.ref_video_0']=['24',0]
            p['6']['inputs']['prompt']+=' <Video 1> is a continuity reference for the same courier running left to right and the coat trailing behind. Carry that identity and fabric momentum into the voluntary downward leap shown in Picture 2. Do not repeat running on a floor; she is now leaving the ledge and descending.'
    if sid=='11':
        p['6']['inputs'].pop('first_frame')
        p['6']['inputs']['last_frame']=['16',0]
        p['6']['inputs']['prompt']=COMMON+'Begin with a nearly closed dark stone sky shell over the city and a tiny burgundy courier at center. A narrow seam of light appears, then the giant ceiling fractures outward, reaching the open sky composition shown by the final reference. '+PROMPTS[sid]
    (OUT/'workflows'/f'{sid}-API.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
    if prepare:
        print('PREPARED',sid,flush=True)
        continue
    previous=OUT/'records'/f'{sid}-submitted.json'
    submission=req('/prompt',{'prompt':p,'client_id':'codex-feisheng-v7'})
    if submission.get('node_errors'):raise RuntimeError(submission)
    pid=submission['prompt_id'];previous.write_text(json.dumps(submission,indent=2));print('SUBMITTED',sid,pid,flush=True)
    (WORK/'active.json').write_text(json.dumps(dict(shot=sid,prompt_id=pid,started=time.time(),width=1280,height=736,steps=25)),encoding='utf-8')
    while True:
        time.sleep(10)
        stat=resources()
        with (WORK/'resources.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(stat)+'\n')
        if stat['ram_free_mib']<768 or stat['commit_free_mib']<1536 or stat['temp']>=84:
            running=req('/queue')['queue_running']
            if any(x[1]==pid for x in running):req('/interrupt',{})
            (WORK/'resource-stop.json').write_text(json.dumps(stat,indent=2))
            raise RuntimeError('Stopped own generation due to resource threshold; no process was killed')
        history=req('/history/'+pid)
        if pid not in history:continue
        record=history[pid]
        if record.get('status',{}).get('completed') or record.get('status',{}).get('status_str')=='error':break
    recordpath.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    if record['status']['status_str']!='success':raise RuntimeError(record['status'])
    f=record['outputs']['15']['images'][0]
    generated=Path('<LOCAL_PATH>/output')/f.get('subfolder','')/f['filename']
    native=OUT/'clips'/f'{sid}-native.mp4';shutil.copy2(generated,native)
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(native),'-vf','crop=1280:720:0:8,setsar=1','-an','-c:v','libx264','-preset','slow','-crf','16','-threads','2','-color_primaries','bt709','-color_trc','iec61966-2-1','-colorspace','bt709','-movflags','+faststart',str(final)],check=True)
    ts={a:b.get('timestamp') for a,b in record['status']['messages']}
    manifest=dict(shot=sid,prompt_id=pid,generation_seconds=(ts['execution_success']-ts['execution_start'])/1000,native_size=[1280,736],output_size=[1280,720],frames=124,fps=24,steps=25,seed=p['10']['inputs']['noise_seed'],model=p['1']['inputs']['unet_name'],reference_mode='image-and-video-reference-plus-first-guide' if sid=='08' else 'two-image-reference-plus-first-guide' if sid=='05' else 'text-plus-last-guide' if sid=='11' else 'image-to-video',sha256=hashlib.sha256(final.read_bytes()).hexdigest())
    (OUT/'records'/f'{sid}-manifest.json').write_text(json.dumps(manifest,indent=2))
    print('COMPLETE',sid,manifest['generation_seconds'],flush=True)
print('WORKFLOWS_PREPARED' if prepare else 'ALL_REQUESTED_SHOTS_COMPLETE',flush=True)
