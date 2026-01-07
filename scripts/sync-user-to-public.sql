-- Script SQL pour synchroniser un utilisateur de auth.users vers public.users
-- Usage: Exécutez cette requête dans Supabase SQL Editor avec l'ID utilisateur

-- Remplacez 'fd599f98-56cf-445f-93d6-abdde48f959c' par l'ID de votre utilisateur

INSERT INTO public.users (id, email, name, role, status, created_at)
SELECT 
    au.id,
    au.email,
    COALESCE(
        au.raw_user_meta_data->>'name', 
        SPLIT_PART(au.email, '@', 1)
    ) as name,
    'user' as role, -- Rôle par défaut
    'active' as status, -- Statut par défaut
    au.created_at
FROM auth.users as au
WHERE au.id = 'fd599f98-56cf-445f-93d6-abdde48f959c' -- ⬅️ REMPLACEZ PAR L'ID UTILISATEUR
  AND au.id NOT IN (SELECT id FROM public.users)
ON CONFLICT (id) DO UPDATE
SET 
    email = EXCLUDED.email,
    name = COALESCE(EXCLUDED.name, users.name);

-- Vérifier le résultat
SELECT id, email, name, role, status, created_at
FROM public.users
WHERE id = 'fd599f98-56cf-445f-93d6-abdde48f959c'; -- ⬅️ REMPLACEZ PAR L'ID UTILISATEUR

