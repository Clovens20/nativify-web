# Configuration du Système de Build Android

Ce document explique comment configurer le backend pour compiler réellement les projets Android et générer des APKs fonctionnels.

## ✅ Fonctionnalités Implémentées

Le système inclut maintenant :
- ✅ **Compilation réelle des projets Android** avec Gradle
- ✅ **Génération d'APKs fonctionnels** prêts à être installés sur des appareils Android
- ✅ **Vérification automatique des dépendances** (Java, Android SDK)
- ✅ **Téléchargement automatique** du gradle-wrapper.jar si nécessaire

## 📋 Prérequis

Pour que le système de build fonctionne correctement, vous devez installer :

### 1. Java JDK 17 ou supérieur

**Windows:**
```powershell
# Vérifier si Java est installé
java -version

# Si non installé, télécharger depuis:
# https://adoptium.net/
# Installer JDK 17 ou supérieur
```

**Linux/Mac:**
```bash
# Vérifier si Java est installé
java -version

# Installer avec le gestionnaire de paquets
# Ubuntu/Debian:
sudo apt update && sudo apt install openjdk-17-jdk

# Mac (avec Homebrew):
brew install openjdk@17
```

**Configurer JAVA_HOME:**

**Windows:**
```powershell
# Trouver le chemin d'installation de Java (généralement: C:\Program Files\Java\jdk-17)
# Puis configurer la variable d'environnement:
[System.Environment]::SetEnvironmentVariable("JAVA_HOME", "C:\Program Files\Java\jdk-17", "Machine")
```

**Linux/Mac:**
```bash
# Trouver le chemin Java
which java
# ou
echo $JAVA_HOME

# Configurer JAVA_HOME dans ~/.bashrc ou ~/.zshrc
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
# (Ajustez le chemin selon votre installation)
```

### 2. Android SDK (Optionnel mais Recommandé)

L'Android SDK n'est pas strictement nécessaire car Gradle peut télécharger automatiquement les composants nécessaires, mais c'est recommandé pour un build plus rapide.

**Option A: Android Studio (Recommandé)**
1. Télécharger Android Studio depuis: https://developer.android.com/studio
2. Installer Android Studio
3. Android Studio installera automatiquement l'Android SDK
4. Notez le chemin d'installation (généralement):
   - Windows: `C:\Users\<username>\AppData\Local\Android\Sdk`
   - Linux/Mac: `~/Android/Sdk`

**Option B: SDK Tools uniquement**
```bash
# Télécharger les command line tools
# https://developer.android.com/studio#command-tools

# Extraire et configurer
# Linux/Mac:
unzip commandlinetools-linux-*.zip
mkdir -p ~/android-sdk/cmdline-tools/latest
mv cmdline-tools/* ~/android-sdk/cmdline-tools/latest/

# Windows: Extraire avec un outil de décompression
```

**Configurer ANDROID_HOME:**

**Windows:**
```powershell
# Trouver le chemin Android SDK (généralement: C:\Users\<username>\AppData\Local\Android\Sdk)
# Puis configurer la variable d'environnement:
[System.Environment]::SetEnvironmentVariable("ANDROID_HOME", "C:\Users\<username>\AppData\Local\Android\Sdk", "User")
```

**Linux/Mac:**
```bash
# Configurer ANDROID_HOME dans ~/.bashrc ou ~/.zshrc
export ANDROID_HOME=~/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin
```

## 🚀 Vérification de l'Installation

Après avoir installé Java et (optionnellement) Android SDK, redémarrez le backend et vérifiez les logs:

```bash
# Démarrer le backend
cd backend
python -m uvicorn main:app --reload

# Les logs devraient afficher:
# INFO: Java trouvé: openjdk version "17.0.x"
# INFO: Android SDK trouvé: /path/to/android/sdk (si configuré)
```

## 📱 Comment ça Fonctionne

1. **L'utilisateur crée un build** dans l'interface web
2. **Le backend génère le projet source** Android (ZIP avec code source)
3. **Le système extrait le projet** dans un répertoire temporaire
4. **Le système compile réellement l'APK** avec Gradle:
   - Vérifie que Java est disponible
   - Vérifie que Android SDK est disponible (optionnel)
   - Exécute `./gradlew assembleDebug` pour compiler l'APK
   - Récupère l'APK compilé depuis `app/build/outputs/apk/debug/app-debug.apk`
5. **L'APK compilé est retourné** directement au téléchargement
6. **L'utilisateur peut installer l'APK** sur son appareil Android

## ⚠️ Note Importante sur les APKs Générés

Les APKs générés sont des **APKs Debug** non signés. Ils sont :
- ✅ **Installables** sur des appareils Android (après activation de "Sources inconnues")
- ✅ **Testables** sur des appareils réels
- ❌ **Non publiable** sur le Play Store (nécessite un APK Release signé)

Pour publier sur le Play Store, l'utilisateur devra :
1. Créer un keystore pour la signature
2. Compiler un APK Release signé
3. Ou utiliser Android Studio pour générer un AAB signé

## 🐛 Dépannage

### Erreur "Java not found"
- Vérifiez que Java JDK 17+ est installé: `java -version`
- Vérifiez que JAVA_HOME est configuré correctement
- Redémarrez le backend après avoir configuré JAVA_HOME

### Erreur "Android SDK not found"
- L'Android SDK est optionnel, le build peut fonctionner sans
- Si vous voulez l'installer, suivez les instructions ci-dessus
- Vérifiez que ANDROID_HOME est configuré si vous installez le SDK

### Erreur de compilation Gradle
- Vérifiez votre connexion Internet (Gradle doit télécharger des dépendances)
- Vérifiez les logs du backend pour plus de détails
- La première compilation peut prendre 5-10 minutes (téléchargement des dépendances)

### Timeout de compilation
- Par défaut, le timeout est de 10 minutes
- Si cela ne suffit pas, vous pouvez augmenter le timeout dans `android_builder.py` ligne `timeout=600`

## 🔒 Sécurité

Les APKs générés sont compilés dans des répertoires temporaires qui sont automatiquement nettoyés après compilation. Aucun code source n'est conservé sur le serveur après le build.

## 📚 Documentation Additionnelle

Pour plus d'informations :
- [Android Developer Documentation](https://developer.android.com/)
- [Gradle Documentation](https://docs.gradle.org/)
- [Java JDK Documentation](https://adoptium.net/documentation/)

