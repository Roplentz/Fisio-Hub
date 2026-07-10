$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workstationDir = Split-Path -Parent $scriptDir
$envFile = Join-Path $workstationDir '.env'
$envExample = Join-Path $workstationDir '.env.example'
$composeFile = Join-Path $workstationDir 'docker-compose.yml'

if (-not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    Write-Host "Arquivo .env criado a partir do modelo." -ForegroundColor Yellow
    Write-Host "Edite dev-workstation/.env e troque a senha antes de executar novamente." -ForegroundColor Yellow
    exit 1
}

$envContent = Get-Content $envFile -Raw
if ($envContent -match 'troque-esta-senha') {
    Write-Host "Troque N8N_BASIC_AUTH_PASSWORD no arquivo dev-workstation/.env." -ForegroundColor Red
    exit 1
}

try {
    docker info | Out-Null
} catch {
    Write-Host "Docker Desktop nao esta em execucao." -ForegroundColor Red
    exit 1
}

Push-Location $workstationDir
try {
    docker compose --env-file .env -f $composeFile up -d
    Write-Host "`nn8n iniciado com sucesso." -ForegroundColor Green
    Write-Host "Abra: http://localhost:5678" -ForegroundColor Cyan
} finally {
    Pop-Location
}
