"""Gate the final HD package on all source videos and individual visual reviews."""
import json,hashlib,zipfile,time,sys,csv
from pathlib import Path
import av
R=Path(__file__).resolve().parents[3];O=R/'outputs/Feisheng-MV/高清素材-v10';OLD=R/'outputs/Feisheng-MV/补充与舞蹈-v9'
items=json.loads((OLD/'素材清单.json').read_text(encoding='utf-8'))
prompts=json.loads((OLD/'视频提示词.json').read_text(encoding='utf-8'))
reviews_file=O/'审查/视觉验收.json'
reviews=json.loads(reviews_file.read_text(encoding='utf-8')) if reviews_file.exists() else {}
errors=[];data=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def probe(path,expect_fps,expect_frames,expect_width,expect_height):
    with av.open(str(path)) as c:
        v=c.streams.video[0];a=list(c.streams.audio)
        timestamps=[float(frame.pts*frame.time_base) for frame in c.decode(video=0)]
        cadence_ok=len(timestamps)==expect_frames and all(abs(t-index/expect_fps)<1e-5 for index,t in enumerate(timestamps))
        return dict(fps=float(v.average_rate),frames=len(timestamps),width=v.width,height=v.height,audio_streams=len(a),cadence_ok=cadence_ok,color_tags=[v.color_primaries,v.color_trc,v.colorspace])
for item in items:
    sid=item['shot'];man=O/'records'/f'{sid}-manifest.json';wf=O/'workflows'/f'{sid}-API.json';h=O/'records'/f'{sid}-history.json'
    missing=[path.name for path in (man,wf,h) if not path.exists()]
    if missing:errors.append(f'{sid}: missing {", ".join(missing)}');continue
    m=json.loads(man.read_text(encoding='utf-8'));p=json.loads(wf.read_text(encoding='utf-8'));history=json.loads(h.read_text(encoding='utf-8'))
    master=O/m['master_file'];smooth=O/m['smooth_file'];native=O/'原生视频'/f"{sid}-{item['name']}.mp4";frame=O/'frames'/f'{sid}.png'
    expected_manifest={'shot':sid,'name':item['name'],'steps':25,'turbo_lora':False,'native_size':[1280,736],'output_size':[1280,720],'source_frames':124,'source_fps':24,'output_frames':248,'output_fps':48,'duration':124/24,'seed':item['seed'],'verified':True}
    if any(m.get(key)!=value for key,value in expected_manifest.items()):errors.append(f'{sid}: manifest spec mismatch')
    if any(m.get('qa_'+kind,{}).get('black_frames')!=[] for kind in ('master','smooth')):errors.append(f'{sid}: black frame QA mismatch')
    if p['6']['inputs'].get('width')!=1280 or p['6']['inputs'].get('height')!=736 or p['6']['inputs'].get('length')!=124 or p['8']['inputs']['steps']!=25 or p['10']['inputs']['noise_seed']!=item['seed'] or '5' in p:errors.append(f'{sid}: workflow spec mismatch')
    if p['1']['inputs'].get('unet_name')!='minimax_h3_fl2va_pruned_int8_convrot.safetensors' or p['2']['inputs'].get('clip_name')!='qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors' or p['3']['inputs'].get('vae_name')!='minimax_h3_video_vae_int8_convrot.safetensors':errors.append(f'{sid}: model mismatch')
    if p['6']['inputs'].get('first_frame')!=['16',0] or p['16']['inputs'].get('image')!=f'FeishengHDV10/{sid}.png' or p['6']['inputs'].get('prompt')!=prompts[sid]:errors.append(f'{sid}: reference or prompt mismatch')
    if history.get('status',{}).get('status_str')!='success':errors.append(f'{sid}: ComfyUI history not success')
    if len(history.get('prompt',[]))<2 or history['prompt'][1]!=m['prompt_id']:errors.append(f'{sid}: manifest/history prompt ID mismatch')
    if len(history.get('prompt',[]))<3 or history['prompt'][2]!=p:errors.append(f'{sid}: saved workflow differs from executed graph')
    for path,digest in [(master,m['master_sha256']),(smooth,m['smooth_sha256']),(native,m['native_sha256']),(frame,m['source_reference_sha256'])]:
        if not path.exists() or sha(path)!=digest:errors.append(f'{sid}: missing/hash mismatch {path.name}')
    if sha(OLD/'frames'/f'{sid}.png')!=m['source_reference_sha256']:errors.append(f'{sid}: first frame differs from approved v9 reference')
    if not master.exists() or not smooth.exists() or not native.exists():continue
    for path,rate,num,width,height in [(native,24,124,1280,736),(master,24,124,1280,720),(smooth,48,248,1280,720)]:
        info=probe(path,rate,num,width,height)
        if info!=dict(fps=rate,frames=num,width=width,height=height,audio_streams=0,cadence_ok=True,color_tags=[1,13,1]):errors.append(f'{sid}: stream mismatch {path.name} {info}')
    review_images=[f'{sid}-24fps-contact.jpg',f'{sid}-48fps-contact.jpg',f'{sid}-v9-v10-对照.jpg',f'{sid}-插帧奇数帧.jpg',f'{sid}-强运动插帧三联.jpg']
    if sid in ('16','21'):review_images.append(f'{sid}-面部连续性.jpg')
    for name in review_images:
        if not (O/'审查'/name).exists():errors.append(f'{sid}: missing review image {name}')
    review=reviews.get(sid)
    if not isinstance(review,dict) or review.get('accepted') is not True or not review.get('notes') or not review.get('method'):errors.append(f'{sid}: no accepted visual review')
    data.append(dict(id=sid,name=item['name'],steps=m['steps'],native_resolution=m['native_size'],master_24fps=m['master_file'],smooth_48fps=m['smooth_file'],duration_seconds=m['duration'],generation_seconds=m['generation_seconds'],master_sha256=m['master_sha256'],smooth_sha256=m['smooth_sha256'],visual=review))
report={'passed':len(errors)==0 and len(data)==10,'checked':len(data),'required':10,'errors':errors,'data':data,'checked_at':time.time()}
(O/'审查/最终验收.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(passed=report['passed'],checked=report['checked'],errors=errors),ensure_ascii=False))
if not report['passed']:raise SystemExit(1)
with (O/'剪辑素材索引.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['镜头','名称','24fps母版','48fps插帧','时长秒','生成耗时秒','画面审查备注'])
    for x in data:w.writerow([x['id'],x['name'],x['master_24fps'],x['smooth_48fps'],x['duration_seconds'],x['generation_seconds'],x['visual']['notes']])
archive=O.parent/'飞升-高清10镜头-720p-25步-48fps.zip'
source_files=[f for f in sorted(O.rglob('*')) if f.is_file()]
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED) as z:
    for f in source_files:z.write(f,Path(O.name)/f.relative_to(O))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(source_files)
    for f in source_files:
        name=(Path(O.name)/f.relative_to(O)).as_posix()
        assert z.getinfo(name).file_size==f.stat().st_size,name
package=dict(archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),files=len(source_files),crc_verified=True)
(O.parent/'飞升-高清10镜头-压缩包校验.json').write_text(json.dumps(package,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(package,ensure_ascii=False))
