import json, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
P=ROOT/'remotion-v2';OUT=ROOT.parents[1]/'outputs/Feisheng-MV/重剪版-v2'
NODE='<USER_HOME>/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
CLI=P/'node_modules/@remotion/cli/remotion-cli.js'
target=OUT/'飞升-MV-1080p-节奏重剪-v2.mp4'
assert not target.exists()
begin=time.monotonic()
with (OUT/'渲染日志.log').open('w',encoding='utf-8') as log:
    subprocess.run([NODE,str(CLI),'render','src/index.ts','Feisheng',str(target),'--concurrency=1','--gl=swangle','--crf=16','--audio-codec=aac','--audio-bitrate=320k','--log=error'],cwd=P,stdout=log,stderr=subprocess.STDOUT,check=True)
result={'render_seconds':time.monotonic()-begin,'bytes':target.stat().st_size,'file':target.name}
(OUT/'导出耗时.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False),flush=True)
