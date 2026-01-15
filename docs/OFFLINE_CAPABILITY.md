# Offline Capability & Asset Bundling

## Vue d'ensemble

NativiWeb Studio génère automatiquement un Service Worker pour permettre aux applications natives de fonctionner hors ligne. Cette fonctionnalité permet de mettre en cache les assets de l'application web et d'assurer une expérience utilisateur fluide même sans connexion Internet.

## Activation

Activez la feature **"Offline Capability & Asset Bundling"** lors de la création ou modification d'un projet dans NativiWeb Studio.

## Fonctionnement

### Service Worker automatique

Un Service Worker est généré et injecté automatiquement dans chaque projet :

- **Stratégie de cache** : Cache First, Network Fallback
- **Assets mis en cache** : HTML, CSS, JS, images de l'application web
- **Mise à jour automatique** : Le cache est mis à jour lors de la prochaine connexion

### Assets inclus

Par défaut, les assets suivants sont mis en cache :
- Page principale (`/`)
- Fichiers HTML
- Fichiers CSS
- Fichiers JavaScript
- Images
- Manifest

### Configuration personnalisée

Vous pouvez personnaliser le cache en modifiant la configuration du projet :

```json
{
  "features": [
    {
      "id": "offline_bundling",
      "enabled": true,
      "config": {
        "cache_strategy": "cache-first",
        "cache_duration": "7d",
        "additional_urls": ["/api/data", "/static/images"]
      }
    }
  ]
}
```

## Utilisation dans l'application

Le Service Worker est automatiquement enregistré dans les projets générés. L'application fonctionne automatiquement hors ligne si :

1. La feature "offline_bundling" est activée
2. L'utilisateur a visité l'application au moins une fois en ligne
3. Les assets nécessaires ont été mis en cache

## Détection en ligne/hors ligne

Utilisez le SDK JavaScript pour détecter l'état de connexion :

```javascript
// Vérifier si en ligne
const isOnline = await NativiWeb.isOnline();
console.log('En ligne:', isOnline);

// Écouter les changements de connexion
NativiWeb.onOnline(() => {
  console.log('Connexion rétablie');
  // Synchroniser les données
  syncData();
});

NativiWeb.onOffline(() => {
  console.log('Mode hors ligne activé');
  // Activer le mode offline
  showOfflineIndicator();
});

// Exemple d'utilisation complète
async function checkConnectionAndSync() {
  const online = await NativiWeb.isOnline();
  
  if (online) {
    try {
      // Synchroniser les données
      await syncWithServer();
    } catch (error) {
      console.error('Erreur de synchronisation:', error);
    }
  } else {
    // Utiliser les données en cache
    loadCachedData();
  }
}
```

## Stratégies de cache

### Cache First (par défaut)

Le Service Worker cherche d'abord dans le cache local, puis sur le réseau si non trouvé :

```
Requête → Cache → (Non trouvé) → Réseau → Mise à jour cache
```

**Avantages :**
- Performance maximale
- Fonctionne hors ligne
- Réduction de la consommation de données

**Inconvénients :**
- Peut servir des données obsolètes
- Nécessite une stratégie de mise à jour

### Network First

Le Service Worker cherche d'abord sur le réseau, puis dans le cache si échec :

```
Requête → Réseau → (Échec) → Cache
```

**Avantages :**
- Données toujours à jour
- Fallback automatique hors ligne

**Inconvénients :**
- Plus lent si réseau instable
- Consomme plus de données

## Gestion du cache

### Vider le cache

Pour forcer une mise à jour du cache, utilisez la méthode du Service Worker :

```javascript
// Depuis votre application web
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.ready.then(registration => {
    registration.active.postMessage({
      type: 'CLEAR_CACHE'
    });
  });
}
```

### Vérifier la taille du cache

```javascript
if ('caches' in window) {
  caches.keys().then(cacheNames => {
    cacheNames.forEach(cacheName => {
      caches.open(cacheName).then(cache => {
        cache.keys().then(keys => {
          console.log(`Cache "${cacheName}" contient ${keys.length} entrées`);
        });
      });
    });
  });
}
```

## Limitations

- **Taille du cache** : La taille totale du cache est limitée par le navigateur (généralement plusieurs centaines de MB)
- **Domaines externes** : Le Service Worker ne peut pas mettre en cache les requêtes vers des domaines externes (sécurité)
- **Requêtes dynamiques** : Les données dynamiques (API) ne sont pas mises en cache par défaut
- **Mises à jour** : Les mises à jour du cache nécessitent une visite de l'utilisateur

## Bonnes pratiques

### 1. Tester en mode offline

Toujours tester votre application sans connexion Internet :

```javascript
// Dans la console du navigateur
// Chrome DevTools > Network > Offline
```

### 2. Optimiser les assets

- Compressez les images (WebP, AVIF)
- Minifiez le CSS et JavaScript
- Utilisez la mise en cache des navigateurs (Cache-Control headers)

### 3. Gérer les erreurs réseau

Implémentez des fallbacks pour les requêtes API :

```javascript
async function fetchData() {
  try {
    const response = await fetch('/api/data');
    if (!response.ok) throw new Error('Network error');
    return await response.json();
  } catch (error) {
    // Fallback vers le cache local
    const cached = await getCachedData();
    if (cached) {
      return cached;
    }
    throw error;
  }
}
```

### 4. Indicateur visuel

Affichez un indicateur lorsque l'app est en mode offline :

```javascript
NativiWeb.onOffline(() => {
  // Afficher un bandeau "Mode hors ligne"
  showOfflineBanner();
});

NativiWeb.onOnline(() => {
  // Masquer le bandeau
  hideOfflineBanner();
  
  // Optionnel : afficher "Connexion rétablie"
  showSyncIndicator();
});
```

### 5. Synchronisation des données

Implémentez une queue de synchronisation pour les données modifiées hors ligne :

```javascript
const syncQueue = [];

function addToSyncQueue(data) {
  syncQueue.push({
    ...data,
    timestamp: Date.now()
  });
  // Sauvegarder dans localStorage
  localStorage.setItem('syncQueue', JSON.stringify(syncQueue));
}

async function syncQueueWithServer() {
  const online = await NativiWeb.isOnline();
  if (!online) return;
  
  const queue = JSON.parse(localStorage.getItem('syncQueue') || '[]');
  
  for (const item of queue) {
    try {
      await fetch('/api/sync', {
        method: 'POST',
        body: JSON.stringify(item)
      });
      // Retirer de la queue après succès
      syncQueue.shift();
    } catch (error) {
      console.error('Erreur de sync:', error);
      break; // Arrêter si erreur
    }
  }
  
  localStorage.setItem('syncQueue', JSON.stringify(syncQueue));
}
```

## Architecture technique

### Service Worker généré

Le Service Worker est généré automatiquement et inclus dans le projet Android/iOS généré :

- **Fichier** : `app/src/main/assets/service-worker.js` (Android)
- **Enregistrement** : Automatique dans MainActivity.kt
- **Version** : Cache versionné pour faciliter les mises à jour

### Structure du cache

```
nativiweb-cache-v1/
├── / (page principale)
├── /index.html
├── /assets/css/styles.css
├── /assets/js/app.js
├── /assets/images/logo.png
└── /manifest.json
```

## Exemples d'utilisation

### Exemple 1 : Application de lecture

```javascript
// Détecter le mode offline et charger depuis le cache
NativiWeb.onOffline(async () => {
  const articles = await getCachedArticles();
  displayArticles(articles);
  showMessage('Mode hors ligne - Articles en cache');
});

// Synchroniser lors de la reconnexion
NativiWeb.onOnline(async () => {
  await syncArticles();
  showMessage('Articles synchronisés');
});
```

### Exemple 2 : Application de messagerie

```javascript
// Sauvegarder les messages localement
function saveMessage(message) {
  // Sauvegarder dans IndexedDB ou localStorage
  const messages = JSON.parse(localStorage.getItem('messages') || '[]');
  messages.push({ ...message, synced: false });
  localStorage.setItem('messages', JSON.stringify(messages));
}

// Synchroniser lors de la reconnexion
NativiWeb.onOnline(async () => {
  const messages = JSON.parse(localStorage.getItem('messages') || '[]');
  const unsynced = messages.filter(m => !m.synced);
  
  for (const message of unsynced) {
    try {
      await fetch('/api/messages', {
        method: 'POST',
        body: JSON.stringify(message)
      });
      message.synced = true;
    } catch (error) {
      console.error('Erreur sync message:', error);
    }
  }
  
  localStorage.setItem('messages', JSON.stringify(messages));
});
```

## Dépannage

### Le Service Worker ne se charge pas

1. Vérifiez que la feature "offline_bundling" est activée
2. Vérifiez que le fichier `service-worker.js` est présent dans les assets
3. Vérifiez la console du navigateur pour les erreurs

### Le cache ne se met pas à jour

1. Vérifiez la version du cache dans le Service Worker
2. Forcez un rafraîchissement (Ctrl+Shift+R)
3. Vérifiez que les nouveaux assets sont accessibles

### Erreurs de permissions

Certains navigateurs nécessitent HTTPS pour les Service Workers. En développement local, utilisez `http://localhost` qui fonctionne sans HTTPS.

## Documentation supplémentaire

- [MDN Service Workers](https://developer.mozilla.org/fr/docs/Web/API/Service_Worker_API)
- [Workbox Documentation](https://developers.google.com/web/tools/workbox)
- [Progressive Web Apps](https://web.dev/progressive-web-apps/)

