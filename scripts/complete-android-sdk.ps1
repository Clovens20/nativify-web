# Script pour compléter l'installation Android SDK
# Installe les composants manquants du Android SDK

param(
    [string]$AndroidSdkPath = $env:ANDROID_HOME,
    [switch]$InstallCmdlineTools = $false,
    [switch]$AcceptLicenses = $false
)

Write-Host "🔧 Script de complétion Android SDK" -ForegroundColor Cyan
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
            Write-Host "✅ Android SDK trouvé: $path" -ForegroundColor Green
            return $path
        }
    }
    
    Write-Host "❌ Android SDK non trouvé" -ForegroundColor Red
    return $null
}

# Trouver Android SDK
if (-not $AndroidSdkPath) {
    $AndroidSdkPath = Find-AndroidSdk
}

if (-not $AndroidSdkPath) {
    Write-Host ""
    Write-Host "⚠️  Android SDK non trouvé. Options:" -ForegroundColor Yellow
    Write-Host "1. Installer Android Studio (recommandé): https://developer.android.com/studio"
    Write-Host "2. Télécharger les Command Line Tools: https://developer.android.com/studio#command-tools"
    Write-Host ""
    Write-Host "Après installation, définissez ANDROID_HOME:"
    Write-Host '  [System.Environment]::SetEnvironmentVariable("ANDROID_HOME", "C:\Users\<username>\AppData\Local\Android\Sdk", "User")'
    exit 1
}

$sdkPath = [System.IO.Path]::Combine($AndroidSdkPath)
Write-Host "📁 Chemin SDK: $sdkPath" -ForegroundColor Cyan
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
        Write-Host "✅ sdkmanager trouvé: $path" -ForegroundColor Green
        break
    }
}

if (-not $sdkmanager) {
    Write-Host "⚠️  sdkmanager non trouvé" -ForegroundColor Yellow
    
    if ($InstallCmdlineTools) {
        Write-Host "📥 Installation des Command Line Tools..." -ForegroundColor Cyan
        Write-Host ""
        Write-Host "📥 Veuillez télécharger les Command Line Tools depuis:"
        Write-Host "   https://developer.android.com/studio#command-tools"
        Write-Host ""
        Write-Host "📋 Instructions:"
        Write-Host "1. Téléchargez commandlinetools-win-*.zip"
        Write-Host "2. Créez le dossier: $sdkPath\cmdline-tools\latest"
        Write-Host "3. Extrayez le contenu dans: $sdkPath\cmdline-tools\latest"
        Write-Host ""
        Write-Host "Ou installez Android Studio qui inclut tout automatiquement."
        exit 1
    } else {
        Write-Host "💡 Pour installer sdkmanager, exécutez:" -ForegroundColor Yellow
        Write-Host "   .\scripts\complete-android-sdk.ps1 -InstallCmdlineTools"
        Write-Host ""
        Write-Host "⚠️  Note: Sans sdkmanager, Gradle téléchargera les dépendances automatiquement."
        exit 0
    }
}

# Vérifier les composants essentiels
$components = @{
    "platform-tools" = "$sdkPath\platform-tools"
    "build-tools" = "$sdkPath\build-tools"
    "platforms" = "$sdkPath\platforms"
}

$missing = @()
$present = @()

Write-Host "🔍 Vérification des composants..." -ForegroundColor Cyan
Write-Host ""

foreach ($component in $components.GetEnumerator()) {
    $path = $component.Value
    if (Test-Path $path) {
        $items = Get-ChildItem $path -ErrorAction SilentlyContinue
        if ($items.Count -gt 0) {
            Write-Host "✅ $($component.Key) : Présent ($($items.Count) éléments)" -ForegroundColor Green
            $present += $component.Key
        } else {
            Write-Host "⚠️  $($component.Key) : Dossier vide" -ForegroundColor Yellow
            $missing += $component.Key
        }
    } else {
        Write-Host "❌ $($component.Key) : Manquant" -ForegroundColor Red
        $missing += $component.Key
    }
}

Write-Host ""

if ($missing.Count -eq 0) {
    Write-Host "✅ Android SDK est complet et opérationnel!" -ForegroundColor Green
    exit 0
}

Write-Host "⚠️  Composants manquants: $($missing -join ', ')" -ForegroundColor Yellow
Write-Host ""

# Installer les composants manquants
if ($sdkmanager) {
    Write-Host "📦 Installation des composants manquants..." -ForegroundColor Cyan
    Write-Host ""
    
    $packages = @()
    
    if ($missing -contains "platform-tools") {
        $packages += "platform-tools"
    }
    if ($missing -contains "build-tools") {
        $packages += "build-tools;34.0.0"
    }
    if ($missing -contains "platforms") {
        $packages += "platforms;android-34"
    }
    
    if ($packages.Count -gt 0) {
        $packagesStr = $packages -join " "
        
        Write-Host "📥 Installation des packages: $packagesStr" -ForegroundColor Cyan
        Write-Host ""
        
        if ($AcceptLicenses) {
            # Accepter les licences d'abord
            Write-Host "✅ Acceptation des licences..." -ForegroundColor Green
            & $sdkmanager --licenses | Out-Null
            Write-Host ""
        }
        
        # Installer les packages
        Write-Host "📥 Installation en cours (peut prendre plusieurs minutes)..." -ForegroundColor Cyan
        Write-Host ""
        
        try {
            $process = Start-Process -FilePath $sdkmanager -ArgumentList $packagesStr -NoNewWindow -Wait -PassThru
            if ($process.ExitCode -eq 0) {
                Write-Host ""
                Write-Host "✅ Installation réussie!" -ForegroundColor Green
                Write-Host "✅ Android SDK est maintenant complet et opérationnel!" -ForegroundColor Green
            } else {
                Write-Host ""
                Write-Host "⚠️  Installation échouée (code: $($process.ExitCode))" -ForegroundColor Yellow
                Write-Host "💡 Essayez d'exécuter manuellement:" -ForegroundColor Yellow
                Write-Host "   $sdkmanager $packagesStr"
                Write-Host ""
                Write-Host "💡 Ou installez Android Studio qui inclut tout automatiquement."
            }
        } catch {
            Write-Host ""
            Write-Host "❌ Erreur lors de l'installation: $_" -ForegroundColor Red
            Write-Host "💡 Essayez d'exécuter manuellement:" -ForegroundColor Yellow
            Write-Host "   $sdkmanager $packagesStr"
        }
    }
} else {
    Write-Host "⚠️  Impossible d'installer les composants sans sdkmanager" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 Options:" -ForegroundColor Yellow
    Write-Host "1. Installer Android Studio (recommandé): https://developer.android.com/studio"
    Write-Host "2. Installer les Command Line Tools manuellement (voir GUIDE_CONFIGURATION_JAVA_ANDROID.md)"
    Write-Host ""
    Write-Host "⚠️  Note: Sans ces composants, Gradle téléchargera les dépendances automatiquement lors du build."
    Write-Host "   Les builds fonctionneront mais seront plus lents (première fois)."
}

Write-Host ""

