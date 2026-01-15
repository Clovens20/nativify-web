# Solution : Synchroniser un utilisateur manquant dans l'interface admin

## Problème
L'utilisateur avec l'ID `fd599f98-56cf-445f-93d6-abdde48f959c` existe dans le projet mais n'apparaît pas dans la liste des utilisateurs de l'interface admin.

## Cause
L'utilisateur existe probablement dans `auth.users` (table Supabase Auth) mais pas dans `public.users` (table publique de votre application). L'interface admin ne liste que les utilisateurs de `public.users`.

## Solutions

### Solution 1 : Script SQL (Recommandé - Le plus rapide)

1. Ouvrez le **Supabase SQL Editor**
2. Exécutez cette requête (remplacez l'ID si nécessaire) :

```sql
-- Synchroniser l'utilisateur spécifique
INSERT INTO public.users (id, email, name, role, status, created_at)
SELECT 
    au.id,
    au.email,
    COALESCE(
        au.raw_user_meta_data->>'name', 
        SPLIT_PART(au.email, '@', 1),
        'Utilisateur'
    ) as name,
    'user' as role,
    'active' as status,
    COALESCE(au.created_at, NOW())
FROM auth.users as au
WHERE au.id = 'fd599f98-56cf-445f-93d6-abdde48f959c'
ON CONFLICT (id) DO UPDATE
SET 
    email = EXCLUDED.email,
    name = COALESCE(NULLIF(EXCLUDED.name, ''), users.name),
    updated_at = NOW()
RETURNING *;

-- Vérifier le résultat
SELECT id, email, name, role, status, created_at
FROM public.users
WHERE id = 'fd599f98-56cf-445f-93d6-abdde48f959c';
```

✅ **Avantages** : Rapide, direct, pas besoin de redémarrer le serveur

---

### Solution 2 : Script Python

1. Assurez-vous que votre fichier `.env` contient :
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`

2. Exécutez le script :
```bash
python scripts/sync-user.py fd599f98-56cf-445f-93d6-abdde48f959c
```

✅ **Avantages** : Automatique, affiche les détails de l'utilisateur

---

### Solution 3 : Via l'API (Nouveau endpoint)

Un nouvel endpoint a été ajouté : `POST /api/admin/users/sync/{user_id}`

Vous pouvez l'appeler depuis votre interface admin ou via curl :

```bash
curl -X POST "http://localhost:8000/api/admin/users/sync/fd599f98-56cf-445f-93d6-abdde48f959c" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

---

## Vérification

Après avoir exécuté une des solutions ci-dessus :

1. Rafraîchissez l'interface admin (`/admin`)
2. Allez dans l'onglet **Utilisateurs**
3. L'utilisateur devrait maintenant apparaître dans la liste

## Pour éviter ce problème à l'avenir

Les utilisateurs devraient être automatiquement créés dans `public.users` lors de leur inscription. Si ce n'est pas le cas, cela peut être dû à :

- Une erreur lors de l'inscription
- Un utilisateur créé manuellement dans Supabase Auth
- Un problème de synchronisation

**Solution préventive** : Un trigger SQL automatique peut être créé pour synchroniser automatiquement tous les nouveaux utilisateurs de `auth.users` vers `public.users`.

---

## Fichiers créés

- `scripts/sync-specific-user.sql` - Script SQL pour synchroniser un utilisateur
- `scripts/sync-user.py` - Script Python pour synchroniser un utilisateur
- `backend/admin_sync.py` - Module backend pour la synchronisation

## Questions ?

Si l'utilisateur n'apparaît toujours pas après la synchronisation :
1. Vérifiez que l'ID est correct
2. Vérifiez les permissions RLS dans Supabase
3. Vérifiez les logs du backend pour des erreurs

