$ErrorActionPreference = "Stop"

$bundledPython = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if (Test-Path -LiteralPath $bundledPython) {
    & $bundledPython convert_manual_case.py --out output/notification_switch_persist.json
    exit $LASTEXITCODE
}

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) {
    & $pythonCmd.Source convert_manual_case.py --out output/notification_switch_persist.json
    exit $LASTEXITCODE
}

$pyCmd = Get-Command py -ErrorAction SilentlyContinue
if ($pyCmd) {
    & $pyCmd.Source convert_manual_case.py --out output/notification_switch_persist.json
    exit $LASTEXITCODE
}

Write-Error "Python 3 was not found. Please install Python 3 or run inside the Codex environment."
