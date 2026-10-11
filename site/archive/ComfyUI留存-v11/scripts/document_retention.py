import html
import json
import shutil
import zipfile
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "outputs/Feisheng-MV"
OUT = PROJECT / "ComfyUI留存-v11"
STYLES = PROJECT / "风格实验-v11"
WORK = ROOT / "work/feisheng/style-v11"
rows = json.loads((OUT / "工作流索引.json").read_text(encoding="utf-8"))
models = json.loads((OUT / "模型清单.json").read_text(encoding="utf-8"))
audit = json.loads((STYLES / "review/technical-audit.json").read_text(encoding="utf-8"))
audit["paired_comparison_visually_reviewed"] = True
audit["confidence"] = {"asset_retention_and_generation": "high", "aesthetic_preference": "medium", "browser_loading": "not tested by user choice"}
(STYLES / "review/final-audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
stats = audit["generation_seconds"]
readme = f'''# 飞升 · ComfyUI 本地留存

本项目截至 v11 的 68 份 API 工作流、68 份原生节点版工作流、76 项输入素材和 61 份历史执行记录已留存。ComfyUI 文件列表接口已确认全部节点版可被发现。67 份使用当前原生节点；1 份早期 Image Studio 文生图工作流依赖自定义节点，作为历史版本保留，当前专用原生后端禁用了自定义节点。

## 在 ComfyUI Web 打开

1. 手动访问 http://127.0.0.1:8000/ 。本轮按你的要求只保存文件，没有继续操作网页或自动切换画布。
2. 左侧「工作流」刷新列表，打开 `Feisheng-MV / 风格-v11 / 16-C.json`，或任意其它分镜。也可以把本目录「工作流」下的 JSON 拖进 ComfyUI 画布。`-API.json` 是精确执行记录，节点版 JSON 更适合编辑。
3. 首帧、模型和 LoRA 都已放在本机对应目录。点击 ComfyUI 的「运行」，从队列/底部执行面板查看实时步骤和结果。注意：工作流保存的输出是原生视频，720p 裁切缩放另由脚本完成。
4. 本轮 14 个任务均已完成，留存时队列为 0。完成结果在当前 ComfyUI 历史中；重启后旧历史未自动恢复，但本地 JSON 快照会一直保留。

ComfyUI 实际保存目录：`<LOCAL_PATH>/Feisheng-MV`。

## 版本对应

| 文件夹 | 数量 | 内容 |
|---|---:|---|
| 基础试验 | 6 | 本机低显存测试、艺术试片、32 步测试及早期文生图 |
| 早期红绸 | 14 | 首尾帧、红绸意象版本 |
| 剧情-v7 | 12 | 定稿英雄旅程；含两组角色/视频参考与引导帧 |
| 补充-v8 | 1 | 早期追加镜头尝试，留存参数，不代表全部验收通过 |
| 快速-v9 | 10 | 追加场景与舞蹈的快速版 |
| 高清-v10 | 10 | 1280×736 原生、25 步的 720p 母版配置 |
| 快速档示例 | 1 | 5 分钟目标档示例 |
| 风格-v11 | 14 | 12 段四风格试片，另加两组关闭风格 LoRA 对照 |

API 不改写，原节点文件另存于 `source-ui/`。每一版的种子、步数、分辨率、首尾/参考帧与节点连线都保留。执行完成与否应以对应历史 `status_str` 为准。

## 模型保留方式

8 个 H3 生成权重/适配器仍在 `<LOCAL_PATH>/COMFY`；超分对照使用的 4x-UltraSharp 仍在原 E 盘模型目录。总计 9 项。没有复制约 59 GiB 的生成权重到 C 盘；ZIP 包保存路径、文件大小、配置、版本与校验记录，模型实体继续使用本机原目录。`模型清单.json` 逐项给出实际绝对路径。

新装的 Realism People 与 Looping Sketch 两个 LoRA 已按固定 Hugging Face revision 下载，并复验完整 SHA256。已有的大模型复验了文件存在、大小和 safetensors 头部，未重新扫描整份大权重，也未把头部哈希当成整文件哈希。

当前后端：ComfyUI 0.37.4，前端 1.52.7，RTX 4060 Ti 8GB / 32GB RAM；dynamic VRAM、fast disk、关闭 pinned memory、VRAM headroom 2.5GB、cache-ram 6 8、关闭动态预览。配置快照在 `configs/`。原生工作流使用的节点无需新装插件；历史 Image Studio 的节点代码另存于 `plugins/`。

## 风格试片与参数

v11 已完成 12 张参考首帧、12 段风格短片和 2 段 LoRA 关闭对照。每段 73 帧、24fps、约 3.04 秒，Turbo 8 步；640×384 原生生成，中央裁切至 640×360 后 Lanczos 缩放到 1280×720。参考试片无声，供放入已有音乐剪辑。没有补帧。

单段 ComfyUI 执行时间实测 {stats['min']/60:.2f}–{stats['max']/60:.2f} 分钟，中位数 {stats['median']/60:.2f} 分钟，14 段执行累计 {stats['total']/60:.2f} 分钟；不包含首帧重绘、模型下载、审查与打包时间。峰值 GPU 温度 {audit['resources']['peak_gpu_celsius']}℃，最低可用系统内存 {audit['resources']['min_free_ram_mib']} MiB。

图片材质由参考重绘产生；LoRA 参与本地视频运动生成。不要把全部风格转化归因于 LoRA。`16-C` 与 `19-D` 的开关对照保持首帧、提示词、种子、步数一致，只变风格适配器及输出文件名。

蓝晒舞蹈 19-D 在约 0.4 秒后由深蓝摄影棚转为奶白留白，作为材质转化试验保留；关闭 Sketch 的版本维持深色背景。C 更适合保留原人物和剧情质感，A 适合纸感静段，B 适合地貌与高潮意象，D 适合记忆/幻象插镜。审美判断置信度：中。

## 后续保存与进度

当前生成脚本 `work/feisheng/style-v11/render.py` 已改为提交前同时保存 API 与节点版，并把节点图附入生成 metadata。脚本提交不再使用与网页不匹配的固定 client_id，采样进度事件可广播给本地已连接客户端；从网页直接运行会使用网页自身的连接。这个修改没有重新排队，也没有改变已生成的 14 段。网页实际载入/显示未在本轮复测。

脚本原位置：`{WORK.as_posix()}`；留存目录 `scripts/` 中是源代码快照，不能随意移动后假定路径不变。`Start-H3.ps1` 可从本目录启动同一原生低内存后端；若 8000 已有 ComfyUI，则直接复用，不关闭已有进程。它不会启动浏览器。

素材和工作流留存置信度：高，见 `留存检查.json` 与风格素材的 `review/final-audit.json`。
'''
# Calculate model size from current verified manifest rather than a rounded guess.
gib = sum(m['bytes'] for m in models) / 1024**3
readme = readme.replace('约 59 GiB', f'约 {gib:.2f} GiB')
(OUT / "使用说明.md").write_text(readme, encoding="utf-8")

ps = '''$ErrorActionPreference = 'Stop'
try {
    $null = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/queue' -TimeoutSec 3
    Write-Output 'ComfyUI is already available on port 8000. Existing process reused.'
    exit 0
} catch {
    # No process is stopped or replaced.
}
$taskPython = '<LOCAL_PATH>/python.exe'
$taskCode = '<USER_HOME>/AppData/Local/Comfy-Desktop/ComfyUI-Installs/ComfyUI'
$taskConfig = Join-Path $PSScriptRoot 'configs/instance-model-paths.yaml'
$taskLog = Join-Path $PSScriptRoot 'launch-logs'
New-Item -ItemType Directory -Path $taskLog -Force | Out-Null
$taskStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$taskArgs = @('-s', 'ComfyUI/main.py', '--base-directory', '<LOCAL_PATH>/newcomfyui', '--user-directory', '<LOCAL_PATH>/user', '--input-directory', '<LOCAL_PATH>/input', '--output-directory', '<LOCAL_PATH>/output', '--temp-directory', ('"' + (Join-Path $taskLog 'temp') + '"'), '--extra-model-paths-config', ('"' + $taskConfig + '"'), '--port', '8000', '--disable-all-custom-nodes', '--disable-api-nodes', '--enable-dynamic-vram', '--fast-disk', '--disable-pinned-memory', '--vram-headroom', '2.5', '--cache-ram', '6', '8', '--preview-method', 'none')
$taskProcess = Start-Process -FilePath $taskPython -ArgumentList $taskArgs -WorkingDirectory $taskCode -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskLog ($taskStamp + '.stdout.log')) -RedirectStandardError (Join-Path $taskLog ($taskStamp + '.stderr.log')) -PassThru
$taskProcess.Id | Set-Content -LiteralPath (Join-Path $taskLog ($taskStamp + '.pid'))
Write-Output ('Started ComfyUI process ' + $taskProcess.Id + '. Open http://127.0.0.1:8000/ manually.')
'''
(OUT / "Start-H3.ps1").write_text(ps, encoding="utf-8-sig")
plugin = Path("<LOCAL_PATH>/ComfyUI-MiniMax-H3-Image-Studio")
(OUT / "plugins").mkdir(exist_ok=True)
with zipfile.ZipFile(OUT / "plugins/历史-ComfyUI-MiniMax-H3-Image-Studio.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for p in plugin.rglob('*'):
        if p.is_file() and p.suffix.lower() in ['.py', '.js', '.json', '.toml', '.md', '.txt'] and not any(part in ['.git', '__pycache__', 'node_modules'] for part in p.relative_to(plugin).parts):
            z.write(p, p.relative_to(plugin).as_posix())
css = 'body{margin:0;background:#0b1016;color:#e1e8ee;font:16px/1.7 system-ui,"Microsoft YaHei",sans-serif}main{max-width:1250px;margin:auto;padding:36px 24px}h1{font-size:32px}a{color:#b9dfed;text-underline-offset:4px}table{width:100%;border-collapse:collapse;margin:24px 0}td,th{padding:12px;text-align:left;border-bottom:1px solid #2c3945}code{overflow-wrap:anywhere}details{background:#141e28;padding:16px;margin:24px 0;border-radius:8px}summary{cursor:pointer}.links{display:flex;gap:20px;flex-wrap:wrap}small{color:#a7b7c5}'
body = '<h1>飞升 · 模型与工作流留存</h1><p>68 份节点版 + 68 份 API · 76 项输入素材 · 61 份历史记录 · 9 项模型路径</p><p>已保存到 ComfyUI 文件列表；本轮依照你的选择未继续操作网页。当前风格试片 14 段全部完成，队列为空。</p><div class="links"><a href="使用说明.md">详细使用说明</a><a href="模型清单.json">完整模型清单</a><a href="工作流索引.json">逐项工作流与依赖</a><a href="留存检查.json">留存检查记录</a><a href="../风格实验-v11/index.html">四风格分镜与短片</a><a href="http://127.0.0.1:8000/" target="_blank" rel="noopener">手动打开 ComfyUI</a></div><p>打开 ComfyUI 左侧「工作流」，进入 <code>Feisheng-MV → 风格-v11</code>。或下载下方 JSON，拖入画布后运行；通过队列/执行面板查看实时进度。</p><h2>本次风格试片工作流</h2><table><tr><th>编号</th><th>节点版</th><th>API 原始参数</th></tr>'
for row in rows:
    if row['group'] != '风格-v11': continue
    body += '<tr><td>'+html.escape(row['name'].removesuffix('.json'))+'</td><td><a href="'+quote(row['retained_native'], safe='/')+'" download>下载 / 拖入 ComfyUI</a></td><td><a href="'+quote(row['retained_api'], safe='/')+'" download>API</a></td></tr>'
body += '</table><h2>本机模型实体</h2><p>模型留在实际安装目录，未把大权重重复复制到 C 盘。两个新增 LoRA 已复验完整 SHA256；其余大模型校验范围详见清单。</p><table><tr><th>模型</th><th>大小 GiB</th><th>实际路径</th></tr>'
for m in models:
    body += '<tr><td>'+html.escape(m['name'])+'</td><td>'+f"{m['bytes']/1024**3:.3f}"+'</td><td><code>'+html.escape(m['path'])+'</code></td></tr>'
body += '</table><details><summary>全部版本的 68 份工作流</summary><table><tr><th>版本</th><th>工作流</th><th>说明</th></tr>'
for row in rows:
    body += '<tr><td>'+html.escape(row['group'])+'</td><td><a href="'+quote(row['retained_native'], safe='/')+'" download>'+html.escape(row['name'])+'</a></td><td>'+('历史自定义节点，当前后端禁用' if row['unavailable_nodes_in_current_backend'] else '参数、连接、模型和输入已核对')+'</td></tr>'
body += '</table></details><p><small>ComfyUI 节点文件目录：<LOCAL_PATH>/Feisheng-MV。执行记录也独立保存，不依赖 ComfyUI 内存中的历史列表。</small></p>'
(OUT / "index.html").write_text('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>飞升 · ComfyUI 留存</title><style>'+css+'</style></head><body><main>'+body+'</main></body></html>', encoding="utf-8")
shutil.copy2(WORK / 'publish.py', OUT / 'scripts/publish.py')
shutil.copy2(WORK / 'finish.py', OUT / 'scripts/finish.py')
shutil.copy2(WORK / 'document_retention.py', OUT / 'scripts/document_retention.py')
print('Retention instructions and index written; native workflows remain in ComfyUI user directory.')
