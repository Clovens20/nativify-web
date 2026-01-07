# 🚀 Démarrage Rapide - NativiWeb Studio

## Installation Rapide

### 1. Installer les dépendances

```powershell
# Installer les dépendances frontend
cd frontend
npm install
cd ..

# Installer les dépendances backend (si pas déjà fait)
cd backend
pip install -r requirements.txt
cd ..
```

### 2. Configurer les variables d'environnement

**Backend** - Créez `backend/.env` :
```env
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_ANON_KEY=votre_cle_anon
PORT=8001
```

**Frontend** - Créez `frontend/.env.local` :
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8001
NEXT_PUBLIC_SUPABASE_URL=https://votre-projet.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=votre_cle_anon
```

### 3. Démarrer le projet

**Option A : Script PowerShell (Recommandé)**
```powershell
.\start-dev.ps1
```
Ce script ouvre automatiquement 2 terminaux (backend + frontend)

**Option B : Scripts séparés (2 terminaux)**

Terminal 1 - Backend :
```powershell
.\start-backend.ps1
```

Terminal 2 - Frontend :
```powershell
.\start-frontend.ps1
```

**Option C : Manuellement (2 terminaux)**

Terminal 1 - Backend :
```powershell
cd backend
python -m uvicorn server:app --reload --port 8001
```

Terminal 2 - Frontend :
```powershell
cd frontend
npm run dev
```

**Option D : Script npm (peut avoir des problèmes sur Windows)**
```powershell
npm run dev
```

## Accès

- **Frontend** : http://localhost:3000
- **Backend API** : http://localhost:8001
- **Documentation API** : http://localhost:8001/docs

## ⚠️ Important

Avant de démarrer, assurez-vous d'avoir :
1. ✅ Créé un projet Supabase
2. ✅ Créé les tables dans Supabase (voir `SETUP.md`)
3. ✅ Configuré les fichiers `.env` et `.env.local`

## Problèmes courants

### Erreur "Cannot find module"
```powershell
cd frontend
npm install
```

### Erreur "Module not found" (Python)
```powershell
cd backend
pip install -r requirements.txt
```

### Erreur de connexion Supabase
Vérifiez que vos variables d'environnement sont correctes dans `.env` et `.env.local`

