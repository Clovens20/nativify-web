# Guide de Configuration - NativiWeb Studio

Ce guide vous aidera à configurer et lancer le projet NativiWeb Studio.

## Prérequis

- Python 3.9+
- Node.js 18+
- Un compte Supabase (gratuit)

## Configuration Supabase

1. Créez un projet sur [Supabase](https://supabase.com)
2. Allez dans Settings > API
3. Copiez l'URL du projet et la clé anonyme (anon key)

## Configuration Backend

1. Créez un fichier `.env` dans le dossier `backend/` :

```env
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_ANON_KEY=votre_cle_anon
PORT=8001
```

2. Installez les dépendances Python :

```bash
cd backend
pip install -r requirements.txt
```

3. Créez les tables nécessaires dans Supabase :

Allez dans l'éditeur SQL de Supabase et exécutez ce script :

```sql
-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  email TEXT NOT NULL,
  name TEXT NOT NULL,
  role TEXT DEFAULT 'user',
  status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table des projets
CREATE TABLE IF NOT EXISTS projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  name TEXT NOT NULL,
  web_url TEXT NOT NULL,
  description TEXT,
  platform TEXT[] DEFAULT ARRAY['android', 'ios'],
  features JSONB DEFAULT '[]',
  status TEXT DEFAULT 'draft',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table des builds
CREATE TABLE IF NOT EXISTS builds (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id),
  user_id UUID NOT NULL REFERENCES users(id),
  platform TEXT NOT NULL,
  build_type TEXT DEFAULT 'debug',
  build_config JSONB DEFAULT '{}',
  certificate_id TEXT,
  status TEXT DEFAULT 'pending',
  phase TEXT DEFAULT 'queued',
  progress INTEGER DEFAULT 0,
  logs JSONB DEFAULT '[]',
  artifacts JSONB DEFAULT '[]',
  download_url TEXT,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  duration_seconds INTEGER
);

-- Table des clés API
CREATE TABLE IF NOT EXISTS api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  name TEXT NOT NULL,
  key TEXT NOT NULL UNIQUE,
  permissions TEXT[] DEFAULT ARRAY['read'],
  last_used TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table des logs système
CREATE TABLE IF NOT EXISTS system_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  level TEXT NOT NULL,
  category TEXT NOT NULL,
  message TEXT NOT NULL,
  details JSONB DEFAULT '{}',
  user_id UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table de configuration de la plateforme
CREATE TABLE IF NOT EXISTS platform_config (
  id TEXT PRIMARY KEY DEFAULT 'platform_config',
  maintenance_mode BOOLEAN DEFAULT FALSE,
  max_builds_per_user INTEGER DEFAULT 10,
  max_projects_per_user INTEGER DEFAULT 5,
  allowed_domains TEXT[] DEFAULT ARRAY[]::TEXT[],
  build_timeout_minutes INTEGER DEFAULT 30,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_builds_user_id ON builds(user_id);
CREATE INDEX IF NOT EXISTS idx_builds_project_id ON builds(project_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_user_id ON system_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at DESC);
```

4. Activez Row Level Security (RLS) sur les tables :

```sql
-- Activer RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE builds ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform_config ENABLE ROW LEVEL SECURITY;

-- Politiques pour users
CREATE POLICY "Users can view own profile" ON users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
  FOR UPDATE USING (auth.uid() = id);

-- Politiques pour projects
CREATE POLICY "Users can view own projects" ON projects
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own projects" ON projects
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own projects" ON projects
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own projects" ON projects
  FOR DELETE USING (auth.uid() = user_id);

-- Politiques pour builds
CREATE POLICY "Users can view own builds" ON builds
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own builds" ON builds
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Politiques pour api_keys
CREATE POLICY "Users can view own api keys" ON api_keys
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own api keys" ON api_keys
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own api keys" ON api_keys
  FOR DELETE USING (auth.uid() = user_id);
```

5. Lancez le serveur backend :

```bash
cd backend
uvicorn server:app --reload --port 8001
```

## Configuration Frontend

1. Créez un fichier `.env.local` dans le dossier `frontend/` :

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8001
NEXT_PUBLIC_SUPABASE_URL=https://votre-projet.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=votre_cle_anon
```

2. Installez les dépendances :

```bash
cd frontend
npm install
# ou
yarn install
```

3. Lancez le serveur de développement :

```bash
npm run dev
# ou
yarn dev
```

Le frontend sera accessible sur http://localhost:3000

## Configuration OAuth (Optionnel)

Pour activer la connexion GitHub :

1. Allez dans Authentication > Providers dans Supabase
2. Activez GitHub
3. Configurez les credentials GitHub OAuth
4. Ajoutez l'URL de callback : `http://localhost:3000/auth/callback`

## Première Utilisation

1. Créez un compte via l'interface d'inscription
2. Connectez-vous
3. Créez votre premier projet
4. Configurez les fonctionnalités natives
5. Lancez un build

## Dépannage

### Erreur "Invalid token"
- Vérifiez que les variables d'environnement Supabase sont correctes
- Vérifiez que les tables sont créées dans Supabase
- Vérifiez que RLS est configuré correctement

### Erreur CORS
- Vérifiez que le backend autorise les requêtes depuis le frontend
- Vérifiez que `NEXT_PUBLIC_BACKEND_URL` est correct

### Erreur de connexion à Supabase
- Vérifiez que `NEXT_PUBLIC_SUPABASE_URL` et `NEXT_PUBLIC_SUPABASE_ANON_KEY` sont corrects
- Vérifiez que votre projet Supabase est actif

## Support

Pour toute question, consultez la documentation dans `/docs` ou créez une issue sur le dépôt.

