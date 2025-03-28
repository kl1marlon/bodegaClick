# Script para restaurar la configuración original de Railway
Write-Host "Restaurando configuración original para Railway..." -ForegroundColor Green

# Restaurar railway.json
if (Test-Path -Path "railway.json.bak" -PathType Leaf) {
    Copy-Item -Path "railway.json.bak" -Destination "railway.json" -Force
    Write-Host "railway.json restaurado" -ForegroundColor Green
} else {
    Write-Host "No se encontró railway.json.bak" -ForegroundColor Red
}

# Restaurar Dockerfile
if (Test-Path -Path "Dockerfile.bak" -PathType Leaf) {
    Copy-Item -Path "Dockerfile.bak" -Destination "Dockerfile" -Force
    Write-Host "Dockerfile restaurado" -ForegroundColor Green
} else {
    Write-Host "No se encontró Dockerfile.bak" -ForegroundColor Red
}

Write-Host "Proceso completado. Recuerda hacer git commit y git push para actualizar los cambios." -ForegroundColor Yellow
Write-Host "Comando sugerido:"
Write-Host "git add railway.json Dockerfile"
Write-Host "git commit -m ""Restaurar configuración para migraciones automáticas"""
Write-Host "git push" 