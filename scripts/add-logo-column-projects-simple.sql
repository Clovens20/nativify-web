-- Script SQL simplifié pour ajouter la colonne logo_url
-- Exécutez cette requête dans Supabase SQL Editor (une ligne à la fois si nécessaire)

-- Étape 1: Ajouter la colonne
ALTER TABLE public.projects ADD COLUMN logo_url TEXT;

-- Étape 2: Vérifier que la colonne existe
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'projects' AND column_name = 'logo_url';

