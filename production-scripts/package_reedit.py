import json, shutil, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
P=ROOT/'remotion-v2';OUT=ROOT.parents[1]/'outputs/Feisheng-MV/重剪版-v2'
v=json.loads((OUT/'成片验证.json').read_text(encoding='utf-8'))
check=json.loads((OUT/'重剪约束验证.json').read_text(encoding='utf-8'))
note=(OUT/'重剪说明.md').read_text(encoding='utf-8')
note+=f"\n## 验证结果\n\n最终 2282 帧完整解码，音频检测偏移 {v['audio_offset_ms']} ms，与原母带相关系数 {v['audio_vs_master_correlation']:.6f}。综合响度 {v['integrated_lufs']} LUFS，真峰值 {v['true_peak_dbfs']} dBTP。14 段原生素材与母带哈希和原版相同；38 秒前抽样画面最大平均像素差 {check['early_frame_max_mae_255']:.4f}/255（导出编码误差）。\n"
(OUT/'重剪说明.md').write_text(note,encoding='utf-8');(P/'制作说明.md').write_text(note,encoding='utf-8')
archive=OUT/'飞升-节奏重剪-v2-可编辑工程.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
    for folder in ['src','public']:
        for f in (P/folder).rglob('*'):
            if f.is_file():z.write(f,'Feisheng-v2/'+f.relative_to(P).as_posix())
    for f in P.iterdir():
        if f.is_file():z.write(f,'Feisheng-v2/'+f.name)
    for f in (ROOT/'remotion/generation').glob('*manifest.json'):z.write(f,'Feisheng-v2/generation/'+f.name)
    for f in (OUT.parent/'工作流').glob('*.json'):z.write(f,'Feisheng-v2/ComfyUI-workflows/'+f.name)
    for f in (ROOT/'analysis/reedit-v2').glob('*.json'):z.write(f,'Feisheng-v2/analysis/'+f.name)
    z.write(OUT/'重剪约束验证.json','Feisheng-v2/analysis/constraint-validation.json')
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'file':archive.name,'bytes':archive.stat().st_size},ensure_ascii=False),flush=True)
