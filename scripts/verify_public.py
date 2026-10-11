"""Validate the static publication; no network requests or execution of archived code."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import re,json,argparse

class Links(HTMLParser):
 def __init__(self):super().__init__();self.refs=[]
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if v and k in {'src','href','poster'}:self.refs.append((tag,k,v))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path);a=ap.parse_args()
 root=Path(__file__).resolve().parents[1];site=root/'site';problems=[];missing=[];json_count=0
 text_ext={'.html','.css','.js','.json','.md','.py','.ts','.tsx','.ps1','.yaml','.yml','.txt','.csv'}
 patterns={'credential':r'\b(?:sk_[A-Za-z0-9]{24,}|sk-[A-Za-z0-9_-]{24,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b','private_home':r'(?i)[A-Z]:[/\\]+Users[/\\]+(?!PUBLIC)[^/\\\s"<>]+','private_key':r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----'}
 for f in root.rglob('*'):
  if not f.is_file() or '.git' in f.parts or f.suffix not in text_ext:continue
  if f.name.startswith('local-'):continue
  s=f.read_text(encoding='utf-8-sig',errors='replace')
  for name,pat in patterns.items():
   if re.search(pat,s):problems.append({'file':f.relative_to(root).as_posix(),'type':name})
  if f.suffix=='.json':
   try:json.loads(s);json_count+=1
   except ValueError:problems.append({'file':f.relative_to(root).as_posix(),'type':'invalid_json'})
  if f.suffix=='.html' and site in f.parents:
   h=Links();h.feed(s)
   for tag,key,url in h.refs:
    u=urlsplit(url)
    if u.scheme or u.netloc or not u.path:continue
    p=unquote(u.path);dest=(site/p.lstrip('/') if p.startswith('/') else f.parent/p)
    if not dest.exists():missing.append({'file':f.relative_to(site).as_posix(),'tag':tag,'attribute':key,'url':url})
 result={'json_files_validated':json_count,'html_pages':len(list(site.rglob('*.html'))),'security_findings':problems,'missing_html_references':missing}
 if a.output:a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'json_files':json_count,'security_findings':len(problems),'missing_references':len(missing)}))
 if problems or missing:raise SystemExit(1)
if __name__=='__main__':main()
