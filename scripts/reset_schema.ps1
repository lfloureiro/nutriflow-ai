$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $projectRoot

Write-Host "A recriar schema com Alembic..." -ForegroundColor Cyan

.\.venv\Scripts\python.exe -m alembic downgrade base
.\.venv\Scripts\python.exe -m alembic upgrade head

Write-Host "Schema recriado com sucesso." -ForegroundColor Green