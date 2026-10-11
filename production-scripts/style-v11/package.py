"""Package the completed style assets and local workflow retention, without weights."""
import hashlib
import json
import re
import shutil
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "outputs/Feisheng-MV"
STYLES = PROJECT / "风格实验-v11"
RETAIN = PROJECT / "ComfyUI留存-v11"
WORK = ROOT / "work/feisheng/style-v11"
ARCHIVE = PROJECT / "飞升-四风格分镜与短片-v11.zip"


def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def local_links():
    bad = []
    for directory in [STYLES, RETAIN]:
        for page in directory.rglob('*.html'):
            contents = page.read_text(encoding='utf-8')
            for url in re.findall(r'(?:href|src)="([^"]+)"', contents):
                part = urlsplit(url)
                if part.scheme or not part.path: continue
                target = (page.parent / unquote(part.path)).resolve()
                # This archive is created immediately after index publication.
                if target == ARCHIVE.resolve(): continue
                if not target.exists(): bad.append({'page': str(page), 'url': url})
    assert not bad, bad


def main():
    assert json.loads((STYLES / 'review/final-audit.json').read_text(encoding='utf-8'))['passed']
    assert json.loads((RETAIN / '留存检查.json').read_text(encoding='utf-8'))['missing_inputs'] == []
    runtime = json.load(urllib.request.urlopen('http://127.0.0.1:8000/system_stats', timeout=30))
    (RETAIN / 'configs/system-stats.json').write_text(json.dumps(runtime, ensure_ascii=False, indent=2), encoding='utf-8')
    shutil.copy2(WORK / 'package.py', RETAIN / 'scripts/package.py')
    # Publish an archive link only after all required components exist. The actual
    # file is written atomically below; no placeholder or duplicate ZIP entries.
    index = STYLES / 'index.html'
    body = index.read_text(encoding='utf-8')
    if ARCHIVE.name not in body:
        body = body.replace('<div class="source">', '<p><a href="../'+ARCHIVE.name+'" download>下载完整素材与工作流包</a></p><div class="source">', 1)
        index.write_text(body, encoding='utf-8')
    local_links()
    text_suffixes = {'.json', '.md', '.py', '.ps1', '.html', '.csv', '.yaml', '.txt', '.log'}
    files = sorted(p for directory in [STYLES, RETAIN] for p in directory.rglob('*') if p.is_file() and p.name != 'SHA256SUMS.txt')
    leaked = []
    for p in files:
        if p.suffix.lower() in text_suffixes:
            text = p.read_text(encoding='utf-8-sig', errors='replace')
            if re.search(r'\bsk_[0-9a-fA-F]{24,}\b', text): leaked.append(str(p))
    assert not leaked, 'Credential pattern in archive text files: ' + repr(leaked)
    for directory in [STYLES, RETAIN]:
        entries = sorted(p for p in directory.rglob('*') if p.is_file() and p.name != 'SHA256SUMS.txt')
        sums = '\n'.join(digest(p)+'  '+p.relative_to(directory).as_posix() for p in entries) + '\n'
        (directory / 'SHA256SUMS.txt').write_text(sums, encoding='utf-8')
    files = sorted(p for directory in [STYLES, RETAIN] for p in directory.rglob('*') if p.is_file())
    temp = ARCHIVE.with_suffix('.building.zip')
    with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED, compresslevel=2) as z:
        for p in files: z.write(p, p.relative_to(PROJECT).as_posix())
    with zipfile.ZipFile(temp) as z:
        assert len(z.namelist()) == len(set(z.namelist())) == len(files)
        assert z.testzip() is None
        assert sum(n.startswith('风格实验-v11/clips/') and n.endswith('.mp4') for n in z.namelist()) == 14
        assert sum(n.startswith('风格实验-v11/frames/') and n.endswith('.png') for n in z.namelist()) == 12
        assert sum(n.startswith('ComfyUI留存-v11/API/') and n.endswith('.json') for n in z.namelist()) == 68
        assert sum(n.startswith('ComfyUI留存-v11/工作流/') and n.endswith('.json') for n in z.namelist()) == 68
    temp.replace(ARCHIVE)
    report = {'archive': str(ARCHIVE), 'bytes': ARCHIVE.stat().st_size, 'sha256': digest(ARCHIVE),
              'members': len(files), 'crc_verified': True, 'local_html_links_verified': True,
              'credential_pattern_scan_passed': True, 'full_weights_in_archive': False,
              'weight_retention': 'Actual model files remain at the verified installed <LOCAL_PATH>/COMFY and <LOCAL_PATH>/... paths in 模型清单.json',
              'browser_qa_performed': False, 'reason': 'User chose file saving only.'}
    (PROJECT / '飞升-v11-交付检查.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__': main()
