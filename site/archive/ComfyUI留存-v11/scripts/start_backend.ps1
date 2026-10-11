$ErrorActionPreference = 'Stop'
$taskRoot = '<PROJECT>'
$taskWork = Join-Path $taskRoot 'work/feisheng/style-v11'
try {
    $queue = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/queue' -TimeoutSec 3
    Write-Output 'Existing ComfyUI backend is reachable; reuse it.'
    exit 0
} catch [System.Net.Http.HttpRequestException] {
}
$pythonExe = '<LOCAL_PATH>/python.exe'
$codeRoot = '<USER_HOME>/AppData/Local/Comfy-Desktop/ComfyUI-Installs/ComfyUI'
$taskTemp = Join-Path $taskWork 'ComfyTemp'
New-Item -ItemType Directory -Path $taskTemp -Force | Out-Null
$arguments = @('-s', 'ComfyUI/main.py', '--base-directory', '<LOCAL_PATH>/newcomfyui', '--user-directory', '<LOCAL_PATH>/user', '--input-directory', '<LOCAL_PATH>/input', '--output-directory', '<LOCAL_PATH>/output', '--temp-directory', $taskTemp, '--extra-model-paths-config', '"<USER_HOME>/AppData/Roaming/Comfy Desktop/instance-model-paths/inst-1786180594835.yaml"', '--port', '8000', '--disable-all-custom-nodes', '--disable-api-nodes', '--enable-dynamic-vram', '--fast-disk', '--disable-pinned-memory', '--vram-headroom', '2.5', '--cache-ram', '6', '8', '--preview-method', 'none')
$taskProcess = Start-Process -FilePath $pythonExe -ArgumentList $arguments -WorkingDirectory $codeRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskWork 'backend.stdout.log') -RedirectStandardError (Join-Path $taskWork 'backend.stderr.log') -PassThru
$taskProcess.Id | Set-Content -LiteralPath (Join-Path $taskWork 'backend.pid')
Write-Output "Started ComfyUI backend process $($taskProcess.Id) using the existing low-memory flags."
