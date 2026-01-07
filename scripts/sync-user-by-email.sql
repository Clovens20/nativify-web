-- Script SQL pour synchroniser un utilisateur par son EMAIL
-- Usage: Remplacez 'desirdalia@gmail.com' par l'email de l'utilisateur

-- Synchroniser l'utilisateur de auth.users vers public.users par email
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
WHERE au.email = 'desirdalia@gmail.com' -- ⬅️ REMPLACEZ PAR L'EMAIL
ON CONFLICT (id) DO UPDATE
SET 
    email = EXCLUDED.email,
    name = COALESCE(NULLIF(EXCLUDED.name, ''), users.name)
RETURNING *;

-- Vérifier que l'utilisateur est bien synchronisé
SELECT 
    id, 
    email, 
    name, 
    role, 
    status, 
    created_at,
    '✅ Synchronisé' as status_message
FROM public.users
WHERE email = 'desirdalia@gmail.com'; -- ⬅️ REMPLACEZ PAR L'EMAIL

