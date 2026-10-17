$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$interpreter = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $interpreter)) { throw 'Create .venv and install the backend dependencies using README.md first.' }
Push-Location (Join-Path $projectRoot 'backend')
try {
    & $interpreter -m uvicorn app.main:app --host 127.0.0.1 --port 8000
} finally {
    Pop-Location
}
