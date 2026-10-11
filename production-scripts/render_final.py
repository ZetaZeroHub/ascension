import json, subprocess, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT/'remotion'
OUT=ROOT.parents[1]/'outputs/Feisheng-MV'
NODE=Path('<USER_HOME>/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
CLI=PROJECT/'node_modules/@remotion/cli/remotion-cli.js'
target=OUT/'飞升-MV-1080p.mp4'
assert not target.exists(), 'Keep an existing render intact'
begin=time.monotonic()
with (OUT/'成片渲染.log').open('w',encoding='utf-8') as log:
    subprocess.run([str(NODE),str(CLI),'render','src/index.ts','Feisheng',str(target),'--concurrency=1','--gl=swangle','--crf=16','--audio-codec=aac','--audio-bitrate=320k','--log=error'],cwd=PROJECT,stdout=log,stderr=subprocess.STDOUT,check=True)
report={'render_seconds':time.monotonic()-begin,'bytes':target.stat().st_size,'file':target.name,'concurrency':1,'crf':16,'profile':'balanced Lanczos 1080p'}
(OUT/'成片渲染实测.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False),flush=True)
