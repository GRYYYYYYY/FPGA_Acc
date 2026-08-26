$ErrorActionPreference="Stop"
$vitis=Get-Command vitis_hls -ErrorAction SilentlyContinue
if(-not $vitis){Write-Error "vitis_hls not found. Install/source Vitis 2022.2 and rerun.";exit 3}
foreach($name in @("tileplace","routecast","persistroute","dieroute","fusionpar")){
  Push-Location (Join-Path $PSScriptRoot $name)
  try{& $vitis.Source -f run_hls.tcl;if($LASTEXITCODE-ne 0){throw "$name HLS failed"}}finally{Pop-Location}
}
