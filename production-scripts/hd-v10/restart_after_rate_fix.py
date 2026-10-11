"""One-time continuation of the currently running batch after its known fps validation error."""
import ctypes,json,subprocess,time,os
from pathlib import Path
R=Path(__file__).resolve().parents[3];W=R/'work/feisheng/hd-v10';O=R/'outputs/Feisheng-MV/高清素材-v10'
INITIAL_PID=8044
SYNCHRONIZE=0x00100000
k=ctypes.windll.kernel32
k.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];k.OpenProcess.restype=ctypes.c_void_p
k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong];k.WaitForSingleObject.restype=ctypes.c_ulong
k.CloseHandle.argtypes=[ctypes.c_void_p]
handle=k.OpenProcess(SYNCHRONIZE,False,INITIAL_PID)
if not handle:
    print('Original process handle unavailable; no automatic restart',flush=True);raise SystemExit(1)
try:
    while True:
        result=k.WaitForSingleObject(handle,30000)
        if result==0:break
        if result!=258:raise RuntimeError(f'WaitForSingleObject {result}')
finally:k.CloseHandle(handle)
failure=O/'failure.json'
if not failure.exists():
    print('Original batch exited without an fps validation error; no restart',flush=True);raise SystemExit(0)
data=json.loads(failure.read_text(encoding='utf-8'))
trace=data.get('traceback','')
if 'validate(smooth,248,48' not in trace:
    print('Different failure; no restart:',data.get('error'),flush=True);raise SystemExit(0)
status=json.loads((O/'status.json').read_text(encoding='utf-8'))
if status.get('completed'):
    print('Unexpected completed clips in failed batch; inspect first',flush=True);raise SystemExit(1)
time.sleep(2)
shutil=None
log=W/'batch-restart.stdout.log';err=W/'batch-restart.stderr.log'
with log.open('w',encoding='utf-8') as out,err.open('w',encoding='utf-8') as e:
    p=subprocess.Popen(['<LOCAL_PATH>/python.exe','-u',str(W/'batch.py')],cwd=R,stdout=out,stderr=e,creationflags=subprocess.CREATE_NO_WINDOW)
print('Started fixed batch process',p.pid,flush=True)
