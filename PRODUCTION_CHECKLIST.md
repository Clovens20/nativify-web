# ✅ Checklist de Préparation Production

Utilisez cette checklist pour vous assurer que tout est prêt avant le déploiement.

## 🔐 Sécurité

- [ ] **Variables d'environnement**
  - [ ] Toutes les variables sont définies dans `.env` (ne jamais commiter `.env`)
  - [ ] `SUPABASE_SERVICE_ROLE_KEY` est configuré et sécurisé
  - [ ] `NEXT_PUBLIC_*` variables sont correctes pour la production
  - [ ] Les secrets sont stockés de manière sécurisée (pas dans le code)

- [ ] **Authentification & Autorisation**
  - [ ] JWT validation fonctionne correctement
  - [ ] RLS (Row Level Security) est activé sur toutes les tables Supabase
  - [ ] Les politiques RLS sont testées et fonctionnent
  - [ ] Le rate limiting est activé sur les endpoints sensibles

- [ ] **HTTPS & SSL**
  - [ ] Certificat SSL valide configuré
  - [ ] Redirection HTTP → HTTPS activée
  - [ ] HSTS header configuré

- [ ] **Headers de Sécurité**
  - [ ] X-Frame-Options: DENY
  - [ ] X-Content-Type-Options: nosniff
  - [ ] X-XSS-Protection activé
  - [ ] Content-Security-Policy configuré
  - [ ] Strict-Transport-Security activé

- [ ] **CORS**
  - [ ] CORS strictement configuré avec les domaines de production uniquement
  - [ ] Pas de wildcard `*` en production

## 🔧 Configuration

- [ ] **Backend**
  - [ ] `ENVIRONMENT=production` dans `.env`
  - [ ] `ALLOWED_ORIGINS` contient uniquement les domaines de production
  - [ ] `LOG_LEVEL=INFO` ou `WARNING` (pas DEBUG)
  - [ ] Rate limiting configuré
  - [ ] Health check endpoint fonctionne (`/health`)

- [ ] **Frontend**
  - [ ] `NODE_ENV=production`
  - [ ] `NEXT_PUBLIC_BACKEND_URL` pointe vers l'API de production
  - [ ] `NEXT_PUBLIC_APP_URL` est le domaine de production
  - [ ] Build Next.js réussi sans erreurs

- [ ] **Database**
  - [ ] Tables créées et migrations appliquées
  - [ ] Index créés pour les performances
  - [ ] RLS activé sur toutes les tables
  - [ ] Backups automatiques configurés

- [ ] **Supabase Storage**
  - [ ] Bucket `project-logos` existe
  - [ ] Permissions configurées correctement
  - [ ] Policies RLS activées

## 🐳 Docker & Infrastructure

- [ ] **Docker**
  - [ ] Images Docker construites avec succès
  - [ ] `docker-compose.yml` configuré pour la production
  - [ ] Variables d'environnement passées aux conteneurs
  - [ ] Health checks fonctionnent

- [ ] **Reverse Proxy (Nginx)**
  - [ ] Configuration Nginx créée
  - [ ] SSL/TLS configuré
  - [ ] Redirection HTTP → HTTPS
  - [ ] Proxy vers backend et frontend configuré
  - [ ] Headers de sécurité ajoutés

- [ ] **Monitoring**
  - [ ] Health checks configurés
  - [ ] Logs centralisés (optionnel mais recommandé)
  - [ ] Alertes configurées (optionnel)

## 📊 Performance

- [ ] **Optimisations**
  - [ ] Compression gzip activée
  - [ ] Images optimisées
  - [ ] Cache configuré (si applicable)
  - [ ] CDN configuré (optionnel)

- [ ] **Tests**
  - [ ] Tests de charge effectués
  - [ ] Temps de réponse acceptables (< 2s)
  - [ ] Pas de fuites mémoire

## 📝 Documentation

- [ ] **Documentation utilisateur**
  - [ ] README.md à jour
  - [ ] Guide de déploiement créé
  - [ ] Documentation API complète

- [ ] **Documentation technique**
  - [ ] Architecture documentée
  - [ ] Procédures de déploiement documentées
  - [ ] Procédures de rollback documentées

## 🧪 Tests

- [ ] **Fonctionnalités**
  - [ ] Authentification fonctionne
  - [ ] Création de projet fonctionne
  - [ ] Upload de logo fonctionne
  - [ ] Build de projet fonctionne
  - [ ] Téléchargement d'APK/IPA fonctionne
  - [ ] Interface admin fonctionne

- [ ] **Sécurité**
  - [ ] Tests d'injection SQL (si applicable)
  - [ ] Tests XSS
  - [ ] Tests CSRF
  - [ ] Tests d'autorisation

## 🚀 Déploiement

- [ ] **Pré-déploiement**
  - [ ] Backup de la base de données effectué
  - [ ] Variables d'environnement vérifiées
  - [ ] DNS configuré et propagé
  - [ ] Certificat SSL obtenu

- [ ] **Déploiement**
  - [ ] Build des images Docker réussis
  - [ ] Services démarrés avec succès
  - [ ] Health checks passent
  - [ ] Pas d'erreurs dans les logs

- [ ] **Post-déploiement**
  - [ ] Application accessible via HTTPS
  - [ ] Toutes les fonctionnalités testées
  - [ ] Performance vérifiée
  - [ ] Monitoring actif

## 📞 Support

- [ ] **Plan de support**
  - [ ] Procédure de monitoring en place
  - [ ] Contacts d'urgence définis
  - [ ] Procédure de rollback testée
  - [ ] Documentation d'incident créée

## ⚠️ Points d'Attention

1. **Ne jamais commiter** :
   - Fichiers `.env`
   - Secrets et clés API
   - Certificats SSL

2. **Vérifier avant chaque déploiement** :
   - Variables d'environnement
   - Configuration CORS
   - Certificat SSL valide
   - Backups récents

3. **Après déploiement** :
   - Vérifier les logs pendant 24h
   - Monitorer les erreurs
   - Vérifier les performances
   - Tester toutes les fonctionnalités critiques

## 🎯 Commandes de Vérification

```bash
# Vérifier la santé des services
npm run healthcheck

# Vérifier les logs
docker-compose logs -f

# Vérifier les conteneurs
docker-compose ps

# Build pour production
npm run build
docker-compose build

# Déployer
docker-compose up -d
```

