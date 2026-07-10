$ErrorActionPreference = 'SilentlyContinue'

function Test-Command {
    param(
        [string]$Name,
        [string]$Label,
        [string]$VersionArgs = '--version'
    )

    $command = Get-Command $Name
    if ($null -eq $command) {
        Write-Host "[FALTA] $Label" -ForegroundColor Red
        return $false
    }

    $version = & $Name $VersionArgs 2>$null | Select-Object -First 1
    Write-Host "[OK] $Label - $version" -ForegroundColor Green
    return $true
}

Write-Host "`nFisioHub Developer Workstation - Verificacao" -ForegroundColor Cyan
Write-Host "================================================`n"

$results = @()
$results += Test-Command -Name 'git' -Label 'Git'
$results += Test-Command -Name 'code' -Label 'VS Code CLI'
$results += Test-Command -Name 'python' -Label 'Python'
$results += Test-Command -Name 'node' -Label 'Node.js'
$results += Test-Command -Name 'npm' -Label 'npm'
$results += Test-Command -Name 'docker' -Label 'Docker'

Write-Host ""
if ($results -contains $false) {
    Write-Host "Existem componentes ausentes. Instale os itens marcados como FALTA antes de continuar." -ForegroundColor Yellow
    exit 1
}

$dockerInfo = docker info 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ATENCAO] Docker esta instalado, mas o Docker Desktop nao parece estar em execucao." -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Docker Desktop esta em execucao." -ForegroundColor Green
Write-Host "`nEstacao pronta para iniciar o ambiente local do FisioHub." -ForegroundColor Cyan
