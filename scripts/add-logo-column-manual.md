# Instructions pour ajouter la colonne logo_url manuellement

Si vous obtenez une erreur "Failed to fetch" lors de l'exécution du script SQL, voici plusieurs solutions :

## Solution 1: Via l'interface Supabase (Table Editor)

1. Allez dans **Supabase Dashboard** → Votre projet
2. Cliquez sur **Table Editor** dans le menu de gauche
3. Sélectionnez la table **`projects`**
4. Cliquez sur **Add Column** (ou le bouton "+" en haut à droite)
5. Remplissez les informations :
   - **Name**: `logo_url`
   - **Type**: `text`
   - **Default value**: (laissez vide)
   - **Is nullable**: ✓ (coché)
6. Cliquez sur **Save**

## Solution 2: Via SQL Editor (ligne par ligne)

Exécutez ces commandes **une par une** dans l'ordre :

```sql
-- 1. D'abord, vérifiez si la colonne existe déjà
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'projects' AND column_name = 'logo_url';
```

Si aucun résultat n'est retourné, alors exécutez :

```sql
-- 2. Ajoutez la colonne
ALTER TABLE public.projects ADD COLUMN logo_url TEXT;
```

## Solution 3: Via Supabase CLI

Si vous avez Supabase CLI installé :

```bash
supabase db execute --file scripts/add-logo-column-projects.sql
```

## Solution 4: Vérification après ajout

Pour vérifier que la colonne a été ajoutée avec succès :

```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'projects'
ORDER BY ordinal_position;
```

Vous devriez voir `logo_url` dans la liste des colonnes.

## Note importante

Si la colonne existe déjà, vous obtiendrez une erreur. Dans ce cas, c'est normal et vous pouvez ignorer l'erreur - la colonne est déjà présente.

