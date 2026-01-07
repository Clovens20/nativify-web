# NativiWeb SDK Documentation

## Prerequisites

Avant d'intégrer le SDK NativiWeb dans votre application, assurez-vous que votre environnement répond aux exigences suivantes :

### 📱 Versions de Plateforme Minimales

**Android :**
- **API Level minimum** : Android 5.0 (API Level 21) / Lollipop
- **API Level recommandé** : Android 8.0 (API Level 26) / Oreo ou supérieur
- **Gradle** : Version 7.0+ (inclus dans le projet généré)
- **Kotlin** : Version 1.7.0+ (inclus dans le projet généré)

**iOS :**
- **Version iOS minimum** : iOS 13.0
- **Version iOS recommandée** : iOS 15.0 ou supérieur
- **Xcode** : Version 14.0+ (requis pour compiler les projets générés)
- **Swift** : Version 5.5+ (inclus dans le projet généré)

### 🖥️ Navigateurs Compatibles (pour le développement)

L'interface NativiWeb Studio et le développement web sont compatibles avec :
- ✅ **Chrome** : Version 90+
- ✅ **Firefox** : Version 88+
- ✅ **Safari** : Version 14+
- ✅ **Edge** : Version 90+
- ⚠️ **Note** : L'interface nécessite JavaScript activé

### 💻 Node.js et npm

**Versions requises :**
- **Node.js** : Version 18.0.0 ou supérieure (LTS recommandé)
- **npm** : Version 9.0.0 ou supérieure (inclus avec Node.js)

**Vérification :**
```bash
node --version  # Doit afficher v18.x.x ou supérieur
npm --version   # Doit afficher 9.x.x ou supérieur
```

### 🔐 Comptes Développeur

**Apple Developer Account :**
- **Requis pour** : Publication sur l'App Store, utilisation de fonctionnalités natives iOS
- **Coût** : 99$/an (individuel) ou 299$/an (entreprise)
- **Inscription** : https://developer.apple.com/programs/
- **Certificats requis** :
  - Certificat de développement (Development Certificate)
  - Certificat de distribution (Distribution Certificate)
  - Profils d'approvisionnement (Provisioning Profiles)
  - Identifiants App ID
- ⚠️ **Important** : Nécessaire uniquement pour la compilation finale et la publication. Non requis pour le développement local ni pour générer les projets.

**Google Play Console :**
- **Requis pour** : Publication sur Google Play Store
- **Coût** : 25$ (paiement unique, à vie)
- **Inscription** : https://play.google.com/console/
- **Certificats requis** :
  - Keystore de signature (pour signer l'APK/AAB)
  - Certificat de signature d'application (obligatoire pour la publication)
- ⚠️ **Important** : Nécessaire uniquement pour la publication finale. Non requis pour le développement local.

### 🔑 Identifiants et Certificats

**Pour Android :**
- **Keystore** : Fichier `.jks` ou `.keystore` pour signer l'application
  - Génération : `keytool -genkey -v -keystore my-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias my-key-alias`
- **SHA-1/SHA-256** : Empreintes pour Firebase/Google Services (si nécessaire)

**Pour iOS :**
- **Team ID** : Identifiant d'équipe Apple Developer
- **Bundle Identifier** : Identifiant unique de l'application (ex: `com.votre-entreprise.mon-app`)
- **Certificat Push Notification** : Pour les notifications push (si activées)

> 💡 **Note** : Les comptes développeur et certificats ne sont pas requis pour le développement local ni pour générer les projets. Ils sont nécessaires uniquement lors de la compilation finale et de la soumission aux stores.

---

## Installation

### Option 1 : Installation via npm/yarn (Recommandé)

```bash
npm install @nativiweb/sdk
# ou
yarn add @nativiweb/sdk
```

### Option 2 : Installation via CDN

```html
<script src="https://cdn.nativiweb.io/sdk/v1/nativiweb-sdk.min.js"></script>
```

### Option 3 : Téléchargement Direct

Téléchargez le SDK depuis votre projet dans NativiWeb Studio et incluez-le dans votre application :

```html
<script src="/path/to/nativiweb-sdk.js"></script>
```

## Step 3 - Intégration SDK

### Installation via NPM (Recommandé pour apps modernes)

```bash
npm install @nativiweb/sdk

# ou

yarn add @nativiweb/sdk
```

### Initialisation Complète avec Gestion d'Erreurs

Créez un fichier `app.js` (ou `sdk-init.js`) pour initialiser le SDK :

```javascript
// app.js

import NativiWeb from '@nativiweb/sdk';

/**
 * Initialise le SDK NativiWeb
 * Cette fonction doit être appelée au démarrage de votre application
 */
async function initializeNativiWeb() {
  try {
    // Configuration d'initialisation
    const config = {
      // Votre clé API obtenue depuis NativiWeb Studio
      apiKey: process.env.NATIVIWEB_API_KEY || 'your-api-key-here',
      
      // ID du projet (optionnel si vous n'avez qu'un seul projet)
      projectId: process.env.NATIVIWEB_PROJECT_ID || 'your-project-id',
      
      // Mode debug (affiche les logs détaillés en développement)
      debug: process.env.NODE_ENV === 'development',
      
      // Callback appelé quand le SDK est prêt
      onReady: () => {
        console.log('✅ NativiWeb SDK initialisé avec succès');
        console.log('Platform:', NativiWeb.platform);
        console.log('Version:', NativiWeb.version);
      },
      
      // Callback appelé en cas d'erreur
      onError: (error) => {
        console.error('❌ Erreur SDK NativiWeb:', error);
        
        // Gestion spécifique des erreurs
        if (error.code === 'INVALID_API_KEY') {
          console.error('Clé API invalide. Vérifiez votre configuration.');
        } else if (error.code === 'NETWORK_ERROR') {
          console.error('Erreur réseau. Vérifiez votre connexion.');
        }
      },
      
      // Options additionnelles
      options: {
        // Délai d'attente pour l'initialisation (en ms)
        timeout: 10000,
        
        // Auto-retry en cas d'échec
        autoRetry: true,
        
        // Nombre de tentatives de retry
        retryCount: 3
      }
    };

    // Initialisation asynchrone du SDK
    const nw = await NativiWeb.init(config);
    
    // Vérification que l'application tourne en mode natif
    if (nw.isNative()) {
      console.log('📱 Application en mode NATIF');
      
      // Code spécifique au mode natif
      setupNativeFeatures(nw);
    } else {
      console.log('🌐 Application en mode WEB');
      
      // Code de fallback pour le web
      setupWebFallbacks();
    }
    
    return nw;
    
  } catch (error) {
    console.error('💥 Échec de l\'initialisation du SDK:', error);
    
    // Gestion de l'erreur et fallback
    handleInitializationError(error);
    
    // Retourner null pour indiquer que le SDK n'est pas disponible
    return null;
  }
}

/**
 * Configuration des fonctionnalités natives
 */
function setupNativeFeatures(nw) {
  // Demander les permissions nécessaires au démarrage
  requestNativePermissions(nw);
  
  // Écouter les événements natifs
  setupNativeEventListeners(nw);
}

/**
 * Configuration des fallbacks web
 */
function setupWebFallbacks() {
  console.log('Utilisation des APIs web standard');
  // Implémentez vos fallbacks web ici
}

/**
 * Gestion des erreurs d'initialisation
 */
function handleInitializationError(error) {
  // Log de l'erreur pour debugging
  if (window.console && window.console.error) {
    console.error('Détails de l\'erreur:', {
      message: error.message,
      code: error.code,
      stack: error.stack
    });
  }
  
  // Optionnel : Envoyer l'erreur à un service de monitoring
  // sendErrorToMonitoring(error);
  
  // Afficher un message à l'utilisateur si nécessaire
  if (error.code === 'INVALID_API_KEY') {
    alert('Erreur de configuration. Veuillez contacter le support.');
  }
}

/**
 * Demander les permissions natives au démarrage
 */
async function requestNativePermissions(nw) {
  try {
    // Permissions pour les notifications
    if (nw.features.notifications) {
      const notifPermission = await nw.requestNotificationPermission();
      console.log('Permission notifications:', notifPermission);
    }
    
    // Vous pouvez demander d'autres permissions ici
    // selon les besoins de votre application
  } catch (error) {
    console.warn('Erreur lors de la demande de permissions:', error);
  }
}

/**
 * Configuration des écouteurs d'événements natifs
 */
function setupNativeEventListeners(nw) {
  // Écouter les push notifications
  nw.on('push-received', (data) => {
    console.log('Notification push reçue:', data);
    // Traiter la notification
  });
  
  // Écouter le retour de l'app en foreground
  nw.on('app-resume', () => {
    console.log('Application revenue au premier plan');
    // Rafraîchir les données, etc.
  });
  
  // Écouter la mise en arrière-plan
  nw.on('app-pause', () => {
    console.log('Application mise en arrière-plan');
    // Sauvegarder l'état, etc.
  });
}

// Initialiser le SDK au chargement de la page
if (typeof window !== 'undefined') {
  // Pour les applications web/navigateur
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeNativiWeb);
  } else {
    initializeNativiWeb();
  }
}

// Export pour utilisation dans d'autres modules
export default initializeNativiWeb;
```

### Initialisation Simplifiée Recommandée

**Méthode asynchrone recommandée :**

```javascript
import NativiWeb from '@nativiweb/sdk';

// Méthode asynchrone recommandée
async function initNativiWeb() {
  try {
    const nw = await NativiWeb.init({
      apiKey: process.env.NATIVIWEB_API_KEY, // Ne jamais hardcoder
      projectId: 'your-project-id',
      debug: process.env.NODE_ENV === 'development',
      
      // Callbacks optionnels
      onReady: () => {
        console.log('NativiWeb SDK ready');
      },
      onError: (error) => {
        console.error('SDK error:', error);
        // Envoi à votre système de monitoring
      }
    });

    // Vérifier si on est en mode natif
    if (nw.isNative()) {
      console.log('Running as native app');
      console.log('Platform:', nw.getPlatform()); // 'ios' ou 'android'
    } else {
      console.log('Running as web app');
    }

    return nw;
  } catch (error) {
    console.error('Failed to initialize NativiWeb:', error.message);
    // Fallback pour fonctionnalités web
    return null;
  }
}

// Utilisation
const nw = await initNativiWeb();
```

### Détection de Plateforme et Code Conditionnel

```javascript
// Exécuter du code spécifique par plateforme
if (nw && nw.isNative()) {
  if (nw.getPlatform() === 'ios') {
    // Code spécifique iOS
    console.log('Running on iOS');
  } else if (nw.getPlatform() === 'android') {
    // Code spécifique Android
    console.log('Running on Android');
  }
}
```

### Détection Mode Natif vs Web

```javascript
// Vérification fiable du mode d'exécution

function detectExecutionMode(nw) {
  if (!nw) {
    return 'web'; // SDK non initialisé = mode web
  }
  
  // Méthode 1 : Propriété isNative
  if (nw.isNative && nw.isNative()) {
    return 'native';
  }
  
  // Méthode 2 : Propriété platform
  if (nw.platform && nw.platform !== 'web') {
    return 'native';
  }
  
  // Méthode 3 : User Agent (fallback)
  const userAgent = navigator.userAgent || '';
  if (userAgent.includes('NativiWeb')) {
    return 'native';
  }
  
  return 'web';
}

// Utilisation
const mode = detectExecutionMode(nwInstance);
console.log('Mode d\'exécution:', mode);
```

## Quick Start

```javascript
// Import simple du SDK
import NativiWeb from '@nativiweb/sdk';

// Initialisation basique
const nw = await NativiWeb.init({
  apiKey: 'your-api-key'
});

// Vérifier si l'app tourne en mode natif
if (nw.isNative()) {
  console.log('📱 Mode natif:', nw.platform); // 'android' ou 'ios'
} else {
  console.log('🌐 Mode web');
}
```

## Core Properties & Methods

### Propriétés

| Property | Type | Description |
|----------|------|-------------|
| `NativiWeb.isNative` | boolean | True si l'app tourne dans un WebView natif |
| `NativiWeb.platform` | string | 'android', 'ios', ou 'web' |
| `NativiWeb.version` | string | Version du SDK (ex: '1.0.0') |

### Méthodes Core

#### `isNative()`

Vérifie si l'application tourne en mode natif.

**Signature TypeScript :**
```typescript
/**
 * Vérifie si l'application tourne en mode natif
 * 
 * @returns {boolean} True si natif, false si web
 * 
 * @platform android, ios, web
 */
isNative(): boolean
```

**Exemple d'utilisation :**
```javascript
const nw = await NativiWeb.init({ apiKey: 'your-key' });

if (nw.isNative()) {
  console.log('Mode natif');
  // Utiliser les fonctionnalités natives
} else {
  console.log('Mode web');
  // Utiliser les fallbacks web
}
```

---

#### `getPlatform()`

Retourne la plateforme actuelle.

**Signature TypeScript :**
```typescript
/**
 * Retourne la plateforme actuelle
 * 
 * @returns {'android' | 'ios' | 'web'}
 * 
 * @platform android, ios, web
 * 
 * @example
 * const platform = nw.getPlatform();
 * if (platform === 'ios') {
 *   // Code spécifique iOS
 * }
 */
getPlatform(): 'android' | 'ios' | 'web'
```

**Exemple d'utilisation :**
```javascript
const nw = await NativiWeb.init({ apiKey: 'your-key' });
const platform = nw.getPlatform();

switch (platform) {
  case 'ios':
    // Code spécifique iOS
    applyiOSStyles();
    break;
  case 'android':
    // Code spécifique Android
    applyAndroidStyles();
    break;
  case 'web':
    // Code web
    applyWebStyles();
    break;
}
```

## SDK Reference

### Device Information

#### `getDeviceInfo()`

Récupère les informations sur l'appareil et les fonctionnalités disponibles.

**Signature TypeScript :**
```typescript
getDeviceInfo(): Promise<DeviceInfo>

interface DeviceInfo {
  platform: 'android' | 'ios' | 'web';
  platformVersion: string;
  appVersion: string;
  sdkVersion: string;
  deviceModel: string;
  deviceManufacturer: string;
  userAgent: string;
  screenWidth: number;
  screenHeight: number;
  pixelRatio: number;
  features: {
    camera: boolean;
    geolocation: boolean;
    notifications: boolean;
    biometrics: boolean;
    haptics: boolean;
    share: boolean;
    clipboard: boolean;
    fileSystem: boolean;
    contacts: boolean;
    deepLinks: boolean;
    appBadge: boolean;
  };
}
```

**Paramètres :** Aucun

**Valeur de retour :** `Promise<DeviceInfo>` - Objet contenant les informations de l'appareil

**Exemple d'utilisation :**
```javascript
try {
  const deviceInfo = await NativiWeb.getDeviceInfo();
  
  console.log('Platform:', deviceInfo.platform); // 'android' | 'ios' | 'web'
  console.log('Version OS:', deviceInfo.platformVersion);
  console.log('Modèle:', deviceInfo.deviceModel);
  
  // Vérifier les fonctionnalités disponibles
  if (deviceInfo.features.camera) {
    console.log('Caméra disponible');
  }
  
  if (deviceInfo.features.biometrics) {
    console.log('Authentification biométrique disponible');
  }
} catch (error) {
  console.error('Erreur lors de la récupération des infos:', error);
  // Gestion de l'erreur
}
```

**Permissions requises :** Aucune

**Disponibilité :** ✅ Android, ✅ iOS, ✅ Web (avec limitations)

---

### Push Notifications

#### `requestNotificationPermission()`

Demande la permission pour afficher des notifications.

**Signature TypeScript :**
```typescript
/**
 * Demande la permission pour les notifications
 * 
 * @returns {Promise<'granted' | 'denied' | 'default'>}
 * @throws {NativiWebError} Si l'appareil ne supporte pas les notifications (code: 'NOT_SUPPORTED')
 * 
 * @platform Android, iOS
 * @permission iOS: NSUserNotificationsUsageDescription dans Info.plist
 * @permission Android: POST_NOTIFICATIONS (Android 13+)
 * 
 * @example
 * try {
 *   const permission = await nw.requestNotificationPermission();
 *   if (permission === 'granted') {
 *     console.log('Permission accordée');
 *     // Obtenir le device token pour les notifications push
 *     const token = await nw.getPushToken();
 *   }
 * } catch (error) {
 *   if (error.code === 'NOT_SUPPORTED') {
 *     console.error('Notifications non supportées');
 *   }
 * }
 */
requestNotificationPermission(): Promise<'granted' | 'denied' | 'default'>
```

**Paramètres :** Aucun

**Valeur de retour :** `Promise<'granted' | 'denied' | 'default'>`
- `'granted'` : Permission accordée
- `'denied'` : Permission refusée
- `'default'` : L'utilisateur n'a pas encore répondu

**Exemple d'utilisation :**
```javascript
try {
  const permission = await NativiWeb.requestNotificationPermission();
  
  if (permission === 'granted') {
    console.log('Permission accordée');
    // Envoyer une notification de test
    await NativiWeb.showNotification({
      title: 'Notifications activées',
      body: 'Vous recevrez maintenant nos notifications'
    });
  } else if (permission === 'denied') {
    console.log('Permission refusée');
    // Afficher un message à l'utilisateur
    alert('Les notifications sont désactivées. Activez-les dans les paramètres.');
  }
} catch (error) {
  if (error.code === 'NOT_SUPPORTED') {
    console.error('Les notifications ne sont pas supportées sur cet appareil');
  } else {
    console.error('Erreur:', error);
  }
}
```

**Permissions requises :**
- **iOS** : `NSUserNotificationsUsageDescription` dans `Info.plist`
  ```xml
  <key>NSUserNotificationsUsageDescription</key>
  <string>Nous avons besoin de votre permission pour vous envoyer des notifications</string>
  ```
- **Android** : `POST_NOTIFICATIONS` (Android 13+ / API 33+)
  ```xml
  <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
  ```

**Disponibilité :** ✅ Android (13+), ✅ iOS, ✅ Web (Web Push API)

---

#### `getPushToken()`

Récupère le device token pour envoyer des notifications push depuis le backend.

**Signature TypeScript :**
```typescript
/**
 * Récupère le device token pour les notifications push
 * 
 * @returns {Promise<string>} Device token unique de l'appareil
 * @throws {NativiWebError} Si la permission n'est pas accordée (code: 'PERMISSION_DENIED')
 * 
 * @platform Android, iOS
 * @permission Nécessite requestNotificationPermission() accordé au préalable
 * 
 * @example
 * try {
 *   const token = await nw.getPushToken();
 *   // Envoyer le token à votre backend
 *   await fetch('/api/register-push-token', {
 *     method: 'POST',
 *     body: JSON.stringify({ token })
 *   });
 * } catch (error) {
 *   if (error.code === 'PERMISSION_DENIED') {
 *     console.error('Permission nécessaire');
 *   }
 * }
 */
getPushToken(): Promise<string>
```

**Exemple d'utilisation - Enregistrer le token sur le backend :**
```javascript
async function registerPushToken() {
  try {
    // Demander la permission d'abord
    const permission = await nw.requestNotificationPermission();
    
    if (permission === 'granted') {
      // Obtenir le token
      const deviceToken = await nw.getPushToken();
      
      // Envoyer le token à votre backend
      const response = await fetch('https://your-api.com/api/push/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          token: deviceToken,
          platform: nw.getPlatform(),
          deviceId: (await nw.getDeviceInfo()).uuid
        })
      });
      
      if (response.ok) {
        console.log('Token enregistré avec succès');
        // Stocker localement pour référence
        await nw.storage.set('push_token_registered', true);
      }
    }
  } catch (error) {
    console.error('Erreur lors de l\'enregistrement du token:', error);
  }
}

// Appeler au démarrage de l'app
registerPushToken();
```

**Différences iOS vs Android :**
- **iOS** : Le token est un UUID unique fourni par Apple Push Notification service (APNs)
- **Android** : Le token est un FCM (Firebase Cloud Messaging) token ou similaire
- Le token peut changer, il faut le réenregistrer périodiquement

---

#### Gérer les notifications en foreground vs background

```javascript
// Écouter les notifications reçues quand l'app est en foreground
nw.on('push-received', (notification) => {
  console.log('Notification reçue (foreground):', notification);
  
  // Afficher la notification manuellement
  nw.showNotification({
    title: notification.title,
    body: notification.body,
    data: notification.data
  });
  
  // Traiter les données
  if (notification.data?.type === 'new_message') {
    // Naviguer vers les messages
    router.push('/messages');
  }
});

// Écouter les notifications quand l'app est en background
nw.on('push-notification-opened', (notification) => {
  console.log('Notification ouverte depuis background:', notification);
  
  // Deep linking : naviguer vers la page appropriée
  if (notification.data?.url) {
    window.location.href = notification.data.url;
  }
});
```

---

#### Deep linking depuis une notification

```javascript
// Configuration du deep linking dans la notification
await nw.showNotification({
  title: 'Nouveau message',
  body: 'Vous avez reçu un message de John',
  data: {
    type: 'message',
    messageId: '12345',
    url: '/messages/12345', // URL de deep link
    userId: 'user-123'
  }
});

// Écouter le clic sur la notification
nw.on('notification-click', (data) => {
  const { url, type, messageId } = data.data;
  
  // Naviguer vers la page appropriée
  if (url) {
    window.location.href = url;
  } else if (type === 'message') {
    window.location.href = `/messages/${messageId}`;
  }
});
```

---

#### Permissions iOS vs Android (Différences)

**iOS :**
- Demande explicite de permission requise (via `requestNotificationPermission()`)
- Peut être refusée et nécessite d'aller dans les paramètres pour réactiver
- Supporte les notifications silencieuses (background fetch)
- Supporte les notifications avec actions personnalisées

**Android :**
- Android 12 (API 31) et inférieur : Permission automatique
- Android 13+ (API 33) : Demande explicite requise
- Notifications plus flexibles (canaux de notification)
- Supporte les notifications en tête (heads-up notifications)

---

#### `showNotification(options)`

Affiche une notification locale.

**Signature TypeScript :**
```typescript
showNotification(options: NotificationOptions): Promise<string>

interface NotificationOptions {
  title: string;
  body: string;
  icon?: string;
  badge?: string;
  image?: string;
  tag?: string;
  data?: Record<string, any>;
  sound?: string;
  vibrate?: number | number[];
  requireInteraction?: boolean;
  silent?: boolean;
  timestamp?: number;
  actions?: NotificationAction[];
}

interface NotificationAction {
  action: string;
  title: string;
  icon?: string;
}
```

**Paramètres :**
- `options` (obligatoire) : Options de la notification
  - `title` (string, obligatoire) : Titre de la notification
  - `body` (string, obligatoire) : Corps du message
  - `icon` (string, optionnel) : URL de l'icône
  - `badge` (string, optionnel) : URL du badge
  - `image` (string, optionnel) : URL de l'image à afficher
  - `tag` (string, optionnel) : Tag pour remplacer les notifications similaires
  - `data` (object, optionnel) : Données personnalisées associées
  - `sound` (string, optionnel) : Nom du fichier son (iOS)
  - `vibrate` (number | number[], optionnel) : Pattern de vibration (Android)
  - `requireInteraction` (boolean, optionnel) : Nécessite une interaction (web)
  - `silent` (boolean, optionnel) : Notification silencieuse
  - `timestamp` (number, optionnel) : Timestamp de la notification
  - `actions` (array, optionnel) : Actions disponibles (web)

**Valeur de retour :** `Promise<string>` - ID unique de la notification

**Exemple d'utilisation :**
```javascript
try {
  const notificationId = await NativiWeb.showNotification({
    title: 'Nouvel achat',
    body: 'Votre commande #12345 a été confirmée',
    icon: '/assets/icon.png',
    badge: '/assets/badge.png',
    image: '/assets/product.jpg',
    data: {
      orderId: '12345',
      type: 'order_confirmation',
      url: '/orders/12345'
    },
    tag: 'order-12345',
    sound: 'default',
    vibrate: [200, 100, 200]
  });
  
  console.log('Notification affichée avec l\'ID:', notificationId);
  
  // Écouter le clic sur la notification
  NativiWeb.on('notification-click', (data) => {
    if (data.notificationId === notificationId) {
      console.log('Notification cliquée:', data.data);
      // Naviguer vers la page appropriée
      window.location.href = data.data.url;
    }
  });
} catch (error) {
  if (error.code === 'PERMISSION_DENIED') {
    console.error('Permission de notification refusée');
  } else if (error.code === 'NOT_SUPPORTED') {
    console.error('Notifications non supportées');
  } else {
    console.error('Erreur:', error);
  }
}
```

**Permissions requises :**
- Même que `requestNotificationPermission()`

**Disponibilité :** ✅ Android, ✅ iOS, ✅ Web (Web Notifications API)

---

### Geolocation

#### `getCurrentPosition(options?)`

Récupère la position actuelle de l'appareil.

**Signature TypeScript :**
```typescript
/**
 * Récupère la position actuelle de l'appareil
 * 
 * @param {PositionOptions} options - Options de géolocalisation
 * @returns {Promise<Position>} Objet contenant les coordonnées
 * @throws {NativiWebError} Si la permission est refusée (code: 'PERMISSION_DENIED')
 * @throws {NativiWebError} Si la position est indisponible (code: 'POSITION_UNAVAILABLE')
 * @throws {NativiWebError} Si le délai d'attente est dépassé (code: 'TIMEOUT')
 * 
 * @platform Android, iOS, Web
 * @permission iOS: NSLocationWhenInUseUsageDescription dans Info.plist
 * @permission Android: ACCESS_FINE_LOCATION ou ACCESS_COARSE_LOCATION
 * 
 * @example
 * try {
 *   const position = await nw.getCurrentPosition({
 *     enableHighAccuracy: true,
 *     timeout: 10000
 *   });
 *   console.log('Latitude:', position.coords.latitude);
 * } catch (error) {
 *   if (error.code === 'PERMISSION_DENIED') {
 *     console.error('Permission refusée');
 *   }
 * }
 */
getCurrentPosition(options?: PositionOptions): Promise<Position>

interface PositionOptions {
  enableHighAccuracy?: boolean;  // Utiliser GPS haute précision (consomme plus de batterie)
  timeout?: number;              // Délai d'attente en millisecondes (défaut: Infinity)
  maximumAge?: number;           // Age maximum d'une position en cache en ms (défaut: 0)
}

interface Position {
  coords: {
    latitude: number;            // Latitude en degrés décimaux (-90 à 90)
    longitude: number;           // Longitude en degrés décimaux (-180 à 180)
    altitude: number | null;     // Altitude en mètres (peut être null)
    accuracy: number;            // Précision horizontale en mètres
    altitudeAccuracy: number | null; // Précision verticale en mètres (peut être null)
    heading: number | null;      // Direction en degrés (0-360, peut être null)
    speed: number | null;        // Vitesse en m/s (peut être null)
  };
  timestamp: number;             // Timestamp Unix en millisecondes
}
```

**Paramètres :**
- `options` (optionnel) : Options de géolocalisation
  - `enableHighAccuracy` (boolean, défaut: `false`) : Utiliser le GPS haute précision (consomme plus de batterie)
  - `timeout` (number, défaut: `Infinity`) : Délai d'attente en millisecondes
  - `maximumAge` (number, défaut: `0`) : Age maximum d'une position en cache (ms)

**Valeur de retour :** `Promise<Position>` - Objet contenant les coordonnées complètes

**Exemple d'utilisation avec gestion d'erreurs complète :**
```javascript
try {
  const position = await NativiWeb.getCurrentPosition({
    enableHighAccuracy: true,  // GPS haute précision
    timeout: 10000,            // 10 secondes max
    maximumAge: 60000          // Accepter une position jusqu'à 1 minute
  });
  
  console.log('Latitude:', position.coords.latitude);
  console.log('Longitude:', position.coords.longitude);
  console.log('Précision:', position.coords.accuracy, 'mètres');
  
  // Utiliser toutes les informations disponibles
  if (position.coords.altitude !== null) {
    console.log('Altitude:', position.coords.altitude, 'mètres');
  }
  
  if (position.coords.heading !== null) {
    console.log('Direction:', position.coords.heading, 'degrés');
  }
  
  if (position.coords.speed !== null) {
    console.log('Vitesse:', position.coords.speed * 3.6, 'km/h'); // Conversion m/s -> km/h
  }
  
  // Utiliser la position
  displayOnMap(position.coords.latitude, position.coords.longitude);
  
} catch (error) {
  if (error.code === 'PERMISSION_DENIED') {
    console.error('Permission de géolocalisation refusée');
    alert('Veuillez autoriser la géolocalisation dans les paramètres de l\'app');
    // Rediriger vers les paramètres (si supporté)
    nw.openSettings();
  } else if (error.code === 'POSITION_UNAVAILABLE') {
    console.error('Position non disponible');
    // Fallback : utiliser une position approximative ou par défaut
    useDefaultLocation();
  } else if (error.code === 'TIMEOUT') {
    console.error('Délai d\'attente dépassé');
    // Réessayer avec moins de précision
    const position = await NativiWeb.getCurrentPosition({
      enableHighAccuracy: false,
      timeout: 5000
    });
  } else {
    console.error('Erreur:', error);
  }
}
```

**Permissions requises :**
- **iOS** : `NSLocationWhenInUseUsageDescription` ou `NSLocationAlwaysUsageDescription` dans `Info.plist`
  ```xml
  <!-- Pour utilisation en cours d'utilisation -->
  <key>NSLocationWhenInUseUsageDescription</key>
  <string>Nous avons besoin de votre position pour vous montrer les points d'intérêt à proximité</string>
  
  <!-- Pour utilisation en arrière-plan (optionnel) -->
  <key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
  <string>Nous avons besoin de votre position en arrière-plan pour les fonctionnalités de suivi</string>
  ```
- **Android** : `ACCESS_FINE_LOCATION` ou `ACCESS_COARSE_LOCATION` dans `AndroidManifest.xml`
  ```xml
  <!-- Localisation précise (GPS) -->
  <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
  
  <!-- OU localisation approximative (réseau/WiFi) -->
  <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
  
  <!-- Optionnel : localisation en arrière-plan (Android 10+) -->
  <uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION" />
  ```

**Disponibilité :** ✅ Android, ✅ iOS, ✅ Web (Geolocation API)

**Notes importantes :**
- `enableHighAccuracy: true` consomme plus de batterie mais donne une meilleure précision
- Sur iOS, la localisation précise nécessite que l'app soit en foreground
- Sur Android, `ACCESS_FINE_LOCATION` est requis pour `enableHighAccuracy: true`

---

#### `watchPosition(callback, options?)`

Surveille les changements de position en continu.

**Signature TypeScript :**
```typescript
/**
 * Surveille les changements de position en continu
 * 
 * @param {Function} callback - Fonction appelée à chaque changement de position
 * @param {PositionOptions} options - Options de géolocalisation
 * @returns {Promise<number>} ID du watcher (à utiliser avec clearWatch)
 * @throws {NativiWebError} Si la permission est refusée (code: 'PERMISSION_DENIED')
 * 
 * @platform Android, iOS, Web
 * @permission Même que getCurrentPosition()
 * 
 * @example
 * try {
 *   const watchId = await nw.watchPosition((position) => {
 *     updateMapMarker(position.coords.latitude, position.coords.longitude);
 *   });
 *   
 *   // Plus tard, arrêter la surveillance
 *   nw.clearWatch(watchId);
 * } catch (error) {
 *   console.error('Erreur:', error);
 * }
 */
watchPosition(
  callback: (position: Position) => void,
  options?: PositionOptions
): Promise<number>
```

**Paramètres :**
- `callback` (obligatoire) : Fonction appelée à chaque changement de position
  - Reçoit un objet `Position` comme paramètre
- `options` (optionnel) : Options de géolocalisation (voir `getCurrentPosition`)

**Valeur de retour :** `Promise<number>` - ID du watcher (à utiliser avec `clearWatch`)

**Exemple d'utilisation :**
```javascript
let watchId = null;

try {
  watchId = await NativiWeb.watchPosition((position) => {
    console.log('Nouvelle position:', {
      lat: position.coords.latitude,
      lng: position.coords.longitude,
      accuracy: position.coords.accuracy,
      speed: position.coords.speed,
      heading: position.coords.heading
    });
    
    // Mettre à jour la carte en temps réel
    updateMapMarker(position.coords.latitude, position.coords.longitude);
    
    // Tracker le trajet
    trackRoute(position);
  }, {
    enableHighAccuracy: true,
    timeout: 5000,
    maximumAge: 1000 // Accepter une position jusqu'à 1 seconde
  });
  
  console.log('Surveillance de position active, ID:', watchId);
  
} catch (error) {
  if (error.code === 'PERMISSION_DENIED') {
    console.error('Permission refusée');
  } else {
    console.error('Erreur lors du démarrage de la surveillance:', error);
  }
}

// Arrêter la surveillance
function stopWatching() {
  if (watchId !== null) {
    NativiWeb.clearWatch(watchId);
    watchId = null;
    console.log('Surveillance arrêtée');
  }
}

// Arrêter automatiquement quand on quitte la page
window.addEventListener('beforeunload', () => {
  if (watchId !== null) {
    NativiWeb.clearWatch(watchId);
  }
});
```

**Permissions requises :** Même que `getCurrentPosition()`

**Disponibilité :** ✅ Android, ✅ iOS, ✅ Web (Geolocation API)

**Notes importantes :**
- ⚠️ **Consommation de batterie** : Surveiller la position en continu consomme beaucoup de batterie
- Arrêtez toujours la surveillance avec `clearWatch()` quand elle n'est plus nécessaire
- Sur iOS, la surveillance en arrière-plan nécessite des permissions spéciales

---

#### `clearWatch(watchId)`

Arrête la surveillance de position.

**Signature TypeScript :**
```typescript
/**
 * Arrête la surveillance de position
 * 
 * @param {number} watchId - ID retourné par watchPosition()
 * @returns {void}
 * 
 * @platform Android, iOS, Web
 * 
 * @example
 * const watchId = await nw.watchPosition(callback);
 * // Plus tard...
 * nw.clearWatch(watchId);
 */
clearWatch(watchId: number): void
```

**Paramètres :**
- `watchId` (obligatoire) : ID retourné par `watchPosition()`

**Valeur de retour :** `void`

**Exemple d'utilisation :**
```javascript
// Stocker tous les watchers actifs
const activeWatchers = new Set();

async function startTracking() {
  const watchId = await nw.watchPosition(handlePosition);
  activeWatchers.add(watchId);
  return watchId;
}

function stopTracking(watchId) {
  if (activeWatchers.has(watchId)) {
    nw.clearWatch(watchId);
    activeWatchers.delete(watchId);
  }
}

// Arrêter tous les watchers
function stopAllTracking() {
  activeWatchers.forEach(watchId => {
    nw.clearWatch(watchId);
  });
  activeWatchers.clear();
}
```

**Disponibilité :** ✅ Android, ✅ iOS, ✅ Web

---

### Camera

#### `takePhoto(options?)`

Prend une photo avec la caméra ou depuis la galerie.

**Signature TypeScript :**
```typescript
/**
 * Prend une photo avec la caméra ou sélectionne une image depuis la galerie
 * 
 * @param {TakePhotoOptions} options - Options de la photo
 * @returns {Promise<string>} Image encodée en base64 (data URI) ou chemin de fichier selon le format
 * @throws {NativiWebError} Si la permission est refusée (code: 'PERMISSION_DENIED')
 * @throws {NativiWebError} Si aucune caméra n'est disponible (code: 'NO_CAMERA')
 * @throws {NativiWebError} Si l'utilisateur annule (code: 'USER_CANCEL')
 * 
 * @platform Android, iOS
 * @permission iOS: NSCameraUsageDescription et NSPhotoLibraryUsageDescription dans Info.plist
 * @permission Android: CAMERA et READ_EXTERNAL_STORAGE
 * 
 * @example
 * try {
 *   // Prendre une photo avec la caméra
 *   const photo = await nw.takePhoto({
 *     source: 'camera',
 *     quality: 85,
 *     format: 'jpeg'
 *   });
 *   console.log('Photo prise:', photo);
 * } catch (error) {
 *   if (error.code === 'PERMISSION_DENIED') {
 *     console.error('Permission refusée');
 *   }
 * }
 */
takePhoto(options?: TakePhotoOptions): Promise<string | PhotoResult>

interface TakePhotoOptions {
  source?: 'camera' | 'gallery';  // Source de l'image (défaut: 'camera')
  quality?: number;                // Qualité JPEG 0-100 (défaut: 90)
  format?: 'jpeg' | 'png' | 'webp'; // Format de l'image (défaut: 'jpeg')
  maxWidth?: number;               // Largeur maximale en pixels
  maxHeight?: number;              // Hauteur maximale en pixels
  allowEdit?: boolean;             // Permettre l'édition avant de prendre la photo (iOS)
  cameraFacing?: 'front' | 'back'; // Caméra avant ou arrière (défaut: 'back')
  returnType?: 'base64' | 'file';  // Type de retour (défaut: 'base64')
}

interface PhotoResult {
  base64?: string;     // Image en base64 (si returnType: 'base64')
  filePath?: string;   // Chemin du fichier (si returnType: 'file')
  width: number;       // Largeur de l'image
  height: number;      // Hauteur de l'image
  size: number;        // Taille du fichier en bytes
}
```

**Paramètres :**
- `options` (optionnel) : Options de la photo
  - `source` (string, défaut: `'camera'`) : `'camera'` pour caméra, `'gallery'` pour galerie
  - `quality` (number, défaut: `90`) : Qualité JPEG (0-100)
  - `format` (string, défaut: `'jpeg'`) : Format de l'image
  - `maxWidth` (number, optionnel) : Largeur maximale (redimensionnement automatique)
  - `maxHeight` (number, optionnel) : Hauteur maximale (redimensionnement automatique)
  - `allowEdit` (boolean, optionnel) : Permettre l'édition avant sélection (iOS)
  - `cameraFacing` (string, optionnel) : Caméra avant ou arrière
  - `returnType` (string, optionnel) : Type de retour (`'base64'` ou `'file'`)

**Valeur de retour :** 
- Si `returnType: 'base64'` : `Promise<string>` - Image encodée en base64 (data URI)
- Si `returnType: 'file'` : `Promise<PhotoResult>` - Objet avec chemin de fichier et métadonnées

**Exemple d'utilisation :**
```javascript
try {
  // Prendre une photo avec la caméra
  const photo = await NativiWeb.takePhoto({
    source: 'camera',
    quality: 85,
    format: 'jpeg',
    maxWidth: 1920,
    maxHeight: 1080,
    cameraFacing: 'back',
    returnType: 'base64'
  });
  
  // photo est une string base64: "data:image/jpeg;base64,/9j/4AAQ..."
  console.log('Photo prise, taille:', photo.length, 'caractères');
  
  // Afficher la photo
  const imgElement = document.createElement('img');
  imgElement.src = photo;
  document.body.appendChild(imgElement);
  
  // Ou envoyer au serveur
  await uploadPhoto(photo);
  
} catch (error) {
  if (error.code === 'NO_CAMERA') {
    console.error('Aucune caméra disponible');
    // Fallback : sélectionner depuis la galerie
    const photo = await NativiWeb.takePhoto({ source: 'gallery' });
  } else if (error.code === 'PERMISSION_DENIED') {
    console.error('Permission caméra refusée');
    alert('Veuillez autoriser l\'accès à la caméra dans les paramètres');
  } else if (error.code === 'USER_CANCEL') {
    console.log('Prise de photo annulée');
  } else {
    console.error('Erreur:', error);
  }
}
```

**Exemple avec sélection depuis la galerie :**
```javascript
try {
  // Sélectionner une image depuis la galerie
  const image = await NativiWeb.takePhoto({
    source: 'gallery',
    allowEdit: true,  // Permettre de recadrer/éditer
    quality: 80,
    maxWidth: 1024,
    maxHeight: 1024
  });
  
  console.log('Image sélectionnée:', image);
  
} catch (error) {
  if (error.code === 'USER_CANCEL') {
    console.log('Sélection annulée');
  } else {
    console.error('Erreur:', error);
  }
}
```

**Exemple avec retour de fichier (plus efficace pour grandes images) :**
```javascript
try {
  // Obtenir le chemin du fichier au lieu de base64 (plus efficace)
  const result = await NativiWeb.takePhoto({
    returnType: 'file',
    quality: 90
  });
  
  console.log('Fichier:', result.filePath);
  console.log('Dimensions:', `${result.width}x${result.height}`);
  console.log('Taille:', result.size, 'bytes');
  
  // Utiliser le fichier directement (upload, etc.)
  await uploadFile(result.filePath);
  
} catch (error) {
  console.error('Erreur:', error);
}
```

**Gestion mémoire pour grandes images :**
```javascript
async function takePhotoWithCompression() {
  try {
    // Option 1 : Prendre la photo en haute qualité
    const highQuality = await NativiWeb.takePhoto({
      quality: 95,
      format: 'jpeg'
    });
    
    // Option 2 : Redimensionner immédiatement pour réduire la taille
    const compressed = await NativiWeb.takePhoto({
      quality: 75,
      maxWidth: 1024,
      maxHeight: 1024,
      format: 'jpeg'
    });
    
    // La version compressée utilise beaucoup moins de mémoire
    console.log('Taille originale:', highQuality.length);
    console.log('Taille compressée:', compressed.length);
    
    // Utiliser la version compressée pour l'upload
    await uploadPhoto(compressed);
    
  } catch (error) {
    console.error('Erreur:', error);
  }
}
```

**Permissions requises :**
- **iOS** : 
  - `NSCameraUsageDescription` dans `Info.plist` (pour caméra)
  ```xml
  <key>NSCameraUsageDescription</key>
  <string>Nous avons besoin de la caméra pour prendre des photos</string>
  ```
  - `NSPhotoLibraryUsageDescription` (pour galerie)
  ```xml
  <key>NSPhotoLibraryUsageDescription</key>
  <string>Nous avons besoin d'accéder à vos photos pour sélectionner une image</string>
  ```
- **Android** : 
  - `CAMERA` dans `AndroidManifest.xml`
  ```xml
  <uses-permission android:name="android.permission.CAMERA" />
  <uses-feature android:name="android.hardware.camera" android:required="false" />
  <uses-feature android:name="android.hardware.camera.front" android:required="false" />
  ```
  - `READ_EXTERNAL_STORAGE` ou `READ_MEDIA_IMAGES` (Android 13+)
  ```xml
  <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
  <!-- Android 13+ -->
  <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
  ```

**Disponibilité :** ✅ Android, ✅ iOS, ✅ Web (via input file + MediaDevices API)

**Notes importantes :**
- ⚠️ **Mémoire** : Les images base64 peuvent être très volumineuses. Utilisez `maxWidth`/`maxHeight` pour réduire la taille
- Pour les grandes images, préférez `returnType: 'file'` qui est plus efficace
- Sur iOS, `allowEdit: true` permet à l'utilisateur de recadrer l'image avant de la prendre

---

### Local Storage

Le SDK NativiWeb fournit une API de stockage local native qui persiste même après la fermeture de l'application.

#### `storage.set(key, value)`

Stocke une valeur dans le stockage local natif.

**Signature TypeScript :**
```typescript
/**
 * Stocke une valeur dans le stockage local
 * 
 * @param {string} key - Clé de stockage
 * @param {any} value - Valeur à stocker (sera sérialisée en JSON si objet)
 * @returns {Promise<void>}
 * @throws {NativiWebError} Si le stockage est plein (code: 'QUOTA_EXCEEDED')
 * 
 * @platform android, ios, web
 * @permission Aucune permission requise
 * 
 * @example
 * try {
 *   await nw.storage.set('username', 'john_doe');
 *   await nw.storage.setJSON('user', { id: 1, name: 'John' });
 * } catch (error) {
 *   if (error.code === 'QUOTA_EXCEEDED') {
 *     console.error('Stockage insuffisant');
 *   }
 * }
 */
storage.set(key: string, value: any): Promise<void>
```

**Paramètres :**
- `key` (string, obligatoire) : Clé de stockage (max 256 caractères)
- `value` (any, obligatoire) : Valeur à stocker

**Valeur de retour :** `Promise<void>`

**Exemple d'utilisation :**
```javascript
try {
  // Stocker une chaîne
  await nw.storage.set('username', 'john_doe');
  
  // Stocker un nombre
  await nw.storage.set('score', 1250);
  
  // Stocker un booléen
  await nw.storage.set('settings_synced', true);
  
  console.log('Données sauvegardées');
} catch (error) {
  if (error.code === 'QUOTA_EXCEEDED') {
    console.error('Stockage insuffisant. Limite atteinte.');
  } else {
    console.error('Erreur:', error);
  }
}
```

---

#### `storage.setJSON(key, value)`

Stocke un objet JavaScript en le sérialisant automatiquement en JSON.

**Signature TypeScript :**
```typescript
/**
 * Stocke un objet JavaScript (sérialisation JSON automatique)
 * 
 * @param {string} key - Clé de stockage
 * @param {any} value - Objet à stocker (sera sérialisé en JSON)
 * @returns {Promise<void>}
 * @throws {NativiWebError} Si le stockage est plein ou si l'objet ne peut pas être sérialisé
 * 
 * @platform android, ios, web
 */
storage.setJSON(key: string, value: any): Promise<void>
```

**Exemple d'utilisation :**
```javascript
try {
  // Stocker un objet complexe
  await nw.storage.setJSON('user', {
    id: 123,
    name: 'John Doe',
    email: 'john@example.com',
    preferences: {
      theme: 'dark',
      language: 'fr',
      notifications: true
    }
  });
  
  // Stocker un tableau
  await nw.storage.setJSON('favorites', [1, 2, 3, 4, 5]);
  
} catch (error) {
  console.error('Erreur lors du stockage:', error);
}
```

---

#### `storage.get(key)`

Récupère une valeur du stockage local.

**Signature TypeScript :**
```typescript
/**
 * Récupère une valeur du stockage local
 * 
 * @param {string} key - Clé à récupérer
 * @returns {Promise<string | null>} Valeur stockée ou null si inexistante
 * 
 * @platform android, ios, web
 */
storage.get(key: string): Promise<string | null>
```

**Exemple d'utilisation :**
```javascript
try {
  const username = await nw.storage.get('username');
  if (username) {
    console.log('Username:', username);
  } else {
    console.log('Clé non trouvée');
  }
} catch (error) {
  console.error('Erreur:', error);
}
```

---

#### `storage.getJSON(key)`

Récupère et désérialise automatiquement un objet JSON.

**Signature TypeScript :**
```typescript
/**
 * Récupère et désérialise un objet JSON
 * 
 * @param {string} key - Clé à récupérer
 * @returns {Promise<T | null>} Objet désérialisé ou null si inexistant ou invalide
 * 
 * @platform android, ios, web
 * 
 * @example
 * try {
 *   const user = await nw.storage.getJSON('user');
 *   if (user) {
 *     console.log('User:', user.name);
 *   }
 * } catch (error) {
 *   console.error('Erreur:', error);
 * }
 */
storage.getJSON<T = any>(key: string): Promise<T | null>
```

**Exemple d'utilisation :**
```javascript
try {
  // Récupérer un objet
  const user = await nw.storage.getJSON('user');
  if (user) {
    console.log('User:', user.name, user.email);
    console.log('Theme:', user.preferences.theme);
  }
  
  // Récupérer un tableau
  const favorites = await nw.storage.getJSON('favorites');
  if (favorites && Array.isArray(favorites)) {
    console.log('Favoris:', favorites.length);
  }
} catch (error) {
  console.error('Erreur lors de la récupération:', error);
}
```

---

#### `storage.remove(key)`

Supprime une clé du stockage local.

**Signature TypeScript :**
```typescript
/**
 * Supprime une clé du stockage local
 * 
 * @param {string} key - Clé à supprimer
 * @returns {Promise<void>}
 * 
 * @platform android, ios, web
 */
storage.remove(key: string): Promise<void>
```

**Exemple d'utilisation :**
```javascript
try {
  await nw.storage.remove('username');
  console.log('Clé supprimée');
} catch (error) {
  console.error('Erreur:', error);
}
```

---

#### `storage.clear()`

Vide tout le stockage local.

**Signature TypeScript :**
```typescript
/**
 * Vide tout le stockage local
 * 
 * @returns {Promise<void>}
 * 
 * @platform android, ios, web
 * 
 * @example
 * // ⚠️ Attention : Cette action est irréversible
 * await nw.storage.clear();
 */
storage.clear(): Promise<void>
```

**Exemple d'utilisation :**
```javascript
try {
  // ⚠️ Attention : Cette action supprime toutes les données
  if (confirm('Voulez-vous vraiment supprimer toutes les données ?')) {
    await nw.storage.clear();
    console.log('Stockage vidé');
  }
} catch (error) {
  console.error('Erreur:', error);
}
```

---

#### `storage.keys()`

Liste toutes les clés stockées.

**Signature TypeScript :**
```typescript
/**
 * Liste toutes les clés stockées
 * 
 * @returns {Promise<string[]>} Tableau des clés
 * 
 * @platform android, ios, web
 * 
 * @example
 * const keys = await nw.storage.keys();
 * console.log('Clés stockées:', keys);
 */
storage.keys(): Promise<string[]>
```

**Exemple d'utilisation :**
```javascript
try {
  const keys = await nw.storage.keys();
  console.log('Clés stockées:', keys);
  console.log('Nombre de clés:', keys.length);
  
  // Parcourir toutes les clés
  for (const key of keys) {
    const value = await nw.storage.get(key);
    console.log(`${key}:`, value);
  }
} catch (error) {
  console.error('Erreur:', error);
}
```

**Permissions requises :** Aucune

**Disponibilité :** ✅ Android, ✅ iOS, ✅ Web (localStorage avec fallback)

**Limites :**
- Taille maximale par clé : ~10 MB
- Stockage total disponible : Variable selon l'appareil (généralement plusieurs centaines de MB)

---

### Biometric Authentication

#### `authenticateWithBiometrics(reason?)`

Authentifie l'utilisateur avec l'authentification biométrique (Touch ID, Face ID, empreinte digitale).

**Signature TypeScript :**
```typescript
/**
 * Authentifie l'utilisateur avec l'authentification biométrique
 * 
 * @param {string} reason - Message affiché à l'utilisateur (iOS/Android)
 * @returns {Promise<BiometricResult>} Résultat de l'authentification
 * @throws {NativiWebError} Si la biométrie n'est pas disponible (code: 'NOT_AVAILABLE')
 * @throws {NativiWebError} Si aucune empreinte n'est enregistrée (code: 'NOT_ENROLLED')
 * @throws {NativiWebError} Si l'utilisateur annule (code: 'USER_CANCEL')
 * @throws {NativiWebError} Si l'authentification échoue (code: 'AUTHENTICATION_FAILED')
 * 
 * @platform Android (API 23+), iOS
 * @permission iOS: NSFaceIDUsageDescription dans Info.plist (pour Face ID)
 * @permission Android: Aucune permission explicite (utilise BiometricPrompt)
 * 
 * @example
 * try {
 *   const result = await nw.authenticateWithBiometrics('Confirmez votre identité');
 *   if (result.success) {
 *     console.log('Authentifié avec succès');
 *   }
 * } catch (error) {
 *   if (error.code === 'NOT_AVAILABLE') {
 *     // Fallback vers PIN/password
 *   }
 * }
 */
authenticateWithBiometrics(reason?: string): Promise<BiometricResult>

interface BiometricResult {
  success: boolean;
  biometricType?: 'fingerprint' | 'face' | 'iris' | 'voice'; // Type de biométrie utilisée
  error?: string;
  errorCode?: string;
}

interface BiometricAvailability {
  available: boolean;
  types: ('fingerprint' | 'face' | 'iris' | 'voice')[];
  enrolled: boolean; // Au moins une empreinte/face est enregistrée
}
```

**Paramètres :**
- `reason` (string, optionnel) : Message affiché à l'utilisateur expliquant pourquoi l'authentification est nécessaire

**Valeur de retour :** `Promise<BiometricResult>` - Résultat de l'authentification

**Types de biométrie disponibles :**
- **Fingerprint** : Empreinte digitale (Android, iPhone avec Touch ID)
- **Face** : Reconnaissance faciale (Face ID sur iOS, Face Unlock sur Android)
- **Iris** : Reconnaissance de l'iris (Android uniquement, rare)
- **Voice** : Reconnaissance vocale (Android uniquement, rare)

**Exemple d'utilisation :**
```javascript
try {
  const result = await NativiWeb.authenticateWithBiometrics('Confirmez votre identité pour accéder à vos données sensibles');
  
  if (result.success) {
    console.log('Authentification réussie');
    console.log('Type utilisé:', result.biometricType);
    // Accéder aux fonctionnalités sécurisées
    showSecureContent();
  } else {
    console.error('Authentification échouée:', result.error);
    alert('Authentification échouée. Veuillez réessayer.');
  }
} catch (error) {
  if (error.code === 'NOT_AVAILABLE') {
    console.error('Authentification biométrique non disponible');
    // Fallback vers mot de passe
    showPasswordForm();
  } else if (error.code === 'NOT_ENROLLED') {
    console.error('Aucune empreinte biométrique enregistrée');
    alert('Veuillez enregistrer une empreinte biométrique dans les paramètres de l\'appareil');
    // Fallback vers PIN/password
    showPasswordForm();
  } else if (error.code === 'USER_CANCEL') {
    console.log('Utilisateur a annulé');
    // L'utilisateur peut réessayer
  } else if (error.code === 'AUTHENTICATION_FAILED') {
    console.error('Échec de l\'authentification');
    // L'utilisateur peut réessayer
  } else {
    console.error('Erreur:', error);
  }
}
```

**Vérifier la disponibilité avant d'authentifier :**
```javascript
/**
 * Vérifie si la biométrie est disponible et configurée
 */
async function checkBiometricAvailability() {
  try {
    const availability = await NativiWeb.checkBiometricAvailability();
    
    if (!availability.available) {
      console.log('Biométrie non disponible sur cet appareil');
      return false;
    }
    
    if (!availability.enrolled) {
      console.log('Aucune empreinte biométrique enregistrée');
      alert('Veuillez enregistrer une empreinte dans les paramètres');
      return false;
    }
    
    console.log('Types disponibles:', availability.types);
    return true;
  } catch (error) {
    console.error('Erreur:', error);
    return false;
  }
}

// Utilisation
if (await checkBiometricAvailability()) {
  // Proposer l'authentification biométrique
  try {
    await NativiWeb.authenticateWithBiometrics('Accéder à vos données');
  } catch (error) {
    // Fallback
    showPasswordForm();
  }
} else {
  // Utiliser directement le mot de passe
  showPasswordForm();
}
```

**Fallback vers PIN/password :**
```javascript
async function authenticateUser() {
  try {
    // Essayer d'abord la biométrie
    const result = await NativiWeb.authenticateWithBiometrics('Confirmez votre identité');
    
    if (result.success) {
      return { authenticated: true, method: 'biometric' };
    }
  } catch (error) {
    if (error.code === 'NOT_AVAILABLE' || error.code === 'NOT_ENROLLED') {
      // Fallback vers mot de passe
      const password = await showPasswordForm();
      const isValid = await validatePassword(password);
      
      if (isValid) {
        return { authenticated: true, method: 'password' };
      } else {
        return { authenticated: false, error: 'Mot de passe incorrect' };
      }
    } else if (error.code === 'USER_CANCEL') {
      // L'utilisateur a annulé, ne rien faire
      return { authenticated: false, error: 'Annulé par l\'utilisateur' };
    }
  }
  
  return { authenticated: false, error: 'Authentification échouée' };
}
```

**Permissions requises :**
- **iOS** : 
  - Pour Face ID : `NSFaceIDUsageDescription` dans `Info.plist`
  ```xml
  <key>NSFaceIDUsageDescription</key>
  <string>Utilisez Face ID pour vous authentifier de manière sécurisée</string>
  ```
  - Pour Touch ID : Aucune description nécessaire, mais la fonctionnalité doit être disponible
- **Android** : 
  - Aucune permission explicite dans le manifest
  - Utilise l'API `BiometricPrompt` (Android 6.0+ / API 23+)
  - Nécessite qu'au moins une empreinte soit enregistrée sur l'appareil

**Disponibilité :** ✅ Android (API 23+), ✅ iOS (Touch ID / Face ID), ❌ Web

**Notes importantes :**
- Sur iOS, Face ID nécessite un iPhone X ou plus récent
- Sur Android, l'authentification biométrique peut être désactivée par l'utilisateur
- Toujours prévoir un fallback vers PIN/password si la biométrie n'est pas disponible
- Le nombre d'échecs est limité (généralement 5 tentatives) avant de verrouiller temporairement

---

### Haptic Feedback

#### `vibrate(duration)`

Fait vibrer l'appareil.

**Signature TypeScript :**
```typescript
vibrate(duration: number | number[]): Promise<void>
```

**Paramètres :**
- `duration` (number | number[], obligatoire) :
  - Si `number` : Durée de la vibration en millisecondes
  - Si `array` : Pattern de vibration `[vibrate, pause, vibrate, pause, ...]`

**Valeur de retour :** `Promise<void>`

**Exemple d'utilisation :**
```javascript
try {
  // Vibration simple
  await NativiWeb.vibrate(100); // 100ms
  
  // Pattern de vibration
  await NativiWeb.vibrate([100, 50, 100, 50, 200]);
  // Vibrer 100ms, pause 50ms, vibrer 100ms, pause 50ms, vibrer 200ms
  
} catch (error) {
  if (error.code === 'NOT_SUPPORTED') {
    console.warn('Vibration non supportée sur cet appareil');
  } else {
    console.error('Erreur:', error);
  }
}
```

**Permissions requises :**
- **Android** : `VIBRATE` dans `AndroidManifest.xml`
  ```xml
  <uses-permission android:name="android.permission.VIBRATE" />
  ```
- **iOS** : Aucune

**Disponibilité :** ✅ Android, ✅ iOS (via UIImpactFeedbackGenerator), ⚠️ Web (limitée)

---

### Native Share

#### `share(options)`

Partage du contenu via le sélecteur natif de partage.

**Signature TypeScript :**
```typescript
share(options: ShareOptions): Promise<ShareResult>

interface ShareOptions {
  title?: string;
  text?: string;
  url?: string;
  files?: File[];
}

interface ShareResult {
  success: boolean;
  activityType?: string; // iOS seulement
}
```

**Paramètres :**
- `options` (obligatoire) : Options de partage
  - `title` (string, optionnel) : Titre du partage
  - `text` (string, optionnel) : Texte à partager
  - `url` (string, optionnel) : URL à partager
  - `files` (File[], optionnel) : Fichiers à partager

**Valeur de retour :** `Promise<ShareResult>` - Résultat du partage

**Exemple d'utilisation :**
```javascript
try {
  const result = await NativiWeb.share({
    title: 'Découvrez cette application !',
    text: 'J\'utilise cette super app pour gérer mes projets',
    url: 'https://example.com/app'
  });
  
  if (result.success) {
    console.log('Partage réussi');
    if (result.activityType) {
      console.log('Partagé via:', result.activityType); // iOS seulement
    }
  }
} catch (error) {
  if (error.code === 'USER_CANCEL') {
    console.log('Partage annulé par l\'utilisateur');
  } else if (error.code === 'NOT_SUPPORTED') {
    console.error('Partage non supporté');
    // Fallback : copier dans le presse-papier
    await NativiWeb.copyToClipboard('https://example.com/app');
  } else {
    console.error('Erreur:', error);
  }
}
```

**Permissions requises :** Aucune

**Disponibilité :** ✅ Android, ✅ iOS, ✅ Web (Web Share API)

---

### Clipboard

#### `copyToClipboard(text)`

Copie du texte dans le presse-papier.

**Signature TypeScript :**
```typescript
copyToClipboard(text: string): Promise<void>
```

**Paramètres :**
- `text` (string, obligatoire) : Texte à copier

**Valeur de retour :** `Promise<void>`

**Exemple d'utilisation :**
```javascript
try {
  await NativiWeb.copyToClipboard('Texte à copier');
  console.log('Texte copié dans le presse-papier');
  showToast('Copié !');
} catch (error) {
  console.error('Erreur lors de la copie:', error);
}
```

**Permissions requises :** Aucune

**Disponibilité :** ✅ Android, ✅ iOS, ✅ Web (Clipboard API)

---

#### `readFromClipboard()`

Lit le texte du presse-papier.

**Signature TypeScript :**
```typescript
readFromClipboard(): Promise<string>
```

**Paramètres :** Aucun

**Valeur de retour :** `Promise<string>` - Texte du presse-papier

**Exemple d'utilisation :**
```javascript
try {
  const clipboardText = await NativiWeb.readFromClipboard();
  console.log('Texte du presse-papier:', clipboardText);
  
  if (clipboardText) {
    // Utiliser le texte
    pasteText(clipboardText);
  }
} catch (error) {
  console.error('Erreur lors de la lecture:', error);
}
```

**Permissions requises :** Aucune

**Disponibilité :** ✅ Android, ✅ iOS, ✅ Web (Clipboard API)

---

### Contacts

#### `requestContactsPermission()`

Demande la permission d'accéder aux contacts.

**Signature TypeScript :**
```typescript
/**
 * Demande la permission d'accéder aux contacts
 * 
 * @returns {Promise<'granted' | 'denied' | 'default'>}
 * @throws {NativiWebError} Si l'appareil ne supporte pas les contacts (code: 'NOT_SUPPORTED')
 * 
 * @platform android, ios
 * @permission android: READ_CONTACTS
 * @permission ios: NSContactsUsageDescription dans Info.plist
 * 
 * @example
 * try {
 *   const permission = await nw.requestContactsPermission();
 *   if (permission === 'granted') {
 *     const contacts = await nw.getAllContacts();
 *   }
 * } catch (error) {
 *   if (error.code === 'PERMISSION_DENIED') {
 *     console.error('Permission refusée');
 *   }
 * }
 */
requestContactsPermission(): Promise<'granted' | 'denied' | 'default'>
```

**Permissions requises :**
- **iOS** : `NSContactsUsageDescription` dans `Info.plist`
  ```xml
  <key>NSContactsUsageDescription</key>
  <string>Nous avons besoin d'accéder à vos contacts pour vous permettre de partager avec vos amis</string>
  ```
- **Android** : `READ_CONTACTS` dans `AndroidManifest.xml`
  ```xml
  <uses-permission android:name="android.permission.READ_CONTACTS" />
  ```

**Disponibilité :** ✅ Android, ✅ iOS, ❌ Web

---

#### `selectContact()`

Ouvre le sélecteur natif de contacts et retourne le contact sélectionné.

**Signature TypeScript :**
```typescript
/**
 * Ouvre le sélecteur natif de contacts
 * 
 * @returns {Promise<Contact | null>} Contact sélectionné ou null si annulé
 * @throws {NativiWebError} Si la permission n'est pas accordée (code: 'PERMISSION_DENIED')
 * 
 * @platform android, ios
 * @permission Nécessite requestContactsPermission() au préalable
 * 
 * @example
 * try {
 *   const contact = await nw.selectContact();
 *   if (contact) {
 *     console.log('Contact sélectionné:', contact.name);
 *     console.log('Email:', contact.emails?.[0]);
 *   }
 * } catch (error) {
 *   if (error.code === 'USER_CANCEL') {
 *     console.log('Sélection annulée');
 *   }
 * }
 */
selectContact(): Promise<Contact | null>

interface Contact {
  id: string;
  name: string;
  firstName?: string;
  lastName?: string;
  emails?: string[];
  phones?: string[];
  organization?: string;
  jobTitle?: string;
  addresses?: ContactAddress[];
  avatar?: string; // Base64 ou URL
}

interface ContactAddress {
  street?: string;
  city?: string;
  region?: string;
  postalCode?: string;
  country?: string;
}
```

**Exemple d'utilisation :**
```javascript
try {
  // Demander la permission d'abord
  const permission = await nw.requestContactsPermission();
  
  if (permission === 'granted') {
    const contact = await nw.selectContact();
    
    if (contact) {
      console.log('Contact:', contact.name);
      if (contact.emails && contact.emails.length > 0) {
        console.log('Email:', contact.emails[0]);
      }
      if (contact.phones && contact.phones.length > 0) {
        console.log('Téléphone:', contact.phones[0]);
      }
      
      // Utiliser le contact (envoyer un email, appeler, etc.)
      sendEmailToContact(contact.emails[0]);
    } else {
      console.log('Sélection annulée par l\'utilisateur');
    }
  }
} catch (error) {
  if (error.code === 'PERMISSION_DENIED') {
    alert('Permission nécessaire pour accéder aux contacts');
  } else if (error.code === 'USER_CANCEL') {
    console.log('Sélection annulée');
  } else {
    console.error('Erreur:', error);
  }
}
```

**Disponibilité :** ✅ Android, ✅ iOS, ❌ Web

---

#### `getAllContacts(options?)`

Récupère tous les contacts de l'appareil.

**Signature TypeScript :**
```typescript
/**
 * Récupère tous les contacts de l'appareil
 * 
 * @param {Object} options - Options de récupération
 * @param {string[]} options.fields - Champs à récupérer (défaut: tous)
 * @returns {Promise<Contact[]>} Liste des contacts
 * @throws {NativiWebError} Si la permission n'est pas accordée (code: 'PERMISSION_DENIED')
 * 
 * @platform android, ios
 * @permission Nécessite requestContactsPermission() au préalable
 * 
 * @example
 * try {
 *   const contacts = await nw.getAllContacts({
 *     fields: ['name', 'phone', 'email']
 *   });
 *   console.log('Nombre de contacts:', contacts.length);
 * } catch (error) {
 *   if (error.code === 'PERMISSION_DENIED') {
 *     console.error('Permission refusée');
 *   }
 * }
 */
getAllContacts(options?: GetAllContactsOptions): Promise<Contact[]>

interface GetAllContactsOptions {
  fields?: ('name' | 'phone' | 'email' | 'address' | 'organization')[];
}
```

**Exemple d'utilisation :**
```javascript
try {
  // Demander la permission d'abord
  await nw.requestContactsPermission();
  
  // Récupérer tous les contacts avec certains champs uniquement
  const contacts = await nw.getAllContacts({
    fields: ['name', 'phone', 'email']
  });
  
  console.log(`Trouvé ${contacts.length} contacts`);
  
  // Filtrer les contacts avec email
  const contactsWithEmail = contacts.filter(c => 
    c.emails && c.emails.length > 0
  );
  
  // Afficher les contacts
  contactsWithEmail.forEach(contact => {
    console.log(`${contact.name}: ${contact.emails[0]}`);
  });
  
} catch (error) {
  if (error.code === 'PERMISSION_DENIED') {
    console.error('Permission refusée');
  } else {
    console.error('Erreur:', error);
  }
}
```

**Permissions requises :** Même que `requestContactsPermission()`

**Disponibilité :** ✅ Android, ✅ iOS, ❌ Web

---

### Device Information (Amélioré)

#### `getDeviceInfo()`

Récupère les informations détaillées sur l'appareil.

**Signature TypeScript :**
```typescript
/**
 * Récupère les informations détaillées sur l'appareil
 * 
 * @returns {Promise<DeviceInfo>} Informations de l'appareil
 * 
 * @platform android, ios, web
 * @permission Aucune permission requise
 * 
 * @example
 * try {
 *   const info = await nw.getDeviceInfo();
 *   console.log('Modèle:', info.model);
 *   console.log('OS Version:', info.osVersion);
 * } catch (error) {
 *   console.error('Erreur:', error);
 * }
 */
getDeviceInfo(): Promise<DeviceInfo>

interface DeviceInfo {
  model: string;              // Ex: "iPhone 14 Pro", "Samsung Galaxy S23"
  osVersion: string;          // Ex: "16.2", "13"
  appVersion: string;         // Version de votre app
  uuid: string;               // Identifiant unique de l'appareil
  platform: 'android' | 'ios' | 'web';
  manufacturer?: string;      // Android seulement
  brand?: string;             // Android seulement
  isTablet: boolean;          // Indique si c'est une tablette
  isVirtual: boolean;         // Indique si c'est un émulateur/simulateur
  screenWidth: number;        // Largeur de l'écran en pixels
  screenHeight: number;       // Hauteur de l'écran en pixels
  pixelRatio: number;         // Ratio de pixels (ex: 2, 3 pour Retina)
}
```

**Exemple d'utilisation :**
```javascript
try {
  const info = await nw.getDeviceInfo();
  
  console.log('Modèle:', info.model);
  console.log('OS Version:', info.osVersion);
  console.log('Plateforme:', info.platform);
  console.log('Tablette:', info.isTablet);
  console.log('Résolution:', `${info.screenWidth}x${info.screenHeight}`);
  
  // Adapter l'UI selon l'appareil
  if (info.isTablet) {
    // Layout tablette
    showTabletLayout();
  } else {
    // Layout smartphone
    showPhoneLayout();
  }
  
} catch (error) {
  console.error('Erreur:', error);
}
```

**Disponibilité :** ✅ Android, ✅ iOS, ✅ Web (avec limitations)

---

#### `getNetworkInfo()`

Récupère les informations sur la connexion réseau.

**Signature TypeScript :**
```typescript
/**
 * Récupère les informations sur la connexion réseau
 * 
 * @returns {Promise<NetworkInfo>} Informations réseau
 * 
 * @platform android, ios, web
 * @permission Aucune permission requise
 * 
 * @example
 * try {
 *   const network = await nw.getNetworkInfo();
 *   if (network.isConnected) {
 *     if (network.type === 'wifi') {
 *       // Connexion WiFi, OK pour téléchargements volumineux
 *     } else if (network.type === 'cellular') {
 *       // Données mobiles, limiter les téléchargements
 *     }
 *   }
 * } catch (error) {
 *   console.error('Erreur:', error);
 * }
 */
getNetworkInfo(): Promise<NetworkInfo>

interface NetworkInfo {
  type: 'wifi' | 'cellular' | 'ethernet' | 'none' | 'unknown';
  isConnected: boolean;
  isInternetReachable?: boolean; // Vérifie si Internet est accessible
}
```

**Exemple d'utilisation :**
```javascript
try {
  const network = await nw.getNetworkInfo();
  
  if (!network.isConnected) {
    showOfflineMessage();
    return;
  }
  
  switch (network.type) {
    case 'wifi':
      console.log('Connexion WiFi - OK pour téléchargements');
      // Télécharger des fichiers volumineux
      downloadLargeFile();
      break;
      
    case 'cellular':
      console.log('Données mobiles - Mode économique');
      // Limiter les téléchargements
      downloadSmallFilesOnly();
      break;
      
    case 'none':
      console.log('Aucune connexion');
      showOfflineMode();
      break;
  }
  
} catch (error) {
  console.error('Erreur:', error);
}
```

**Disponibilité :** ✅ Android, ✅ iOS, ✅ Web (Network Information API)

---

#### `getPlatform()`

Retourne la plateforme actuelle.

**Signature TypeScript :**
```typescript
/**
 * Retourne la plateforme actuelle
 * 
 * @returns {'android' | 'ios' | 'web'}
 * 
 * @platform android, ios, web
 */
getPlatform(): 'android' | 'ios' | 'web'
```

**Exemple d'utilisation :**
```javascript
const platform = nw.getPlatform();

if (platform === 'ios') {
  // Code spécifique iOS
  applyiOSStyles();
} else if (platform === 'android') {
  // Code spécifique Android
  applyAndroidStyles();
} else {
  // Code web
  applyWebStyles();
}
```

---

### Share API (Amélioré)

#### `share(options)`

Partage du contenu via le sélecteur natif de partage.

**Signature TypeScript :**
```typescript
/**
 * Partage du contenu via le sélecteur natif de partage
 * 
 * @param {ShareOptions} options - Options de partage
 * @returns {Promise<ShareResult>} Résultat du partage
 * @throws {NativiWebError} Si l'utilisateur annule (code: 'USER_CANCEL') ou si non supporté (code: 'NOT_SUPPORTED')
 * 
 * @platform android, ios, web
 * @permission Aucune permission requise
 * 
 * @example
 * try {
 *   const result = await nw.share({
 *     title: 'Check this out',
 *     text: 'Amazing content',
 *     url: 'https://example.com'
 *   });
 *   if (result.success) {
 *     console.log('Partagé avec succès');
 *   }
 * } catch (error) {
 *   if (error.code === 'USER_CANCEL') {
 *     console.log('Partage annulé');
 *   }
 * }
 */
share(options: ShareOptions): Promise<ShareResult>

interface ShareOptions {
  title?: string;      // Titre du partage
  text?: string;       // Texte à partager
  url?: string;        // URL à partager
  files?: File[];      // Fichiers à partager (images, PDFs, etc.)
}

interface ShareResult {
  success: boolean;
  activityType?: string; // iOS seulement (ex: 'com.apple.UIKit.activity.Message')
}
```

**Exemple d'utilisation :**
```javascript
try {
  // Partager du texte et une URL
  const result = await nw.share({
    title: 'Découvrez cette application !',
    text: 'J\'utilise cette super app pour gérer mes projets',
    url: 'https://example.com/app'
  });
  
  if (result.success) {
    console.log('Partage réussi');
    // iOS seulement : savoir via quelle app
    if (result.activityType) {
      console.log('Partagé via:', result.activityType);
    }
  }
} catch (error) {
  if (error.code === 'USER_CANCEL') {
    console.log('Partage annulé par l\'utilisateur');
  } else if (error.code === 'NOT_SUPPORTED') {
    console.error('Partage non supporté');
    // Fallback : copier dans le presse-papier
    await nw.copyToClipboard('https://example.com/app');
    alert('Lien copié dans le presse-papier');
  } else {
    console.error('Erreur:', error);
  }
}
```

**Exemple avec fichier :**
```javascript
try {
  // Partager une image
  const imageFile = await fetch('/path/to/image.jpg').then(r => r.blob()).then(b => new File([b], 'image.jpg'));
  
  await nw.share({
    text: 'Regardez cette image !',
    files: [imageFile]
  });
} catch (error) {
  console.error('Erreur lors du partage de fichier:', error);
}
```

**Disponibilité :** ✅ Android, ✅ iOS, ✅ Web (Web Share API)

---

## Event Handling

```javascript
// Listen for native events
NativiWeb.on('push-received', (data) => {
  console.log('Push notification received:', data);
});

NativiWeb.on('app-resume', () => {
  console.log('App resumed from background');
});

NativiWeb.on('app-pause', () => {
  console.log('App going to background');
});

// Remove event listener
NativiWeb.off('push-received', handler);
```

## Error Handling

All SDK methods return Promises and should be wrapped in try-catch blocks:

```javascript
try {
  const position = await NativiWeb.getCurrentPosition();
  console.log('Position:', position);
} catch (error) {
  if (error.code === 'PERMISSION_DENIED') {
    console.error('Location permission denied');
  } else if (error.code === 'NOT_NATIVE') {
    console.error('This feature requires the native app');
  } else {
    console.error('Error:', error.message);
  }
}
```

## Feature Detection

```javascript
// Check if feature is available before using
if (NativiWeb.isNative && NativiWeb.platform === 'android') {
  // Android-specific code
}

// Check specific feature availability
const features = await NativiWeb.getDeviceInfo();
if (features.camera) {
  // Camera is available
}
```

## Best Practices

1. **Always check `isNative`** before calling native-only features
2. **Handle errors gracefully** with try-catch blocks
3. **Request permissions** before using sensitive features
4. **Provide fallbacks** for web browser usage
5. **Test on real devices** when possible

## Supported Platforms

| Feature | Android | iOS | Web (Fallback) |
|---------|---------|-----|----------------|
| Device Info | ✅ | ✅ | ✅ |
| Push Notifications | ✅ | ✅ | ✅ (Web Push) |
| Geolocation | ✅ | ✅ | ✅ |
| Camera | ✅ | ✅ | ✅ |
| Local Storage | ✅ | ✅ | ✅ |
| Biometrics | ✅ | ✅ | ❌ |
| Haptics | ✅ | ✅ | Limited |
| Share | ✅ | ✅ | ✅ (Web Share) |
| Clipboard | ✅ | ✅ | ✅ |

## Version History

### v1.0.0
- Initial release
- Support for all core native features
- Android and iOS support

---

For more information, visit [NativiWeb Studio Documentation](https://nativiweb.io/docs)
