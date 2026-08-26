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
$config = Join-Path $root "experiments/configs/conflict_sweep.json"
$resultDir = python (Join-Path $root "experiments/run_experiments.py") --exe $exe --config $config
if ($LASTEXITCODE -ne 0) { throw "conflict sweep failed" }
python (Join-Path $root "experiments/validate_results.py") $resultDir
if ($LASTEXITCODE -ne 0) { throw "conflict sweep validation failed" }
Write-Host $resultDir
