param(
  [string]$Platform = $env:XILINX_PLATFORM,
  [ValidateSet("hw","hw_emu")][string]$Target = "hw"
)
$ErrorActionPreference = "Stop"
if (-not $Platform) { throw "Pass -Platform or set XILINX_PLATFORM to the exact U280/U55C .xpfm" }
$vitisHls = Get-Command vitis_hls -ErrorAction SilentlyContinue
$vpp = Get-Command v++ -ErrorAction SilentlyContinue
if (-not $vitisHls -or -not $vpp) { throw "vitis_hls and v++ must be on PATH (target release: 2022.2)" }
Push-Location $PSScriptRoot
try {
  & $vitisHls.Source -f run_hls.tcl
  if ($LASTEXITCODE -ne 0) { throw "HLS export failed" }
  $outDir = Join-Path $PSScriptRoot "build/xclbin/$Target"
  New-Item -ItemType Directory -Force -Path $outDir | Out-Null
  & $vpp.Source -l -t $Target --platform $Platform --config connectivity.cfg `
    (Join-Path $PSScriptRoot "build/search_hbm_kernel.xo") `
    (Join-Path $PSScriptRoot "build/commit_hbm_kernel.xo") `
    -o (Join-Path $outDir "persistroute.xclbin")
  if ($LASTEXITCODE -ne 0) { throw "v++ link failed" }
  Write-Host "xclbin: $(Join-Path $outDir 'persistroute.xclbin')"
} finally { Pop-Location }
