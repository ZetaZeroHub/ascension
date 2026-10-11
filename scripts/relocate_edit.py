"""Resolve the sanitized MCP edit manifest against the downloaded media tree."""
from pathlib import Path
import argparse,json,re

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 if a.output.exists():raise SystemExit('Output already exists; choose a new filename.')
 root=Path(__file__).resolve().parents[1]/'site/editing'
 source=root/'剪映MCP编辑清单-普通导出-v2.json'
 data=json.loads(source.read_text(encoding='utf-8'));lookup={}
 for p in root.rglob('*'):
  if p.is_file():lookup.setdefault(p.name,[]).append(p)
 errors=[]
 def visit(v,key=''):
  if isinstance(v,dict):return {k:visit(x,k) for k,x in v.items()}
  if isinstance(v,list):return [visit(x,key) for x in v]
  if isinstance(v,str) and key in {'source','path','file_path','audio_path','video_path'}:
   name=re.split(r'[/\\]',v)[-1];matches=lookup.get(name,[])
   if len(matches)==1:return str(matches[0].resolve())
   errors.append(f'{name}: {len(matches)} matches')
  return v
 data=visit(data)
 if errors:raise SystemExit('Cannot resolve media:\n'+'\n'.join(sorted(set(errors))))
 data['draft']['name']='Ascension-relocated'
 a.output.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Wrote relocated editing manifest. Run your MCP dry_run before creating a new draft.')
if __name__=='__main__':main()
