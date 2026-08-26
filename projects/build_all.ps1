param([string]$BuildRoot = "build")
$ErrorActionPreference="Stop"
$root=$PSScriptRoot
$compiler=(Get-Command g++ -ErrorAction Stop).Source
$projects=@("tileplace","routecast","persistroute","dieroute","fusionpar")
foreach($name in $projects){
  $p=Join-Path $root $name;$out=Join-Path (Join-Path $root $BuildRoot) $name
  New-Item -ItemType Directory -Force -Path $out|Out-Null
  $sources=@((Join-Path $p "src/$name.cpp"),(Join-Path $p "tb/${name}_tb.cpp"))
  if($name -eq "persistroute"){$sources=@((Join-Path $p "src/persistroute.cpp"),(Join-Path $p "src/multiqueue.cpp"),(Join-Path $p "tb/persistroute_tb.cpp"))}
  & $compiler -std=c++17 -O2 -Wall -Wextra -Wpedantic -I (Join-Path $p "include") $sources -o (Join-Path $out "${name}_tb.exe")
  if($LASTEXITCODE-ne 0){throw "$name build failed"}
  Write-Host "$name build: PASS"
}
$persist=Join-Path $root "persistroute";$persistOut=Join-Path (Join-Path $root $BuildRoot) "persistroute"
& $compiler -std=c++17 -O2 -Wall -Wextra -Wpedantic -I (Join-Path $persist "include") (Join-Path $persist "src/multiqueue.cpp") (Join-Path $persist "tb/multiqueue_tb.cpp") -o (Join-Path $persistOut "multiqueue_tb.exe")
if($LASTEXITCODE-ne 0){throw "multiqueue build failed"}
& $compiler -std=c++17 -O2 -Wall -Wextra -Wpedantic -I (Join-Path $persist "include") (Join-Path $persist "src/multi_pe.cpp") (Join-Path $persist "tb/multi_pe_tb.cpp") -o (Join-Path $persistOut "multi_pe_tb.exe")
if($LASTEXITCODE-ne 0){throw "multi_pe build failed"}
& $compiler -std=c++17 -O2 -Wall -Wextra -Wpedantic -I (Join-Path $persist "include") (Join-Path $persist "src/multiqueue.cpp") (Join-Path $persist "src/search_hbm.cpp") (Join-Path $persist "tb/search_hbm_tb.cpp") -o (Join-Path $persistOut "search_hbm_tb.exe")
if($LASTEXITCODE-ne 0){throw "search_hbm build failed"}
& $compiler -std=c++17 -O2 -Wall -Wextra -Wpedantic -I (Join-Path $persist "include") (Join-Path $persist "src/commit_hbm.cpp") (Join-Path $persist "tb/commit_hbm_tb.cpp") -o (Join-Path $persistOut "commit_hbm_tb.exe")
if($LASTEXITCODE-ne 0){throw "commit_hbm build failed"}
& $compiler -std=c++17 -O2 -Wall -Wextra -Wpedantic -I (Join-Path $persist "include") (Join-Path $persist "src/pathfinder.cpp") (Join-Path $persist "tb/pathfinder_tb.cpp") -o (Join-Path $persistOut "pathfinder_tb.exe")
if($LASTEXITCODE-ne 0){throw "pathfinder build failed"}
$accelerated=@((Join-Path $persist "src/accelerated_pathfinder.cpp"),(Join-Path $persist "src/hbm_cmodel_backend.cpp"),(Join-Path $persist "src/search_hbm.cpp"),(Join-Path $persist "src/commit_hbm.cpp"),(Join-Path $persist "src/multiqueue.cpp"),(Join-Path $persist "src/pathfinder.cpp"))
& $compiler -std=c++17 -O2 -Wall -Wextra -Wpedantic -I (Join-Path $persist "include") $accelerated (Join-Path $persist "tb/accelerated_pathfinder_tb.cpp") -o (Join-Path $persistOut "accelerated_pathfinder_tb.exe")
if($LASTEXITCODE-ne 0){throw "accelerated pathfinder build failed"}
& $compiler -std=c++17 -O2 -Wall -Wextra -Wpedantic -I (Join-Path $persist "include") (Join-Path $persist "src/pathfinder.cpp") (Join-Path $persist "host/pathfinder_host.cpp") -o (Join-Path $persistOut "persistroute_pathfinder.exe")
if($LASTEXITCODE-ne 0){throw "pathfinder host build failed"}
& $compiler -std=c++17 -O2 -Wall -Wextra -Wpedantic -I (Join-Path $persist "include") $accelerated (Join-Path $persist "host/accelerated_pathfinder_host.cpp") -o (Join-Path $persistOut "persistroute_accelerated_cmodel.exe")
if($LASTEXITCODE-ne 0){throw "accelerated pathfinder host build failed"}
