# NativiWeb Studio

> Transform your web applications into native Android & iOS apps without writing native code.

## 🚀 Overview

NativiWeb Studio is a comprehensive platform that enables developers to convert existing web applications into native mobile apps. Our platform generates native project templates and provides a JavaScript SDK for accessing device features.

## 🏗 Architecture

```
nativify-web/
├── src/                # Next.js 14 App Router (frontend)
│   ├── app/            # Pages et routes (App Router)
│   ├── components/      # Composants UI réutilisables
│   ├── context/        # React Context (Auth)
│   └── lib/            # Utilitaires (API, Supabase)
├── backend/            # FastAPI Python backend
│   ├── main.py         # Point d'entrée API
│   └── requirements.txt
├── docs/               # Documentation
└── tests/              # Tests Python
```

## ✨ Features

- **Project Management**: Create and manage multiple native app projects
- **Native Features Configuration**: Enable/disable device features (Camera, GPS, Push Notifications, etc.)
- **Template Generation**: Generate Android (Kotlin/Gradle) and iOS (Swift/SwiftUI) project templates
- **JavaScript SDK**: Seamless bridge between web app and native features
- **Build Management**: Track build history and download generated packages
- **API Keys**: Secure authentication for SDK integration
- **Documentation**: Comprehensive SDK and API documentation

## 🛠 Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Shadcn/UI
- **Backend**: FastAPI (Python), MongoDB (Motor async driver)
- **Authentication**: Supabase Auth
- **Styling**: Custom Neon Tech theme with cyan/violet accents

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- Supabase account (free tier works)
- **Java JDK 17+** (pour compiler des APKs - voir [Guide de Configuration](GUIDE_CONFIGURATION_JAVA_ANDROID.md))
- **Android SDK** (optionnel mais recommandé pour des builds plus rapides)

### Installation

1. **Installer les dépendances frontend**
```bash
npm install
```

2. **Installer les dépendances backend**
```bash
cd backend
pip install -r requirements.txt
cd ..
```

3. **Configuration des variables d'environnement**

⚠️ **IMPORTANT** : Vous devez créer un fichier `.env.local` à la racine du projet avant de lancer l'application.

Copiez le fichier `env.example` vers `.env.local` :
```bash
copy env.example .env.local
# ou sur Linux/Mac:
cp env.example .env.local
```

Puis éditez `.env.local` et remplacez les valeurs par vos propres credentials Supabase :
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

**Où trouver vos credentials Supabase ?**
1. Allez sur https://supabase.com/dashboard
2. Sélectionnez votre projet
3. Allez dans Settings > API
4. Copiez l'URL du projet et la clé `anon` `public`

Créer un fichier `backend/.env` pour le backend :
```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
MONGO_URL=mongodb://localhost:27017
DB_NAME=nativiweb_studio
```

### Running the Application

**✨ Méthode Simplifiée (Recommandée) - Un seul terminal :**
```bash
npm run dev
```
Cette commande démarre automatiquement :
- Frontend (Next.js) sur http://localhost:3000
- Backend (FastAPI) sur http://localhost:8000

Les logs sont préfixés avec `[frontend]` et `[backend]` pour faciliter la distinction.

**🔧 Méthode Alternative - Deux terminaux séparés :**
```bash
# Terminal 1 - Frontend
npm run dev:frontend

# Terminal 2 - Backend
npm run dev:backend
```

### Configuration pour Compiler des APKs

Pour activer la compilation automatique d'APKs Android, vous devez installer et configurer Java JDK 17+ :

**Méthode Rapide :**
```powershell
.\scripts\setup-java-android.ps1
```

**Vérification :**
```powershell
.\scripts\check-build-dependencies.ps1
```

📖 **Guide complet :** Voir [GUIDE_CONFIGURATION_JAVA_ANDROID.md](GUIDE_CONFIGURATION_JAVA_ANDROID.md)

## 📱 Supported Native Features

| Feature | Android | iOS |
|---------|---------|-----|
| Push Notifications | ✅ | ✅ |
| Camera | ✅ | ✅ |
| Geolocation (GPS) | ✅ | ✅ |
| Local Storage | ✅ | ✅ |
| Biometric Auth | ✅ | ✅ |
| Contacts | ✅ | ✅ |
| File System | ✅ | ✅ |
| Native Share | ✅ | ✅ |
| Haptic Feedback | ✅ | ✅ |
| Deep Links | ✅ | ✅ |
| App Badge | ✅ | ✅ |
| Clipboard | ✅ | ✅ |

## 📖 SDK Usage

```javascript
// Check if running in native app
if (NativiWeb.isNative) {
  // Get device info
  const info = await NativiWeb.getDeviceInfo();
  
  // Get user location
  const position = await NativiWeb.getCurrentPosition();
  
  // Show notification
  await NativiWeb.showNotification("Hello!", {
    body: "Welcome to NativiWeb"
  });
  
  // Haptic feedback
  await NativiWeb.vibrate(100);
}
```

## 🔑 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

### Projects
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `GET /api/projects/:id` - Get project
- `PUT /api/projects/:id` - Update project
- `DELETE /api/projects/:id` - Delete project

### Builds
- `GET /api/builds` - List builds
- `POST /api/builds` - Start build
- `GET /api/builds/:id` - Get build
- `GET /api/builds/:id/download` - Download build

### API Keys
- `GET /api/api-keys` - List API keys
- `POST /api/api-keys` - Create API key
- `DELETE /api/api-keys/:id` - Delete API key

## 📄 License

MIT License - See LICENSE file for details.

---

Built with ❤️ by NativiWeb Studio Team
