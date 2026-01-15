# Guide de Test sur Devices Réels

## 📱 Préparation

### Android

1. **Activer le mode développeur** :
   - Aller dans `Paramètres` > `À propos du téléphone`
   - Appuyer 7 fois sur `Numéro de build`
   - Retourner dans `Paramètres` > `Options développeur`
   - Activer `Débogage USB`

2. **Installer ADB** (si pas déjà fait) :
   ```bash
   # Windows (via Android SDK)
   # ADB est dans: C:\Users\<user>\AppData\Local\Android\Sdk\platform-tools
   ```

3. **Vérifier la connexion** :
   ```bash
   adb devices
   # Devrait afficher votre device
   ```

### iOS

1. **Activer le mode développeur** :
   - Aller dans `Réglages` > `Confidentialité et sécurité` > `Mode développeur`
   - Activer le mode développeur

2. **Installer Xcode** (nécessaire pour signer et installer)

## 🧪 Tests à Effectuer

### 1. Installation de l'APK/IPA

**Android** :
```bash
# Télécharger l'APK depuis le dashboard
# Installer via ADB
adb install -r path/to/app.apk

# Ou installer manuellement depuis le téléphone
# Transférer l'APK et ouvrir depuis le gestionnaire de fichiers
```

**iOS** :
- Utiliser Xcode pour installer sur un device connecté
- Ou utiliser TestFlight pour distribution

### 2. Tests des Features Natives

#### ✅ Camera
```javascript
// Dans la console du navigateur de l'app
window.NativiWeb.takePicture()
  .then(result => console.log('Photo:', result))
  .catch(err => console.error('Erreur:', err));
```

**Vérifier** :
- [ ] L'appareil photo s'ouvre
- [ ] La photo est capturée
- [ ] Le chemin du fichier est retourné

#### ✅ Géolocalisation
```javascript
window.NativiWeb.getCurrentPosition()
  .then(pos => console.log('Position:', pos))
  .catch(err => console.error('Erreur:', err));
```

**Vérifier** :
- [ ] La permission est demandée
- [ ] Les coordonnées GPS sont retournées
- [ ] La précision est raisonnable (< 50m)

#### ✅ Contacts
```javascript
window.NativiWeb.getContacts()
  .then(contacts => console.log('Contacts:', contacts))
  .catch(err => console.error('Erreur:', err));
```

**Vérifier** :
- [ ] La permission est demandée
- [ ] La liste des contacts est retournée
- [ ] Les noms et téléphones sont corrects

#### ✅ Push Notifications

**Android (FCM)** :
1. Obtenir le token FCM depuis l'app :
```javascript
// Dans l'app native, le token est généré automatiquement
// Vérifier dans les logs Android: adb logcat | grep FCM
```

2. Envoyer une notification via l'API :
```bash
curl -X POST http://localhost:8000/api/push/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "Test Notification",
    "body": "Ceci est un test",
    "android_tokens": ["FCM_TOKEN_ICI"]
  }'
```

**Vérifier** :
- [ ] La notification apparaît dans la barre de notification
- [ ] Le clic ouvre l'app
- [ ] Les données personnalisées sont reçues

#### ✅ In-App Purchases

**Android** :
```javascript
// Initialiser
window.NativiWeb.initializeBilling()
  .then(() => {
    // Récupérer les produits
    return window.NativiWeb.getAvailableProducts('inapp');
  })
  .then(products => {
    console.log('Produits:', products);
    // Acheter un produit
    return window.NativiWeb.purchaseProduct('product_id_here');
  })
  .then(result => console.log('Achat:', result))
  .catch(err => console.error('Erreur:', err));
```

**Vérifier** :
- [ ] La connexion Google Play est établie
- [ ] Les produits sont listés
- [ ] Le processus d'achat démarre (sandbox)

#### ✅ Audio/Video Recording
```javascript
// Audio
window.NativiWeb.startAudioRecording()
  .then(() => {
    // Enregistrer pendant 5 secondes
    setTimeout(() => {
      window.NativiWeb.stopAudioRecording()
        .then(result => console.log('Audio:', result));
    }, 5000);
  });

// Video
window.NativiWeb.startVideoRecording()
  .then(() => {
    setTimeout(() => {
      window.NativiWeb.stopVideoRecording()
        .then(result => console.log('Video:', result));
    }, 5000);
  });
```

**Vérifier** :
- [ ] L'enregistrement démarre
- [ ] Le fichier est créé
- [ ] Le fichier est jouable

#### ✅ QR Scanner
```javascript
window.NativiWeb.scanQRCode()
  .then(result => console.log('QR Code:', result))
  .catch(err => console.error('Erreur:', err));
```

**Vérifier** :
- [ ] Le scanner s'ouvre
- [ ] Le QR code est détecté
- [ ] Les données sont retournées

### 3. Tests Multi-Devices

**Devices à tester** :
- [ ] Android 10+ (API 29+)
- [ ] Android 13+ (API 33+)
- [ ] iOS 15+
- [ ] iOS 17+

**Points à vérifier** :
- [ ] L'app se lance correctement
- [ ] Les permissions sont demandées correctement
- [ ] Les features natives fonctionnent
- [ ] Pas de crash
- [ ] Performance acceptable

### 4. Tests de Performance

**Métriques à surveiller** :
- Temps de lancement : < 3 secondes
- Utilisation mémoire : < 200MB
- Taille de l'APK : < 50MB
- Taille de l'IPA : < 100MB

**Outils** :
```bash
# Android - Profiler
adb shell dumpsys meminfo com.nativiweb.appname

# iOS - Instruments (via Xcode)
```

### 5. Tests de Publication

**Android - Play Store** :
1. Générer un AAB (pas un APK) :
   ```bash
   # Dans le projet Android généré
   ./gradlew bundleRelease
   # AAB dans: app/build/outputs/bundle/release/app-release.aab
   ```

2. Tester l'upload via l'API :
   ```bash
   curl -X POST http://localhost:8000/api/builds/{build_id}/publish \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "google_credentials_path": "/path/to/service-account.json",
       "track": "internal"
     }'
   ```

**iOS - App Store** :
1. Générer un IPA signé (via Xcode ou Fastlane)
2. Tester l'upload via l'API :
   ```bash
   curl -X POST http://localhost:8000/api/builds/{build_id}/publish \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "apple_key_id": "KEY_ID",
       "apple_issuer_id": "ISSUER_ID",
       "apple_private_key_path": "/path/to/AuthKey.p8",
       "ipa_path": "/path/to/app.ipa",
       "apple_id": "your@email.com",
       "app_specific_password": "xxxx-xxxx-xxxx-xxxx"
     }'
   ```

## 🐛 Debugging

### Android Logs
```bash
# Voir tous les logs
adb logcat

# Filtrer par tag
adb logcat -s NativiWebBridge

# Filtrer par niveau
adb logcat *:E  # Erreurs seulement
```

### iOS Logs
```bash
# Via Xcode Console
# Ou via device logs
xcrun simctl spawn booted log stream --level=error
```

### Erreurs Communes

**"Permission denied"** :
- Vérifier que les permissions sont dans `AndroidManifest.xml`
- Vérifier que les permissions sont demandées à l'exécution (Android 6+)

**"Class not found"** :
- Vérifier que les dépendances sont dans `build.gradle`
- Vérifier que le package name est correct

**"APK not installable"** :
- Vérifier la signature
- Vérifier que l'app précédente est désinstallée
- Vérifier la compatibilité Android (minSdkVersion)

## ✅ Checklist Finale

Avant de soumettre au challenge :

- [ ] Tous les tests passent sur au moins 2 devices Android
- [ ] Tous les tests passent sur au moins 1 device iOS
- [ ] Les push notifications fonctionnent
- [ ] La publication aux stores est testée (au moins en sandbox)
- [ ] Aucun crash majeur
- [ ] Les performances sont acceptables
- [ ] La documentation est à jour

