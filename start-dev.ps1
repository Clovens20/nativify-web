# Script PowerShell pour démarrer frontend et backend ensemble
Write-Host "🚀 Démarrage de NativiWeb Studio..." -ForegroundColor Cyan
Write-Host ""

# Démarrer le backend dans une nouvelle fenêtre PowerShell
Write-Host "[backend] Démarrage du backend FastAPI dans une nouvelle fenêtre..." -ForegroundColor Magenta
$backendScript = @"
cd '$PWD'
Write-Host '[backend] Uvicorn starting...' -ForegroundColor Magenta
uvicorn main:app --reload --app-dir backend
"@

$backendScript | Out-File -FilePath "$env:TEMP\start-backend.ps1" -Encoding UTF8
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "$env:TEMP\start-backend.ps1"

# Attendre un peu pour que le backend démarre
Start-Sleep -Seconds 3

# Démarrer le frontend (bloquant)
Write-Host "[frontend] Démarrage du frontend Next.js..." -ForegroundColor Cyan
Write-Host ""
npm run dev:frontend

