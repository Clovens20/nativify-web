@echo off
REM Script Windows pour promouvoir un utilisateur en admin

if "%~1"=="" (
    echo ❌ Erreur: Email requis
    echo.
    echo Usage:
    echo   setup-admin.bat your-email@example.com
    echo.
    echo OU avec PowerShell:
    echo   curl.exe -X POST "http://localhost:8000/api/admin/setup?email=your-email@example.com^&secret=nativiweb_admin_setup_2024"
    exit /b 1
)

set EMAIL=%~1
set BACKEND_URL=http://localhost:8000
set SECRET=nativiweb_admin_setup_2024

echo 🔄 Promotion de %EMAIL% en admin...
echo.

curl.exe -X POST "%BACKEND_URL%/api/admin/setup?email=%EMAIL%&secret=%SECRET%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ SUCCÈS!
    echo.
    echo 📝 Instructions:
    echo    1. Déconnectez-vous de l'application
    echo    2. Reconnectez-vous avec cet email
    echo    3. Vous devriez maintenant avoir accès à /admin
) else (
    echo.
    echo ❌ ERREUR lors de la promotion
    echo 💡 Assurez-vous que le backend tourne sur %BACKEND_URL%
)

