import json,sys
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'剪映MCP编辑清单-普通导出-v2.json').read_text(encoding='utf-8'))
for track in manifest['tracks']:
    for item in track.get('segments',[]):
        if 'source' not in item:continue
        name=Path(item['source']).name
        candidates=[root/name,root/'剪辑片段'/name,root/'全部视频素材'/name,root.parent/name]
        target=next((p for p in candidates if p.is_file()),None)
        if target is None:raise FileNotFoundError(name)
        item['source']=str(target)
manifest['draft']['name']=sys.argv[1] if len(sys.argv)>1 else '飞升-MV-节拍衔接精修-v2-迁移副本'
target=root/'剪映MCP编辑清单-重定位-v2.json'
target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(target)
