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

Most endpoints require authentication via a token passed as a query parameter or header.

### Register

```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "John Doe"
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "token": "abc123...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

### Get Current User

```http
GET /api/auth/me?token=abc123...
```

### Logout

```http
POST /api/auth/logout?token=abc123...
```

---

## Projects

### List Projects

```http
GET /api/projects?user_id=uuid
```

**Response:**
```json
[
  {
    "id": "project-uuid",
    "user_id": "user-uuid",
    "name": "My App",
    "web_url": "https://myapp.com",
    "description": "My awesome app",
    "platform": ["android", "ios"],
    "features": [...],
    "status": "draft",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### Create Project

```http
POST /api/projects?user_id=uuid
Content-Type: application/json

{
  "name": "My App",
  "web_url": "https://myapp.com",
  "description": "Optional description",
  "platform": ["android", "ios"]
}
```

### Get Project

```http
GET /api/projects/{project_id}?user_id=uuid
```

### Update Project

```http
PUT /api/projects/{project_id}?user_id=uuid
Content-Type: application/json

{
  "name": "Updated Name",
  "features": [
    {
      "id": "push_notifications",
      "name": "Push Notifications",
      "enabled": true,
      "config": {}
    }
  ]
}
```

### Delete Project

```http
DELETE /api/projects/{project_id}?user_id=uuid
```

---

## Builds

### List Builds

```http
GET /api/builds?user_id=uuid
GET /api/builds?user_id=uuid&project_id=project-uuid
```

**Response:**
```json
[
  {
    "id": "build-uuid",
    "project_id": "project-uuid",
    "user_id": "user-uuid",
    "platform": "android",
    "build_type": "debug",
    "status": "completed",
    "progress": 100,
    "logs": ["Build started...", "Completed!"],
    "download_url": "/api/builds/build-uuid/download",
    "created_at": "2024-01-01T00:00:00Z",
    "completed_at": "2024-01-01T00:00:30Z"
  }
]
```

### Create Build

```http
POST /api/builds?user_id=uuid
Content-Type: application/json

{
  "project_id": "project-uuid",
  "platform": "android",
  "build_type": "debug"
}
```

**Build Status Values:**
- `pending` - Build queued
- `processing` - Build in progress
- `completed` - Build successful
- `failed` - Build failed

### Get Build

```http
GET /api/builds/{build_id}?user_id=uuid
```

### Download Build

```http
GET /api/builds/{build_id}/download?user_id=uuid
```

Returns a ZIP file containing:
- Native project template (Android/iOS)
- SDK JavaScript file
- Configuration files

---

## API Keys

### List API Keys

```http
GET /api/api-keys?user_id=uuid
```

**Response:**
```json
[
  {
    "id": "key-uuid",
    "user_id": "user-uuid",
    "name": "Production Key",
    "key": "nw_abc123...",
    "permissions": ["read", "write"],
    "last_used": null,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### Create API Key

```http
POST /api/api-keys?user_id=uuid
Content-Type: application/json

{
  "name": "Production Key",
  "permissions": ["read", "write"]
}
```

### Delete API Key

```http
DELETE /api/api-keys/{key_id}?user_id=uuid
```

---

## Generator

### Download SDK

```http
GET /api/generator/sdk/{project_id}?user_id=uuid
```

Returns the JavaScript SDK file customized for the project's enabled features.

### Get Template Preview

```http
GET /api/generator/template/{project_id}/{platform}?user_id=uuid
```

**platform**: `android` or `ios`

Returns a JSON object with the template code preview.

---

## Features

### List Available Features

```http
GET /api/features
```

**Response:**
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
  ...
]
```

---

## Stats

### Get User Stats

```http
GET /api/stats?user_id=uuid
```

**Response:**
```json
{
  "projects": 5,
  "total_builds": 12,
  "successful_builds": 10,
  "api_keys": 2
}
```

---

## Health Check

### API Health

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
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
