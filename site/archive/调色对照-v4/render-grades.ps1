$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot '../可视化分镜-v3-胶片调色/storyboard.png'
$grades = [ordered]@{
 'A-cool' = "curves=all='0/0.028 0.18/0.16 0.5/0.51 0.78/0.76 1/0.92':interp=pchip,colorbalance=rs=-0.025:gs=0.012:bs=0.035:rh=0.012:bh=-0.025:pl=1,eq=saturation=0.78,unsharp=5:5:-0.22:3:3:0,noise=alls=2:all_seed=128"
 'B-soft' = "curves=all='0/0.045 0.2/0.21 0.5/0.56 0.8/0.79 1/0.91':interp=pchip,colorbalance=rs=0.012:gs=0.008:bs=0.012:rh=0.028:gh=0.012:bh=-0.025:pl=1,eq=saturation=0.72,unsharp=5:5:-0.3:3:3:0,noise=alls=2:all_seed=128"
 'C-dense' = "curves=all='0/0.014 0.15/0.105 0.45/0.43 0.72/0.76 1/0.96':interp=pchip,colorbalance=rs=-0.012:bs=0.018:rh=0.014:bh=-0.012:pl=1,eq=saturation=0.87,unsharp=5:5:-0.12:3:3:0,noise=alls=3:all_seed=128"
}
Copy-Item -LiteralPath $source -Destination (Join-Path $PSScriptRoot 'original.png') -Force
foreach ($entry in $grades.GetEnumerator()) {
 & ffmpeg -hide_banner -loglevel error -y -i $source -vf $entry.Value -frames:v 1 -update 1 -pix_fmt rgb24 (Join-Path $PSScriptRoot ($entry.Key + '.png'))
 if ($LASTEXITCODE -ne 0) { throw "Failed: $($entry.Key)" }
}
$grades | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'filters.json') -Encoding utf8
