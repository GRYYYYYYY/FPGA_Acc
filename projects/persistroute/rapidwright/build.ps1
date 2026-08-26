param([string]$RapidWrightRoot = $env:RAPIDWRIGHT_PATH)
$ErrorActionPreference = "Stop"
if (-not $RapidWrightRoot) { throw "Set RAPIDWRIGHT_PATH or pass -RapidWrightRoot" }
$project = $PSScriptRoot
$classes = Join-Path $project "build/classes"
New-Item -ItemType Directory -Force -Path $classes | Out-Null
$classPath = (Join-Path $RapidWrightRoot "bin") + ";" + (Join-Path $RapidWrightRoot "jars/*")
$source = Join-Path $project "src/main/java/edu/fpgaacc/persistroute/RapidWrightBridge.java"
& javac -encoding UTF-8 -cp $classPath -d $classes $source
if ($LASTEXITCODE -ne 0) { throw "RapidWright bridge compilation failed" }
Write-Host "RapidWrightBridge build: PASS"
