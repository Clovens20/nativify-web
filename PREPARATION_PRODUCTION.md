# 🚀 Préparation pour la Production

## ✅ Améliorations Implémentées

### 1. Tests Automatisés ✅

#### Backend (pytest)
- ✅ Configuration pytest (`pytest.ini`)
- ✅ Fixtures communes (`tests/conftest.py`)
- ✅ Tests unitaires :
  - `tests/unit/test_auth.py` - Authentification et JWT
  - `tests/unit/test_validation.py` - Validation des inputs
- ✅ Tests d'intégration :
  - `tests/integration/test_api_endpoints.py` - Endpoints API

**Commandes** :
```bash
# Tous les tests
npm run test:backend

# Tests unitaires uniquement
npm run test:backend:unit

# Tests d'intégration uniquement
npm run test:backend:integration
```

### 2. Monitoring d'Erreurs (Sentry) ✅

- ✅ Configuration Sentry pour production
- ✅ Intégration FastAPI
- ✅ Tracking des erreurs et performance
- ✅ Configuration via variable `SENTRY_DSN`

**Configuration** :
```env
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
RELEASE_VERSION=1.0.0
```

### 3. Logging Structuré ✅

#### Backend
- ✅ Logging JSON pour production
- ✅ Format texte pour développement
- ✅ Niveaux de log configurables
- ✅ Logging structuré avec `python-json-logger`

#### Frontend
- ✅ Logger structuré (`src/lib/logger.ts`)
- ✅ Remplacement de `console.log/error` par logger
- ✅ Support JSON en production
- ✅ Context logging pour debugging

**Variables d'environnement** :
```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json  # json ou text
```

### 4. Rate Limiting ✅

- ✅ Activé par défaut en production
- ✅ Configurable via variables d'environnement
- ✅ Limite par défaut : 100 req/min par IP
- ✅ Désactivable via `RATE_LIMIT_ENABLED=false`

**Configuration** :
```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
```

### 5. Validation des Variables d'Environnement ✅

- ✅ Validation au démarrage
- ✅ Messages d'erreur clairs
- ✅ Blocage en production si variables manquantes
- ✅ Avertissements en développement

**Variables requises** :
- Production : `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- Développement : `SUPABASE_URL`, `SUPABASE_ANON_KEY`

## 📋 Checklist de Déploiement

### Avant le Déploiement

- [ ] **Variables d'environnement** : Configurer toutes les variables dans `.env`
- [ ] **Sentry** : Créer un projet Sentry et configurer `SENTRY_DSN`
- [ ] **Tests** : Exécuter tous les tests (`npm run test`)
- [ ] **Build** : Vérifier que le build fonctionne (`npm run build`)
- [ ] **Supabase** : Vérifier que RLS est activé sur toutes les tables
- [ ] **Rate Limiting** : Vérifier les limites selon votre trafic attendu

### Configuration Production

1. **Créer `.env` à partir de `.env.example`** :
```bash
cp backend/.env.example backend/.env
# Éditer backend/.env avec vos valeurs
```

2. **Variables obligatoires** :
```env
ENVIRONMENT=production
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
ALLOWED_ORIGINS=https://your-domain.com
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

3. **Variables optionnelles** (avec valeurs par défaut) :
```env
PORT=8000
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Déploiement

1. **Build** :
```bash
npm run build
```

2. **Lancer en production** :
```bash
npm run start:production
```

Ou avec Docker :
```bash
docker-compose up -d
```

### Monitoring Post-Déploiement

1. **Vérifier les logs** :
```bash
# Logs Docker
docker-compose logs -f

# Logs système
tail -f /var/log/nativiweb/app.log
```

2. **Vérifier Sentry** :
   - Se connecter à votre dashboard Sentry
   - Vérifier que les erreurs sont capturées
   - Configurer des alertes pour erreurs critiques

3. **Vérifier les health checks** :
```bash
curl https://api.your-domain.com/api/health
```

## 🔍 Tests de Validation

### Tests Automatisés
```bash
# Backend
npm run test:backend

# Vérifier la couverture (optionnel)
cd backend && pytest --cov=. --cov-report=html
```

### Tests Manuels

1. **Health Check** :
```bash
curl http://localhost:8000/api/health
```

2. **Rate Limiting** :
```bash
# Faire 101 requêtes rapidement
for i in {1..101}; do curl http://localhost:8000/api/health; done
# La 101ème devrait retourner 429
```

3. **Authentification** :
   - Tester login/logout
   - Vérifier que les tokens JWT sont valides
   - Tester l'accès aux ressources protégées

## 📊 Métriques à Surveiller

- **Taux d'erreur** : < 1%
- **Temps de réponse** : < 500ms (p95)
- **Rate limiting** : Nombre de 429 retournés
- **Erreurs Sentry** : Trier par criticité

## 🐛 Troubleshooting

### Erreur "Missing required environment variables"
- Vérifier que toutes les variables sont définies dans `.env`
- Vérifier que `.env` est chargé correctement

### Rate limiting trop restrictif
- Augmenter `RATE_LIMIT_PER_MINUTE` dans `.env`
- Ou désactiver temporairement avec `RATE_LIMIT_ENABLED=false`

### Sentry ne capture pas les erreurs
- Vérifier que `SENTRY_DSN` est correct
- Vérifier que `sentry-sdk` est installé : `pip install sentry-sdk[fastapi]`
- Vérifier les logs pour voir si Sentry s'initialise

### Logs non structurés
- Vérifier que `LOG_FORMAT=json` est défini
- Vérifier que `python-json-logger` est installé

## 📚 Documentation

- [Tests](./tests/README.md) - Guide des tests
- [Déploiement](./DEPLOIEMENT.md) - Guide de déploiement
- [Audit Stabilité](./AUDIT_STABILITE_PRODUCTION.md) - Audit complet

---

*Dernière mise à jour : 2026-01-07*

