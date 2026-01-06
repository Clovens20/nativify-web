# NativiWeb Studio

> Transform your web applications into native Android & iOS apps without writing native code.

## 🚀 Overview

NativiWeb Studio is a comprehensive platform that enables developers to convert existing web applications into native mobile apps. Our platform generates native project templates and provides a JavaScript SDK for accessing device features.

## 🏗 Architecture

```
/app
├── backend/           # FastAPI Python backend
│   ├── server.py      # Main API server
│   └── .env           # Environment variables
├── frontend/          # React frontend
│   ├── src/
│   │   ├── pages/     # App pages (Dashboard, Projects, Builds, etc.)
│   │   ├── components/# Reusable UI components
│   │   ├── context/   # React context (Auth)
│   │   └── lib/       # API utilities
│   └── .env           # Frontend environment
└── docs/              # Documentation
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

- **Frontend**: React 19, Tailwind CSS, Shadcn/UI, React Router
- **Backend**: FastAPI (Python), MongoDB (Motor async driver)
- **Authentication**: Token-based auth with Supabase-ready structure
- **Styling**: Custom Neon Tech theme with cyan/violet accents

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- MongoDB

### Installation

1. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt
```

2. **Frontend Setup**
```bash
cd frontend
yarn install
```

3. **Environment Variables**

Backend `.env`:
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=nativiweb_studio
```

Frontend `.env`:
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Running the Application

```bash
# Start backend
cd backend
uvicorn server:app --reload --port 8001

# Start frontend (in another terminal)
cd frontend
yarn start
```

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
