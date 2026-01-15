# Script pour vérifier si Android SDK est complet et opérationnel

param(
    [string]$AndroidSdkPath = $env:ANDROID_HOME
)

Write-Host "🔍 Vérification Android SDK" -ForegroundColor Cyan
Write-Host ""

# Fonction pour trouver Android SDK
function Find-AndroidSdk {
    $paths = @(
        $env:ANDROID_HOME,
        $env:ANDROID_SDK_ROOT,
        "$env:LOCALAPPDATA\Android\Sdk",
        "C:\Android\Sdk",
        "C:\Android"
    )
    
    foreach ($path in $paths) {
        if ($path -and (Test-Path $path)) {
            return $path
        }
    }
    
    return $null
}

# Trouver Android SDK
if (-not $AndroidSdkPath) {
    $AndroidSdkPath = Find-AndroidSdk
}

if (-not $AndroidSdkPath) {
    Write-Host "❌ Android SDK non trouvé" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Pour installer Android SDK:" -ForegroundColor Yellow
    Write-Host "   1. Installer Android Studio: https://developer.android.com/studio"
    Write-Host "   2. Ou télécharger Command Line Tools: https://developer.android.com/studio#command-tools"
    exit 1
}

$sdkPath = $AndroidSdkPath
Write-Host "📁 Android SDK: $sdkPath" -ForegroundColor Cyan
Write-Host ""

# Vérifier sdkmanager
$sdkmanagerPaths = @(
    "$sdkPath\cmdline-tools\latest\bin\sdkmanager.bat",
    "$sdkPath\cmdline-tools\bin\sdkmanager.bat",
    "$sdkPath\tools\bin\sdkmanager.bat"
)

$sdkmanager = $null
foreach ($path in $sdkmanagerPaths) {
    if (Test-Path $path) {
        $sdkmanager = $path
        break
    }
}

if ($sdkmanager) {
    Write-Host "✅ sdkmanager: Présent" -ForegroundColor Green
} else {
    Write-Host "⚠️  sdkmanager: Non disponible" -ForegroundColor Yellow
}

# Vérifier les composants essentiels
$components = @{
    "platform-tools" = "$sdkPath\platform-tools"
    "build-tools" = "$sdkPath\build-tools"
    "platforms" = "$sdkPath\platforms"
}

$allComplete = $true
$missing = @()

Write-Host ""
Write-Host "📦 Composants:" -ForegroundColor Cyan

foreach ($component in $components.GetEnumerator()) {
    $path = $component.Value
    if (Test-Path $path) {
        $items = Get-ChildItem $path -ErrorAction SilentlyContinue
        if ($items.Count -gt 0) {
            Write-Host "   ✅ $($component.Key): $($items.Count) élément(s)" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  $($component.Key): Dossier vide" -ForegroundColor Yellow
            $allComplete = $false
            $missing += $component.Key
        }
    } else {
        Write-Host "   ❌ $($component.Key): Manquant" -ForegroundColor Red
        $allComplete = $false
        $missing += $component.Key
    }
}

Write-Host ""

if ($allComplete) {
    Write-Host "✅ Android SDK est complet et opérationnel!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️  Android SDK est incomplet" -ForegroundColor Yellow
    Write-Host "   Composants manquants: $($missing -join ', ')" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 Pour compléter l'installation:" -ForegroundColor Cyan
    Write-Host "   .\scripts\complete-android-sdk.ps1"
    Write-Host ""
    Write-Host "⚠️  Note: Les builds fonctionneront quand même, Gradle téléchargera les dépendances manquantes."
    exit 1
}

