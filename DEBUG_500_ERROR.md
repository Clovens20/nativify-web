# 🐛 Debug Erreur 500

## ✅ Bonne Nouvelle : CORS Résolu !

Les erreurs CORS sont maintenant **résolues** ! Les requêtes passent correctement :
- ✅ Avant : `http://localhost:8000/api/auth/login` → Erreur CORS
- ✅ Maintenant : `http://localhost:3000/api/auth/login` → Proxy Next.js → Backend (pas d'erreur CORS)

## ⚠️ Nouveau Problème : Erreur 500

Le backend retourne maintenant des erreurs 500 sur toutes les requêtes API :
- `GET /api/auth/me` → 500
- `POST /api/auth/login` → 500
- `POST /api/track-visit` → 500

## 🔍 Diagnostic

Cela signifie que :
1. ✅ Le proxy Next.js fonctionne correctement
2. ✅ Les requêtes sont bien proxifiées vers le backend
3. ❌ Le backend retourne une erreur 500

## 📝 Actions à Effectuer

### 1. Vérifier que le Backend est Démarré

```powershell
# Vérifier si le backend tourne sur le port 8000
Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*uvicorn*"}
```

### 2. Vérifier les Logs du Backend

Dans le terminal où le backend tourne, vous devriez voir les erreurs. Les logs devraient montrer :
- L'erreur exacte qui cause le 500
- La stack trace
- Les détails de la requête

### 3. Tester le Backend Directement

```powershell
# Tester le health endpoint directement
curl http://localhost:8000/api/health
```

Si cette commande échoue, le backend n'est probablement pas démarré ou a une erreur.

### 4. Redémarrer le Backend

Si le backend n'est pas démarré ou a des erreurs :

```powershell
# Arrêter le backend (Ctrl+C)
# Puis redémarrer
npm run dev:backend
```

### 5. Vérifier les Variables d'Environnement

Assurez-vous que `backend/.env` existe et contient les bonnes variables :
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY` (si nécessaire)

## 🔍 Causes Possibles

1. **Backend non démarré** : Le backend n'est pas en cours d'exécution
2. **Erreur de configuration** : Variables d'environnement manquantes
3. **Erreur dans le code backend** : Une exception non gérée
4. **Problème de connexion Supabase** : Si le backend dépend de Supabase

## ✅ Solution Rapide

1. **Vérifier les logs du backend** (terminal où `npm run dev:backend` tourne)
2. **Redémarrer le backend** si nécessaire
3. **Vérifier les variables d'environnement** dans `backend/.env`

---

**Note** : Le proxy Next.js fonctionne correctement, il faut maintenant résoudre l'erreur 500 du backend.

