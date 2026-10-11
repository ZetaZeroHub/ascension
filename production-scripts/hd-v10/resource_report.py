"""Summarize observed hardware headroom for the local 720p MiniMax H3 batch."""
import json
from collections import defaultdict
from pathlib import Path

root = Path(__file__).resolve().parents[3]
work = root / 'work/feisheng/hd-v10'
out = root / 'outputs/Feisheng-MV/高清素材-v10'
samples = defaultdict(list)
for line in (work / 'resources.jsonl').read_text(encoding='utf-8').splitlines():
    entry = json.loads(line)
    samples[entry['shot']].append(entry)
report = {}
for sid, rows in sorted(samples.items()):
    report[sid] = {
        'samples': len(rows),
        'max_gpu_temperature_c': max(row['temp'] for row in rows),
        'min_ram_free_mib': min(row['ram_free_mib'] for row in rows),
        'min_commit_free_mib': min(row['commit_free_mib'] for row in rows),
        'max_gpu_memory_used_mib': max(row['gpu_mib'] for row in rows),
        'mean_gpu_utilization_percent': round(sum(row['gpu_util'] for row in rows) / len(rows), 1),
    }
target = out / '审查/运行资源汇总.json'
target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'shots_observed': len(report), 'overall_max_gpu_temperature_c': max(x['max_gpu_temperature_c'] for x in report.values()), 'overall_min_commit_free_mib': min(x['min_commit_free_mib'] for x in report.values())}, ensure_ascii=False))
