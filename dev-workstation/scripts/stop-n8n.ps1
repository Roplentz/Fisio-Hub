$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workstationDir = Split-Path -Parent $scriptDir
$composeFile = Join-Path $workstationDir 'docker-compose.yml'

Push-Location $workstationDir
try {
    docker compose -f $composeFile down
    Write-Host "n8n parado. Os dados foram preservados no volume Docker." -ForegroundColor Green
} finally {
    Pop-Location
}
