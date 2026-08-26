$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$vitis = Get-Command vitis_hls -ErrorAction SilentlyContinue
if (-not $vitis) {
    Write-Error "vitis_hls is not installed or not present in PATH. Install/source Vitis 2022.2, then rerun this script."
    exit 3
}
Push-Location (Join-Path $root "hls")
try {
    & $vitis.Source -f "run_hls.tcl"
    if ($LASTEXITCODE -ne 0) { throw "Vitis HLS flow failed" }
} finally {
    Pop-Location
}
