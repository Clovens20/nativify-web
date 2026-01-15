# 🚀 Guide de Déploiement en Production - NativiWeb Studio

Ce guide vous accompagne dans le déploiement de NativiWeb Studio en production.

## 📋 Prérequis

- **Docker** et **Docker Compose** installés
- **Domaine** configuré avec DNS pointant vers votre serveur
- **Certificat SSL** (Let's Encrypt recommandé)
- **Serveur** avec au moins 2GB RAM et 2 CPU cores
- **Compte Supabase** avec projet configuré

## 🔧 Configuration

### 1. Variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
# Frontend
NEXT_PUBLIC_SUPABASE_URL=https://votre-projet.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=votre_cle_anon
NEXT_PUBLIC_BACKEND_URL=https://api.votre-domaine.com
NEXT_PUBLIC_APP_URL=https://votre-domaine.com
NODE_ENV=production

# Backend
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_ANON_KEY=votre_cle_anon
SUPABASE_SERVICE_ROLE_KEY=votre_service_role_key
PORT=8000
HOST=0.0.0.0
ENVIRONMENT=production
ALLOWED_ORIGINS=https://votre-domaine.com,https://www.votre-domaine.com
LOG_LEVEL=INFO
```

### 2. Configuration Supabase

Assurez-vous que :
- ✅ RLS (Row Level Security) est activé sur toutes les tables
- ✅ Les politiques de sécurité sont correctement configurées
- ✅ Le bucket `project-logos` existe dans Storage
- ✅ La configuration de la plateforme (`platform_config`) est initialisée

### 3. Configuration du Reverse Proxy (Nginx)

Créez un fichier `/etc/nginx/sites-available/nativiweb` :

```nginx
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com www.votre-domaine.com;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
```

Activez la configuration :
```bash
sudo ln -s /etc/nginx/sites-available/nativiweb /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🐳 Déploiement avec Docker

### 1. Build des images

```bash
docker-compose build
```

### 2. Démarrer les services

```bash
docker-compose up -d
```

### 3. Vérifier les logs

```bash
docker-compose logs -f
```

### 4. Vérifier la santé des services

```bash
npm run healthcheck
```

## 📊 Monitoring

### Health Checks

- **Backend** : `https://api.votre-domaine.com/health`
- **Frontend** : `https://votre-domaine.com`

### Logs

```bash
# Logs en temps réel
docker-compose logs -f

# Logs backend uniquement
docker-compose logs -f backend

# Logs frontend uniquement
docker-compose logs -f frontend
```

## 🔄 Mise à jour

```bash
# Pull les dernières modifications
git pull

# Rebuild et redémarrer
docker-compose build
docker-compose up -d

# Nettoyer les anciennes images
docker image prune -f
```

## 🛡️ Sécurité

### Checklist de sécurité

- [ ] Variables d'environnement sécurisées (jamais commitées)
- [ ] Certificat SSL valide et auto-renouvelé
- [ ] Rate limiting activé sur l'API
- [ ] CORS strictement configuré
- [ ] Headers de sécurité configurés
- [ ] Backups automatiques de la base de données
- [ ] Monitoring des erreurs (Sentry recommandé)
- [ ] Logs d'accès configurés

### Rate Limiting

Le backend utilise `slowapi` pour limiter les requêtes :
- **Register** : 10 requêtes/minute
- **Login** : 5 requêtes/minute
- Autres endpoints : limites par défaut

### Backup

Configurez des backups automatiques de Supabase :
1. Allez dans votre dashboard Supabase
2. Configuration > Database > Backups
3. Activez les backups quotidiens

## 🔍 Dépannage

### Services ne démarrent pas

```bash
# Vérifier les logs
docker-compose logs

# Vérifier les conteneurs
docker-compose ps

# Redémarrer un service spécifique
docker-compose restart backend
```

### Erreurs de connexion à Supabase

1. Vérifiez les variables d'environnement
2. Vérifiez que les clés API sont correctes
3. Vérifiez que RLS est bien configuré

### Problèmes de performance

1. Augmentez le nombre de workers backend dans `docker-compose.yml`
2. Configurez un cache Redis
3. Utilisez un CDN pour les assets statiques

## 📞 Support

Pour toute question ou problème :
1. Consultez les logs : `docker-compose logs`
2. Vérifiez le health check : `npm run healthcheck`
3. Consultez la documentation : `docs/`

## 🎯 Prochaines étapes

- [ ] Configurer un monitoring complet (Prometheus + Grafana)
- [ ] Mettre en place des alertes (Email, Slack)
- [ ] Configurer un CDN (Cloudflare, AWS CloudFront)
- [ ] Ajouter des tests automatisés
- [ ] Configurer CI/CD (GitHub Actions, GitLab CI)

