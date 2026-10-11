"""Package website media and optional image inputs; exclude source clips and weights."""
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
 images={'.png','.jpg','.jpeg','.webp'}
 website=sorted(p for folder in ['archive','editing','media'] for p in (root/'site'/folder).rglob('*') if p.is_file() and (p.suffix.lower() in images or p==root/'site/media/ascension-720p.mp4'))
 inputs=sorted(p for p in (root/'reproduction/inputs').rglob('*') if p.is_file() and p.suffix.lower() in images)
 packs=[]
 for name,files,optional in [('ascension-website-media.zip',website,False),('ascension-comfy-input-images.zip',inputs,True)]:
  out=a.output/name
  with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
   for f in files:z.write(f,f.relative_to(root).as_posix())
  with zipfile.ZipFile(out) as z:
   if z.testzip():raise SystemExit('CRC failure: '+name)
  packs.append({'name':name,'bytes':out.stat().st_size,'files':len(files),'optional':optional,'sha256':digest(out),'url':'https://github.com/ZetaZeroHub/ascension/releases/download/v1.0.0/'+name})
  print(name,round(out.stat().st_size/1024**2,1),'MiB',flush=True)
 data={'version':'v1.0.0','packs':packs,'policy':'Only static art and the featured film on the website. Original input images are optional, outside the web root. No source video/audio or weights.'}
 (root/'docs/media-release.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
 (a.output/'SHA256SUMS.txt').write_text(''.join(f"{x['sha256']}  {x['name']}\n" for x in packs),encoding='utf-8')
if __name__=='__main__':main()
