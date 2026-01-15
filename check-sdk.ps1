Write-Host "Verification de la configuration Android..." -ForegroundColor Cyan

# Java
Write-Host "`nJAVA:" -ForegroundColor Yellow
if ($env:JAVA_HOME) {
    Write-Host "  JAVA_HOME: $env:JAVA_HOME" -ForegroundColor Green
    java -version
} else {
    Write-Host "  JAVA_HOME non defini" -ForegroundColor Red
}

# Android SDK
Write-Host "`nANDROID SDK:" -ForegroundColor Yellow
if ($env:ANDROID_HOME) {
    Write-Host "  ANDROID_HOME: $env:ANDROID_HOME" -ForegroundColor Green
    if (Test-Path $env:ANDROID_HOME) {
        Write-Host "  Repertoire existe: OK" -ForegroundColor Green
        
        # Chercher sdkmanager
        $paths = @(
            "$env:ANDROID_HOME\cmdline-tools\latest\bin\sdkmanager.bat",
            "$env:ANDROID_HOME\cmdline-tools\bin\sdkmanager.bat",
            "$env:ANDROID_HOME\tools\bin\sdkmanager.bat"
        )
        
        $found = $false
        foreach ($p in $paths) {
            if (Test-Path $p) {
                Write-Host "  sdkmanager trouve: $p" -ForegroundColor Green
                $found = $true
                break
            }
        }
        
        if (-not $found) {
            Write-Host "  sdkmanager NON trouve (optionnel)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  Repertoire n'existe pas" -ForegroundColor Red
    }
} else {
    Write-Host "  ANDROID_HOME non defini (optionnel)" -ForegroundColor Yellow
}

Write-Host "`nPour generer des APK, il faut au minimum Java JDK 17+" -ForegroundColor Cyan
