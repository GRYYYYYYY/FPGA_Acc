param([string]$BuildRoot = "build")
$ErrorActionPreference="Stop"
$root=$PSScriptRoot
$projects=@("tileplace","routecast","persistroute","dieroute","fusionpar")
foreach($name in $projects){$exe=Join-Path (Join-Path (Join-Path $root $BuildRoot) $name) "${name}_tb.exe";if(-not(Test-Path $exe)){powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "build_all.ps1") -BuildRoot $BuildRoot;break}}
foreach($name in $projects){$exe=Join-Path (Join-Path (Join-Path $root $BuildRoot) $name) "${name}_tb.exe";& $exe;if($LASTEXITCODE-ne 0){throw "$name test failed"}}
$persistOut=Join-Path (Join-Path $root $BuildRoot) "persistroute"
foreach($test in @("multiqueue_tb","multi_pe_tb","search_hbm_tb","commit_hbm_tb","pathfinder_tb","accelerated_pathfinder_tb")){& (Join-Path $persistOut "${test}.exe");if($LASTEXITCODE-ne 0){throw "$test failed"}}
python (Join-Path (Join-Path $root "persistroute") "tools/test_converters.py")
if($LASTEXITCODE-ne 0){throw "converter tests failed"}
python (Join-Path (Join-Path $root "persistroute") "tools/static_interface_audit.py")
if($LASTEXITCODE-ne 0){throw "static interface audit failed"}
python (Join-Path (Join-Path (Join-Path $root "experiments") "strong_baselines") "test_runner.py")
if($LASTEXITCODE-ne 0){throw "strong baseline tests failed"}
