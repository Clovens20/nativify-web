# 🔄 Configuration du Proxy Next.js

## ✅ Solution Implémentée

Un **proxy Next.js** a été configuré pour éliminer les erreurs CORS en développement. Toutes les requêtes `/api/*` sont maintenant automatiquement proxifiées vers le backend `http://localhost:8000/api/*`.

## 📝 Modifications Apportées

### 1. Configuration Next.js (`next.config.js`)

Ajout d'un `rewrites()` pour proxifier les requêtes API en développement :

```javascript
async rewrites() {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
  
  // In development, proxy /api/* to backend
  if (process.env.NODE_ENV === 'development') {
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  }
  return [];
},
```

**Fonctionnement** :
- ✅ En **développement** : `/api/*` → `http://localhost:8000/api/*` (proxy automatique)
- ✅ En **production** : Utilise directement `NEXT_PUBLIC_BACKEND_URL` (pas de proxy)

### 2. Fichiers Frontend Modifiés

#### `src/lib/api.ts`
- ✅ Utilise `/api` en développement (proxy Next.js)
- ✅ Utilise `NEXT_PUBLIC_BACKEND_URL/api` en production

#### `src/context/AuthContext.tsx`
- ✅ Utilise `/api` en développement (proxy Next.js)
- ✅ Utilise `NEXT_PUBLIC_BACKEND_URL/api` en production

#### `src/app/projects/new/page.tsx`
- ✅ Upload logo utilise `/api` en développement
- ✅ Utilise `NEXT_PUBLIC_BACKEND_URL/api` en production

#### `src/hooks/useTrackVisit.ts`
- ✅ Tracking des visites utilise `/api` en développement
- ✅ Utilise `NEXT_PUBLIC_BACKEND_URL/api` en production

## 🎯 Avantages

1. **Zéro erreur CORS en développement** : Toutes les requêtes passent par Next.js (même origine)
2. **Configuration simple** : Pas besoin de modifier le backend
3. **Sécurisé** : Le proxy fonctionne uniquement en développement
4. **Production-ready** : En production, utilise directement l'URL du backend (via reverse proxy)

## 🚀 Utilisation

### Développement

1. **Démarrer le backend** (port 8000) :
   ```powershell
   npm run dev:backend
   ```

2. **Démarrer le frontend** (port 3000) :
   ```powershell
   npm run dev:frontend
   ```

3. **Accéder à l'application** :
   - Frontend : http://localhost:3000
   - Les requêtes `/api/*` sont automatiquement proxifiées vers `http://localhost:8000/api/*`

### Production

En production, configurez `NEXT_PUBLIC_BACKEND_URL` dans vos variables d'environnement :

```env
NEXT_PUBLIC_BACKEND_URL=https://api.votre-domaine.com
```

Le frontend utilisera directement cette URL (via un reverse proxy comme nginx).

## 🔍 Comment ça fonctionne

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Navigateur    │         │   Next.js (3000) │         │  Backend (8000) │
│  localhost:3000 │────────>│                  │────────>│                 │
│                 │         │  Proxy /api/*    │         │  FastAPI        │
│ Requête /api/   │         │  vers 8000       │         │                 │
│ auth/login      │         │                  │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
     ↓ Même origine              ↓ Pas de CORS               ↓ Réponse
   Pas d'erreur CORS
```

## ✅ Résultat

- ✅ **Zéro erreur CORS** en développement
- ✅ **Login fonctionne** sans blocage
- ✅ **Toutes les requêtes API** fonctionnent correctement
- ✅ **Backend inchangé** (aucune modification nécessaire)
- ✅ **Production-ready** (fonctionne avec reverse proxy)

## 📝 Notes

- Le proxy Next.js fonctionne **uniquement en développement**
- En production, utilisez un reverse proxy (nginx, Apache, etc.) pour proxifier les requêtes
- Le backend reste sur le port 8000, aucune modification nécessaire
- Les variables d'environnement `NEXT_PUBLIC_BACKEND_URL` fonctionnent toujours pour la production

