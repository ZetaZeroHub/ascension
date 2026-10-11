from pathlib import Path
import json
R=Path(__file__).resolve().parents[3]
s=(R/'work/feisheng/v7/render_shots.py').read_text(encoding='utf-8')
s=s.replace("WORK=ROOT/'work/feisheng/v7'","WORK=ROOT/'work/feisheng/extra-v8'").replace("OUT=ROOT/'outputs/Feisheng-MV/成片-v7'","OUT=ROOT/'outputs/Feisheng-MV/补充镜头-v8'").replace("ASSETS=ROOT/'outputs/Feisheng-MV/独立分镜-v6'","ASSETS=OUT").replace('FeishengV7','FeishengExtraV8').replace('codex-feisheng-v7','codex-feisheng-extra-v8')
a=s.index('PROMPTS={');b=s.index('\nbase=',a)
prompts={
'13':'Extreme close-up of the right hand and the single cracked golden seed beside the burgundy coat. The fingers slowly tighten around the seed with deliberate resolve, then hold still. The thin amber crack softly brightens once and fades back. Slight coat movement from wind. Camera makes a tiny slow push in. Same one hand with five fingers, preserve exact seed shape and gold wrist bracelet. No hand changing sides, no new objects.',
'14':'Low side closeup of the courier boots and lower burgundy coat at the broken bridge. The leading boot carefully slides a few centimeters forward and plants firmly just before the edge. A few small stone chips crumble from the edge and fall downward into the abyss. The coat hem moves in the breeze. Camera stays low and steady, bridge remains rigid. She stays on the bridge, both boots retain contact with solid ground. One continuous tense detail shot.',
'15':'Ground-level macro view of the single cracked gold seed resting stationary in the center of the dark stone core. One thin amber circular ripple travels slowly outward across the engraved concentric rings. Tiny grains of dust gently rise a few centimeters as the ripple passes. The seed remains stationary and keeps its shape. Very slow backward dolly reveals more of the ripple. Restrained soft light, no explosion, no flicker, no new seed or people.',
'16':'Medium close rear three-quarter portrait of the same courier in the restored city. She slowly turns her head over her right shoulder toward camera, pauses with a faint relieved smile and a quiet exhale. Her short black bob and burgundy coat move gently in the breeze. Warm city lights, water and pale foliage stay in soft background focus. Camera moves gently closer. Her face remains identical throughout, no dialogue, hands out of frame, no seed.'}
s=s[:a]+'PROMPTS='+repr(prompts)+s[b:]
a=s.index(" or ['02'");b=s.index(':\n    final=',a);s=s[:a]+" or ['13','14','15','16']"+s[b:]
a=s.index("    if sid in ('05','08'):");b=s.index("    (OUT/'workflows'",a);s=s[:a]+s[b:]
s=s.replace("source=ASSETS/'frames'/f'{sid}.png';shutil.copy2(source,INPUT/f'{sid}.png')", "source=ASSETS/'frames'/f'{sid}.png'\n    while not source.exists():\n        print('WAIT_FRAME',sid,flush=True);time.sleep(10)\n    shutil.copy2(source,INPUT/f'{sid}.png')")
# Recover already submitted work rather than submit a duplicate after a runner restart.
old="submission=req('/prompt',{'prompt':p,'client_id':'codex-feisheng-extra-v8'})"
new="""submission=None
    if previous.exists():
        saved=json.loads(previous.read_text());saved_pid=saved['prompt_id']
        h=req('/history/'+saved_pid);q=req('/queue')
        if saved_pid in h or any(x[1]==saved_pid for x in q['queue_running']+q['queue_pending']):submission=saved
    if submission is None:submission=req('/prompt',{'prompt':p,'client_id':'codex-feisheng-extra-v8'})"""
s=s.replace(old,new)
# Publish durable minimal progress as each clip finishes.
s=s.replace("print('COMPLETE',sid,manifest['generation_seconds'],flush=True)","print('COMPLETE',sid,manifest['generation_seconds'],flush=True)\n    (WORK/'active.json').write_text(json.dumps(dict(shot=sid,state='completed',time=time.time())))")
(R/'work/feisheng/extra-v8/render_shots.py').write_text(s,encoding='utf-8')
(R/'outputs/Feisheng-MV/补充镜头-v8/prompts.json').write_text(json.dumps(prompts,ensure_ascii=False,indent=2),encoding='utf-8')
print('SETUP_OK')
