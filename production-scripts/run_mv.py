import copy,json,time,urllib.request,urllib.error,hashlib,shutil,sys
from pathlib import Path
root=Path(__file__).resolve().parent;workspace=root.parent.parent
plan=json.loads((root/'src/data/storyboard.json').read_text(encoding='utf-8'))
base=json.loads((workspace/'outputs/H3-Quality-768p-32step-API.json').read_text(encoding='utf-8'))
ui=json.loads((workspace/'outputs/H3-Quality-768p-32step.json').read_text(encoding='utf-8'))
public=root/'remotion/public';dest=workspace/'outputs/Feisheng-MV'
for p in [root/'generation',dest/'工作流',dest/'首尾帧',public/'clips']:p.mkdir(parents=True,exist_ok=True)
def req(path,data=None):
    request=urllib.request.Request('http://127.0.0.1:8000'+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request,timeout=60) as r:return json.load(r)
    except urllib.error.HTTPError as e:raise RuntimeError(e.read().decode())
def make_ui(s,p):
    w=copy.deepcopy(ui);w['nodes']=[n for n in w['nodes'] if n['id'] not in (4,13)]
    w['links']=[l for l in w['links'] if l[1] not in (4,13) and l[3] not in (4,13)]
    nextid=max(l[0] for l in w['links'])+1
    for nid,kind,y in [(16,'first',100),(17,'last',500)]:
        n={'id':nid,'type':'LoadImage','pos':[-500,y],'size':[310,300],'flags':{},'order':0,'mode':0,'inputs':[],'outputs':[{'name':'IMAGE','type':'IMAGE','links':[],'slot_index':0},{'name':'MASK','type':'MASK','links':[],'slot_index':1}],'properties':{'Node name for S&R':'LoadImage'},'widgets_values':[f"Feisheng/{s['id']}-{kind}.png",'image'],'title':kind.upper()+' FRAME'}
        w['nodes'].append(n)
        target=next(n for n in w['nodes'] if n['id']==6)
        slot=next(i for i,x in enumerate(target['inputs']) if x['name']==kind+'_frame')
        w['links'].append([nextid,nid,0,6,slot,'IMAGE']);nextid+=1
    for n in w['nodes']:
        for i in n.get('inputs',[]):i['link']=None
        for o in n.get('outputs',[]):o['links']=[]
        if n['id']==6:n['widgets_values']=[s['motion_prompt'],704,384,124];n['title']=s['id']+' '+s['title']
        elif n['id']==8:n['widgets_values']=['simple',20,1]
        elif n['id']==10:n['widgets_values']=[s['seed'],'fixed']
        elif n['id']==14:n['widgets_values']=[24,8,'sRGB','none']
        elif n['id']==15:n['widgets_values']=[f"video/Feisheng_{s['id']}",'mp4','h264','re-encode',16]
    for lid,src,ss,dst,ds,typ in w['links']:
        next(n for n in w['nodes'] if n['id']==src)['outputs'][ss]['links'].append(lid)
        next(n for n in w['nodes'] if n['id']==dst)['inputs'][ds]['link']=lid
    w['last_node_id']=17;w['last_link_id']=nextid-1
    return w
for s in plan['scenes']:
    sid=s['id'];output=public/s['native_video']
    if output.exists() and (root/'generation'/f'{sid}-history.json').exists():
        print('REUSE',sid,flush=True);continue
    paths=[public/s['first_image'],public/s['last_image']]
    print('WAIT_FRAMES',sid,flush=True)
    while not all(p.exists() for p in paths):time.sleep(5)
    for image in paths:
        shutil.copy2(image,Path('<LOCAL_PATH>/Feisheng')/image.name)
        shutil.copy2(image,dest/'首尾帧'/image.name)
    p=copy.deepcopy(base)
    del p['4'];del p['13'];p['14']['inputs'].pop('audio',None)
    p['6']['inputs'].update(prompt=s['motion_prompt'],width=704,height=384,length=124,first_frame=['16',0],last_frame=['17',0])
    p['8']['inputs']['steps']=20;p['10']['inputs']['noise_seed']=s['seed']
    p['14']['inputs']['codec']='none';p['15']['inputs']['filename_prefix']=f'video/Feisheng_{sid}'
    p['16']={'class_type':'LoadImage','inputs':{'image':f'Feisheng/{sid}-first.png'}}
    p['17']={'class_type':'LoadImage','inputs':{'image':f'Feisheng/{sid}-last.png'}}
    w=make_ui(s,p)
    (dest/'工作流'/f'{sid}-API.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
    (dest/'工作流'/f'{sid}.json').write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')
    (Path('<LOCAL_PATH>/workflows')/f'Feisheng-{sid}.json').write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')
    submitted=req('/prompt',{'prompt':p,'client_id':'codex-feisheng','extra_data':{'extra_pnginfo':{'workflow':w}}})
    (root/'generation'/f'{sid}-submitted.json').write_text(json.dumps(submitted,indent=2))
    if submitted.get('node_errors'):raise RuntimeError(submitted)
    pid=submitted['prompt_id'];print('SUBMITTED',sid,pid,flush=True)
    while True:
        time.sleep(10);history=req('/history/'+pid)
        if pid not in history:continue
        record=history[pid]
        if record.get('status',{}).get('completed') or record.get('status',{}).get('status_str')=='error':break
    (root/'generation'/f'{sid}-history.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    if record['status']['status_str']!='success':raise RuntimeError(record['status'])
    f=record['outputs']['15']['images'][0]
    source=Path('<LOCAL_PATH>/output')/f.get('subfolder','')/f['filename']
    shutil.copy2(source,output)
    ts={a:b.get('timestamp') for a,b in record['status']['messages']}
    elapsed=(ts['execution_success']-ts['execution_start'])/1000
    manifest={'scene':sid,'prompt_id':pid,'model':p['1']['inputs']['unet_name'],'seed':s['seed'],'steps':20,'native_size':[704,384],'frames':124,'generation_seconds':elapsed,'file':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'first_sha256':hashlib.sha256(paths[0].read_bytes()).hexdigest(),'last_sha256':hashlib.sha256(paths[1].read_bytes()).hexdigest()}
    (root/'generation'/f'{sid}-manifest.json').write_text(json.dumps(manifest,indent=2))
    print('COMPLETE',sid,elapsed,flush=True)
print('ALL_SCENES_COMPLETED',flush=True)
