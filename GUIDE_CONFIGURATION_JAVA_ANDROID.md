# 🚀 Guide de Configuration Java JDK et Android SDK

Ce guide vous aidera à installer et configurer Java JDK et Android SDK pour activer la compilation automatique d'APKs dans NativiWeb Studio.

## 📋 Vue d'ensemble

Pour compiler automatiquement des APKs Android, vous avez besoin de :
- ✅ **Java JDK 17+** (requis)
- ⚠️ **Android SDK** (optionnel mais recommandé)

## 🎯 Méthode Rapide (Recommandée)

Utilisez le script PowerShell fourni pour une configuration automatique :

```powershell
.\scripts\setup-java-android.ps1
```

Ce script va :
1. Vérifier si Java est installé
2. Vous guider pour l'installation si nécessaire
3. Configurer automatiquement JAVA_HOME
4. Vérifier et configurer ANDROID_HOME (optionnel)

## 📦 Installation Manuelle

### Étape 1 : Installer Java JDK 17+

#### Option A : Eclipse Temurin (Recommandé)

1. **Télécharger Java JDK 17 LTS**
   - Allez sur : https://adoptium.net/
   - Choisissez "Temurin 17" (LTS)
   - Sélectionnez votre système d'exploitation (Windows x64)
   - Téléchargez le fichier `.msi`

2. **Installer**
   - Exécutez le fichier `.msi` téléchargé
   - Suivez l'assistant d'installation
   - ✅ Cochez "Add to PATH" si proposé
   - ✅ Cochez "Set JAVA_HOME variable" si proposé

3. **Vérifier l'installation**
   ```powershell
   java -version
   ```
   Vous devriez voir quelque chose comme :
   ```
   openjdk version "17.0.x" ...
   ```

#### Option B : Oracle JDK

1. Téléchargez depuis : https://www.oracle.com/java/technologies/downloads/#java17
2. Installez avec les options par défaut

### Étape 2 : Configurer JAVA_HOME

#### Méthode Automatique (PowerShell en tant qu'Administrateur)

```powershell
# Trouver le chemin d'installation Java
# Généralement : C:\Program Files\Eclipse Adoptium\jdk-17.x.x-hotspot
# ou : C:\Program Files\Java\jdk-17

# Configurer JAVA_HOME (remplacez le chemin par le vôtre)
[System.Environment]::SetEnvironmentVariable("JAVA_HOME", "C:\Program Files\Eclipse Adoptium\jdk-17.0.10+9-hotspot", "Machine")
```

#### Méthode Manuelle (Interface Graphique)

1. Ouvrez "Paramètres système avancés"
   - Appuyez sur `Win + R`
   - Tapez `sysdm.cpl` et appuyez sur Entrée
   - Cliquez sur l'onglet "Avancé"
   - Cliquez sur "Variables d'environnement"

2. Créer/modifier JAVA_HOME
   - Dans "Variables système", cliquez sur "Nouveau"
   - Nom de la variable : `JAVA_HOME`
   - Valeur : Le chemin vers votre installation JDK (ex: `C:\Program Files\Eclipse Adoptium\jdk-17.0.10+9-hotspot`)
   - Cliquez sur "OK"

3. Ajouter Java au PATH (si pas déjà fait)
   - Sélectionnez "Path" dans les variables système
   - Cliquez sur "Modifier"
   - Ajoutez : `%JAVA_HOME%\bin`
   - Cliquez sur "OK"

4. **Redémarrer votre terminal/PowerShell** pour que les changements prennent effet

### Étape 3 : Installer Android SDK (Optionnel)

L'Android SDK n'est pas strictement nécessaire car Gradle peut télécharger automatiquement les composants nécessaires, mais c'est recommandé pour des builds plus rapides.

#### Option A : Android Studio (Recommandé - Plus Simple)

1. **Télécharger Android Studio**
   - Allez sur : https://developer.android.com/studio
   - Téléchargez et installez Android Studio

2. **Android Studio installera automatiquement l'Android SDK**
   - Emplacement par défaut : `C:\Users\<VotreNom>\AppData\Local\Android\Sdk`

3. **Configurer ANDROID_HOME**
   ```powershell
   [System.Environment]::SetEnvironmentVariable("ANDROID_HOME", "$env:LOCALAPPDATA\Android\Sdk", "User")
   ```

#### Option B : Command Line Tools uniquement

1. Téléchargez les command line tools depuis : https://developer.android.com/studio#command-tools
2. Extrayez dans un dossier (ex: `C:\Android\Sdk`)
3. Configurez ANDROID_HOME :
   ```powershell
   [System.Environment]::SetEnvironmentVariable("ANDROID_HOME", "C:\Android\Sdk", "User")
   ```

## ✅ Vérification de la Configuration

### Méthode Rapide

Utilisez le script de vérification :

```powershell
.\scripts\check-build-dependencies.ps1
```

### Vérification Manuelle

```powershell
# Vérifier Java
java -version

# Vérifier JAVA_HOME
echo $env:JAVA_HOME

# Vérifier ANDROID_HOME (optionnel)
echo $env:ANDROID_HOME
```

## 🔄 Redémarrer le Backend

Après avoir configuré Java et Android SDK :

1. **Arrêtez le backend** (Ctrl+C dans le terminal)
2. **Redémarrez le backend** :
   ```powershell
   npm run dev:backend
   # ou
   npm run dev
   ```

3. **Vérifiez les logs** - Vous devriez voir :
   ```
   ✅ AndroidBuilder disponible - Compilation d'APK activée
   ```

Au lieu de :
   ```
   ⚠️ AndroidBuilder disponible mais dépendances manquantes
   ```

## 🎯 Test de Compilation

Pour tester si la compilation fonctionne :

1. Créez un projet dans l'interface web
2. Lancez un build Android
3. Le système devrait compiler automatiquement l'APK
4. L'APK sera disponible au téléchargement une fois la compilation terminée

## 🐛 Dépannage

### Erreur "Java not found"

1. Vérifiez que Java est installé : `java -version`
2. Vérifiez que JAVA_HOME est configuré : `echo $env:JAVA_HOME`
3. Redémarrez votre terminal après avoir configuré JAVA_HOME
4. Redémarrez le backend

### Erreur "Android SDK not found"

- L'Android SDK est optionnel, le build peut fonctionner sans
- Si vous voulez l'installer, suivez l'étape 3 ci-dessus
- Vérifiez que ANDROID_HOME pointe vers le bon répertoire

### Erreur de compilation Gradle

1. Vérifiez votre connexion Internet (Gradle doit télécharger des dépendances)
2. La première compilation peut prendre 5-10 minutes (téléchargement des dépendances)
3. Vérifiez les logs du backend pour plus de détails

### Les variables d'environnement ne sont pas prises en compte

1. **Redémarrez votre terminal/PowerShell** après avoir configuré les variables
2. Si ça ne fonctionne pas, redémarrez votre ordinateur
3. Vérifiez que vous avez configuré les variables au bon niveau :
   - `User` : Pour votre utilisateur uniquement
   - `Machine` : Pour tous les utilisateurs (nécessite les droits administrateur)

## 📚 Ressources

- [Eclipse Temurin (Java JDK)](https://adoptium.net/)
- [Android Studio](https://developer.android.com/studio)
- [Documentation Android SDK](https://developer.android.com/studio/command-line)
- [Documentation Gradle](https://docs.gradle.org/)

## 💡 Astuce

Pour une configuration rapide, utilisez les scripts fournis :
- `.\scripts\setup-java-android.ps1` - Configuration interactive
- `.\scripts\check-build-dependencies.ps1` - Vérification rapide

