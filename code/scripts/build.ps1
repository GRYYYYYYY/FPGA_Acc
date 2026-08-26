param(
    [string]$BuildDir = "build"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$target = Join-Path $root $BuildDir
New-Item -ItemType Directory -Force -Path $target | Out-Null

$compiler = (Get-Command g++ -ErrorAction Stop).Source
& $compiler -std=c++17 -O2 -Wall -Wextra -Wpedantic `
    -I (Join-Path $root "include") `
    (Join-Path $root "src/router.cpp") `
    (Join-Path $root "src/main.cpp") `
    -o (Join-Path $target "persist_route_sw.exe")
if ($LASTEXITCODE -ne 0) { throw "persist_route_sw build failed" }

& $compiler -std=c++17 -O2 -Wall -Wextra -Wpedantic `
    -I (Join-Path $root "include") `
    (Join-Path $root "src/router.cpp") `
    (Join-Path $root "tests/router_tests.cpp") `
    -o (Join-Path $target "router_tests.exe")
if ($LASTEXITCODE -ne 0) { throw "router_tests build failed" }

Write-Host "Built $target"
