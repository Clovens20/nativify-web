# 🔄 Système de Vérification de Version Automatique

## Vue d'ensemble

Le système de vérification de version automatique permet à votre application web d'informer l'application native lorsqu'une nouvelle version est disponible. Cela garantit que les utilisateurs obtiennent toujours la dernière version de votre application web sans avoir à mettre à jour l'application native depuis le store.

## Fonctionnement

### Architecture

1. **Backend API** : Un endpoint vérifie la version actuelle du projet et compare avec la version envoyée par l'app native
2. **Bridge Natif** : Méthode `forceReload()` pour recharger le WebView avec ou sans cache
3. **JavaScript SDK** : Méthodes pour vérifier la version et déclencher le rechargement

### Flux de Vérification

```
App Native → SDK JS → API Backend → Réponse (update_available?)
                    ↓
              Si mise à jour disponible
                    ↓
         forceReload(clearCache=true)
                    ↓
           WebView recharge avec nouvelle version
```

## Configuration

### 1. Définir la Version dans le Projet

Lors de la création ou de la mise à jour d'un projet, définissez `web_app_version` :

```json
PUT /api/projects/{project_id}
{
  "web_app_version": "1.2.3"
}
```

**Formats de version supportés :**
- Format sémantique : `"1.2.3"`, `"2.0.0-beta"`
- Format date : `"2024.01.15"`, `"2024-01-15"`
- Format personnalisé : Tout string qui peut être comparé

### 2. Désactiver la Vérification (optionnel)

Si vous ne souhaitez pas utiliser la vérification de version :

```json
PUT /api/projects/{project_id}
{
  "version_check_enabled": false
}
```

## Utilisation dans l'Application Web

### Méthode 1 : Vérification Manuelle

```javascript
// Vérifier la version une fois
const projectId = 'your-project-id'; // Récupéré depuis les métadonnées ou configuré
const currentVersion = '1.0.0'; // Version actuelle dans l'app native

NativiWeb.checkVersion(projectId, currentVersion, 'https://api.nativiweb.io')
  .then(result => {
    if (result.update_available) {
      console.log('Nouvelle version disponible:', result.version);
      // Demander confirmation à l'utilisateur
      if (confirm('Une nouvelle version est disponible. Recharger maintenant ?')) {
        NativiWeb.forceReload(true); // true = clear cache
      }
    } else {
      console.log('Vous avez la dernière version');
    }
  })
  .catch(error => {
    console.error('Erreur de vérification:', error);
  });
```

### Méthode 2 : Vérification Automatique Périodique

```javascript
const projectId = 'your-project-id';
const currentVersion = '1.0.0';
const apiBaseUrl = 'https://api.nativiweb.io';

// Démarrer la vérification automatique toutes les 30 minutes
NativiWeb.startVersionChecker(projectId, currentVersion, apiBaseUrl, 30);

// Écouter les événements de mise à jour
window.addEventListener('nativiweb:update-available', (event) => {
  const result = event.detail;
  console.log('Mise à jour disponible:', result.version);
  
  // Afficher une notification ou forcer le rechargement
  showUpdateNotification(result, () => {
    NativiWeb.forceReload(true);
  });
});

// Arrêter la vérification (si nécessaire)
// NativiWeb.stopVersionChecker();
```

### Méthode 3 : Vérification au Démarrage

```javascript
// Dans votre code d'initialisation de l'app
document.addEventListener('DOMContentLoaded', () => {
  const projectId = getProjectIdFromConfig(); // À implémenter
  const currentVersion = getAppVersion(); // À implémenter
  
  // Vérifier et recharger automatiquement si mise à jour disponible
  NativiWeb.checkVersionAndReload(projectId, currentVersion, API_BASE_URL, true)
    .catch(error => {
      console.error('Vérification de version échouée:', error);
      // Continuer avec la version actuelle
    });
});
```

## Récupérer le Project ID

### Option 1 : Dans les Métadonnées du Projet Généré

Le `project_id` peut être stocké dans les ressources Android :

```kotlin
// Dans MainActivity.kt (généré)
val projectId = getString(R.string.project_id)
```

### Option 2 : Via les Métadonnées Web

Inclure le project ID dans votre HTML initial :

```html
<script>
  window.NATIVIWEB_PROJECT_ID = 'your-project-id';
</script>
<script src="nativiweb-sdk.js"></script>
```

Puis dans votre code :

```javascript
const projectId = window.NATIVIWEB_PROJECT_ID || getProjectIdFromConfig();
```

### Option 3 : Depuis l'URL de l'API

Si votre API backend peut retourner le project_id basé sur l'URL web :

```javascript
// Endpoint personnalisé sur votre backend
fetch('https://your-backend.com/api/project-id')
  .then(r => r.json())
  .then(data => {
    const projectId = data.project_id;
    // Utiliser projectId pour la vérification
  });
```

## API Backend

### Endpoint : Vérifier la Version

```
GET /api/projects/{project_id}/version/check?current_version={version}
```

**Paramètres :**
- `project_id` : ID du projet (dans l'URL)
- `current_version` : Version actuelle dans l'app native (query param, optionnel)

**Réponse :**

```json
{
  "version": "1.2.3",
  "current_version": "1.0.0",
  "update_available": true,
  "project_id": "project-uuid",
  "web_url": "https://example.com",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Si la vérification est désactivée :

```json
{
  "version_check_enabled": false,
  "message": "Version check is disabled for this project"
}
```

## Méthodes SDK Disponibles

### `checkVersion(projectId, currentVersion, apiBaseUrl)`

Vérifie si une nouvelle version est disponible.

**Paramètres :**
- `projectId` (string) : ID du projet
- `currentVersion` (string, optionnel) : Version actuelle
- `apiBaseUrl` (string, optionnel) : URL de base de l'API (défaut: placeholder dans le SDK)

**Retourne :** Promise qui se résout avec un objet de résultat

### `checkVersionAndReload(projectId, currentVersion, apiBaseUrl, autoReload)`

Vérifie la version et recharge automatiquement si une mise à jour est disponible.

**Paramètres :**
- `projectId` (string) : ID du projet
- `currentVersion` (string, optionnel) : Version actuelle
- `apiBaseUrl` (string, optionnel) : URL de base de l'API
- `autoReload` (boolean, défaut: true) : Recharger automatiquement

**Retourne :** Promise

### `startVersionChecker(projectId, currentVersion, apiBaseUrl, intervalMinutes)`

Démarre une vérification périodique automatique.

**Paramètres :**
- `projectId` (string) : ID du projet
- `currentVersion` (string) : Version actuelle
- `apiBaseUrl` (string) : URL de base de l'API
- `intervalMinutes` (number, défaut: 30) : Intervalle entre les vérifications (en minutes)

### `stopVersionChecker()`

Arrête la vérification automatique périodique.

### `forceReload(clearCache)`

Force le rechargement de la WebView.

**Paramètres :**
- `clearCache` (boolean, défaut: false) : Vider le cache avant de recharger

## Événements

### `nativiweb:update-available`

Déclenché lorsqu'une nouvelle version est détectée par la vérification automatique.

```javascript
window.addEventListener('nativiweb:update-available', (event) => {
  const { version, current_version, update_available } = event.detail;
  // Gérer la mise à jour
});
```

## Bonnes Pratiques

### 1. Gestion des Erreurs

Toujours gérer les erreurs de vérification :

```javascript
NativiWeb.checkVersion(projectId, currentVersion)
  .catch(error => {
    console.error('Version check failed:', error);
    // Ne pas bloquer l'application si la vérification échoue
  });
```

### 2. Ne Pas Forcer le Rechargement Immédiat

Laissez l'utilisateur choisir quand mettre à jour (sauf cas critiques) :

```javascript
if (result.update_available) {
  // Afficher une notification discrète
  showUpdateBanner({
    message: 'Une nouvelle version est disponible',
    action: () => NativiWeb.forceReload(true)
  });
}
```

### 3. Vérification au Bon Moment

- **Au démarrage** : Vérifier silencieusement
- **Périodiquement** : Utiliser `startVersionChecker()` avec un intervalle raisonnable (30 min - 1h)
- **Après action utilisateur** : Vérifier après une interaction majeure

### 4. Stocker la Version Actuelle

Stockez la version actuelle pour la réutiliser :

```javascript
// LocalStorage ou autre mécanisme de stockage
const CURRENT_VERSION = '1.0.0';
localStorage.setItem('app_version', CURRENT_VERSION);

// Utiliser lors de la vérification
const storedVersion = localStorage.getItem('app_version');
NativiWeb.checkVersion(projectId, storedVersion);
```

## Limitations

1. **Project ID requis** : Le système nécessite le `project_id` pour fonctionner. Il doit être fourni à l'application web d'une manière ou d'une autre.

2. **URL API** : L'URL de base de l'API doit être configurée dans le SDK ou fournie à chaque appel.

3. **Comparaison de versions** : La comparaison est actuellement basée sur l'égalité stricte des strings. Les versions sémantiques complexes peuvent nécessiter une logique personnalisée.

4. **Authentification** : L'endpoint de vérification de version ne nécessite pas d'authentification pour le moment, mais le `project_id` doit être valide.

## Exemples Complets

### Exemple 1 : Vérification Simple avec Notification

```javascript
// config.js
const CONFIG = {
  projectId: 'your-project-id',
  currentVersion: '1.0.0',
  apiBaseUrl: 'https://api.nativiweb.io'
};

// app.js
async function checkForUpdates() {
  try {
    const result = await NativiWeb.checkVersion(
      CONFIG.projectId,
      CONFIG.currentVersion,
      CONFIG.apiBaseUrl
    );
    
    if (result.update_available) {
      showUpdateNotification({
        title: 'Mise à jour disponible',
        message: `Version ${result.version} est maintenant disponible`,
        buttons: [
          {
            text: 'Plus tard',
            action: () => {}
          },
          {
            text: 'Mettre à jour',
            action: () => NativiWeb.forceReload(true)
          }
        ]
      });
    }
  } catch (error) {
    console.error('Erreur de vérification:', error);
  }
}

// Vérifier au démarrage
document.addEventListener('DOMContentLoaded', checkForUpdates);

// Vérifier toutes les heures
setInterval(checkForUpdates, 60 * 60 * 1000);
```

### Exemple 2 : Vérification Automatique avec Détection Silencieuse

```javascript
const APP_CONFIG = {
  projectId: window.NATIVIWEB_PROJECT_ID,
  version: '1.0.0',
  apiBaseUrl: window.API_BASE_URL || 'https://api.nativiweb.io'
};

// Démarrer la vérification automatique (30 minutes)
NativiWeb.startVersionChecker(
  APP_CONFIG.projectId,
  APP_CONFIG.version,
  APP_CONFIG.apiBaseUrl,
  30
);

// Écouter les mises à jour
window.addEventListener('nativiweb:update-available', (event) => {
  const { version } = event.detail;
  
  // Afficher une badge ou notification discrète
  updateNotificationBadge(true);
  
  // Optionnel : forcer le rechargement pour les mises à jour critiques
  // NativiWeb.forceReload(true);
});
```

## Support

Pour plus d'informations ou de l'aide, consultez :
- [Documentation API](../docs/API.md)
- [Documentation SDK](../docs/SDK.md)
- [Issues GitHub](https://github.com/nativiweb/studio/issues)

