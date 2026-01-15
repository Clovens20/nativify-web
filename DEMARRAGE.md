# 🚀 Guide de Démarrage - NativiWeb Studio

## ✨ Démarrage Simplifié (Recommandé)

**Un seul terminal suffit maintenant !** 🎉

```bash
npm run dev
```

Cette commande démarre automatiquement :
- ✅ **Frontend** (Next.js) sur http://localhost:3000
- ✅ **Backend** (FastAPI) sur http://localhost:8000

Les logs sont colorés et préfixés pour faciliter la distinction :
- `[frontend]` en cyan pour Next.js
- `[backend]` en magenta pour FastAPI

---

## 🔧 Étape 0 : Installation des Prérequis (IMPORTANT !)

### ⚠️ Avant de démarrer, vous devez installer les dépendances :

**1. Installer les dépendances Node.js :**
```bash
npm install
```

**2. Installer les dépendances Python (Backend) :**

**Option A - Installation globale (simple mais moins recommandé) :**
```powershell
pip install -r backend/requirements.txt
```

**Option B - Avec environnement virtuel (recommandé) :**
```powershell
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Installer les dépendances
pip install -r backend/requirements.txt
```

> 💡 **Note Windows** : Si vous obtenez une erreur lors de l'activation du venv, exécutez cette commande dans PowerShell (en tant qu'administrateur) :
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

**3. Vérifier l'installation :**
```powershell
uvicorn --version
```
Vous devriez voir une version (ex: `uvicorn 0.25.0`)

---

## 📋 Prerequisites

Avant de commencer avec NativiWeb Studio, assurez-vous que votre environnement répond aux exigences suivantes :

### 📱 Versions de Plateforme Minimales

**Android :**
- **API Level minimum** : Android 5.0 (API Level 21) / Lollipop
- **API Level recommandé** : Android 8.0 (API Level 26) / Oreo ou supérieur
- **Gradle** : Version 7.0+ (inclus dans le projet généré)
- **Kotlin** : Version 1.7.0+ (inclus dans le projet généré)

**iOS :**
- **Version iOS minimum** : iOS 13.0
- **Version iOS recommandée** : iOS 15.0 ou supérieur
- **Xcode** : Version 14.0+ (requis pour compiler les projets générés)
- **Swift** : Version 5.5+ (inclus dans le projet généré)

### 🖥️ Navigateurs Compatibles (pour le développement)

L'interface NativiWeb Studio est compatible avec :
- ✅ **Chrome** : Version 90+
- ✅ **Firefox** : Version 88+
- ✅ **Safari** : Version 14+
- ✅ **Edge** : Version 90+
- ⚠️ **Note** : L'interface nécessite JavaScript activé

### 💻 Node.js et npm

**Versions requises :**
- **Node.js** : Version 18.0.0 ou supérieure (LTS recommandé)
- **npm** : Version 9.0.0 ou supérieure (inclus avec Node.js)

**Vérification :**
```bash
node --version  # Doit afficher v18.x.x ou supérieur
npm --version   # Doit afficher 9.x.x ou supérieur
```

**Installation :**
- Téléchargez Node.js depuis https://nodejs.org/
- Ou utilisez un gestionnaire de versions : `nvm` (Linux/Mac) ou `nvm-windows`

### 🐍 Python

**Versions requises :**
- **Python** : Version 3.9.0 ou supérieure (3.11+ recommandé)

**Vérification :**
```bash
python --version  # Doit afficher Python 3.9.x ou supérieur
```

**Installation :**
- Windows : https://www.python.org/downloads/
- macOS : `brew install python@3.11`
- Linux : Utilisez votre gestionnaire de paquets (`apt`, `yum`, etc.)

### 🔐 Comptes Développeur

**Apple Developer Account :**
- **Requis pour** : Publication sur l'App Store, utilisation de fonctionnalités natives iOS
- **Coût** : 99$/an (individuel) ou 299$/an (entreprise)
- **Inscription** : https://developer.apple.com/programs/
- ⚠️ **Important** : Nécessaire uniquement pour la compilation et la publication finale

**Google Play Console :**
- **Requis pour** : Publication sur Google Play Store
- **Coût** : 25$ (paiement unique, à vie)
- **Inscription** : https://play.google.com/console/
- ⚠️ **Important** : Nécessaire uniquement pour la publication finale

> 💡 **Note** : Les comptes développeur ne sont pas requis pour le développement local ni pour générer les projets. Ils sont nécessaires uniquement lors de la compilation finale et de la soumission aux stores.

### 📦 Outils Supplémentaires (Optionnels mais Recommandés)

**Git :**
- Version 2.30+ recommandée
- Installation : https://git-scm.com/downloads

**Code Editor :**
- **VS Code** : Recommandé (avec extensions TypeScript, Python)
- **WebStorm** : Alternative pour développement JavaScript/TypeScript
- **PyCharm** : Alternative pour développement Python

---

## 📋 Étape 1 : Configuration des variables d'environnement

### Frontend (`.env.local` à la racine)
Le fichier existe déjà avec :
```env
NEXT_PUBLIC_SUPABASE_URL=https://nrjadlmluharqvlqymtp.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### Backend (`backend/.env`)
Créez ce fichier si il n'existe pas :
```env
SUPABASE_URL=https://nrjadlmluharqvlqymtp.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5yamFkbG1sdWhhcnF2bHF5bXRwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc2NzM2OTYsImV4cCI6MjA4MzI0OTY5Nn0.F68c5SETbif9HWdNMRBbXa5tEvXVegrbdob5fFjLo38
SUPABASE_SERVICE_ROLE_KEY=votre_service_role_key_ici
```

> ⚠️ **Important** : Pour que l'inscription et les autres fonctionnalités fonctionnent correctement, vous devez ajouter la **clé SERVICE_ROLE** de Supabase dans le fichier `.env`.
> 
> 1. Allez sur votre projet Supabase : https://supabase.com/dashboard
> 2. Sélectionnez votre projet
> 3. Allez dans **Settings** → **API**
> 4. Copiez la clé **service_role** (⚠️ **Gardez-la secrète, ne la partagez jamais !**)
> 5. Ajoutez-la dans `backend/.env` comme `SUPABASE_SERVICE_ROLE_KEY=votre_cle`

---

## 🖥️ Étape 2 : Démarrer l'Application (Méthode Unifiée)

**Dans un seul terminal**, exécutez :

```bash
npm run dev
```

Vous verrez les deux serveurs démarrer en même temps :
```
[frontend] ▲ Next.js 14.2.35
[frontend] - Local:        http://localhost:3000
[frontend] ✓ Ready in 1376ms

[backend] INFO:     Uvicorn running on http://127.0.0.1:8000
[backend] INFO:     Started reloader process
[backend] INFO:     Application startup complete.
```

✅ **C'est tout !** Les deux serveurs tournent dans le même terminal.

---

## 🔧 Méthode Alternative : Démarrage Séparé

Si vous préférez démarrer les serveurs séparément (2 terminaux) :

**Terminal 1 - Frontend :**
```bash
npm run dev:frontend
```

**Terminal 2 - Backend :**
```bash
npm run dev:backend
```

---

## ✅ Vérification

1. **Backend** : Ouvrez http://localhost:8000/api/health dans votre navigateur
   - Vous devriez voir : `{"status":"healthy","timestamp":"..."}`

2. **Frontend** : Ouvrez http://localhost:3000
   - La page d'accueil devrait s'afficher

3. **Test d'inscription** : Allez sur http://localhost:3000/register
   - L'erreur "Cannot connect to server" devrait disparaître
   - Vous pouvez maintenant créer un compte

---

## 🔧 Dépannage

### Erreur "Cannot connect to server"
- ✅ Vérifiez que le backend est démarré (Terminal 2)
- ✅ Vérifiez que vous voyez "Uvicorn running on http://127.0.0.1:8000"
- ✅ Testez http://localhost:8000/api/health dans votre navigateur

### Erreur "uvicorn n'est pas reconnu" ou "'uvicorn' n'est pas reconnu"
Cela signifie que `uvicorn` n'est pas dans le PATH de votre terminal.

**Solution 1 : Utiliser `python -m uvicorn` (Recommandé)**
Le fichier `package.json` a été configuré pour utiliser `python -m uvicorn` automatiquement. Si vous rencontrez encore l'erreur :

**Vérification :**
```powershell
python -m uvicorn --version
```

**Solution 2 : Installer les dépendances Python**
Si les dépendances ne sont pas installées :
```powershell
# Depuis la racine du projet
pip install -r backend/requirements.txt

# Ou si vous utilisez un environnement virtuel
.\venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

**Solution 3 : Ajouter les scripts Python au PATH (Optionnel)**
Si vous voulez utiliser `uvicorn` directement, ajoutez le répertoire des scripts Python au PATH :
```powershell
# Trouver le répertoire des scripts (remplacez python313 par votre version)
$pythonScripts = "$env:APPDATA\Python\Python313\Scripts"
# Ajouter au PATH pour cette session
$env:Path += ";$pythonScripts"
```

### Erreur "Module not found" dans le backend
```powershell
pip install -r backend/requirements.txt
```

### Erreur "spawn taskkill ENOENT" (Windows)
Cette erreur peut survenir si `taskkill` n'est pas dans le PATH. Elle est généralement résolue après l'installation des dépendances Python. Si elle persiste :
- Redémarrez PowerShell en tant qu'administrateur
- Vérifiez que Python est bien installé : `python --version`

### Erreur "403 Forbidden" ou "406 Not Acceptable" lors de l'inscription/connexion
Ces erreurs indiquent des problèmes avec les politiques RLS (Row Level Security) de Supabase.

**Solutions :**

1. **Ajoutez la clé SERVICE_ROLE dans `backend/.env`** :
   ```env
   SUPABASE_SERVICE_ROLE_KEY=votre_service_role_key
   ```
   ⚠️ **Important** : La clé SERVICE_ROLE contourne toutes les politiques RLS. Ne l'exposez jamais au frontend !

2. **Vérifiez les politiques RLS dans Supabase** :
   - Allez dans votre projet Supabase → **Authentication** → **Policies**
   - Assurez-vous que les tables `users` et `system_logs` ont les bonnes politiques
   - Pour le développement, vous pouvez temporairement désactiver RLS sur certaines tables

3. **Vérifiez que les tables existent** :
   - Dans Supabase, vérifiez que les tables `users`, `projects`, `builds`, `system_logs` existent
   - Si elles n'existent pas, créez-les avec les bonnes colonnes

### Le port 8000 est déjà utilisé
Changez le port dans `package.json` :
```json
"dev:backend": "uvicorn main:app --reload --app-dir backend --port 8001"
```
Et mettez à jour `.env.local` :
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8001
```

---

## 📝 Résumé

### ✅ Méthode Recommandée (Un seul terminal)
```bash
npm run dev
```
→ Démarre automatiquement frontend + backend

### 🔧 Méthode Alternative (2 terminaux)
| Terminal | Commande | URL |
|----------|----------|-----|
| Terminal 1 | `npm run dev:frontend` | http://localhost:3000 |
| Terminal 2 | `npm run dev:backend` | http://localhost:8000 |

---

## 🚀 En Production

En production, vous pouvez :
- **Option 1** : Déployer sur un seul domaine avec reverse proxy (Nginx)
  - Frontend : `https://votre-site.com`
  - Backend : `https://votre-site.com/api` (proxifié vers FastAPI)
  
- **Option 2** : Déployer séparément
  - Frontend : Vercel/Netlify (`https://app.votre-site.com`)
  - Backend : Railway/Render (`https://api.votre-site.com`)

- **Option 3** : Migrer le backend vers Next.js API Routes
  - Tout dans Next.js, un seul déploiement

