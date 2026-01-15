-- Script SQL pour ajouter la colonne logo_url à la table projects
-- Exécutez cette requête dans Supabase SQL Editor
-- Si vous obtenez une erreur, essayez d'exécuter les commandes une par une

-- ÉTAPE 1: Ajouter la colonne (exécutez cette ligne d'abord)
ALTER TABLE public.projects ADD COLUMN logo_url TEXT;

-- ÉTAPE 2: Vérifier que la colonne a été ajoutée (optionnel)
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'projects' AND column_name = 'logo_url';

