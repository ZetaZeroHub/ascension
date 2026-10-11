"""Create bounded release media ZIPs and a reproducible checksum manifest."""
from pathlib import Path
import json,zipfile,hashlib,argparse

def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 root=Path(__file__).resolve().parents[1];a.output.mkdir(parents=True,exist_ok=True)
 extensions={'.png','.jpg','.jpeg','.webp','.mp4','.m4a','.wav'}
 files=sorted(p for folder in ['archive','editing','media'] for p in (root/'site'/folder).rglob('*') if p.is_file() and p.suffix.lower() in extensions)
 groups=[];current=[];size=0
 for f in files:
  if current and size+f.stat().st_size>450*1024**2:groups.append(current);current=[];size=0
  current.append(f);size+=f.stat().st_size
 if current:groups.append(current)
 packs=[]
 for i,items in enumerate(groups,1):
  name=f'ascension-media-{i:02d}.zip';out=a.output/name
  with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
   for f in items:z.write(f,f.relative_to(root).as_posix())
  with zipfile.ZipFile(out) as z:
   bad=z.testzip()
   if bad:raise SystemExit('CRC failure: '+bad)
  packs.append({'name':name,'bytes':out.stat().st_size,'files':len(items),'sha256':digest(out),'url':'https://github.com/ZetaZeroHub/ascension/releases/download/v1.0.0/'+name})
  print(name,round(out.stat().st_size/1024**2,1),'MiB',flush=True)
 data={'version':'v1.0.0','packs':packs,'total_media_files':len(files)}
 (root/'docs/media-release.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
 (a.output/'SHA256SUMS.txt').write_text(''.join(f"{x['sha256']}  {x['name']}\n" for x in packs),encoding='utf-8')
 print('Packed',len(files),'media files',flush=True)
if __name__=='__main__':main()
