-- Script SQL pour ajouter la colonne advanced_config à la table projects
-- À exécuter dans l'éditeur SQL de Supabase

-- Ajouter la colonne advanced_config
ALTER TABLE projects 
ADD COLUMN IF NOT EXISTS advanced_config JSONB DEFAULT '{}'::jsonb;

-- Créer un index
CREATE INDEX IF NOT EXISTS idx_projects_advanced_config 
ON projects USING GIN (advanced_config);

-- Mettre à jour les projets existants
UPDATE projects 
SET advanced_config = '{}'::jsonb
WHERE advanced_config IS NULL;

