import gc, importlib.util, json, time, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
hold=ROOT/'analysis/09-first-hold.png';original=ROOT/'remotion/public/frames/09-first.png'
try:
    while not (ROOT/'generation/08-manifest.json').exists():time.sleep(5)
    q=json.load(urllib.request.urlopen('http://127.0.0.1:8000/queue'))
    if q['queue_running'] or q['queue_pending']:raise RuntimeError('Queue must be idle for SR benchmark')
    req=urllib.request.Request('http://127.0.0.1:8000/free',data=b'{"unload_models":true,"free_memory":true}',headers={'Content-Type':'application/json'})
    urllib.request.urlopen(req).close()
    print('H3 idle, models released for isolated SR benchmark',flush=True)
    import torch, av, numpy as np
    from PIL import Image
    torch.set_num_threads(4)
    spec=importlib.util.spec_from_file_location('sr',ROOT.parents[1]/'outputs/Export-H3-1080p.py')
    sr=importlib.util.module_from_spec(spec);spec.loader.exec_module(sr)
    start=time.monotonic()
    model=sr.upscale_model('<LOCAL_PATH>/4x-UltraSharp.pth')
    times=[]
    with av.open(str(ROOT/'remotion/public/retimed/06.mp4')) as c:
        for i,f in enumerate(c.decode(video=0)):
            if i not in [15,85,150]:continue
            sr.guard();a=f.to_ndarray(format='rgb24');left=(a.shape[1]-round(a.shape[0]*16/9))//2;a=a[:,left:left+round(a.shape[0]*16/9)]
            t=time.monotonic();sharp=sr.sharpen_tiled(a,model).resize((1920,1080),Image.Resampling.LANCZOS);torch.cuda.synchronize();elapsed=time.monotonic()-t
            base=Image.fromarray(a).resize((1920,1080),Image.Resampling.LANCZOS)
            blend=Image.blend(base,sharp,.6)
            blend.save(ROOT/'analysis'/f'sr-bench-{i}.png')
            if i==85:base.save(ROOT/'analysis/sr-bench-base-85.png')
            times.append(elapsed);print(json.dumps({'frame':i,'seconds':elapsed}),flush=True)
    result={'method':'4x-UltraSharp tiled FP16, 60% blend, resized to 1080p','seconds_per_frame':times,'warm_estimated_full_seconds':sum(times[1:])/2*2282,'total_seconds':time.monotonic()-start}
    (ROOT/'analysis/sr-benchmark.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result),flush=True)
    del model;gc.collect();torch.cuda.empty_cache()
finally:
    if hold.exists():hold.replace(original)
    print('H3 scene 09 input restored',flush=True)
