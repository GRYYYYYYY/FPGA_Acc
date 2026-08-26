param(
    [string]$BuildDir = "build"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$testExe = Join-Path (Join-Path $root $BuildDir) "router_tests.exe"
if (-not (Test-Path -LiteralPath $testExe)) {
    & (Join-Path $PSScriptRoot "build.ps1") -BuildDir $BuildDir
}
& $testExe
if ($LASTEXITCODE -ne 0) { throw "tests failed" }
