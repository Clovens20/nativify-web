-- Script pour promouvoir un utilisateur en admin
-- Usage: Remplacez 'EMAIL' par l'email de l'utilisateur

-- Méthode 1: Par email
UPDATE public.users
SET role = 'admin'
WHERE email = 'clodenerc@yahoo.fr';

-- Méthode 2: Par ID
UPDATE public.users
SET role = 'admin'
WHERE id = '6488b320-b39f-411d-849e-4d36a5145f70';

-- Vérifier le résultat
SELECT id, email, role, status
FROM public.users
WHERE email = 'clodenerc@yahoo.fr' OR id = '6488b320-b39f-411d-849e-4d36a5145f70';

