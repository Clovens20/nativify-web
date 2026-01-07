-- Script SQL pour synchroniser l'utilisateur desirdalia@gmail.com
-- Exécutez cette requête dans Supabase SQL Editor

-- Vérifier d'abord si l'utilisateur existe dans auth.users
SELECT 
    id, 
    email, 
    created_at,
    raw_user_meta_data
FROM auth.users 
WHERE id = 'fd599f98-56cf-445f-93d6-abdde48f959c'
   OR email = 'desirdalia@gmail.com';

-- Synchroniser l'utilisateur de auth.users vers public.users
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
  AND au.email = 'desirdalia@gmail.com'
ON CONFLICT (id) DO UPDATE
SET 
    email = EXCLUDED.email,
    name = COALESCE(NULLIF(EXCLUDED.name, ''), users.name),
    status = COALESCE(users.status, 'active')
RETURNING *;

-- Vérifier que l'utilisateur est bien synchronisé
SELECT 
    id, 
    email, 
    name, 
    role, 
    status, 
    created_at,
    '✅ Utilisateur synchronisé avec succès' as status_message
FROM public.users
WHERE id = 'fd599f98-56cf-445f-93d6-abdde48f959c'
   OR email = 'desirdalia@gmail.com';

