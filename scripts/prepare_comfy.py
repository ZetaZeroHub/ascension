"""Copy archived ComfyUI workflows and inputs without overwriting different files."""
from pathlib import Path
import argparse,hashlib,shutil

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--comfy-root',type=Path,required=True);p.add_argument('--dry-run',action='store_true');a=p.parse_args()
 source=Path(__file__).resolve().parents[1]/'site/archive/ComfyUI留存-v11'
 jobs=[]
 for folder,target in [(source.parents[2]/'reproduction/inputs','input'),(source/'工作流','user/default/workflows/Ascension')]:
  files=[x for x in folder.rglob('*') if x.is_file()]
  if not files:raise SystemExit('Missing input images: run python scripts/fetch_media.py --inputs first.')
  for f in files:jobs.append((f,a.comfy_root/target/f.relative_to(folder)))
 conflicts=[str(d) for s,d in jobs if d.exists() and digest(s)!=digest(d)]
 if conflicts:raise SystemExit('Refusing to overwrite different files:\n'+'\n'.join(conflicts))
 print(f'{len(jobs)} files; {sum(d.exists() for _,d in jobs)} already identical; dry_run={a.dry_run}')
 if not a.dry_run:
  for s,d in jobs:
   if d.exists():continue
   d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s,d)
  print('Installed. Open ComfyUI and select Ascension from the workflow browser.')
if __name__=='__main__':main()
