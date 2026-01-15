-- Script pour créer le bucket 'project-logos' dans Supabase Storage
-- 
-- INSTRUCTIONS:
-- 1. Ouvrez le SQL Editor dans votre dashboard Supabase
-- 2. Exécutez cette requête
-- 3. Ou créez le bucket manuellement via l'interface Storage dans Supabase Dashboard

-- Option 1: Créer via SQL (si vous avez les permissions)
-- Note: La création de buckets via SQL nécessite des permissions admin
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'project-logos',
  'project-logos',
  true,
  5242880, -- 5MB en bytes
  ARRAY['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/svg+xml']
)
ON CONFLICT (id) DO NOTHING;

-- Option 2: Créer les politiques RLS pour le bucket (après création)
-- Permettre la lecture publique
CREATE POLICY "Public Access"
ON storage.objects FOR SELECT
USING (bucket_id = 'project-logos');

-- Permettre l'upload aux utilisateurs authentifiés
CREATE POLICY "Authenticated users can upload"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'project-logos' 
  AND auth.role() = 'authenticated'
);

-- Permettre la suppression aux propriétaires
CREATE POLICY "Users can delete own files"
ON storage.objects FOR DELETE
USING (
  bucket_id = 'project-logos' 
  AND auth.uid()::text = (storage.foldername(name))[1]
);

