param(
  [Parameter(Mandatory=$true)][string]$ProjectName,
  [Parameter(Mandatory=$true)][string]$RtlDir,
  [string]$Part = "xcu280-fsvh2892-2L-e"
)
$vivado=Get-Command vivado -ErrorAction SilentlyContinue
if(-not $vivado){Write-Error "vivado not found. Install/source Vivado 2022.2 and rerun.";exit 3}
& $vivado.Source -mode batch -source (Join-Path $PSScriptRoot "run_vivado_post_synth.tcl") -tclargs $ProjectName $Part $RtlDir
if($LASTEXITCODE-ne 0){throw "Vivado post-synthesis validation failed"}
