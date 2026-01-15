# TestApp - Android

## ⚠️ IMPORTANT : Ce fichier est un PROJET SOURCE, pas un APK installable

Le fichier ZIP que vous avez téléchargé contient le **code source** du projet Android. 
Pour obtenir un APK installable, vous devez **compiler** le projet.

### Configuration
- **Package Name**: com.test.app
- **URL Web**: https://example.com
- **Plateforme**: Android

## 🚀 Compilation Rapide (Méthode Automatique)

### Option 1 : Script de Build Automatique (Recommandé)

**Sur Linux/Mac :**
```bash
unzip testapp-android.zip
cd testapp-android
chmod +x build.sh
./build.sh
```

**Sur Windows :**
```cmd
REM Décompresser le ZIP, puis dans le dossier du projet:
build.bat
```

Le script va automatiquement :
- ✅ Vérifier que Java est installé
- ✅ Télécharger Gradle si nécessaire
- ✅ Compiler l'APK Debug
- ✅ Afficher l'emplacement de l'APK généré

**L'APK sera disponible dans :** `app/build/outputs/apk/debug/app-debug.apk`

### Option 2 : Android Studio (Méthode Visuelle)

1. **Installer Android Studio**
   - Téléchargez depuis : https://developer.android.com/studio
   - Installez-le et lancez-le

2. **Ouvrir le projet**
   - Dans Android Studio : `File > Open`
   - Sélectionner le dossier décompressé
   - Android Studio va automatiquement configurer Gradle

3. **Compiler l'APK**
   - Menu : `Build > Build Bundle(s) / APK(s) > Build APK(s)`
   - Attendre la fin de la compilation
   - Cliquer sur "locate" dans la notification pour voir l'APK

4. **Installer sur un appareil**
   - Transférez `app/build/outputs/apk/debug/app-debug.apk` sur votre téléphone
   - Activez "Sources inconnues" dans Paramètres > Sécurité
   - Ouvrez l'APK sur votre téléphone pour l'installer

## 📲 Installation de l'APK sur votre appareil

1. **Transférer l'APK**
   - Par câble USB : Copiez `app-debug.apk` sur votre téléphone
   - Par email : Envoyez-vous l'APK par email et ouvrez-le sur le téléphone
   - Par cloud : Uploadez sur Google Drive/Dropbox et téléchargez sur le téléphone

2. **Autoriser l'installation**
   - Allez dans **Paramètres > Sécurité**
   - Activez **"Sources inconnues"** ou **"Installer des applications inconnues"**
   - Sélectionnez le navigateur/la source que vous utiliserez

3. **Installer**
   - Ouvrez le fichier APK sur votre téléphone
   - Suivez les instructions à l'écran
   - L'application apparaîtra dans votre liste d'applications

## ⚠️ Notes Importantes

### Pour le Développement
- L'APK Debug généré est **non signé** et destiné uniquement aux tests
- Vous pouvez l'installer directement sur votre appareil sans compte développeur

### Pour la Production (Publication sur Play Store)
- Vous devez créer un **keystore** pour signer l'APK
- Utilisez `./gradlew assembleRelease` avec votre keystore configuré
- Ou utilisez `Build > Generate Signed Bundle / APK` dans Android Studio

### Configuration Requise
- **Min SDK**: Android 5.0 (API 21) minimum
- **Target SDK**: Android 13 (API 33)
- **Compile SDK**: Android 13 (API 33)

## 🐛 Dépannage

### Erreur "SDK not found"
- Installez Android Studio ou téléchargez l'Android SDK
- Créez un fichier `local.properties` avec : `sdk.dir=/chemin/vers/android/sdk`

### Erreur "Java not found"
- Installez Java JDK 17 ou supérieur : https://adoptium.net/
- Configurez la variable JAVA_HOME

### Erreur de compilation Gradle
- Vérifiez votre connexion Internet (Gradle doit télécharger des dépendances)
- Ouvrez le projet dans Android Studio pour une meilleure gestion des erreurs

## 📚 Documentation

Pour plus d'informations :
- [NativiWeb Studio Documentation](https://docs.nativiweb.io)
- [Android Developer Guide](https://developer.android.com)
- [Gradle Documentation](https://docs.gradle.org)
