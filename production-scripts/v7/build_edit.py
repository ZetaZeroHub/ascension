from pathlib import Path
import json,shutil,subprocess,sys,hashlib,urllib.request
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'outputs/Feisheng-MV/成片-v7'
PROJECT=ROOT/'work/feisheng/v7/remotion'
OLD=ROOT/'work/feisheng/remotion-v2'
NODE=Path('<USER_HOME>/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
PROJECT.mkdir(parents=True,exist_ok=True)
for name in ['package.json','pnpm-lock.yaml','pnpm-workspace.yaml','tsconfig.json','remotion.config.ts','eslint.config.mjs']:
    if (OLD/name).exists():shutil.copy2(OLD/name,PROJECT/name)
for folder in ['src','public/audio','public/graded']:(PROJECT/folder).mkdir(parents=True,exist_ok=True)
shutil.copy2(OLD/'public/audio/feisheng-master.wav',PROJECT/'public/audio/feisheng-master.wav')
if not (PROJECT/'node_modules').exists():
    subprocess.run(['powershell.exe','-NoProfile','-Command',f"New-Item -ItemType Junction -Path '{PROJECT/'node_modules'}' -Target '{ROOT/'work/feisheng/remotion/node_modules'}' | Out-Null"],check=True)
# Continuous source time per clip; insert crops are explicitly editorial details, not new generated camera angles.
plan=[(0,4.8,'01','wide'),(4.8,9.6,'02','wide'),(9.6,14.4,'03','wide'),(14.4,16.8,'02','eye'),(16.8,19.2,'03','wide'),(19.2,24,'04','wide'),(24,26.4,'04','detail'),(26.4,28.8,'05','wide'),(28.8,31.2,'05','detail'),(31.2,33.6,'06','wide'),(33.6,36,'05','wide'),(36,38.4,'06','wide'),(38.4,43.2,'07','wide'),(43.2,45.6,'06','wide'),(45.6,48,'07','eye'),(48,50.4,'07','detail'),(50.4,54,'08','wide'),(54,57.6,'08','wide'),(57.6,60,'09','detail'),(60,62.4,'09','wide'),(62.4,64.8,'10','wide'),(64.8,66,'09','wide'),(66,67.2,'10','detail'),(67.2,69.6,'10','wide'),(69.6,70.8,'11','wide'),(70.8,72,'10','wide'),(72,73.2,'11','wide'),(73.2,74.4,'10','wide'),(74.4,76.8,'11','wide'),(76.8,81.6,'12','wide'),(81.6,84,'12','detail'),(84,86.4,'12','wide'),(86.4,90,'12','wide'),(90,2282/24,'12','wide')]
# Preserve chronology: finish the run before arriving, and finish activation before ascent.
plan=[(a,b,'05' if a==31.2 else '06' if a==33.6 else '09' if a==62.4 else '10' if a==64.8 else sid,
       'detail' if a==62.4 else view) for a,b,sid,view in plan]
segments=[];totals={};offsets={}
for a,b,sid,view in plan:
    start=round(a*24);end=round(b*24);n=end-start
    segments.append(dict(id=f'{len(segments)+1:02d}',source=sid,view=view,fromFrame=start,duration=n))
    totals[sid]=totals.get(sid,0)+n
assert sum(s['duration'] for s in segments)==2282
for sid,n in totals.items():
    if '--prepare-only' in sys.argv:continue
    src=OUT/'clips'/f'{sid}-720p.mp4';target=PROJECT/'public/graded'/f'{sid}.mp4'
    if not src.exists() or not (OUT/'records'/f'{sid}-manifest.json').exists():
        if '--prepare-ready' in sys.argv:continue
        raise RuntimeError(f'Missing generated clip {sid}')
    factor=(n-1)/123
    # Mild B-derived finishing trim; reference images already carry warm-grey color.
    timing=f'{factor:.12f}*(PTS-STARTPTS)'
    if sid=='11':
        # Keep the small first opening in the two anticipation inserts; reveal on 74.4 s.
        anticipation=sum(s['duration'] for s in segments if s['source']=='11' and s['fromFrame']<round(74.4*24))
        timing=f'if(lte(N,21),N*{anticipation}/21,{anticipation}+(N-21)*{n-1-anticipation}/102)/(24*TB)'
    vf=f'tpad=stop_mode=clone:stop_duration=0.5,setpts=\'{timing}\',minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,tpad=stop_mode=clone:stop_duration=1,curves=all=\'0/0.01 0.2/0.2 0.5/0.515 0.8/0.795 1/0.96\':interp=pchip,eq=saturation=0.96,setsar=1'
    filter_args=['-vf',vf,'-filter_threads','2']
    if sid=='08':
        # Ref2VA inserted an unwanted running shot in frames 26-95. Keep only genuine airborne motion.
        pieces=[]
        counts=[s['duration'] for s in segments if s['source']=='08']
        assert len(counts)==2
        for i,((start,end),count) in enumerate(zip([(0,26),(96,124)],counts)):
            rate=(count-1)/(end-start-1)
            pieces.append(f'[p{i}]trim=start_frame={start}:end_frame={end},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.5,setpts={rate:.12f}*(PTS-STARTPTS),minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,tpad=stop_mode=clone:stop_duration=1,trim=end_frame={count},settb=AVTB,setpts=N/(24*TB)[v{i}]')
        vf='[0:v]split=2[p0][p1];'+';'.join(pieces)+";[v0][v1]concat=n=2:v=1:a=0,fps=24,curves=all='0/0.01 0.2/0.2 0.5/0.515 0.8/0.795 1/0.96':interp=pchip,eq=saturation=0.96,setsar=1[v]"
        filter_args=['-filter_complex',vf,'-filter_complex_threads','2','-map','[v]']
        (OUT/'选片记录.json').write_text(json.dumps(dict(shot='08',retained_native_frames_inclusive=[[0,25],[96,123]],discarded_native_frames_inclusive=[[26,95]],output_frames=counts,cut_seconds=54,reason='Reference-video conditioning inserted a running-on-bridge shot during the fall. Removed that discontinuity; retained departure and downward descent, independently retimed to the two musical phrases.'),ensure_ascii=False,indent=2),encoding='utf-8')
    fingerprint=hashlib.sha256((str(src.stat().st_mtime_ns)+str(src.stat().st_size)+vf+str(n)).encode()).hexdigest()
    cache=target.with_suffix('.json')
    if target.exists() and cache.exists() and json.loads(cache.read_text()).get('fingerprint')==fingerprint:
        print('RETIME_CACHED',sid,flush=True)
        continue
    print('RETIME_START',sid,n,flush=True)
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-threads','2','-i',str(src),*filter_args,'-frames:v',str(n),'-r','24','-an','-c:v','libx264','-preset','slow','-crf','15','-threads','2','-color_primaries','bt709','-color_trc','iec61966-2-1','-colorspace','bt709',str(target)],check=True)
    spec=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,r_frame_rate','-of','json',str(target)]))['streams'][0]
    assert int(spec['nb_frames'])==n and spec['r_frame_rate']=='24/1',(sid,spec,n)
    cache.write_text(json.dumps(dict(fingerprint=fingerprint,frames=n,filter=vf),indent=2))
    print('RETIME_DONE',sid,flush=True)
for s in segments:
    sid=s['source'];s['trimBefore']=offsets.get(sid,0);offsets[sid]=s['trimBefore']+s['duration']
(PROJECT/'src/timeline.json').write_text(json.dumps(segments,indent=2),encoding='utf-8')
(OUT/'timeline.json').write_text(json.dumps(segments,indent=2),encoding='utf-8')
(PROJECT/'src/index.ts').write_text("import {registerRoot} from 'remotion';\nimport {Root} from './Root';\nregisterRoot(Root);\n",encoding='utf-8')
shutil.copy2(Path(__file__).with_name('Film.tsx'),PROJECT/'src/Root.tsx')
subprocess.run([str(NODE),'node_modules/typescript/bin/tsc','--noEmit'],cwd=PROJECT,check=True)
if '--prepare-only' in sys.argv or '--prepare-ready' in sys.argv:
    print('EDIT_PROJECT_PREPARED_AND_TYPECHECKED',flush=True)
    sys.exit(0)
final=OUT/'飞升-MV-720p-v7-待视听复核.mp4'
try:
    with urllib.request.urlopen('http://127.0.0.1:8000/queue',timeout=10) as response:queue=json.load(response)
    if not queue['queue_running'] and not queue['queue_pending']:
        request=urllib.request.Request('http://127.0.0.1:8000/free',data=json.dumps(dict(unload_models=True,free_memory=True)).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=10):pass
        print('IDLE_MODEL_MEMORY_RELEASE_REQUESTED',flush=True)
except Exception as exc:
    print('OPTIONAL_MEMORY_RELEASE_SKIPPED',type(exc).__name__,flush=True)
subprocess.run(['<LOCAL_PATH>/python.exe',str(Path(__file__).with_name('validate_sources.py'))],check=True)
subprocess.run([str(NODE),'node_modules/@remotion/cli/remotion-cli.js','render','src/index.ts','FeishengV7',str(final),'--overwrite','--concurrency=1','--gl=swangle','--crf=16','--audio-codec=aac','--audio-bitrate=320k','--log=error'],cwd=PROJECT,check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(final)]))
v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert v['width']==1280 and v['height']==720 and int(v['nb_frames'])==2282
assert a['sample_rate']=='48000'
subprocess.run(['ffmpeg','-v','error','-i',str(final),'-f','null','-'],check=True)
with (OUT/'响度检查.log').open('w') as log:subprocess.run(['ffmpeg','-hide_banner','-i',str(final),'-af','ebur128=peak=true','-f','null','-'],stderr=log,stdout=subprocess.DEVNULL,check=True)
(OUT/'technical-validation.json').write_text(json.dumps(probe,indent=2),encoding='utf-8')
subprocess.run(['<LOCAL_PATH>/python.exe',str(Path(__file__).with_name('validate_film.py'))],check=True)
print('RENDERED_CANDIDATE',final,flush=True)
