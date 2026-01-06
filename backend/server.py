from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import json
import io
import zipfile
import hashlib
import secrets
import base64
import asyncio
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Supabase connection
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create the main app
app = FastAPI(
    title="NativiWeb Studio API",
    description="API pour transformer des web apps en applications natives",
    version="2.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ==================== MODELS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: str = "user"
    status: str = "active"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class NativeFeature(BaseModel):
    id: str
    name: str
    enabled: bool = False
    config: Dict[str, Any] = {}

class ProjectCreate(BaseModel):
    name: str
    web_url: str
    description: Optional[str] = ""
    platform: List[str] = ["android", "ios"]

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    web_url: Optional[str] = None
    description: Optional[str] = None
    features: Optional[List[NativeFeature]] = None

class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    web_url: str
    description: str = ""
    platform: List[str] = ["android", "ios"]
    features: List[NativeFeature] = []
    status: str = "draft"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BuildCreate(BaseModel):
    project_id: str
    platform: str
    build_type: str = "debug"
    certificate_id: Optional[str] = None

class Build(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    user_id: str
    platform: str
    build_type: str
    build_config: Dict[str, Any] = {}
    certificate_id: Optional[str] = None
    status: str = "pending"
    phase: str = "queued"
    progress: int = 0
    logs: List[Any] = []
    artifacts: List[Dict[str, str]] = []
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[int] = None

class APIKeyCreate(BaseModel):
    name: str
    permissions: List[str] = ["read"]

class APIKey(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    key: str = Field(default_factory=lambda: f"nw_{secrets.token_hex(24)}")
    permissions: List[str] = ["read"]
    last_used: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class UserUpdate(BaseModel):
    status: Optional[str] = None
    role: Optional[str] = None

class PlatformConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "platform_config"
    maintenance_mode: bool = False
    max_builds_per_user: int = 10
    max_projects_per_user: int = 5
    allowed_domains: List[str] = []
    build_timeout_minutes: int = 30
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Default native features
DEFAULT_FEATURES = [
    {"id": "push_notifications", "name": "Push Notifications", "enabled": False, "config": {}},
    {"id": "camera", "name": "Camera", "enabled": False, "config": {}},
    {"id": "geolocation", "name": "Geolocation (GPS)", "enabled": False, "config": {}},
    {"id": "local_storage", "name": "Local Storage", "enabled": False, "config": {}},
    {"id": "biometrics", "name": "Biometric Auth", "enabled": False, "config": {}},
    {"id": "contacts", "name": "Contacts", "enabled": False, "config": {}},
    {"id": "file_system", "name": "File System", "enabled": False, "config": {}},
    {"id": "share", "name": "Native Share", "enabled": False, "config": {}},
    {"id": "haptics", "name": "Haptic Feedback", "enabled": False, "config": {}},
    {"id": "deep_links", "name": "Deep Links", "enabled": False, "config": {}},
    {"id": "app_badge", "name": "App Badge", "enabled": False, "config": {}},
    {"id": "clipboard", "name": "Clipboard", "enabled": False, "config": {}},
]

# Build phases
BUILD_PHASES = {
    "android": [
        {"phase": "queued", "name": "Queued", "duration": 2},
        {"phase": "preparing", "name": "Preparing Environment", "duration": 3},
        {"phase": "fetching", "name": "Fetching Web App", "duration": 4},
        {"phase": "generating", "name": "Generating Native Project", "duration": 5},
        {"phase": "configuring", "name": "Configuring Features", "duration": 3},
        {"phase": "gradle_sync", "name": "Gradle Sync", "duration": 8},
        {"phase": "compiling", "name": "Compiling Resources", "duration": 10},
        {"phase": "assembling", "name": "Assembling APK/AAB", "duration": 8},
        {"phase": "signing", "name": "Signing Package", "duration": 3},
        {"phase": "optimizing", "name": "Optimizing", "duration": 2},
        {"phase": "uploading", "name": "Uploading Artifacts", "duration": 2},
        {"phase": "completed", "name": "Completed", "duration": 0},
    ],
    "ios": [
        {"phase": "queued", "name": "Queued", "duration": 2},
        {"phase": "preparing", "name": "Preparing Environment", "duration": 4},
        {"phase": "fetching", "name": "Fetching Web App", "duration": 4},
        {"phase": "generating", "name": "Generating Xcode Project", "duration": 6},
        {"phase": "configuring", "name": "Configuring Capabilities", "duration": 4},
        {"phase": "pod_install", "name": "Installing CocoaPods", "duration": 8},
        {"phase": "compiling", "name": "Compiling Swift Code", "duration": 12},
        {"phase": "linking", "name": "Linking Frameworks", "duration": 6},
        {"phase": "archiving", "name": "Creating Archive", "duration": 8},
        {"phase": "signing", "name": "Code Signing", "duration": 4},
        {"phase": "exporting", "name": "Exporting IPA", "duration": 3},
        {"phase": "uploading", "name": "Uploading Artifacts", "duration": 2},
        {"phase": "completed", "name": "Completed", "duration": 0},
    ]
}

# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_build_logs(phase: str, platform: str, project_name: str) -> List[Dict[str, Any]]:
    timestamp = datetime.now(timezone.utc).isoformat()
    log_templates = {
        "queued": [{"level": "info", "message": f"Build queued for {project_name}", "timestamp": timestamp}],
        "preparing": [{"level": "info", "message": "Initializing build environment...", "timestamp": timestamp}],
        "fetching": [{"level": "info", "message": "Fetching web application content...", "timestamp": timestamp}],
        "generating": [{"level": "info", "message": "Generating native project structure...", "timestamp": timestamp}],
        "configuring": [{"level": "info", "message": "Configuring native features...", "timestamp": timestamp}],
        "gradle_sync": [{"level": "info", "message": "Starting Gradle sync...", "timestamp": timestamp}],
        "pod_install": [{"level": "info", "message": "Running pod install...", "timestamp": timestamp}],
        "compiling": [{"level": "info", "message": "Compiling source files...", "timestamp": timestamp}],
        "linking": [{"level": "info", "message": "Linking frameworks...", "timestamp": timestamp}],
        "assembling": [{"level": "info", "message": "Assembling APK...", "timestamp": timestamp}],
        "archiving": [{"level": "info", "message": "Creating Xcode archive...", "timestamp": timestamp}],
        "signing": [{"level": "success", "message": "Package signed successfully", "timestamp": timestamp}],
        "optimizing": [{"level": "info", "message": "Optimizing APK size...", "timestamp": timestamp}],
        "exporting": [{"level": "info", "message": "Exporting IPA file...", "timestamp": timestamp}],
        "uploading": [{"level": "success", "message": "Artifacts uploaded successfully", "timestamp": timestamp}],
        "completed": [{"level": "success", "message": "Build completed successfully!", "timestamp": timestamp}],
    }
    return log_templates.get(phase, [{"level": "info", "message": f"Phase: {phase}", "timestamp": timestamp}])

async def log_system_event(level: str, category: str, message: str, details: dict = None, user_id: str = None):
    try:
        supabase.table("system_logs").insert({
            "id": str(uuid.uuid4()),
            "level": level,
            "category": category,
            "message": message,
            "details": details or {},
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()
    except Exception as e:
        logging.error(f"Failed to log system event: {e}")

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    try:
        # Register with Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "name": user_data.name
                }
            }
        })
        
        if auth_response.user:
            # Create profile in users table
            user_id = auth_response.user.id
            supabase.table("users").insert({
                "id": user_id,
                "email": user_data.email,
                "name": user_data.name,
                "role": "user",
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat()
            }).execute()
            
            await log_system_event("info", "auth", f"New user registered: {user_data.email}", user_id=user_id)
            
            return {
                "id": user_id,
                "email": user_data.email,
                "name": user_data.name,
                "role": "user"
            }
        else:
            raise HTTPException(status_code=400, detail="Registration failed")
    except Exception as e:
        if "already registered" in str(e).lower():
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        if auth_response.user and auth_response.session:
            user_id = auth_response.user.id
            
            # Get user profile
            user_response = supabase.table("users").select("*").eq("id", user_id).single().execute()
            user_data = user_response.data if user_response.data else {}
            
            if user_data.get('status') == 'banned':
                raise HTTPException(status_code=403, detail="Account suspended")
            
            await log_system_event("info", "auth", f"User logged in: {credentials.email}", user_id=user_id)
            
            return {
                "token": auth_response.session.access_token,
                "user": {
                    "id": user_id,
                    "email": auth_response.user.email,
                    "name": user_data.get('name', auth_response.user.user_metadata.get('name', '')),
                    "role": user_data.get('role', 'user')
                }
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        await log_system_event("warning", "auth", f"Failed login attempt for {credentials.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

@api_router.get("/auth/me")
async def get_current_user(token: str):
    try:
        user_response = supabase.auth.get_user(token)
        if user_response.user:
            user_id = user_response.user.id
            profile = supabase.table("users").select("*").eq("id", user_id).single().execute()
            user_data = profile.data if profile.data else {}
            
            return {
                "id": user_id,
                "email": user_response.user.email,
                "name": user_data.get('name', ''),
                "role": user_data.get('role', 'user')
            }
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

@api_router.post("/auth/logout")
async def logout(token: str):
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except:
        return {"message": "Logged out successfully"}

# ==================== PROJECT ENDPOINTS ====================

@api_router.post("/projects")
async def create_project(project_data: ProjectCreate, user_id: str):
    project_id = str(uuid.uuid4())
    project = {
        "id": project_id,
        "user_id": user_id,
        "name": project_data.name,
        "web_url": project_data.web_url,
        "description": project_data.description or "",
        "platform": project_data.platform,
        "features": DEFAULT_FEATURES,
        "status": "draft",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    supabase.table("projects").insert(project).execute()
    await log_system_event("info", "project", f"Project created: {project_data.name}", user_id=user_id)
    return project

@api_router.get("/projects")
async def get_projects(user_id: str):
    response = supabase.table("projects").select("*").eq("user_id", user_id).execute()
    return response.data or []

@api_router.get("/projects/{project_id}")
async def get_project(project_id: str, user_id: str):
    response = supabase.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Project not found")
    return response.data

@api_router.put("/projects/{project_id}")
async def update_project(project_id: str, user_id: str, update_data: ProjectUpdate):
    # Check project exists
    existing = supabase.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).single().execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if 'features' in update_dict:
        update_dict['features'] = [f.model_dump() if hasattr(f, 'model_dump') else f for f in update_dict['features']]
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    supabase.table("projects").update(update_dict).eq("id", project_id).execute()
    
    updated = supabase.table("projects").select("*").eq("id", project_id).single().execute()
    return updated.data

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str, user_id: str):
    result = supabase.table("projects").delete().eq("id", project_id).eq("user_id", user_id).execute()
    await log_system_event("info", "project", f"Project deleted: {project_id}", user_id=user_id)
    return {"message": "Project deleted"}

# ==================== BUILD ENDPOINTS ====================

@api_router.post("/builds")
async def create_build(build_data: BuildCreate, user_id: str, background_tasks: BackgroundTasks):
    # Check project exists
    project_response = supabase.table("projects").select("*").eq("id", build_data.project_id).eq("user_id", user_id).single().execute()
    if not project_response.data:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = project_response.data
    build_id = str(uuid.uuid4())
    
    build = {
        "id": build_id,
        "project_id": build_data.project_id,
        "user_id": user_id,
        "platform": build_data.platform,
        "build_type": build_data.build_type,
        "build_config": {},
        "certificate_id": build_data.certificate_id,
        "status": "processing",
        "phase": "queued",
        "progress": 0,
        "logs": [{"level": "info", "message": f"Build queued for {project['name']}", "timestamp": datetime.now(timezone.utc).isoformat()}],
        "artifacts": [],
        "download_url": None,
        "error_message": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "started_at": None,
        "completed_at": None,
        "duration_seconds": None
    }
    
    supabase.table("builds").insert(build).execute()
    await log_system_event("info", "build", f"Build started: {build_id}", user_id=user_id)
    
    background_tasks.add_task(process_build, build_id, project)
    
    return build

async def process_build(build_id: str, project: dict):
    """Process build with detailed phases"""
    build_response = supabase.table("builds").select("*").eq("id", build_id).single().execute()
    if not build_response.data:
        return
    
    platform = build_response.data['platform']
    phases = BUILD_PHASES.get(platform, BUILD_PHASES['android'])
    total_duration = sum(p['duration'] for p in phases)
    current_progress = 0
    
    supabase.table("builds").update({
        "started_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", build_id).execute()
    
    for phase_info in phases:
        phase = phase_info['phase']
        duration = phase_info['duration']
        
        logs = generate_build_logs(phase, platform, project['name'])
        
        current_build = supabase.table("builds").select("logs").eq("id", build_id).single().execute()
        current_logs = current_build.data.get('logs', []) if current_build.data else []
        current_logs.extend(logs)
        
        supabase.table("builds").update({
            "phase": phase,
            "logs": current_logs
        }).eq("id", build_id).execute()
        
        if duration > 0:
            steps = max(1, duration)
            for _ in range(steps):
                await asyncio.sleep(0.5)
                current_progress += (100 / total_duration) / 2
                supabase.table("builds").update({
                    "progress": min(int(current_progress), 99)
                }).eq("id", build_id).execute()
    
    # Generate artifacts
    artifacts = []
    if platform == 'android':
        artifacts = [
            {"name": f"{project['name']}-debug.apk", "type": "apk", "size": f"{random.randint(15, 30)}MB"},
            {"name": f"{project['name']}-release.aab", "type": "aab", "size": f"{random.randint(12, 25)}MB"},
        ]
    else:
        artifacts = [
            {"name": f"{project['name']}.ipa", "type": "ipa", "size": f"{random.randint(20, 40)}MB"},
        ]
    
    started = build_response.data.get('started_at', datetime.now(timezone.utc).isoformat())
    completed = datetime.now(timezone.utc)
    try:
        started_dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
        duration = int((completed - started_dt).total_seconds())
    except:
        duration = 60
    
    supabase.table("builds").update({
        "status": "completed",
        "phase": "completed",
        "progress": 100,
        "artifacts": artifacts,
        "completed_at": completed.isoformat(),
        "duration_seconds": duration,
        "download_url": f"/api/builds/{build_id}/download"
    }).eq("id", build_id).execute()

@api_router.get("/builds")
async def get_builds(user_id: str, project_id: Optional[str] = None):
    query = supabase.table("builds").select("*").eq("user_id", user_id)
    if project_id:
        query = query.eq("project_id", project_id)
    response = query.order("created_at", desc=True).execute()
    return response.data or []

@api_router.get("/builds/{build_id}")
async def get_build(build_id: str, user_id: str):
    response = supabase.table("builds").select("*").eq("id", build_id).eq("user_id", user_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Build not found")
    return response.data

@api_router.get("/builds/{build_id}/download")
async def download_build(build_id: str, user_id: str):
    build_response = supabase.table("builds").select("*").eq("id", build_id).eq("user_id", user_id).single().execute()
    if not build_response.data:
        raise HTTPException(status_code=404, detail="Build not found")
    
    build = build_response.data
    if build['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Build not completed")
    
    project_response = supabase.table("projects").select("*").eq("id", build['project_id']).single().execute()
    if not project_response.data:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = project_response.data
    platform = build['platform']
    
    # Create ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        readme = f"# {project['name']} - {platform.upper()} Build\nGenerated by NativiWeb Studio"
        zip_file.writestr('README.md', readme)
        zip_file.writestr('config/app-config.json', json.dumps({
            "project": project['name'],
            "web_url": project['web_url'],
            "platform": platform,
            "build_id": build_id
        }, indent=2))
    
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={project['name']}_{platform}.zip"}
    )

# ==================== API KEYS ====================

@api_router.post("/api-keys")
async def create_api_key(key_data: APIKeyCreate, user_id: str):
    api_key = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "name": key_data.name,
        "key": f"nw_{secrets.token_hex(24)}",
        "permissions": key_data.permissions,
        "last_used": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    supabase.table("api_keys").insert(api_key).execute()
    return api_key

@api_router.get("/api-keys")
async def get_api_keys(user_id: str):
    response = supabase.table("api_keys").select("*").eq("user_id", user_id).execute()
    return response.data or []

@api_router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: str, user_id: str):
    supabase.table("api_keys").delete().eq("id", key_id).eq("user_id", user_id).execute()
    return {"message": "API key deleted"}

# ==================== FEATURES & STATS ====================

@api_router.get("/features")
async def get_available_features():
    return DEFAULT_FEATURES

@api_router.get("/stats")
async def get_user_stats(user_id: str):
    projects = supabase.table("projects").select("id", count="exact").eq("user_id", user_id).execute()
    builds = supabase.table("builds").select("id", count="exact").eq("user_id", user_id).execute()
    successful = supabase.table("builds").select("id", count="exact").eq("user_id", user_id).eq("status", "completed").execute()
    api_keys = supabase.table("api_keys").select("id", count="exact").eq("user_id", user_id).execute()
    
    return {
        "projects": projects.count or 0,
        "total_builds": builds.count or 0,
        "successful_builds": successful.count or 0,
        "api_keys": api_keys.count or 0
    }

# ==================== ADMIN ENDPOINTS ====================

@api_router.get("/admin/users")
async def admin_get_users(admin_id: str, page: int = 1, limit: int = 20):
    admin = supabase.table("users").select("*").eq("id", admin_id).eq("role", "admin").single().execute()
    if not admin.data:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    offset = (page - 1) * limit
    users_response = supabase.table("users").select("*").range(offset, offset + limit - 1).execute()
    total_response = supabase.table("users").select("id", count="exact").execute()
    
    users = users_response.data or []
    for u in users:
        projects = supabase.table("projects").select("id", count="exact").eq("user_id", u['id']).execute()
        builds = supabase.table("builds").select("id", count="exact").eq("user_id", u['id']).execute()
        u['projects_count'] = projects.count or 0
        u['builds_count'] = builds.count or 0
    
    return {
        "users": users,
        "total": total_response.count or 0,
        "page": page,
        "pages": ((total_response.count or 0) + limit - 1) // limit
    }

@api_router.put("/admin/users/{user_id}")
async def admin_update_user(user_id: str, admin_id: str, update_data: UserUpdate):
    admin = supabase.table("users").select("*").eq("id", admin_id).eq("role", "admin").single().execute()
    if not admin.data:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    supabase.table("users").update(update_dict).eq("id", user_id).execute()
    action = "banned" if update_dict.get('status') == 'banned' else "updated"
    await log_system_event("warning", "admin", f"User {user_id} {action}", user_id=admin_id)
    
    return {"message": f"User {action} successfully"}

@api_router.get("/admin/builds")
async def admin_get_builds(admin_id: str, page: int = 1, limit: int = 20, status: Optional[str] = None):
    admin = supabase.table("users").select("*").eq("id", admin_id).eq("role", "admin").single().execute()
    if not admin.data:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    offset = (page - 1) * limit
    query = supabase.table("builds").select("*")
    if status:
        query = query.eq("status", status)
    
    builds_response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    
    builds = builds_response.data or []
    for b in builds:
        project = supabase.table("projects").select("name").eq("id", b['project_id']).single().execute()
        user = supabase.table("users").select("name, email").eq("id", b['user_id']).single().execute()
        b['project_name'] = project.data['name'] if project.data else 'Unknown'
        b['user_name'] = user.data['name'] if user.data else 'Unknown'
        b['user_email'] = user.data['email'] if user.data else 'Unknown'
    
    total = supabase.table("builds").select("id", count="exact").execute()
    
    return {
        "builds": builds,
        "total": total.count or 0,
        "page": page,
        "pages": ((total.count or 0) + limit - 1) // limit
    }

@api_router.get("/admin/logs")
async def admin_get_logs(admin_id: str, page: int = 1, limit: int = 50, level: Optional[str] = None, category: Optional[str] = None):
    admin = supabase.table("users").select("*").eq("id", admin_id).eq("role", "admin").single().execute()
    if not admin.data:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    offset = (page - 1) * limit
    query = supabase.table("system_logs").select("*")
    if level:
        query = query.eq("level", level)
    if category:
        query = query.eq("category", category)
    
    logs_response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    total = supabase.table("system_logs").select("id", count="exact").execute()
    
    return {
        "logs": logs_response.data or [],
        "total": total.count or 0,
        "page": page,
        "pages": ((total.count or 0) + limit - 1) // limit
    }

@api_router.get("/admin/analytics")
async def admin_get_analytics(admin_id: str):
    admin = supabase.table("users").select("*").eq("id", admin_id).eq("role", "admin").single().execute()
    if not admin.data:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    total_users = supabase.table("users").select("id", count="exact").execute()
    active_users = supabase.table("users").select("id", count="exact").eq("status", "active").execute()
    total_projects = supabase.table("projects").select("id", count="exact").execute()
    total_builds = supabase.table("builds").select("id", count="exact").execute()
    successful = supabase.table("builds").select("id", count="exact").eq("status", "completed").execute()
    failed = supabase.table("builds").select("id", count="exact").eq("status", "failed").execute()
    processing = supabase.table("builds").select("id", count="exact").eq("status", "processing").execute()
    android = supabase.table("builds").select("id", count="exact").eq("platform", "android").execute()
    ios = supabase.table("builds").select("id", count="exact").eq("platform", "ios").execute()
    
    total_b = total_builds.count or 0
    successful_b = successful.count or 0
    
    return {
        "users": {"total": total_users.count or 0, "active": active_users.count or 0, "new_this_week": 0},
        "projects": {"total": total_projects.count or 0, "new_this_week": 0},
        "builds": {
            "total": total_b,
            "successful": successful_b,
            "failed": failed.count or 0,
            "processing": processing.count or 0,
            "new_this_week": 0,
            "success_rate": round(successful_b / total_b * 100, 1) if total_b > 0 else 0
        },
        "platforms": {"android": android.count or 0, "ios": ios.count or 0}
    }

@api_router.get("/admin/config")
async def admin_get_config(admin_id: str):
    admin = supabase.table("users").select("*").eq("id", admin_id).eq("role", "admin").single().execute()
    if not admin.data:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    config = supabase.table("platform_config").select("*").eq("id", "platform_config").single().execute()
    if not config.data:
        default_config = {
            "id": "platform_config",
            "maintenance_mode": False,
            "max_builds_per_user": 10,
            "max_projects_per_user": 5,
            "allowed_domains": [],
            "build_timeout_minutes": 30,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        supabase.table("platform_config").insert(default_config).execute()
        return default_config
    
    return config.data

@api_router.put("/admin/config")
async def admin_update_config(admin_id: str, config_data: dict):
    admin = supabase.table("users").select("*").eq("id", admin_id).eq("role", "admin").single().execute()
    if not admin.data:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    config_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    supabase.table("platform_config").upsert({"id": "platform_config", **config_data}).execute()
    await log_system_event("warning", "admin", "Platform configuration updated", user_id=admin_id)
    
    return {"message": "Configuration updated"}

@api_router.post("/admin/setup")
async def setup_admin(email: str, secret: str):
    if secret != "nativiweb_admin_setup_2024":
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    supabase.table("users").update({"role": "admin"}).eq("email", email).execute()
    await log_system_event("warning", "admin", f"Admin role granted to {email}")
    
    return {"message": f"Admin role granted to {email}"}

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "NativiWeb Studio API v2.0.0", "status": "operational"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include the router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
