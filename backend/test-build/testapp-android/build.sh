#!/bin/bash
# Script de build automatique pour TestApp
# Ce script compile automatiquement l'APK de l'application

set -e

echo "🚀 Démarrage de la compilation de TestApp..."
echo ""

# Vérifier que Java est installé
if ! command -v java &> /dev/null; then
    echo "❌ Erreur: Java n'est pas installé."
    echo "   Installez Java JDK 17 ou supérieur: https://adoptium.net/"
    exit 1
fi

echo "✓ Java détecté: $(java -version 2>&1 | head -n 1)"
echo ""

# Vérifier si gradle-wrapper.jar existe, sinon le télécharger
if [ ! -f "gradle/wrapper/gradle-wrapper.jar" ]; then
    echo "⚠️  Gradle Wrapper JAR non trouvé. Téléchargement..."
    mkdir -p gradle/wrapper
    curl -L -o gradle/wrapper/gradle-wrapper.jar https://raw.githubusercontent.com/gradle/gradle/v8.2.0/gradle/wrapper/gradle-wrapper.jar
    if [ $? -ne 0 ]; then
        echo "❌ Erreur: Impossible de télécharger gradle-wrapper.jar"
        echo "   Solution: Ouvrez le projet dans Android Studio, il téléchargera automatiquement tous les fichiers nécessaires"
        exit 1
    fi
    echo "✓ Gradle Wrapper JAR téléchargé"
fi

# Rendre gradlew exécutable
chmod +x ./gradlew

# Compiler l'APK Debug
echo "📦 Compilation de l'APK Debug..."
echo "   (Cela peut prendre 2-10 minutes lors de la première compilation)"
echo ""
./gradlew assembleDebug

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Compilation réussie!"
    echo ""
    echo "📱 Votre APK est disponible dans:"
    echo "   app/build/outputs/apk/debug/app-debug.apk"
    echo ""
    echo "📲 Pour installer l'APK sur votre appareil Android:"
    echo "   1. Activez 'Sources inconnues' dans les paramètres de sécurité"
    echo "   2. Transférez l'APK sur votre appareil (USB, email, etc.)"
    echo "   3. Ouvrez le fichier APK sur l'appareil pour l'installer"
    echo ""
else
    echo ""
    echo "❌ Erreur lors de la compilation"
    echo ""
    echo "💡 Solutions possibles:"
    echo "   1. Utilisez Android Studio (recommandé) : Ouvrez le projet dans Android Studio"
    echo "   2. Vérifiez que l'Android SDK est installé et configuré"
    echo "   3. Créez un fichier local.properties avec: sdk.dir=/chemin/vers/android/sdk"
    exit 1
fi
