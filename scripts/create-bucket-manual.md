# Création du bucket 'project-logos' dans Supabase Storage

## Méthode 1: Via l'interface Supabase Dashboard (Recommandé)

1. Connectez-vous à votre [dashboard Supabase](https://supabase.com/dashboard)
2. Sélectionnez votre projet
3. Allez dans **Storage** dans le menu de gauche
4. Cliquez sur **New bucket**
5. Remplissez les informations :
   - **Name**: `project-logos`
   - **Public bucket**: ✅ Cocher (pour permettre l'accès public aux logos)
   - **File size limit**: `5 MB`
   - **Allowed MIME types**: 
     - `image/png`
     - `image/jpeg`
     - `image/jpg`
     - `image/webp`
     - `image/svg+xml`
6. Cliquez sur **Create bucket**

## Méthode 2: Via SQL Editor

1. Ouvrez le **SQL Editor** dans votre dashboard Supabase
2. Exécutez le script `scripts/create-storage-bucket.sql`
3. Ou copiez-collez cette requête :

```sql
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'project-logos',
  'project-logos',
  true,
  5242880,
  ARRAY['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/svg+xml']
)
ON CONFLICT (id) DO NOTHING;
```

## Configuration des politiques RLS (Row Level Security)

Après avoir créé le bucket, configurez les politiques de sécurité :

### 1. Lecture publique (pour afficher les logos)

```sql
CREATE POLICY "Public Access"
ON storage.objects FOR SELECT
USING (bucket_id = 'project-logos');
```

### 2. Upload pour les utilisateurs authentifiés

```sql
CREATE POLICY "Authenticated users can upload"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'project-logos' 
  AND auth.role() = 'authenticated'
);
```

### 3. Suppression pour les propriétaires

```sql
CREATE POLICY "Users can delete own files"
ON storage.objects FOR DELETE
USING (
  bucket_id = 'project-logos' 
  AND auth.uid()::text = (storage.foldername(name))[1]
);
```

## Vérification

Après avoir créé le bucket, vous devriez pouvoir :
1. Voir le bucket dans la liste des buckets Storage
2. Uploader des logos via l'interface du projet
3. Accéder publiquement aux logos uploadés

## Notes

- Le bucket doit être **public** pour que les logos soient accessibles sans authentification
- La taille maximale des fichiers est limitée à 5MB
- Seuls les types MIME d'images sont autorisés
