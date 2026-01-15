-- Script SQL pour synchroniser les utilisateurs entre auth.users et users
-- À exécuter dans Supabase SQL Editor

-- 1. Vérifier les utilisateurs dans auth.users qui n'existent pas dans users
SELECT 
    au.id,
    au.email,
    au.created_at as auth_created_at,
    u.id as user_table_id
FROM auth.users au
LEFT JOIN public.users u ON au.id = u.id
WHERE u.id IS NULL;

-- 2. Créer les utilisateurs manquants dans la table users
INSERT INTO public.users (id, email, name, role, status, created_at)
SELECT 
    au.id,
    au.email,
    COALESCE(au.raw_user_meta_data->>'name', au.email) as name,
    'user' as role,
    'active' as status,
    au.created_at
FROM auth.users au
LEFT JOIN public.users u ON au.id = u.id
WHERE u.id IS NULL
ON CONFLICT (id) DO NOTHING;

-- 3. Vérifier le résultat
SELECT COUNT(*) as total_auth_users FROM auth.users;
SELECT COUNT(*) as total_users FROM public.users;

-- 4. Vérifier un utilisateur spécifique
-- Remplacez 'USER_ID' par l'ID de l'utilisateur
SELECT 
    au.id,
    au.email,
    au.created_at,
    u.id as exists_in_users,
    u.role,
    u.status
FROM auth.users au
LEFT JOIN public.users u ON au.id = u.id
WHERE au.id = '6488b320-b39f-411d-849e-4d36a5145f70';

