$ErrorActionPreference = "Stop"

$bundledPython = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if (Test-Path -LiteralPath $bundledPython) {
    & $bundledPython full_prd_testpoint_agent.py --out output/full_test_points.json
    exit $LASTEXITCODE
}

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) {
    & $pythonCmd.Source full_prd_testpoint_agent.py --out output/full_test_points.json
    exit $LASTEXITCODE
}

$pyCmd = Get-Command py -ErrorAction SilentlyContinue
if ($pyCmd) {
    & $pyCmd.Source full_prd_testpoint_agent.py --out output/full_test_points.json
    exit $LASTEXITCODE
}

Write-Error "Python 3 was not found. Please install Python 3 or run inside the Codex environment."
