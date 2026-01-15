# NativiWeb Studio API Documentation

## Base URL

```
https://api.nativiweb.io/api
```

For local development:
```
http://localhost:8001/api
```

## Authentication

Tous les endpoints (sauf `/api/auth/register` et `/api/auth/login`) nécessitent une authentification via un token JWT.

### Méthode d'Authentification

Le token doit être fourni dans l'en-tête `Authorization` :

```http
Authorization: Bearer <votre_token_jwt>
```

**Exemple :**
```http
GET /api/projects
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### POST `/api/auth/register`

Inscrit un nouvel utilisateur.

**Signature TypeScript :**
```typescript
POST /api/auth/register
Content-Type: application/json

interface RegisterRequest {
  email: string;        // Email valide (format email)
  password: string;     // Minimum 8 caractères
  name: string;         // Nom complet (1-100 caractères)
}

interface RegisterResponse {
  id: string;           // UUID de l'utilisateur
  email: string;
  name: string;
  role: 'user' | 'admin'; // Rôle par défaut: 'user'
  created_at: string;   // ISO 8601 timestamp
}
```

**Paramètres :**
- **Corps de la requête** (JSON, obligatoire) :
  - `email` (string, obligatoire) : Adresse email valide
  - `password` (string, obligatoire) : Mot de passe (min. 8 caractères)
  - `name` (string, obligatoire) : Nom complet (1-100 caractères)

**Réponse en cas de succès (200 OK) :**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user",
  "created_at": "2024-01-15T10:30:00.000Z"
}
```

**Codes d'erreur :**
- `400 Bad Request` : Données invalides
  ```json
  {
    "detail": "Email already registered"
  }
  ```
- `422 Unprocessable Entity` : Validation échouée
  ```json
  {
    "detail": [
      {
        "loc": ["body", "email"],
        "msg": "value is not a valid email address",
        "type": "value_error.email"
      }
    ]
  }
  ```

**Exemple d'utilisation avec gestion d'erreurs :**
```javascript
async function registerUser(email, password, name) {
  try {
    const response = await fetch('https://api.nativiweb.io/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        password: password,
        name: name
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      
      if (response.status === 400 && error.detail.includes('already registered')) {
        throw new Error('Cet email est déjà utilisé');
      } else if (response.status === 422) {
        throw new Error('Données invalides: ' + JSON.stringify(error.detail));
      } else {
        throw new Error('Erreur lors de l\'inscription: ' + error.detail);
      }
    }
    
    const user = await response.json();
    console.log('Utilisateur créé:', user);
    return user;
    
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}

// Utilisation
try {
  const user = await registerUser(
    'john.doe@example.com',
    'SecurePassword123!',
    'John Doe'
  );
  console.log('Inscription réussie:', user.id);
} catch (error) {
  alert('Erreur: ' + error.message);
}
```

---

### POST `/api/auth/login`

Connecte un utilisateur et retourne un token JWT.

**Signature TypeScript :**
```typescript
POST /api/auth/login
Content-Type: application/json

interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  token: string;        // JWT token à utiliser pour les requêtes authentifiées
  user: {
    id: string;
    email: string;
    name: string;
    role: 'user' | 'admin';
  };
}
```

**Paramètres :**
- **Corps de la requête** (JSON, obligatoire) :
  - `email` (string, obligatoire) : Email de l'utilisateur
  - `password` (string, obligatoire) : Mot de passe

**Réponse en cas de succès (200 OK) :**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user"
  }
}
```

**Codes d'erreur :**
- `401 Unauthorized` : Identifiants invalides
  ```json
  {
    "detail": "Invalid credentials"
  }
  ```
- `403 Forbidden` : Compte suspendu
  ```json
  {
    "detail": "Account suspended"
  }
  ```
- `400 Bad Request` : Données invalides
  ```json
  {
    "detail": "Invalid email or password format"
  }
  ```

**Exemple d'utilisation avec gestion d'erreurs :**
```javascript
async function loginUser(email, password) {
  try {
    const response = await fetch('https://api.nativiweb.io/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        password: password
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      
      if (response.status === 401) {
        throw new Error('Email ou mot de passe incorrect');
      } else if (response.status === 403) {
        throw new Error('Compte suspendu. Contactez le support.');
      } else {
        throw new Error('Erreur lors de la connexion: ' + error.detail);
      }
    }
    
    const data = await response.json();
    
    // Stocker le token (dans localStorage, sessionStorage, ou cookie sécurisé)
    localStorage.setItem('auth_token', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));
    
    console.log('Connexion réussie:', data.user.name);
    return data;
    
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}

// Utilisation
try {
  const result = await loginUser('john.doe@example.com', 'SecurePassword123!');
  console.log('Token:', result.token);
  console.log('User:', result.user);
} catch (error) {
  alert('Erreur: ' + error.message);
}
```

---

### GET `/api/auth/me`

Récupère les informations de l'utilisateur actuellement connecté.

**Signature TypeScript :**
```typescript
GET /api/auth/me
Authorization: Bearer <token>

interface MeResponse {
  id: string;
  email: string;
  name: string;
  role: 'user' | 'admin';
}
```

**Paramètres :**
- **Headers** (obligatoire) :
  - `Authorization: Bearer <token>` : Token JWT obtenu lors de la connexion

**Réponse en cas de succès (200 OK) :**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user"
}
```

**Codes d'erreur :**
- `401 Unauthorized` : Token invalide ou expiré
  ```json
  {
    "detail": "Invalid or expired token"
  }
  ```
- `401 Unauthorized` : Token manquant
  ```json
  {
    "detail": "Not authenticated"
  }
  ```

**Exemple d'utilisation avec gestion d'erreurs :**
```javascript
async function getCurrentUser() {
  try {
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
      throw new Error('Non authentifié');
    }
    
    const response = await fetch('https://api.nativiweb.io/api/auth/me', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        // Token invalide ou expiré, déconnecter l'utilisateur
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        throw new Error('Session expirée. Veuillez vous reconnecter.');
      }
      
      const error = await response.json();
      throw new Error('Erreur: ' + error.detail);
    }
    
    const user = await response.json();
    return user;
    
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}

// Utilisation
try {
  const user = await getCurrentUser();
  console.log('Utilisateur actuel:', user.name);
} catch (error) {
  if (error.message.includes('Session expirée')) {
    // Rediriger vers la page de connexion
    window.location.href = '/login';
  } else {
    alert('Erreur: ' + error.message);
  }
}
```

---

### POST `/api/auth/logout`

Déconnecte l'utilisateur actuel.

**Signature TypeScript :**
```typescript
POST /api/auth/logout
Authorization: Bearer <token>

interface LogoutResponse {
  message: string;
}
```

**Paramètres :**
- **Headers** (obligatoire) :
  - `Authorization: Bearer <token>` : Token JWT

**Réponse en cas de succès (200 OK) :**
```json
{
  "message": "Logged out successfully"
}
```

**Codes d'erreur :**
- `401 Unauthorized` : Token invalide (mais la déconnexion est toujours considérée comme réussie côté client)

**Exemple d'utilisation :**
```javascript
async function logoutUser() {
  try {
    const token = localStorage.getItem('auth_token');
    
    if (token) {
      await fetch('https://api.nativiweb.io/api/auth/logout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
    }
    
    // Toujours nettoyer côté client, même si la requête échoue
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    
    console.log('Déconnexion réussie');
    
    // Rediriger vers la page de connexion
    window.location.href = '/login';
    
  } catch (error) {
    console.error('Erreur lors de la déconnexion:', error);
    // Nettoyer quand même côté client
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  }
}
```

---

### Durée de vie du token

- **Expiration** : Les tokens JWT expirent après 24 heures
- **Renouvellement** : Déconnectez-vous et reconnectez-vous pour obtenir un nouveau token
- **Stockage sécurisé** : Stockez toujours le token de manière sécurisée (localStorage pour dev, cookies httpOnly en production)

---

## Projects

Les endpoints de projets permettent de gérer vos projets d'applications natives.

---

### GET `/api/projects`

Liste tous les projets de l'utilisateur authentifié.

**Signature TypeScript :**
```typescript
GET /api/projects
Authorization: Bearer <token>

interface Project {
  id: string;
  user_id: string;
  name: string;
  web_url: string;
  description: string;
  platform: ('android' | 'ios')[];
  features: NativeFeature[];
  status: 'draft' | 'active' | 'archived';
  created_at: string;
  updated_at: string;
}

interface NativeFeature {
  id: string;
  name: string;
  enabled: boolean;
  config: Record<string, any>;
}
```

**Paramètres :**
- **Headers** (obligatoire) :
  - `Authorization: Bearer <token>`

**Réponse en cas de succès (200 OK) :**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Mon Application",
    "web_url": "https://myapp.com",
    "description": "Ma super application web",
    "platform": ["android", "ios"],
    "features": [
      {
        "id": "push_notifications",
        "name": "Push Notifications",
        "enabled": true,
        "config": {}
      },
      {
        "id": "camera",
        "name": "Camera",
        "enabled": false,
        "config": {}
      }
    ],
    "status": "draft",
    "created_at": "2024-01-15T10:30:00.000Z",
    "updated_at": "2024-01-15T10:30:00.000Z"
  }
]
```

**Codes d'erreur :**
- `401 Unauthorized` : Token invalide ou manquant

**Exemple d'utilisation :**
```javascript
async function getProjects() {
  try {
    const token = localStorage.getItem('auth_token');
    const response = await fetch('https://api.nativiweb.io/api/projects', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) throw new Error('Erreur lors de la récupération');
    
    const projects = await response.json();
    return projects;
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}
```

---

### POST `/api/projects`

Crée un nouveau projet.

**Signature TypeScript :**
```typescript
POST /api/projects
Authorization: Bearer <token>
Content-Type: application/json

interface CreateProjectRequest {
  name: string;                    // Nom du projet (1-100 caractères)
  web_url: string;                 // URL de l'application web (format URL valide)
  description?: string;            // Description optionnelle (max 500 caractères)
  platform?: ('android' | 'ios')[]; // Plateformes cibles (défaut: ["android", "ios"])
}

interface CreateProjectResponse extends Project {}
```

**Paramètres :**
- **Headers** (obligatoire) :
  - `Authorization: Bearer <token>`
  - `Content-Type: application/json`
- **Corps de la requête** (JSON, obligatoire) :
  - `name` (string, obligatoire) : Nom du projet
  - `web_url` (string, obligatoire) : URL de l'application web
  - `description` (string, optionnel) : Description du projet
  - `platform` (array, optionnel) : Plateformes cibles (défaut: `["android", "ios"]`)

**Réponse en cas de succès (200 OK) :**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Mon Application",
  "web_url": "https://myapp.com",
  "description": "Ma super application web",
  "platform": ["android", "ios"],
  "features": [
    {
      "id": "push_notifications",
      "name": "Push Notifications",
      "enabled": false,
      "config": {}
    },
    {
      "id": "camera",
      "name": "Camera",
      "enabled": false,
      "config": {}
    }
  ],
  "status": "draft",
  "created_at": "2024-01-15T10:30:00.000Z",
  "updated_at": "2024-01-15T10:30:00.000Z"
}
```

**Codes d'erreur :**
- `400 Bad Request` : Données invalides
- `401 Unauthorized` : Token invalide
- `422 Unprocessable Entity` : Validation échouée (URL invalide, etc.)

**Exemple d'utilisation avec gestion d'erreurs :**
```javascript
async function createProject(name, webUrl, description = '', platforms = ['android', 'ios']) {
  try {
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch('https://api.nativiweb.io/api/projects', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: name,
        web_url: webUrl,
        description: description,
        platform: platforms
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      
      if (response.status === 422) {
        throw new Error('URL invalide ou données incorrectes');
      } else if (response.status === 400) {
        throw new Error(error.detail || 'Données invalides');
      }
      
      throw new Error('Erreur lors de la création: ' + error.detail);
    }
    
    const project = await response.json();
    console.log('Projet créé:', project.id);
    return project;
    
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}

// Utilisation
try {
  const project = await createProject(
    'Mon App',
    'https://myapp.com',
    'Description de mon app',
    ['android', 'ios']
  );
} catch (error) {
  alert('Erreur: ' + error.message);
}
```

---

### GET `/api/projects/{project_id}`

Récupère un projet spécifique.

**Signature TypeScript :**
```typescript
GET /api/projects/{project_id}
Authorization: Bearer <token>

// Retourne: Project
```

**Paramètres :**
- **Path** (obligatoire) :
  - `project_id` (string) : ID UUID du projet
- **Headers** (obligatoire) :
  - `Authorization: Bearer <token>`

**Réponse en cas de succès (200 OK) :**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Mon Application",
  "web_url": "https://myapp.com",
  "description": "Ma super application web",
  "platform": ["android", "ios"],
  "features": [...],
  "status": "draft",
  "created_at": "2024-01-15T10:30:00.000Z",
  "updated_at": "2024-01-15T10:30:00.000Z"
}
```

**Codes d'erreur :**
- `404 Not Found` : Projet non trouvé ou n'appartient pas à l'utilisateur
- `401 Unauthorized` : Token invalide

**Exemple d'utilisation :**
```javascript
async function getProject(projectId) {
  try {
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch(
      `https://api.nativiweb.io/api/projects/${projectId}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    if (response.status === 404) {
      throw new Error('Projet non trouvé');
    }
    
    if (!response.ok) throw new Error('Erreur lors de la récupération');
    
    return await response.json();
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}
```

---

### PUT `/api/projects/{project_id}`

Met à jour un projet existant.

**Signature TypeScript :**
```typescript
PUT /api/projects/{project_id}
Authorization: Bearer <token>
Content-Type: application/json

interface UpdateProjectRequest {
  name?: string;
  web_url?: string;
  description?: string;
  features?: NativeFeature[];
}

// Retourne: Project (mis à jour)
```

**Paramètres :**
- **Path** (obligatoire) :
  - `project_id` (string) : ID UUID du projet
- **Headers** (obligatoire) :
  - `Authorization: Bearer <token>`
  - `Content-Type: application/json`
- **Corps de la requête** (JSON, tous les champs optionnels) :
  - `name` (string, optionnel) : Nouveau nom
  - `web_url` (string, optionnel) : Nouvelle URL
  - `description` (string, optionnel) : Nouvelle description
  - `features` (array, optionnel) : Liste des fonctionnalités natives

**Réponse en cas de succès (200 OK) :**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Nom Mis à Jour",
  "features": [
    {
      "id": "push_notifications",
      "name": "Push Notifications",
      "enabled": true,
      "config": {}
    }
  ],
  "updated_at": "2024-01-15T11:00:00.000Z",
  ...
}
```

**Codes d'erreur :**
- `404 Not Found` : Projet non trouvé
- `400 Bad Request` : Données invalides
- `401 Unauthorized` : Token invalide

**Exemple d'utilisation :**
```javascript
async function updateProject(projectId, updates) {
  try {
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch(
      `https://api.nativiweb.io/api/projects/${projectId}`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      }
    );
    
    if (response.status === 404) {
      throw new Error('Projet non trouvé');
    }
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Erreur lors de la mise à jour');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}

// Utilisation - Activer les notifications push
try {
  const updated = await updateProject(projectId, {
    features: [
      {
        id: 'push_notifications',
        name: 'Push Notifications',
        enabled: true,
        config: {}
      }
    ]
  });
} catch (error) {
  alert('Erreur: ' + error.message);
}
```

---

### DELETE `/api/projects/{project_id}`

Supprime un projet.

**Signature TypeScript :**
```typescript
DELETE /api/projects/{project_id}
Authorization: Bearer <token>

interface DeleteProjectResponse {
  message: string;
}
```

**Paramètres :**
- **Path** (obligatoire) :
  - `project_id` (string) : ID UUID du projet
- **Headers** (obligatoire) :
  - `Authorization: Bearer <token>`

**Réponse en cas de succès (200 OK) :**
```json
{
  "message": "Project deleted"
}
```

**Codes d'erreur :**
- `404 Not Found` : Projet non trouvé
- `401 Unauthorized` : Token invalide

**Exemple d'utilisation :**
```javascript
async function deleteProject(projectId) {
  try {
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch(
      `https://api.nativiweb.io/api/projects/${projectId}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    if (response.status === 404) {
      throw new Error('Projet non trouvé');
    }
    
    if (!response.ok) throw new Error('Erreur lors de la suppression');
    
    const result = await response.json();
    console.log(result.message);
    return result;
    
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}
```

---

## Builds

Les endpoints de builds permettent de créer, suivre et télécharger les builds de vos applications natives.

---

### GET `/api/builds`

Liste tous les builds de l'utilisateur authentifié.

**Signature TypeScript :**
```typescript
GET /api/builds
Authorization: Bearer <token>
Query Parameters:
  - project_id?: string (optionnel) - Filtrer par projet

interface Build {
  id: string;
  project_id: string;
  user_id: string;
  platform: 'android' | 'ios';
  build_type: 'debug' | 'release';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  phase: string;
  progress: number;              // 0-100
  logs: BuildLog[];
  artifacts: Artifact[];
  download_url?: string;
  error_message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
}

interface BuildLog {
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  timestamp: string;
}

interface Artifact {
  name: string;
  type: 'apk' | 'aab' | 'ipa';
  size: string;
}
```

**Paramètres :**
- **Headers** (obligatoire) :
  - `Authorization: Bearer <token>`
- **Query Parameters** (optionnel) :
  - `project_id` (string) : Filtrer les builds par projet

**Réponse en cas de succès (200 OK) :**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "project_id": "660e8400-e29b-41d4-a716-446655440001",
    "user_id": "770e8400-e29b-41d4-a716-446655440002",
    "platform": "android",
    "build_type": "debug",
    "status": "completed",
    "phase": "completed",
    "progress": 100,
    "logs": [
      {
        "level": "info",
        "message": "Build started for My App",
        "timestamp": "2024-01-15T10:30:00.000Z"
      },
      {
        "level": "success",
        "message": "Build completed successfully!",
        "timestamp": "2024-01-15T10:32:15.000Z"
      }
    ],
    "artifacts": [
      {
        "name": "My-App-debug.apk",
        "type": "apk",
        "size": "25MB"
      }
    ],
    "download_url": "/api/builds/550e8400-e29b-41d4-a716-446655440000/download",
    "created_at": "2024-01-15T10:30:00.000Z",
    "started_at": "2024-01-15T10:30:05.000Z",
    "completed_at": "2024-01-15T10:32:15.000Z",
    "duration_seconds": 130
  }
]
```

**Codes d'erreur :**
- `401 Unauthorized` : Token invalide ou manquant

**Exemple d'utilisation :**
```javascript
async function getBuilds(projectId = null) {
  try {
    const token = localStorage.getItem('auth_token');
    let url = 'https://api.nativiweb.io/api/builds';
    if (projectId) {
      url += `?project_id=${projectId}`;
    }
    
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) throw new Error('Erreur lors de la récupération');
    
    const builds = await response.json();
    return builds;
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}
```

---

### POST `/api/builds`

Crée un nouveau build pour un projet.

**Signature TypeScript :**
```typescript
POST /api/builds
Authorization: Bearer <token>
Content-Type: application/json

interface CreateBuildRequest {
  project_id: string;            // ID du projet
  platform: 'android' | 'ios';   // Plateforme cible
  build_type?: 'debug' | 'release'; // Type de build (défaut: 'debug')
  certificate_id?: string;       // ID du certificat de signature (optionnel)
}

// Retourne: Build
```

**Paramètres :**
- **Headers** (obligatoire) :
  - `Authorization: Bearer <token>`
  - `Content-Type: application/json`
- **Corps de la requête** (JSON, obligatoire) :
  - `project_id` (string, obligatoire) : ID UUID du projet
  - `platform` (string, obligatoire) : `'android'` ou `'ios'`
  - `build_type` (string, optionnel) : `'debug'` ou `'release'` (défaut: `'debug'`)
  - `certificate_id` (string, optionnel) : ID du certificat de signature pour les builds release

**Réponse en cas de succès (200 OK) :**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": "770e8400-e29b-41d4-a716-446655440002",
  "platform": "android",
  "build_type": "debug",
  "status": "processing",
  "phase": "queued",
  "progress": 0,
  "logs": [
    {
      "level": "info",
      "message": "Build queued for My App",
      "timestamp": "2024-01-15T10:30:00.000Z"
    }
  ],
  "artifacts": [],
  "created_at": "2024-01-15T10:30:00.000Z"
}
```

**Codes d'erreur :**
- `400 Bad Request` : Données invalides
- `401 Unauthorized` : Token invalide
- `404 Not Found` : Projet non trouvé
- `429 Too Many Requests` : Trop de builds en cours (limite: 10 par heure par projet)

**Build Status Values :**
- `pending` - Build en file d'attente
- `processing` - Build en cours
- `completed` - Build terminé avec succès
- `failed` - Build échoué

**Exemple d'utilisation avec gestion d'erreurs :**
```javascript
async function createBuild(projectId, platform, buildType = 'debug') {
  try {
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch('https://api.nativiweb.io/api/builds', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        project_id: projectId,
        platform: platform,
        build_type: buildType
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      
      if (response.status === 404) {
        throw new Error('Projet non trouvé');
      } else if (response.status === 429) {
        throw new Error('Trop de builds en cours. Veuillez attendre.');
      } else {
        throw new Error('Erreur lors de la création du build: ' + error.detail);
      }
    }
    
    const build = await response.json();
    console.log('Build créé:', build.id);
    console.log('Statut:', build.status);
    
    // Polling pour suivre le statut
    pollBuildStatus(build.id);
    
    return build;
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}

// Fonction pour suivre le statut du build
async function pollBuildStatus(buildId) {
  const interval = setInterval(async () => {
    try {
      const build = await getBuild(buildId);
      
      console.log(`Build ${buildId}: ${build.status} - ${build.progress}%`);
      
      if (build.status === 'completed' || build.status === 'failed') {
        clearInterval(interval);
        if (build.status === 'completed') {
          console.log('Build terminé avec succès!');
          console.log('Téléchargement:', build.download_url);
        } else {
          console.error('Build échoué:', build.error_message);
        }
      }
    } catch (error) {
      console.error('Erreur lors du suivi:', error);
      clearInterval(interval);
    }
  }, 5000); // Vérifier toutes les 5 secondes
}
```

---

### GET `/api/builds/{build_id}`

Récupère les détails d'un build spécifique.

**Signature TypeScript :**
```typescript
GET /api/builds/{build_id}
Authorization: Bearer <token>

// Retourne: Build
```

**Paramètres :**
- **Path** (obligatoire) :
  - `build_id` (string) : ID UUID du build
- **Headers** (obligatoire) :
  - `Authorization: Bearer <token>`

**Réponse en cas de succès (200 OK) :**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": "770e8400-e29b-41d4-a716-446655440002",
  "platform": "android",
  "build_type": "debug",
  "status": "completed",
  "phase": "completed",
  "progress": 100,
  "logs": [...],
  "artifacts": [
    {
      "name": "My-App-debug.apk",
      "type": "apk",
      "size": "25MB"
    }
  ],
  "download_url": "/api/builds/550e8400-e29b-41d4-a716-446655440000/download",
  "created_at": "2024-01-15T10:30:00.000Z",
  "completed_at": "2024-01-15T10:32:15.000Z",
  "duration_seconds": 130
}
```

**Codes d'erreur :**
- `404 Not Found` : Build non trouvé ou n'appartient pas à l'utilisateur
- `401 Unauthorized` : Token invalide

**Exemple d'utilisation :**
```javascript
async function getBuild(buildId) {
  try {
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch(
      `https://api.nativiweb.io/api/builds/${buildId}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    if (response.status === 404) {
      throw new Error('Build non trouvé');
    }
    
    if (!response.ok) throw new Error('Erreur lors de la récupération');
    
    return await response.json();
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}
```

---

### GET `/api/builds/{build_id}/download`

Télécharge le build terminé sous forme de fichier ZIP.

**Signature TypeScript :**
```typescript
GET /api/builds/{build_id}/download
Authorization: Bearer <token>

// Retourne: Blob (fichier ZIP)
```

**Paramètres :**
- **Path** (obligatoire) :
  - `build_id` (string) : ID UUID du build
- **Headers** (obligatoire) :
  - `Authorization: Bearer <token>`

**Réponse en cas de succès (200 OK) :**
- Type : `application/zip`
- Corps : Fichier ZIP binaire

**Contenu du ZIP :**
- Native project template (Android/iOS)
  - Structure complète du projet natif
  - Fichiers de configuration
  - Code source natif
- SDK JavaScript file (`nativiweb-sdk.js`)
  - Personnalisé selon les fonctionnalités activées du projet
- Configuration files
  - `README.md` avec instructions
  - `app-config.json` avec la configuration du projet

**Codes d'erreur :**
- `404 Not Found` : Build non trouvé
- `400 Bad Request` : Build non terminé (`status !== 'completed'`)
- `401 Unauthorized` : Token invalide

**Exemple d'utilisation :**
```javascript
async function downloadBuild(buildId) {
  try {
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch(
      `https://api.nativiweb.io/api/builds/${buildId}/download`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    if (response.status === 404) {
      throw new Error('Build non trouvé');
    }
    
    if (response.status === 400) {
      throw new Error('Le build n\'est pas encore terminé');
    }
    
    if (!response.ok) throw new Error('Erreur lors du téléchargement');
    
    // Obtenir le blob
    const blob = await response.blob();
    
    // Créer un lien de téléchargement
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `build-${buildId}.zip`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    console.log('Téléchargement terminé');
    
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}
```

---

## API Keys

Les clés API permettent d'authentifier les requêtes vers l'API NativiWeb depuis votre backend ou applications externes.

---

### GET `/api/api-keys`

Liste toutes les clés API de l'utilisateur authentifié.

**Signature TypeScript :**
```typescript
GET /api/api-keys
Authorization: Bearer <token>

interface APIKey {
  id: string;
  user_id: string;
  name: string;
  key: string;                    // Clé API (à garder secrète)
  permissions: string[];          // ['read', 'write']
  last_used?: string;             // ISO 8601 timestamp ou null
  created_at: string;
}
```

**Paramètres :**
- **Headers** (obligatoire) :
  - `Authorization: Bearer <token>`

**Réponse en cas de succès (200 OK) :**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Production Key",
    "key": "nw_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
    "permissions": ["read", "write"],
    "last_used": "2024-01-15T10:30:00.000Z",
    "created_at": "2024-01-10T08:00:00.000Z"
  },
  {
    "id": "551e8400-e29b-41d4-a716-446655440001",
    "user_id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Development Key",
    "key": "nw_xyz789abc123def456ghi789jkl012mno345pqr678stu901vw",
    "permissions": ["read"],
    "last_used": null,
    "created_at": "2024-01-12T14:20:00.000Z"
  }
]
```

**Codes d'erreur :**
- `401 Unauthorized` : Token invalide ou manquant

**Exemple d'utilisation :**
```javascript
async function getAPIKeys() {
  try {
    const token = localStorage.getItem('auth_token');
    const response = await fetch('https://api.nativiweb.io/api/api-keys', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) throw new Error('Erreur lors de la récupération');
    
    const keys = await response.json();
    return keys;
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}
```

---

### POST `/api/api-keys`

Crée une nouvelle clé API.

**Signature TypeScript :**
```typescript
POST /api/api-keys
Authorization: Bearer <token>
Content-Type: application/json

interface CreateAPIKeyRequest {
  name: string;                   // Nom de la clé (pour identification)
  permissions?: string[];         // Permissions (défaut: ['read'])
}

// Retourne: APIKey
```

**Paramètres :**
- **Headers** (obligatoire) :
  - `Authorization: Bearer <token>`
  - `Content-Type: application/json`
- **Corps de la requête** (JSON, obligatoire) :
  - `name` (string, obligatoire) : Nom de la clé (pour identification, ex: "Production Key", "Development Key")
  - `permissions` (array, optionnel) : Permissions disponibles (défaut: `['read']`)
    - `'read'` : Lecture seule (GET)
    - `'write'` : Lecture et écriture (GET, POST, PUT, DELETE)

**Réponse en cas de succès (200 OK) :**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Production Key",
  "key": "nw_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
  "permissions": ["read", "write"],
  "last_used": null,
  "created_at": "2024-01-15T10:30:00.000Z"
}
```

**Codes d'erreur :**
- `400 Bad Request` : Données invalides
- `401 Unauthorized` : Token invalide

**Exemple d'utilisation avec gestion d'erreurs :**
```javascript
async function createAPIKey(name, permissions = ['read']) {
  try {
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch('https://api.nativiweb.io/api/api-keys', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: name,
        permissions: permissions
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error('Erreur lors de la création: ' + error.detail);
    }
    
    const apiKey = await response.json();
    
    // ⚠️ IMPORTANT : La clé est affichée UNE SEULE FOIS
    console.log('Clé API créée:', apiKey.key);
    alert(`Clé API créée. Veuillez la sauvegarder maintenant :\n\n${apiKey.key}\n\n⚠️ Elle ne sera plus affichée après cette fois.`);
    
    return apiKey;
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}

// Utilisation
try {
  // Créer une clé pour la production
  const productionKey = await createAPIKey('Production Key', ['read', 'write']);
  
  // Créer une clé pour le développement (lecture seule)
  const devKey = await createAPIKey('Development Key', ['read']);
  
} catch (error) {
  alert('Erreur: ' + error.message);
}
```

**Utilisation de la clé API :**
```javascript
// Utiliser la clé API dans vos requêtes
const apiKey = 'nw_abc123def456...';

// Faire une requête avec la clé API
const response = await fetch('https://api.nativiweb.io/api/projects', {
  headers: {
    'Authorization': `Bearer ${apiKey}`,
    'X-API-Key': apiKey  // Alternative si Bearer n'est pas supporté
  }
});
```

---

### DELETE `/api/api-keys/{key_id}`

Supprime une clé API.

**Signature TypeScript :**
```typescript
DELETE /api/api-keys/{key_id}
Authorization: Bearer <token>

interface DeleteAPIKeyResponse {
  message: string;
}
```

**Paramètres :**
- **Path** (obligatoire) :
  - `key_id` (string) : ID UUID de la clé API
- **Headers** (obligatoire) :
  - `Authorization: Bearer <token>`

**Réponse en cas de succès (200 OK) :**
```json
{
  "message": "API key deleted"
}
```

**Codes d'erreur :**
- `404 Not Found` : Clé API non trouvée
- `401 Unauthorized` : Token invalide

**Exemple d'utilisation :**
```javascript
async function deleteAPIKey(keyId) {
  try {
    const token = localStorage.getItem('auth_token');
    
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette clé API ?')) {
      return;
    }
    
    const response = await fetch(
      `https://api.nativiweb.io/api/api-keys/${keyId}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    if (response.status === 404) {
      throw new Error('Clé API non trouvée');
    }
    
    if (!response.ok) throw new Error('Erreur lors de la suppression');
    
    const result = await response.json();
    console.log(result.message);
    return result;
    
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}
```

**Bonnes pratiques pour les clés API :**
- ⚠️ **Ne jamais exposer les clés API** dans le code client (frontend JavaScript)
- Stockez les clés API côté serveur uniquement
- Utilisez des variables d'environnement pour stocker les clés
- Régénérez régulièrement les clés (supprimez et recréez)
- Utilisez des clés différentes pour développement et production
- Limitez les permissions au minimum nécessaire (principe du moindre privilège)

---

## Generator

### GET `/api/generator/sdk/{project_id}`

Télécharge le SDK JavaScript personnalisé pour un projet avec uniquement les fonctionnalités activées.

**Signature TypeScript :**
```typescript
GET /api/generator/sdk/{project_id}
Authorization: Bearer <token>

// Retourne: Blob (fichier JavaScript)
```

**Paramètres :**
- **Path** (obligatoire) :
  - `project_id` (string) : ID UUID du projet
- **Headers** (obligatoire) :
  - `Authorization: Bearer <token>`

**Réponse en cas de succès (200 OK) :**
- Type : `application/javascript`
- Corps : Fichier JavaScript du SDK personnalisé

**Exemple d'utilisation :**
```javascript
async function downloadCustomSDK(projectId) {
  try {
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch(
      `https://api.nativiweb.io/api/generator/sdk/${projectId}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    if (!response.ok) throw new Error('Erreur lors du téléchargement');
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'nativiweb-sdk.js';
    a.click();
    window.URL.revokeObjectURL(url);
    
  } catch (error) {
    console.error('Erreur:', error);
  }
}
```

---

### GET `/api/generator/template/{project_id}/{platform}`

Récupère un aperçu du template de code natif généré.

**Signature TypeScript :**
```typescript
GET /api/generator/template/{project_id}/{platform}
Authorization: Bearer <token>

// Retourne: TemplatePreview
```

**Paramètres :**
- **Path** (obligatoire) :
  - `project_id` (string) : ID UUID du projet
  - `platform` (string) : `'android'` ou `'ios'`
- **Headers** (obligatoire) :
  - `Authorization: Bearer <token>`

**Réponse en cas de succès (200 OK) :**
```json
{
  "platform": "android",
  "project_name": "My App",
  "structure": {
    "MainActivity.kt": "...",
    "AndroidManifest.xml": "...",
    "build.gradle": "..."
  },
  "sdk_integration": "..."
}
```

**Exemple d'utilisation :**
```javascript
async function getTemplatePreview(projectId, platform) {
  try {
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch(
      `https://api.nativiweb.io/api/generator/template/${projectId}/${platform}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    if (!response.ok) throw new Error('Erreur lors de la récupération');
    
    const preview = await response.json();
    return preview;
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}
```

---

## Features

### GET `/api/features`

Liste toutes les fonctionnalités natives disponibles.

**Signature TypeScript :**
```typescript
GET /api/features

interface NativeFeature {
  id: string;
  name: string;
  enabled: boolean;
  config: Record<string, any>;
}
```

**Paramètres :**
- **Headers** : Aucun (endpoint public)

**Réponse en cas de succès (200 OK) :**
```json
[
  {
    "id": "push_notifications",
    "name": "Push Notifications",
    "enabled": false,
    "config": {}
  },
  {
    "id": "camera",
    "name": "Camera",
    "enabled": false,
    "config": {}
  },
  {
    "id": "geolocation",
    "name": "Geolocation (GPS)",
    "enabled": false,
    "config": {}
  },
  {
    "id": "local_storage",
    "name": "Local Storage",
    "enabled": false,
    "config": {}
  },
  {
    "id": "biometrics",
    "name": "Biometric Auth",
    "enabled": false,
    "config": {}
  },
  {
    "id": "contacts",
    "name": "Contacts",
    "enabled": false,
    "config": {}
  },
  {
    "id": "file_system",
    "name": "File System",
    "enabled": false,
    "config": {}
  },
  {
    "id": "share",
    "name": "Native Share",
    "enabled": false,
    "config": {}
  },
  {
    "id": "haptics",
    "name": "Haptic Feedback",
    "enabled": false,
    "config": {}
  },
  {
    "id": "deep_links",
    "name": "Deep Links",
    "enabled": false,
    "config": {}
  },
  {
    "id": "app_badge",
    "name": "App Badge",
    "enabled": false,
    "config": {}
  },
  {
    "id": "clipboard",
    "name": "Clipboard",
    "enabled": false,
    "config": {}
  }
]
```

**Exemple d'utilisation :**
```javascript
async function getAvailableFeatures() {
  try {
    const response = await fetch('https://api.nativiweb.io/api/features');
    
    if (!response.ok) throw new Error('Erreur lors de la récupération');
    
    const features = await response.json();
    return features;
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}
```

---

## Stats

### GET `/api/stats`

Récupère les statistiques de l'utilisateur authentifié.

**Signature TypeScript :**
```typescript
GET /api/stats
Authorization: Bearer <token>

interface UserStats {
  projects: number;
  total_builds: number;
  successful_builds: number;
  api_keys: number;
}
```

**Paramètres :**
- **Headers** (obligatoire) :
  - `Authorization: Bearer <token>`

**Réponse en cas de succès (200 OK) :**
```json
{
  "projects": 5,
  "total_builds": 12,
  "successful_builds": 10,
  "api_keys": 2
}
```

**Codes d'erreur :**
- `401 Unauthorized` : Token invalide ou manquant

**Exemple d'utilisation :**
```javascript
async function getUserStats() {
  try {
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch('https://api.nativiweb.io/api/stats', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) throw new Error('Erreur lors de la récupération');
    
    const stats = await response.json();
    
    console.log('Projets:', stats.projects);
    console.log('Builds totaux:', stats.total_builds);
    console.log('Builds réussis:', stats.successful_builds);
    console.log('Taux de succès:', (stats.successful_builds / stats.total_builds * 100).toFixed(1) + '%');
    
    return stats;
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}
```

---

## Health Check

### GET `/api/health`

Vérifie l'état de santé de l'API.

**Signature TypeScript :**
```typescript
GET /api/health

interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  version?: string;
}
```

**Paramètres :**
- **Headers** : Aucun (endpoint public)

**Réponse en cas de succès (200 OK) :**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "version": "2.0.0"
}
```

**Exemple d'utilisation :**
```javascript
async function checkAPIHealth() {
  try {
    const response = await fetch('https://api.nativiweb.io/api/health');
    const health = await response.json();
    
    if (health.status === 'healthy') {
      console.log('API opérationnelle');
      return true;
    } else {
      console.warn('API en état dégradé');
      return false;
    }
  } catch (error) {
    console.error('API inaccessible:', error);
    return false;
  }
}

// Utilisation : vérifier avant de faire des requêtes importantes
if (await checkAPIHealth()) {
  // Continuer avec les requêtes
  await fetchUserData();
} else {
  showErrorMessage('L\'API n\'est pas disponible actuellement');
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (invalid/missing token)
- `404` - Not Found
- `500` - Internal Server Error

---

## Rate Limits

- 100 requests per minute per user
- 1000 requests per hour per user
- Build creation: 10 per hour per project

---

## Webhooks (Coming Soon)

Configure webhooks to receive notifications about:
- Build completion
- Build failure
- Project updates

---

For SDK documentation, see [SDK.md](./SDK.md)
