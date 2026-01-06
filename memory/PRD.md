# NativiWeb Studio - PRD (Product Requirements Document)

## 📋 Overview
NativiWeb Studio est une plateforme web permettant aux utilisateurs de transformer leurs applications web en applications natives Android/iOS. La plateforme génère des templates de projets natifs et un SDK JavaScript pour la communication entre la web app et les fonctionnalités natives.

## 🎯 Objectif Principal
Créer une plateforme crédible et bien architecturée pour un concours, démontrant une solution complète de conversion web-to-native.

---

## 🔧 Stack Technique

| Composant | Technologie | Status |
|-----------|------------|--------|
| Frontend | **Next.js 14 + TypeScript** | ✅ Implémenté |
| Backend | **FastAPI (Python)** | ✅ Implémenté |
| Base de données | **Supabase (PostgreSQL)** | ✅ Intégré |
| Authentication | **Supabase Auth (Email + GitHub OAuth)** | ✅ Configuré |
| Package Manager | **npm** (strictement pas Yarn) | ✅ Vérifié |
| Styling | TailwindCSS + ShadCN UI | ✅ Implémenté |

---

## 📦 Fonctionnalités Implémentées

### 1. Landing Page
- [x] Hero section avec animation "Neon Tech"
- [x] Présentation des fonctionnalités natives
- [x] Section "How it works" (4 étapes)
- [x] Navigation (Login, Register)
- [x] Design responsive

### 2. Authentification
- [x] Page de connexion (email/password)
- [x] Page d'inscription
- [x] Bouton GitHub OAuth
- [x] Context d'authentification avec Supabase
- [x] Callback OAuth (`/auth/callback`)

### 3. Dashboard Utilisateur
- [x] Vue d'ensemble des statistiques
- [x] Actions rapides (nouveau projet, docs, API keys)
- [x] Projets récents
- [x] Builds récents
- [x] Sidebar avec navigation

### 4. Gestion des Projets
- [x] Liste des projets
- [x] Création de projet (nom, URL, description, plateformes)
- [x] Détail de projet avec onglets
- [x] Configuration des features natives
- [x] Suppression de projet

### 5. Système de Build (SIMULÉ)
- [x] Démarrage de build Android/iOS
- [x] Progress bar avec phases
- [x] Génération d'artéfacts de test (non fonctionnels)
- [x] Historique des builds
- [x] Téléchargement des artéfacts

### 6. API Keys
- [x] Création de clés API
- [x] Liste avec masquage/affichage
- [x] Copie dans le presse-papiers
- [x] Suppression

### 7. Documentation
- [x] Quick Start guide
- [x] SDK Reference
- [x] API Reference

### 8. Settings
- [x] Affichage des informations de profil
- [x] Actions du compte (déconnexion, suppression)

### 9. Panel Admin
- [x] Analytics (utilisateurs, projets, builds)
- [x] Gestion des utilisateurs (ban/unban)
- [x] Historique des builds
- [x] Logs système

---

## 🗄️ Structure des Tables Supabase

```sql
-- Users (géré par Supabase Auth)
users: id, email, name, role, status, created_at

-- Projects
projects: id, user_id, name, web_url, description, platform[], features[], status, created_at

-- Builds
builds: id, project_id, user_id, platform, build_type, status, phase, progress, logs[], artifacts[], created_at, completed_at

-- API Keys
api_keys: id, user_id, name, key, permissions[], last_used, created_at

-- System Logs
system_logs: id, level, category, message, created_at
```

---

## 📁 Structure du Projet

```
/app/
├── backend/
│   ├── server.py         # FastAPI + Supabase
│   ├── requirements.txt
│   └── .env              # Supabase credentials
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js App Router
│   │   │   ├── page.tsx          # Landing
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   ├── dashboard/
│   │   │   ├── projects/
│   │   │   ├── builds/
│   │   │   ├── api-keys/
│   │   │   ├── docs/
│   │   │   ├── settings/
│   │   │   ├── admin/
│   │   │   └── auth/callback/
│   │   ├── components/
│   │   │   ├── ui/       # ShadCN components
│   │   │   └── layout/   # Sidebar, DashboardLayout
│   │   ├── context/      # AuthContext
│   │   └── lib/          # API, utils, supabase
│   ├── package.json
│   └── .env
├── docs/
│   ├── API.md
│   ├── SDK.md
│   ├── ARCHITECTURE.md
│   └── ci-cd/
└── test_reports/
```

---

## ⚠️ Points Importants

### Build Simulation
Le système de build est **SIMULÉ** pour le concours. Il génère des artéfacts de test (fichiers JSON) mais ne compile pas réellement d'applications natives.

### GitHub OAuth
Pour que le flux GitHub OAuth fonctionne, il faut configurer le provider GitHub dans le dashboard Supabase avec les clés OAuth de l'application.

### Tables Supabase
Les tables doivent être créées dans Supabase pour que l'application fonctionne complètement. Le backend gère les erreurs gracieusement si les tables n'existent pas.

---

## 🔮 Backlog / Tâches Futures

### P1 - Priorité Haute
- [ ] Créer les tables Supabase via migrations SQL
- [ ] Configurer GitHub OAuth dans Supabase Dashboard
- [ ] Tester le flux complet d'authentification

### P2 - Priorité Moyenne
- [ ] Ajouter des notifications temps réel pour les builds
- [ ] Améliorer les logs de build avec plus de détails
- [ ] Pagination des listes

### P3 - Priorité Basse
- [ ] Mode sombre/clair toggle
- [ ] Export des données utilisateur
- [ ] Statistiques avancées dans le dashboard

---

## 📊 Tests

| Test | Status |
|------|--------|
| Backend API health | ✅ Pass |
| Backend API features | ✅ Pass |
| Auth validation | ✅ Pass |
| Landing page load | ✅ Pass |
| Login page load | ✅ Pass |
| Register page load | ✅ Pass |
| Next.js verification | ✅ Pass |
| npm verification | ✅ Pass |

**Success Rate: 100%**

---

## 📅 Historique

| Date | Action |
|------|--------|
| 2025-01-06 | Migration complète vers Next.js + npm + Supabase |
| 2025-01-06 | Tous les tests passés (iteration_3.json) |

---

## 👤 User's Language
Français
