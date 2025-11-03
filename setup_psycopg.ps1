# ====================================================
# Script PowerShell para configurar PATH do PostgreSQL
# e validar libpq.dll para psycopg (Windows + Python)
# ====================================================

Write-Host "Iniciando configuração do PATH do PostgreSQL..." -ForegroundColor Cyan

# Caminhos padrão do PostgreSQL (adapte se necessário)
$possiblePaths = @(
    "C:\Program Files\PostgreSQL\17\bin",
    "C:\Program Files\PostgreSQL\16\bin",
    "C:\Program Files\PostgreSQL\15\bin"
)

# Detecta o primeiro diretório que existe
$pgBin = $possiblePaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $pgBin) {
    Write-Host "Erro: Não foi possível localizar diretório bin do PostgreSQL. Verifique a instalação." -ForegroundColor Red
    exit 1
}

Write-Host "Diretório PostgreSQL detectado:" $pgBin

# Testa se libpq.dll existe
$libpq = Join-Path $pgBin "libpq.dll"
if (-not (Test-Path $libpq)) {
    Write-Host "Erro: libpq.dll não encontrada em $pgBin" -ForegroundColor Red
    exit 1
}

Write-Host "libpq.dll encontrada"

# Adiciona temporariamente ao PATH do terminal atual
$env:Path += ";$pgBin"
Write-Host "PATH atualizado temporariamente para este terminal"

# Adiciona permanentemente ao PATH do sistema (requer permissão de admin)
try {
    $currentSystemPath = [Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::Machine)
    if ($currentSystemPath -notlike "*$pgBin*") {
        [Environment]::SetEnvironmentVariable("Path", "$currentSystemPath;$pgBin", [System.EnvironmentVariableTarget]::Machine)
        Write-Host "PATH do sistema atualizado permanentemente" -ForegroundColor Green
    } else {
        Write-Host "PATH do sistema já contém o diretório PostgreSQL"
    }
} catch {
    Write-Host "Aviso: Não foi possível atualizar PATH permanentemente. Execute o script como Administrador." -ForegroundColor Yellow
}

# Testa o psycopg
Write-Host "Testando importação do psycopg..."
try {
    python -c "import psycopg; print('psycopg importado com sucesso! Versão:', psycopg.__version__)"
} catch {
    Write-Host "Falha ao importar psycopg. Verifique PATH e instalação do PostgreSQL." -ForegroundColor Red
    exit 1
}

Write-Host "Configuração concluída. Reinicie o terminal para garantir que PATH permanente seja aplicado." -ForegroundColor Cyan
