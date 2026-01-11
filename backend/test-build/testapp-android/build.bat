@echo off
REM Script de build automatique pour TestApp
REM Ce script compile automatiquement l'APK de l'application

echo 🚀 Démarrage de la compilation de TestApp...
echo.

REM Vérifier que Java est installé
java -version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Erreur: Java n'est pas installé.
    echo    Installez Java JDK 17 ou supérieur: https://adoptium.net/
    exit /b 1
)

echo ✓ Java détecté
java -version
echo.

REM Vérifier si gradle-wrapper.jar existe, sinon le télécharger
if not exist "gradle\wrapper\gradle-wrapper.jar" (
    echo ⚠️  Gradle Wrapper JAR non trouvé. Téléchargement...
    if not exist "gradle\wrapper" mkdir "gradle\wrapper"
    curl -L -o "gradle\wrapper\gradle-wrapper.jar" "https://raw.githubusercontent.com/gradle/gradle/v8.2.0/gradle/wrapper/gradle-wrapper.jar"
    if %ERRORLEVEL% neq 0 (
        echo ❌ Erreur: Impossible de télécharger gradle-wrapper.jar
        echo    Solution: Ouvrez le projet dans Android Studio, il téléchargera automatiquement tous les fichiers nécessaires
        exit /b 1
    )
    echo ✓ Gradle Wrapper JAR téléchargé
)

REM Compiler l'APK Debug
echo 📦 Compilation de l'APK Debug...
echo    (Cela peut prendre 2-10 minutes lors de la première compilation)
echo.
call gradlew.bat assembleDebug

if %ERRORLEVEL% equ 0 (
    echo.
    echo ✅ Compilation réussie!
    echo.
    echo 📱 Votre APK est disponible dans:
    echo    app\build\outputs\apk\debug\app-debug.apk
    echo.
    echo 📲 Pour installer l'APK sur votre appareil Android:
    echo    1. Activez 'Sources inconnues' dans les paramètres de sécurité
    echo    2. Transférez l'APK sur votre appareil (USB, email, etc.)
    echo    3. Ouvrez le fichier APK sur l'appareil pour l'installer
    echo.
) else (
    echo.
    echo ❌ Erreur lors de la compilation
    echo.
    echo 💡 Solutions possibles:
    echo    1. Utilisez Android Studio (recommandé) : Ouvrez le projet dans Android Studio
    echo    2. Vérifiez que l'Android SDK est installé et configuré
    echo    3. Créez un fichier local.properties avec: sdk.dir=C:\chemin\vers\android\sdk
    exit /b 1
)
