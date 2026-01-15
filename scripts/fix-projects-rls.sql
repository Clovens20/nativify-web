-- Script SQL pour corriger les politiques RLS de la table projects
-- Ce script permet au backend (via service role) de créer des projets sans violer RLS

-- Supprimer les anciennes politiques si elles existent
DROP POLICY IF EXISTS "Users can view own projects" ON projects;
DROP POLICY IF EXISTS "Users can create own projects" ON projects;
DROP POLICY IF EXISTS "Users can update own projects" ON projects;
DROP POLICY IF EXISTS "Users can delete own projects" ON projects;

-- Politiques pour projects - Permettre l'accès via service role
-- Les utilisateurs peuvent voir leurs propres projets
CREATE POLICY "Users can view own projects" ON projects
  FOR SELECT 
  USING (
    auth.uid() = user_id 
    OR auth.role() = 'service_role'
  );

-- Les utilisateurs peuvent créer leurs propres projets
-- Le service role peut créer des projets pour n'importe quel utilisateur
CREATE POLICY "Users can create own projects" ON projects
  FOR INSERT 
  WITH CHECK (
    auth.uid() = user_id 
    OR auth.role() = 'service_role'
  );

-- Les utilisateurs peuvent mettre à jour leurs propres projets
-- Le service role peut mettre à jour n'importe quel projet
CREATE POLICY "Users can update own projects" ON projects
  FOR UPDATE 
  USING (
    auth.uid() = user_id 
    OR auth.role() = 'service_role'
  );

-- Les utilisateurs peuvent supprimer leurs propres projets
-- Le service role peut supprimer n'importe quel projet
CREATE POLICY "Users can delete own projects" ON projects
  FOR DELETE 
  USING (
    auth.uid() = user_id 
    OR auth.role() = 'service_role'
  );

-- Vérifier que les politiques sont bien créées
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE tablename = 'projects';

