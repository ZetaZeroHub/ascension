"""Download pinned release media packs, verify SHA256, and extract safely."""
from pathlib import Path
import urllib.request,hashlib,json,zipfile,argparse,shutil

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--list',action='store_true');a=ap.parse_args()
 root=Path(__file__).resolve().parents[1]
 packs=json.loads((root/'docs/media-release.json').read_text(encoding='utf-8'))['packs']
 for item in packs:
  print(item['name'],round(item['bytes']/1024**2,1),'MiB')
  if a.list:continue
  cache=root/'downloads';cache.mkdir(exist_ok=True);target=cache/item['name']
  if not target.exists() or sha(target)!=item['sha256']:
   temp=target.with_suffix('.partial')
   req=urllib.request.Request(item['url'],headers={'User-Agent':'Ascension-media/1.0'})
   with urllib.request.urlopen(req,timeout=90) as response,temp.open('wb') as f:shutil.copyfileobj(response,f)
   if sha(temp)!=item['sha256']:raise SystemExit('Download checksum mismatch: '+item['name'])
   temp.replace(target)
  with zipfile.ZipFile(target) as z:
   for info in z.infolist():
    dst=(root/info.filename).resolve()
    if not dst.is_relative_to(root.resolve()) or not info.filename.startswith('site/'):raise SystemExit('Unsafe ZIP entry')
   for info in z.infolist():
    if info.is_dir():continue
    dst=root/info.filename
    if dst.exists():
     with z.open(info) as f:expected=hashlib.sha256(f.read()).hexdigest()
     if sha(dst)!=expected:raise SystemExit('Refusing to overwrite changed local asset: '+info.filename)
    else:z.extract(info,root)
  print('Verified and extracted',item['name'])
if __name__=='__main__':main()
