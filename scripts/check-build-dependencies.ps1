# Script de vérification rapide des dépendances pour le build Android
# Utilisez ce script pour vérifier rapidement si tout est configuré correctement

Write-Host "🔍 Vérification des dépendances pour le build Android" -ForegroundColor Cyan
Write-Host ""

$allOk = $true

# Vérifier Java
Write-Host "Java JDK:" -ForegroundColor Yellow
try {
    $javaOutput = java -version 2>&1
    $javaVersion = $javaOutput | Select-Object -First 1
    if ($javaVersion -match "version") {
        Write-Host "  ✅ Installé: $javaVersion" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Non trouvé" -ForegroundColor Red
        $allOk = $false
    }
} catch {
    Write-Host "  ❌ Non installé ou pas dans le PATH" -ForegroundColor Red
    $allOk = $false
}

# Vérifier JAVA_HOME
Write-Host "JAVA_HOME:" -ForegroundColor Yellow
if ($env:JAVA_HOME) {
    if (Test-Path $env:JAVA_HOME) {
        Write-Host "  ✅ Configuré: $env:JAVA_HOME" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Configuré mais le chemin n'existe pas: $env:JAVA_HOME" -ForegroundColor Yellow
        $allOk = $false
    }
} else {
    Write-Host "  ❌ Non configuré" -ForegroundColor Red
    $allOk = $false
}

# Vérifier Android SDK (optionnel)
Write-Host "Android SDK:" -ForegroundColor Yellow
if ($env:ANDROID_HOME) {
    if (Test-Path $env:ANDROID_HOME) {
        Write-Host "  ✅ Configuré: $env:ANDROID_HOME" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Configuré mais le chemin n'existe pas: $env:ANDROID_HOME" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠️  Non configuré (optionnel mais recommandé)" -ForegroundColor Yellow
}

Write-Host ""

if ($allOk) {
    Write-Host "✅ Toutes les dépendances requises sont installées!" -ForegroundColor Green
    Write-Host "   Le système peut compiler des APKs automatiquement." -ForegroundColor Green
} else {
    Write-Host "❌ Certaines dépendances sont manquantes." -ForegroundColor Red
    Write-Host "   Exécutez: .\scripts\setup-java-android.ps1" -ForegroundColor Yellow
    Write-Host "   pour installer et configurer les dépendances." -ForegroundColor Yellow
}

Write-Host ""

