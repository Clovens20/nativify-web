# Script PowerShell pour configurer Java JDK et Android SDK pour NativiWeb Studio
# Ce script aide à installer et configurer les dépendances nécessaires pour compiler des APKs

Write-Host "🚀 Configuration Java JDK et Android SDK pour NativiWeb Studio" -ForegroundColor Cyan
Write-Host ""

# Fonction pour vérifier si Java est installé
function Test-JavaInstalled {
    try {
        $javaVersion = java -version 2>&1 | Select-Object -First 1
        if ($javaVersion -match "version") {
            Write-Host "✅ Java est déjà installé" -ForegroundColor Green
            Write-Host "   $javaVersion" -ForegroundColor Gray
            return $true
        }
    } catch {
        return $false
    }
    return $false
}

# Fonction pour trouver Java dans les emplacements communs
function Find-JavaInstallation {
    $commonPaths = @(
        "C:\Program Files\Java",
        "C:\Program Files (x86)\Java",
        "$env:LOCALAPPDATA\Programs\Eclipse Adoptium",
        "$env:ProgramFiles\Eclipse Adoptium"
    )
    
    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            $jdkDirs = Get-ChildItem -Path $path -Directory -Filter "jdk*" -ErrorAction SilentlyContinue
            if ($jdkDirs) {
                foreach ($jdk in $jdkDirs) {
                    $javaExe = Join-Path $jdk.FullName "bin\java.exe"
                    if (Test-Path $javaExe) {
                        return $jdk.FullName
                    }
                }
            }
        }
    }
    return $null
}

# Vérifier Java
Write-Host "📋 Vérification de Java JDK..." -ForegroundColor Yellow
$javaInstalled = Test-JavaInstalled

if (-not $javaInstalled) {
    Write-Host "❌ Java JDK n'est pas installé ou n'est pas dans le PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Pour installer Java JDK 17+ :" -ForegroundColor Yellow
    Write-Host "1. Téléchargez depuis: https://adoptium.net/" -ForegroundColor White
    Write-Host "2. Choisissez 'Temurin 17' ou supérieur (LTS recommandé)" -ForegroundColor White
    Write-Host "3. Installez avec les options par défaut" -ForegroundColor White
    Write-Host "4. Relancez ce script après l'installation" -ForegroundColor White
    Write-Host ""
    
    # Vérifier si Java est installé mais pas dans le PATH
    $javaPath = Find-JavaInstallation
    if ($javaPath) {
        Write-Host "⚠️  Java trouvé à: $javaPath" -ForegroundColor Yellow
        Write-Host "   Mais il n'est pas dans le PATH" -ForegroundColor Yellow
        Write-Host ""
        $setJava = Read-Host "Voulez-vous configurer JAVA_HOME maintenant? (O/N)"
        if ($setJava -eq "O" -or $setJava -eq "o") {
            [System.Environment]::SetEnvironmentVariable("JAVA_HOME", $javaPath, "User")
            $env:JAVA_HOME = $javaPath
            Write-Host "✅ JAVA_HOME configuré: $javaPath" -ForegroundColor Green
            Write-Host "   Redémarrez votre terminal pour que les changements prennent effet" -ForegroundColor Yellow
        }
    } else {
        # Ouvrir le navigateur vers Adoptium
        $openBrowser = Read-Host "Voulez-vous ouvrir la page de téléchargement Java? (O/N)"
        if ($openBrowser -eq "O" -or $openBrowser -eq "o") {
            Start-Process "https://adoptium.net/temurin/releases/?version=17"
        }
    }
} else {
    # Vérifier JAVA_HOME
    if ($env:JAVA_HOME) {
        Write-Host "✅ JAVA_HOME est configuré: $env:JAVA_HOME" -ForegroundColor Green
    } else {
        Write-Host "⚠️  JAVA_HOME n'est pas configuré" -ForegroundColor Yellow
        $javaPath = Find-JavaInstallation
        if ($javaPath) {
            Write-Host "   Java trouvé à: $javaPath" -ForegroundColor Gray
            $setJava = Read-Host "Voulez-vous configurer JAVA_HOME maintenant? (O/N)"
            if ($setJava -eq "O" -or $setJava -eq "o") {
                [System.Environment]::SetEnvironmentVariable("JAVA_HOME", $javaPath, "User")
                $env:JAVA_HOME = $javaPath
                Write-Host "✅ JAVA_HOME configuré: $javaPath" -ForegroundColor Green
                Write-Host "   Redémarrez votre terminal pour que les changements prennent effet" -ForegroundColor Yellow
            }
        } else {
            Write-Host "   Impossible de trouver l'installation Java automatiquement" -ForegroundColor Red
            Write-Host "   Configurez JAVA_HOME manuellement vers votre installation JDK" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "📋 Vérification d'Android SDK..." -ForegroundColor Yellow

# Vérifier Android SDK
if ($env:ANDROID_HOME) {
    Write-Host "✅ ANDROID_HOME est configuré: $env:ANDROID_HOME" -ForegroundColor Green
    if (Test-Path $env:ANDROID_HOME) {
        Write-Host "   Le répertoire existe" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Le répertoire n'existe pas!" -ForegroundColor Red
    }
} else {
    Write-Host "⚠️  ANDROID_HOME n'est pas configuré" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Android SDK est optionnel mais recommandé pour des builds plus rapides." -ForegroundColor Gray
    Write-Host ""
    Write-Host "Options pour installer Android SDK:" -ForegroundColor Yellow
    Write-Host "1. Installer Android Studio (recommandé): https://developer.android.com/studio" -ForegroundColor White
    Write-Host "   - Android Studio installera automatiquement l'Android SDK" -ForegroundColor Gray
    Write-Host "   - Emplacement par défaut: $env:LOCALAPPDATA\Android\Sdk" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Installer uniquement les command line tools:" -ForegroundColor White
    Write-Host "   - Téléchargez depuis: https://developer.android.com/studio#command-tools" -ForegroundColor Gray
    Write-Host ""
    
    # Vérifier si Android SDK existe dans l'emplacement par défaut
    $defaultAndroidPath = Join-Path $env:LOCALAPPDATA "Android\Sdk"
    if (Test-Path $defaultAndroidPath) {
        Write-Host "⚠️  Android SDK trouvé à: $defaultAndroidPath" -ForegroundColor Yellow
        $setAndroid = Read-Host "Voulez-vous configurer ANDROID_HOME maintenant? (O/N)"
        if ($setAndroid -eq "O" -or $setAndroid -eq "o") {
            [System.Environment]::SetEnvironmentVariable("ANDROID_HOME", $defaultAndroidPath, "User")
            $env:ANDROID_HOME = $defaultAndroidPath
            Write-Host "✅ ANDROID_HOME configuré: $defaultAndroidPath" -ForegroundColor Green
            Write-Host "   Redémarrez votre terminal pour que les changements prennent effet" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "📊 Résumé de la configuration:" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

# Afficher l'état actuel
if (Test-JavaInstalled) {
    $javaVersion = java -version 2>&1 | Select-Object -First 1
    Write-Host "Java: ✅ Installé - $javaVersion" -ForegroundColor Green
} else {
    Write-Host "Java: ❌ Non installé" -ForegroundColor Red
}

if ($env:JAVA_HOME) {
    Write-Host "JAVA_HOME: ✅ $env:JAVA_HOME" -ForegroundColor Green
} else {
    Write-Host "JAVA_HOME: ❌ Non configuré" -ForegroundColor Red
}

if ($env:ANDROID_HOME) {
    Write-Host "ANDROID_HOME: ✅ $env:ANDROID_HOME" -ForegroundColor Green
} else {
    Write-Host "ANDROID_HOME: ⚠️  Non configuré (optionnel)" -ForegroundColor Yellow
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

# Vérifier si tout est prêt
$javaOk = Test-JavaInstalled -and $env:JAVA_HOME
if ($javaOk) {
    Write-Host "✅ Configuration prête pour compiler des APKs!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Prochaines étapes:" -ForegroundColor Yellow
    Write-Host "1. Redémarrez votre terminal (ou PowerShell)" -ForegroundColor White
    Write-Host "2. Redémarrez le backend: npm run dev:backend" -ForegroundColor White
    Write-Host "3. Les APKs seront compilés automatiquement lors des builds" -ForegroundColor White
} else {
    Write-Host "⚠️  Configuration incomplète" -ForegroundColor Yellow
    Write-Host "   Installez Java JDK 17+ et configurez JAVA_HOME pour activer la compilation d'APKs" -ForegroundColor White
}

Write-Host ""

