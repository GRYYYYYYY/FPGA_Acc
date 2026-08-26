param(
    [string]$BuildDir = "build"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$exe = Join-Path (Join-Path $root $BuildDir) "persist_route_sw.exe"
if (-not (Test-Path -LiteralPath $exe)) {
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "build.ps1") -BuildDir $BuildDir
    if ($LASTEXITCODE -ne 0) { throw "build failed" }
}
$resultDir = python (Join-Path $root "experiments/run_experiments.py") --exe $exe
if ($LASTEXITCODE -ne 0) { throw "smoke experiment failed" }
python (Join-Path $root "experiments/validate_results.py") $resultDir
if ($LASTEXITCODE -ne 0) { throw "smoke result validation failed" }
Write-Host $resultDir
