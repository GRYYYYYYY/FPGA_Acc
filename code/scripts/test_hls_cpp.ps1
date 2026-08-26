param(
    [string]$BuildDir = "build"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$target = Join-Path $root $BuildDir
New-Item -ItemType Directory -Force -Path $target | Out-Null
$compiler = (Get-Command g++ -ErrorAction Stop).Source
$exe = Join-Path $target "commit_kernel_tb.exe"
& $compiler -std=c++17 -O2 -Wall -Wextra -Wpedantic `
    -I (Join-Path $root "hls/include") `
    (Join-Path $root "hls/src/commit_kernel.cpp") `
    (Join-Path $root "hls/tb/commit_kernel_tb.cpp") `
    -o $exe
if ($LASTEXITCODE -ne 0) { throw "HLS C++ testbench build failed" }
& $exe
if ($LASTEXITCODE -ne 0) { throw "HLS C++ testbench failed" }
