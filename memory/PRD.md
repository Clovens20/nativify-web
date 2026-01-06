# NativiWeb Studio - Product Requirements Document

## Original Problem Statement
Construire NativiWeb Studio, une plateforme web pour:
- Soumettre une application web existante (URL)
- Configurer les fonctionnalités natives à activer
- Générer automatiquement des projets natifs Android/iOS (templates)
- Fournir un SDK JavaScript pour interagir avec les fonctionnalités natives
- Orchestrer la génération, la configuration et la documentation
- Préparer la publication sur App Store / Google Play

## User Personas
1. **Web Developer**: Veut convertir sa web app en app native sans apprendre Swift/Kotlin
2. **Startup Founder**: Besoin de publier rapidement sur les stores avec budget limité
3. **Agency Developer**: Doit livrer des apps natives pour clients à partir de web apps

## Core Requirements (Static)
- [ ] Authentification utilisateur (email + futur OAuth)
- [x] Gestion de projets (CRUD)
- [x] Configuration des fonctionnalités natives (12 features)
- [x] Génération de templates Android (Kotlin/Gradle)
- [x] Génération de templates iOS (Swift/SwiftUI)
- [x] SDK JavaScript personnalisé
- [x] Gestion des builds
- [x] Gestion des clés API
- [x] Documentation intégrée

## What's Been Implemented (December 2024)

### Backend (FastAPI + MongoDB)
- Auth endpoints: register, login, logout, me
- Projects CRUD with native features configuration
- Builds management with background processing simulation
- API Keys management
- Template generators (Android/iOS)
- SDK JavaScript generator
- Stats endpoint
- Health check

### Frontend (React + Tailwind CSS)
- Landing page avec hero section
- Auth pages (Login, Register)
- Dashboard avec stats
- Projects list + detail + create wizard
- Native features configuration (toggles)
- Builds page avec progress tracking
- API Keys management
- Documentation (SDK, API, Getting Started)
- Settings page

### Design
- Neon Tech theme (sombre avec accents cyan/violet)
- Glassmorphism effects
- Custom fonts (Outfit, Manrope, JetBrains Mono)
- Responsive layout

## Prioritized Backlog

### P0 (Critical - Done)
- [x] Basic auth flow
- [x] Project management
- [x] Feature configuration
- [x] Build generation
- [x] SDK download

### P1 (High Priority - Pending)
- [ ] Supabase Auth integration (OAuth GitHub)
- [ ] Real build pipeline (CI/CD)
- [ ] Email notifications
- [ ] Improved error handling

### P2 (Medium Priority)
- [ ] Template customization options
- [ ] Multiple SDK versions
- [ ] Build analytics
- [ ] Team collaboration

### P3 (Nice to Have)
- [ ] Template marketplace
- [ ] Custom plugins
- [ ] White-label option

## Next Tasks
1. Intégrer Supabase Auth avec GitHub OAuth
2. Ajouter validation plus stricte des URLs
3. Améliorer les templates générés
4. Ajouter des tests unitaires

---
Last Updated: December 2024
