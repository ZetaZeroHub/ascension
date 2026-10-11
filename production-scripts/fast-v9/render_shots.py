import json,time,urllib.request,urllib.error,shutil,sys,subprocess,ctypes,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'work/feisheng/fast-v9'
OUT=ROOT/'outputs/Feisheng-MV/补充与舞蹈-v9'
ASSETS=OUT
INPUT=Path('<LOCAL_PATH>/FeishengFastV9')
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
PROMPTS={'13': 'Extreme close-up of the right hand and the single cracked golden seed beside the burgundy coat. The fingers slowly tighten around the seed with deliberate resolve, then hold still. The thin amber crack softly brightens once and fades back. Slight coat movement from wind. Camera makes a tiny slow push in. Same one hand with five fingers, preserve exact seed shape and gold wrist bracelet. No hand changing sides, no new objects.', '14': 'Low side closeup of the courier boots and lower burgundy coat at the broken bridge. The leading boot carefully slides a few centimeters forward and plants firmly just before the edge. A few small stone chips crumble from the edge and fall downward into the abyss. The coat hem moves in the breeze. Camera stays low and steady, bridge remains rigid. She stays on the bridge, both boots retain contact with solid ground. One continuous tense detail shot.', '15': 'Ground-level macro view of the single cracked gold seed resting stationary in the center of the dark stone core. One thin amber circular ripple travels slowly outward across the engraved concentric rings. Tiny grains of dust gently rise a few centimeters as the ripple passes. The seed remains stationary and keeps its shape. Very slow backward dolly reveals more of the ripple. Restrained soft light, no explosion, no flicker, no new seed or people.', '16': 'Medium close rear three-quarter portrait of the same courier in the restored city. She slowly turns her head over her right shoulder toward camera, pauses with a faint relieved smile and a quiet exhale. Her short black bob and burgundy coat move gently in the breeze. Warm city lights, water and pale foliage stay in soft background focus. Camera moves gently closer. Her face remains identical throughout, no dialogue, hands out of frame, no seed.'}
base=json.loads((ROOT/'outputs/H3-Quality-768p-32step-API.json').read_text(encoding='utf-8'))
base['5']={'class_type':'LoraLoaderModelOnly','inputs':{'model':['1',0],'lora_name':'minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors','strength_model':1.0}}
base['8']['inputs']['model']=['5',0]
base['9']['inputs']['model']=['5',0]
DANCE_COMMON='Single uninterrupted cinematic dance shot in a black studio, same adult East Asian woman with short black bob, matte burgundy coat, black trousers and black boots. Restrained cool cyan shadows, neutral skin, moving soft light streaks behind the dancer, fine film texture. Coherent human anatomy, grounded feet, stable face, no extra limbs, no cuts, no captions, no graphic overlays. Dance phrase at approximately 100 beats per minute, sharp accents with controlled pauses. White sculptures stay rigid. '
PROMPTS.update(json.loads((WORK/'dance-prompts.json').read_text(encoding='utf-8')))
prepare='--prepare-only' in sys.argv
for sid in [a for a in sys.argv[1:] if not a.startswith('--')] or ['13','14','15','16','17','18','19','20','21','22']:
    final=OUT/'clips'/f'{sid}-720p.mp4'
    recordpath=OUT/'records'/f'{sid}-history.json'
    if not prepare and final.exists() and recordpath.exists():print('REUSE',sid,flush=True);continue
    q={'queue_running':[],'queue_pending':[]} if prepare else req('/queue')
    while q['queue_running'] or q['queue_pending']:
        print('WAIT_QUEUE',sid,flush=True);time.sleep(30);q=req('/queue')
    if not prepare and final.exists() and recordpath.exists():print('REUSE',sid,flush=True);continue
    source=ASSETS/'frames'/f'{sid}.png'
    while not source.exists():
        print('WAIT_FRAME',sid,flush=True);time.sleep(10)
    shutil.copy2(source,INPUT/f'{sid}.png')
    p=json.loads(json.dumps(base));p.pop('4');p.pop('13');p['14']['inputs'].pop('audio',None)
    p['6']['inputs'].update(prompt=(COMMON if int(sid)<17 else DANCE_COMMON)+PROMPTS[sid],width=640,height=384,length=124,first_frame=['16',0])
    p['8']['inputs']['steps']=8;p['10']['inputs']['noise_seed']=26100800+int(sid)
    p['15']['inputs']['filename_prefix']=f'video/FeishengFastV9_{sid}_fast8'
    p['16']={'class_type':'LoadImage','inputs':{'image':f'FeishengFastV9/{sid}.png'}}
    (OUT/'workflows'/f'{sid}-API.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
    if prepare:
        print('PREPARED',sid,flush=True)
        continue
    previous=OUT/'records'/f'{sid}-submitted.json'
    submission=None
    if previous.exists():
        saved=json.loads(previous.read_text());saved_pid=saved['prompt_id']
        h=req('/history/'+saved_pid);q=req('/queue')
        if saved_pid in h or any(x[1]==saved_pid for x in q['queue_running']+q['queue_pending']):submission=saved
    if submission is None:submission=req('/prompt',{'prompt':p,'client_id':'codex-feisheng-fast-v9'})
    if submission.get('node_errors'):raise RuntimeError(submission)
    pid=submission['prompt_id'];previous.write_text(json.dumps(submission,indent=2));print('SUBMITTED',sid,pid,flush=True)
    (WORK/'active.json').write_text(json.dumps(dict(shot=sid,prompt_id=pid,started=time.time(),width=640,height=384,steps=8)),encoding='utf-8')
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
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(native),'-vf','crop=640:360:0:12,scale=1280:720:flags=lanczos,setsar=1','-an','-c:v','libx264','-preset','slow','-crf','16','-threads','2','-color_primaries','bt709','-color_trc','iec61966-2-1','-colorspace','bt709','-movflags','+faststart',str(final)],check=True)
    ts={a:b.get('timestamp') for a,b in record['status']['messages']}
    manifest=dict(shot=sid,prompt_id=pid,generation_seconds=(ts['execution_success']-ts['execution_start'])/1000,native_size=[640,384],output_size=[1280,720],frames=124,fps=24,steps=8,seed=p['10']['inputs']['noise_seed'],model=p['1']['inputs']['unet_name'],reference_mode='image-and-video-reference-plus-first-guide' if sid=='08' else 'two-image-reference-plus-first-guide' if sid=='05' else 'text-plus-last-guide' if sid=='11' else 'image-to-video',sha256=hashlib.sha256(final.read_bytes()).hexdigest())
    (OUT/'records'/f'{sid}-manifest.json').write_text(json.dumps(manifest,indent=2))
    print('COMPLETE',sid,manifest['generation_seconds'],flush=True)
    (WORK/'active.json').write_text(json.dumps(dict(shot=sid,state='completed',time=time.time())))
print('WORKFLOWS_PREPARED' if prepare else 'ALL_REQUESTED_SHOTS_COMPLETE',flush=True)
