param(
  [Parameter(Mandatory=$true)][ValidateSet("export","apply")][string]$Command,
  [Parameter(ValueFromRemainingArguments=$true)][string[]]$BridgeArgs,
  [string]$RapidWrightRoot = $env:RAPIDWRIGHT_PATH
)
$ErrorActionPreference = "Stop"
if (-not $RapidWrightRoot) { throw "Set RAPIDWRIGHT_PATH or pass -RapidWrightRoot" }
$classes = Join-Path $PSScriptRoot "build/classes"
if (-not (Test-Path $classes)) { & (Join-Path $PSScriptRoot "build.ps1") -RapidWrightRoot $RapidWrightRoot }
$classPath = $classes + ";" + (Join-Path $RapidWrightRoot "bin") + ";" + (Join-Path $RapidWrightRoot "jars/*")
& java -cp $classPath edu.fpgaacc.persistroute.RapidWrightBridge $Command @BridgeArgs
exit $LASTEXITCODE
