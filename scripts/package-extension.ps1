$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$source = Join-Path $root "frontend\extension"
$outputDir = Join-Path $root "dist"
$output = Join-Path $outputDir "flick-picker-extension.zip"

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
if (Test-Path $output) { Remove-Item $output }

$files = Get-ChildItem $source -File | Where-Object { $_.Name -notmatch "^(demo\.js)$" }
Compress-Archive -Path $files.FullName -DestinationPath $output -CompressionLevel Optimal
Write-Output $output
