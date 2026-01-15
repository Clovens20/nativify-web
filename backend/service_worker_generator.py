"""
Générateur de Service Worker pour le support offline
"""
from typing import List, Dict, Any


def generate_service_worker(web_url: str, features: List[Dict[str, Any]], cache_name: str = 'nativiweb-cache-v1') -> str:
    """
    Génère un Service Worker pour le caching offline
    
    Args:
        web_url: URL de l'application web
        features: Liste des features activées
        cache_name: Nom du cache
    
    Returns:
        Code du Service Worker
    """
    enabled_features = [f.get("id") for f in features if f.get("enabled")]
    
    # URLs à cacher par défaut
    urls_to_cache = [
        web_url,
        '/',
        '/index.html',
        '/manifest.json'
    ]
    
    # Ajouter des assets statiques si offline_bundling est activé
    if 'offline_bundling' in enabled_features:
        urls_to_cache.extend([
            '/assets/',
            '/css/',
            '/js/',
            '/images/'
        ])
    
    return f"""// NativiWeb Service Worker v1.0.0
// Generated for offline support
const CACHE_NAME = '{cache_name}';
const urlsToCache = {urls_to_cache};

// Installation - Cache les ressources
self.addEventListener('install', (event) => {{
    console.log('[Service Worker] Installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {{
                console.log('[Service Worker] Caching app shell');
                return cache.addAll(urlsToCache.map(url => {{
                    try {{
                        return new Request(url, {{ mode: 'no-cors' }});
                    }} catch (e) {{
                        return url;
                    }}
                }}));
            }})
            .catch((error) => {{
                console.error('[Service Worker] Cache failed:', error);
            }})
    );
    // Force l'activation immédiate
    self.skipWaiting();
}});

// Activation - Nettoie les anciens caches
self.addEventListener('activate', (event) => {{
    console.log('[Service Worker] Activating...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {{
            return Promise.all(
                cacheNames.map((cacheName) => {{
                    if (cacheName !== CACHE_NAME) {{
                        console.log('[Service Worker] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }}
                }})
            );
        }})
    );
    // Prend le contrôle immédiatement
    return self.clients.claim();
}});

// Fetch - Stratégie Cache First, Network Fallback
self.addEventListener('fetch', (event) => {{
    // Ignorer les requêtes non-GET
    if (event.request.method !== 'GET') {{
        return;
    }}
    
    // Ignorer les requêtes vers des domaines externes (sauf l'URL principale)
    const url = new URL(event.request.url);
    const isSameOrigin = url.origin === self.location.origin;
    const isMainApp = url.href.startsWith('{web_url}');
    
    if (!isSameOrigin && !isMainApp) {{
        return; // Laisser passer les requêtes externes normalement
    }}
    
    event.respondWith(
        caches.match(event.request)
            .then((cachedResponse) => {{
                // Retourner le cache si disponible
                if (cachedResponse) {{
                    console.log('[Service Worker] Serving from cache:', event.request.url);
                    return cachedResponse;
                }}
                
                // Sinon, fetch depuis le réseau
                return fetch(event.request)
                    .then((response) => {{
                        // Vérifier que la réponse est valide
                        if (!response || response.status !== 200 || response.type !== 'basic') {{
                            return response;
                        }}
                        
                        // Cloner la réponse pour le cache
                        const responseToCache = response.clone();
                        
                        // Mettre en cache pour la prochaine fois
                        caches.open(CACHE_NAME)
                            .then((cache) => {{
                                cache.put(event.request, responseToCache);
                            }});
                        
                        return response;
                    }})
                    .catch((error) => {{
                        console.error('[Service Worker] Fetch failed:', error);
                        // Retourner une page offline si disponible
                        return caches.match('/offline.html') || new Response('Offline', {{
                            status: 503,
                            statusText: 'Service Unavailable',
                            headers: new Headers({{
                                'Content-Type': 'text/plain'
                            }})
                        }});
                    }});
            }})
    );
}});

// Gestion des messages depuis l'application
self.addEventListener('message', (event) => {{
    if (event.data && event.data.type === 'SKIP_WAITING') {{
        self.skipWaiting();
    }}
    
    if (event.data && event.data.type === 'CACHE_URLS') {{
        event.waitUntil(
            caches.open(CACHE_NAME).then((cache) => {{
                return cache.addAll(event.data.urls);
            }})
        );
    }}
}});

console.log('[Service Worker] Loaded');
"""

