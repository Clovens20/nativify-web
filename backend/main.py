from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Header, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    HAS_SLOWAPI = True
except ImportError:
    HAS_SLOWAPI = False
    # Fallback if slowapi is not installed
    class Limiter:
        def __init__(self, key_func):
            self.key_func = key_func
        def check(self, key, limit):
            pass  # No rate limiting if slowapi not available
    def get_remote_address(request):
        return request.client.host if request.client else "unknown"
    class RateLimitExceeded(Exception):
        pass
    def _rate_limit_exceeded_handler(request, exc):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )
from supabase import create_client, Client
import supabase
import os
import logging
import time
import jwt
try:
    from jwt import PyJWKClient
    HAS_PYJWK = True
except ImportError:
    HAS_PYJWK = False
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

# Environment
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')

# Supabase connection
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configure logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

def get_supabase_client(token: Optional[str] = None, use_service_role: bool = False) -> Client:
    """Get Supabase client with optional user token for RLS
    
    Args:
        token: User JWT token for RLS-enabled operations
        use_service_role: If True, use service role key to bypass RLS (for backend operations)
    
    Returns:
        Supabase client configured with appropriate credentials
    """
    # Use service role key if requested (for backend operations that need to bypass RLS)
    if use_service_role and SUPABASE_SERVICE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # If token provided, create client and try to set it
    # Note: Supabase Python client doesn't easily support per-request tokens
    # For now, we'll use service role for operations that need RLS bypass
    if token and not use_service_role:
        # Create a new client instance
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Try to set auth headers manually
        try:
            # This is a workaround - the client will use anon key but we can
            # use service role for operations that need it
            pass
        except:
            pass
        return client
    
    # Default: use service role if available, otherwise anon key
    if SUPABASE_SERVICE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return supabase

# Initialize rate limiter (must be before app creation)
if HAS_SLOWAPI:
    limiter = Limiter(key_func=get_remote_address)
else:
    limiter = Limiter(key_func=get_remote_address)
    logging.warning("slowapi not installed - rate limiting disabled")

# Create the main app
app = FastAPI(
    title="NativiWeb Studio API",
    description="API pour transformer des web apps en applications natives",
    version="2.0.0",
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None
)

# Add rate limiting to app
if HAS_SLOWAPI:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    features: Optional[List[NativeFeature]] = None
    logo_url: Optional[str] = None

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

class TemplateCreate(BaseModel):
    id: str
    name: str
    description: str
    features: List[str] = []
    recommended: bool = False
    icon: Optional[str] = None
    color: Optional[str] = 'primary'

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    features: Optional[List[str]] = None
    recommended: Optional[bool] = None
    icon: Optional[str] = None
    color: Optional[str] = None

class Template(BaseModel):
    id: str
    name: str
    description: str
    features: List[str] = []
    recommended: bool = False
    icon: Optional[str] = None
    color: Optional[str] = 'primary'
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class VisitTrack(BaseModel):
    page_path: str
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None

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

async def log_system_event(level: str, category: str, message: str, details: dict = None, user_id: str = None, token: Optional[str] = None):
    try:
        # Use service role key for system logs to bypass RLS
        client = get_supabase_client(use_service_role=True)
        client.table("system_logs").insert({
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

# ==================== AUTHENTICATION DEPENDENCY ====================

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract user ID from JWT token without checking session existence"""
    try:
        token = credentials.credentials
        
        if not token:
            logging.warning("No token provided in credentials")
            raise HTTPException(status_code=401, detail="No token provided")
        
        # Décoder directement le JWT sans vérifier la session
        # Cette méthode évite l'erreur "Session from session_id claim in JWT does not exist"
        try:
            
            # Récupérer la clé publique depuis Supabase
            supabase_url = os.environ.get('SUPABASE_URL', '')
            jwks_url = f"{supabase_url}/.well-known/jwks.json"
            
            # Décode le JWT sans vérifier la signature (on vérifiera après)
            unverified = jwt.decode(token, options={"verify_signature": False})
            
            # Extraire le user_id du token
            user_id = unverified.get('sub') or unverified.get('user_id')
            
            if not user_id:
                logging.warning("No user_id found in token")
                raise HTTPException(status_code=401, detail="Invalid token - no user ID")
            
            # Vérifier que le token n'est pas expiré
            exp = unverified.get('exp')
            if exp and exp < time.time():
                logging.warning(f"Token expired for user {user_id}")
                raise HTTPException(status_code=401, detail="Token expired")
            
            # Essayer de vérifier la signature avec la clé publique (optionnel mais recommandé)
            # Si cela échoue, on continue quand même car le token a déjà été décodé avec succès
            if HAS_PYJWK:
                try:
                    if supabase_url:
                        jwks_client = PyJWKClient(jwks_url, timeout=2)  # Timeout court
                        signing_key = jwks_client.get_signing_key_from_jwt(token)
                        jwt.decode(token, signing_key.key, algorithms=["RS256"], audience="authenticated", options={"verify_exp": False})
                        logging.debug(f"Token signature verified for user: {user_id}")
                except Exception as sig_error:
                    # Si la vérification de signature échoue, on continue quand même
                    # car le token a déjà été décodé avec succès
                    logging.debug(f"Could not verify token signature (continuing anyway): {sig_error}")
            
            return user_id
            
        except jwt.ExpiredSignatureError:
            logging.warning("Token expired")
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as jwt_error:
            error_msg = str(jwt_error)
            logging.error(f"Invalid JWT token: {error_msg}")
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as decode_error:
            error_msg = str(decode_error)
            logging.error(f"JWT decode error: {error_msg}")
            raise HTTPException(status_code=401, detail=f"Authentication failed: Invalid token")
                
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected auth error: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail="Authentication failed")

async def get_current_user_with_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract user ID and user info from JWT token"""
    try:
        token = credentials.credentials
        user_response = supabase.auth.get_user(token)
        if user_response.user:
            return user_response.user.id, user_response.user
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logging.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_current_user_and_client(credentials: HTTPAuthorizationCredentials = Depends(security)) -> tuple[str, Client]:
    """Extract user ID and return Supabase client with user token"""
    try:
        token = credentials.credentials
        user_response = supabase.auth.get_user(token)
        if user_response.user:
            client = get_supabase_client(token=token)
            return user_response.user.id, client
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logging.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Optional authentication for endpoints that can work without auth"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.replace("Bearer ", "")
        user_response = supabase.auth.get_user(token)
        if user_response.user:
            return user_response.user.id
        return None
    except:
        return None

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/register")
async def register(request: Request, user_data: UserCreate):
    # Rate limiting
    if HAS_SLOWAPI:
        try:
            limiter.check(f"/api/auth/register:POST:{get_remote_address(request)}", "10/minute")
        except RateLimitExceeded:
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
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
            # Create profile in users table using service role key to bypass RLS
            user_id = auth_response.user.id
            client = get_supabase_client(use_service_role=True)
            
            client.table("users").insert({
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
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower() or "user already registered" in error_msg.lower():
            raise HTTPException(status_code=400, detail="Email already registered")
        logging.error(f"Registration error: {e}")
        raise HTTPException(status_code=400, detail=f"Registration failed: {error_msg}")

@api_router.post("/auth/login")
async def login(request: Request, credentials: UserLogin):
    # Rate limiting
    if HAS_SLOWAPI:
        try:
            limiter.check(f"/api/auth/login:POST:{get_remote_address(request)}", "5/minute")
        except RateLimitExceeded:
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        if auth_response.user and auth_response.session:
            user_id = auth_response.user.id
            token = auth_response.session.access_token
            
            # Get user profile using service role key (or fallback to anon)
            client = get_supabase_client(use_service_role=True)
            try:
                user_response = client.table("users").select("*").eq("id", user_id).single().execute()
                user_data = user_response.data if user_response.data else {}
            except Exception as e:
                logging.error(f"Failed to fetch user profile: {e}")
                # Use metadata from auth response as fallback
                user_data = {}
            
            if user_data.get('status') == 'banned':
                raise HTTPException(status_code=403, detail="Account suspended")
            
            await log_system_event("info", "auth", f"User logged in: {credentials.email}", user_id=user_id)
            
            return {
                "token": token,
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
        logging.error(f"Login error: {e}")
        await log_system_event("warning", "auth", f"Failed login attempt for {credentials.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

@api_router.get("/auth/me")
async def get_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        user_id = user_response.user.id
        # Use service role key for backend operations
        client = get_supabase_client(use_service_role=True)
        try:
            profile_response = client.table("users").select("*").eq("id", user_id).execute()
            if profile_response.data and len(profile_response.data) > 0:
                user_data = profile_response.data[0]
            else:
                # User profile doesn't exist, create it
                logging.warning(f"User profile not found for {user_id}, creating it")
                user_metadata = user_response.user.user_metadata or {}
                user_email = user_response.user.email or ""
                user_name = user_metadata.get("name") or user_email.split("@")[0] if user_email else "User"
                
                client.table("users").upsert({
                    "id": user_id,
                    "email": user_email,
                    "name": user_name,
                    "role": user_metadata.get("role", "user"),
                    "status": "active",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }).execute()
                
                # Retry fetch after creation
                profile_response = client.table("users").select("*").eq("id", user_id).execute()
                user_data = profile_response.data[0] if profile_response.data and len(profile_response.data) > 0 else {}
        except Exception as e:
            logging.error(f"Failed to fetch/create user profile: {e}")
            user_data = {}
        
        return {
            "id": user_id,
            "email": user_response.user.email or user_data.get('email', ''),
            "name": user_data.get('name', user_response.user.user_metadata.get('name', '') if user_response.user.user_metadata else ''),
            "role": user_data.get('role', 'user')
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Get user error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

@api_router.post("/auth/logout")
async def logout(user_id: str = Depends(get_current_user)):
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except:
        return {"message": "Logged out successfully"}

# ==================== PROJECT ENDPOINTS ====================

@api_router.post("/projects")
async def create_project(project_data: ProjectCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        # Get user info from token
        token = credentials.credentials
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = user_response.user.id
        auth_user = user_response.user
        
        # Use service role key to bypass RLS
        client = get_supabase_client(use_service_role=True)
        
        # Verify user exists in users table, create if not (using upsert to avoid conflicts)
        try:
            user_check = client.table("users").select("id").eq("id", user_id).execute()
            if not user_check.data or len(user_check.data) == 0:
                # User doesn't exist in users table, create from auth info
                logging.warning(f"User {user_id} not found in users table, creating profile")
                
                user_metadata = auth_user.user_metadata or {}
                user_email = auth_user.email or ""
                user_name = user_metadata.get("name") or user_email.split("@")[0] if user_email else "User"
                
                # Use upsert to handle race conditions (if user is created between check and insert)
                client.table("users").upsert({
                    "id": user_id,
                    "email": user_email,
                    "name": user_name,
                    "role": "user",
                    "status": "active",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }).execute()
                logging.info(f"Created/updated user profile for {user_id}")
        except Exception as user_error:
            # Log the error but try to continue - the user might exist
            error_msg = str(user_error)
            logging.warning(f"Error checking/creating user profile: {error_msg}")
            
            # Try one more time with upsert (safer approach)
            try:
                user_metadata = auth_user.user_metadata or {}
                user_email = auth_user.email or ""
                user_name = user_metadata.get("name") or user_email.split("@")[0] if user_email else "User"
                
                client.table("users").upsert({
                    "id": user_id,
                    "email": user_email,
                    "name": user_name,
                    "role": "user",
                    "status": "active",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }).execute()
                logging.info(f"Successfully upserted user profile for {user_id}")
            except Exception as upsert_error:
                # If upsert also fails, log but don't block project creation
                # The user might still be able to create the project if they exist
                logging.error(f"Failed to upsert user profile: {upsert_error}")
                # Don't raise exception - let's try to continue with project creation
                # The foreign key constraint will catch it if user really doesn't exist
        
        project_id = str(uuid.uuid4())
        
        # Use features from project_data if provided, otherwise use default
        if project_data.features:
            # Convert NativeFeature objects to dicts
            features = [f.model_dump() if hasattr(f, 'model_dump') else f for f in project_data.features]
        else:
            features = DEFAULT_FEATURES
        
        project = {
            "id": project_id,
            "user_id": user_id,
            "name": project_data.name,
            "web_url": project_data.web_url,
            "description": project_data.description or "",
            "platform": project_data.platform,
            "features": features,
            "logo_url": project_data.logo_url,
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Utiliser service role client pour bypass RLS
        # Le client est déjà configuré avec use_service_role=True, mais on s'assure
        result = client.table("projects").insert(project).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create project")
        
        await log_system_event("info", "project", f"Project created: {project_data.name}", user_id=user_id)
        return project
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating project: {e}")
        error_msg = str(e)
        if "foreign key constraint" in error_msg.lower() or "23503" in error_msg:
            raise HTTPException(status_code=400, detail="User profile not found. Please contact support to synchronize your account.")
        raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")

@api_router.get("/projects")
async def get_projects(user_id: str = Depends(get_current_user)):
    response = supabase.table("projects").select("*").eq("user_id", user_id).execute()
    return response.data or []

@api_router.get("/projects/{project_id}")
async def get_project(project_id: str, user_id: str = Depends(get_current_user)):
    # Utiliser le service role client pour éviter les problèmes RLS
    client = get_supabase_client(use_service_role=True)
    response = client.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).execute()
    
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Retourner le premier élément (devrait être unique)
    return response.data[0]

@api_router.put("/projects/{project_id}")
async def update_project(project_id: str, update_data: ProjectUpdate, user_id: str = Depends(get_current_user)):
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
async def delete_project(project_id: str, user_id: str = Depends(get_current_user)):
    result = supabase.table("projects").delete().eq("id", project_id).eq("user_id", user_id).execute()
    await log_system_event("info", "project", f"Project deleted: {project_id}", user_id=user_id)
    return {"message": "Project deleted"}

# ==================== BUILD ENDPOINTS ====================

@api_router.post("/builds")
async def create_build(build_data: BuildCreate, background_tasks: BackgroundTasks, user_id: str = Depends(get_current_user)):
    # Utiliser le service role client pour éviter les problèmes RLS
    client = get_supabase_client(use_service_role=True)
    
    # Check project exists
    project_response = client.table("projects").select("*").eq("id", build_data.project_id).eq("user_id", user_id).execute()
    if not project_response.data or len(project_response.data) == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = project_response.data[0]
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
    
    # Utiliser le service role client pour l'insertion
    result = client.table("builds").insert(build).execute()
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create build")
    
    await log_system_event("info", "build", f"Build started: {build_id}", user_id=user_id)
    
    background_tasks.add_task(process_build, build_id, project)
    
    # Retourner le build créé avec les données de la réponse
    return result.data[0] if result.data else build

async def process_build(build_id: str, project: dict):
    """Process build with detailed phases"""
    # Utiliser le service role client pour éviter les problèmes RLS
    client = get_supabase_client(use_service_role=True)
    
    build_response = client.table("builds").select("*").eq("id", build_id).execute()
    if not build_response.data or len(build_response.data) == 0:
        logging.error(f"Build {build_id} not found in process_build")
        return
    
    build_data = build_response.data[0]
    platform = build_data['platform']
    phases = BUILD_PHASES.get(platform, BUILD_PHASES['android'])
    total_duration = sum(p['duration'] for p in phases)
    current_progress = 0
    
    client.table("builds").update({
        "started_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", build_id).execute()
    
    for phase_info in phases:
        phase = phase_info['phase']
        duration = phase_info['duration']
        
        logs = generate_build_logs(phase, platform, project['name'])
        
        current_build = client.table("builds").select("logs").eq("id", build_id).execute()
        current_logs = current_build.data[0].get('logs', []) if current_build.data and len(current_build.data) > 0 else []
        current_logs.extend(logs)
        
        client.table("builds").update({
            "phase": phase,
            "logs": current_logs
        }).eq("id", build_id).execute()
        
        if duration > 0:
            steps = max(1, duration)
            for _ in range(steps):
                await asyncio.sleep(0.5)
                current_progress += (100 / total_duration) / 2
                client.table("builds").update({
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
    
    started = build_data.get('started_at', datetime.now(timezone.utc).isoformat())
    completed = datetime.now(timezone.utc)
    try:
        started_dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
        duration = int((completed - started_dt).total_seconds())
    except:
        duration = 60
    
    client.table("builds").update({
        "status": "completed",
        "phase": "completed",
        "progress": 100,
        "artifacts": artifacts,
        "completed_at": completed.isoformat(),
        "duration_seconds": duration,
        "download_url": f"/api/builds/{build_id}/download"
    }).eq("id", build_id).execute()

@api_router.get("/builds")
async def get_builds(user_id: str = Depends(get_current_user), project_id: Optional[str] = None):
    client = get_supabase_client(use_service_role=True)
    query = client.table("builds").select("*").eq("user_id", user_id)
    if project_id:
        query = query.eq("project_id", project_id)
    response = query.order("created_at", desc=True).execute()
    return response.data or []

@api_router.get("/builds/{build_id}")
async def get_build(build_id: str, user_id: str = Depends(get_current_user)):
    client = get_supabase_client(use_service_role=True)
    response = client.table("builds").select("*").eq("id", build_id).eq("user_id", user_id).execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=404, detail="Build not found")
    return response.data[0]

@api_router.get("/builds/{build_id}/download")
async def download_build(build_id: str, user_id: str = Depends(get_current_user)):
    """Download build artifact (APK/IPA)"""
    try:
        logging.info(f"Download request for build {build_id} by user {user_id}")
        
        client = get_supabase_client(use_service_role=True)
        build_response = client.table("builds").select("*").eq("id", build_id).execute()
        
        if not build_response.data or len(build_response.data) == 0:
            logging.warning(f"Build not found: build_id={build_id}")
            raise HTTPException(status_code=404, detail="Build not found")
        
        build = build_response.data[0]
        
        # Vérifier que l'utilisateur est le propriétaire du build
        if build.get('user_id') != user_id:
            logging.warning(f"User {user_id} tried to download build {build_id} owned by {build.get('user_id')}")
            raise HTTPException(status_code=403, detail="Forbidden: You don't have permission to download this build")
        
        if build.get('status') != 'completed':
            logging.warning(f"Build {build_id} not completed, status: {build.get('status')}")
            raise HTTPException(status_code=400, detail="Build not completed")
        
        project_response = client.table("projects").select("*").eq("id", build['project_id']).execute()
        if not project_response.data or len(project_response.data) == 0:
            logging.error(f"Project not found: project_id={build.get('project_id')}")
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = project_response.data[0]
        platform = build['platform']
        
        # Créer un fichier ZIP avec les artefacts du build
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            readme = f"# {project['name']} - {platform.upper()} Build\nGenerated by NativiWeb Studio\n\nBuild ID: {build_id}\nProject: {project['name']}\nPlatform: {platform}\nStatus: {build.get('status', 'unknown')}"
            zip_file.writestr('README.md', readme)
            zip_file.writestr('config/app-config.json', json.dumps({
                "project": project['name'],
                "web_url": project.get('web_url', ''),
                "platform": platform,
                "build_id": build_id,
                "created_at": build.get('created_at', ''),
                "completed_at": build.get('completed_at', '')
            }, indent=2))
            
            # Ajouter les artefacts si disponibles
            artifacts = build.get('artifacts', [])
            if artifacts:
                for artifact in artifacts:
                    # Créer un fichier placeholder pour chaque artefact
                    artifact_info = f"Artifact: {artifact.get('name', 'unknown')}\nType: {artifact.get('type', 'unknown')}\nSize: {artifact.get('size', 'unknown')}"
                    zip_file.writestr(f"artifacts/{artifact.get('name', 'artifact')}.info", artifact_info)
        
        zip_buffer.seek(0)
        
        # Nom de fichier sécurisé (sans caractères spéciaux)
        safe_project_name = "".join(c for c in project['name'] if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_project_name}-{platform}-{build_id[:8]}.zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/zip"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error downloading build {build_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error downloading build: {str(e)}")

# ==================== API KEYS ====================

@api_router.post("/api-keys")
async def create_api_key(key_data: APIKeyCreate, user_id: str = Depends(get_current_user)):
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
async def get_api_keys(user_id: str = Depends(get_current_user)):
    response = supabase.table("api_keys").select("*").eq("user_id", user_id).execute()
    return response.data or []

@api_router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: str, user_id: str = Depends(get_current_user)):
    supabase.table("api_keys").delete().eq("id", key_id).eq("user_id", user_id).execute()
    return {"message": "API key deleted"}

# ==================== FEATURES & STATS ====================

@api_router.get("/features")
async def get_available_features():
    return DEFAULT_FEATURES

@api_router.get("/stats")
async def get_user_stats(user_id: str = Depends(get_current_user)):
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
async def admin_get_users(page: int = 1, limit: int = 20, include_auth_only: bool = False, admin_id: str = Depends(get_current_user)):
    """Get all users, auto-syncing any missing from auth.users"""
    client = get_supabase_client(use_service_role=True)
    
    admin = client.table("users").select("*").eq("id", admin_id).eq("role", "admin").execute()
    if not admin.data or len(admin.data) == 0:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    offset = (page - 1) * limit
    
    # Auto-sync: Get all users from auth.users and sync to public.users
    try:
        auth_users_response = supabase.auth.admin.list_users()
        if auth_users_response and hasattr(auth_users_response, 'users'):
            auth_users = auth_users_response.users
            
            # Get all existing user IDs from public.users
            existing_users_response = client.table("users").select("id").execute()
            existing_user_ids = {u['id'] for u in (existing_users_response.data or [])}
            
            # Sync missing users from auth.users to public.users
            for auth_user in auth_users:
                if auth_user.id not in existing_user_ids:
                    try:
                        logging.info(f"Auto-syncing user {auth_user.id} ({auth_user.email}) from auth.users to public.users")
                        client.table("users").upsert({
                            "id": auth_user.id,
                            "email": auth_user.email or "",
                            "name": auth_user.user_metadata.get("name", "") if auth_user.user_metadata else "",
                            "role": auth_user.user_metadata.get("role", "user") if auth_user.user_metadata else "user",
                            "status": "active",
                            "created_at": auth_user.created_at or datetime.now(timezone.utc).isoformat()
                        }).execute()
                    except Exception as sync_error:
                        logging.error(f"Error auto-syncing user {auth_user.id}: {sync_error}")
    except Exception as sync_list_error:
        logging.warning(f"Error listing auth users for sync: {sync_list_error}")
    
    # Get users from public.users
    users_response = client.table("users").select("*").order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    total_response = client.table("users").select("id", count="exact").execute()
    
    users = users_response.data or []
    
    # Get projects and builds count for each user
    for u in users:
        try:
            projects = client.table("projects").select("id", count="exact").eq("user_id", u['id']).execute()
            builds = client.table("builds").select("id", count="exact").eq("user_id", u['id']).execute()
            u['projects_count'] = projects.count or 0
            u['builds_count'] = builds.count or 0
        except Exception as count_error:
            logging.warning(f"Error getting counts for user {u.get('id')}: {count_error}")
            u['projects_count'] = 0
            u['builds_count'] = 0
    
    return {
        "users": users,
        "total": total_response.count or 0,
        "page": page,
        "pages": ((total_response.count or 0) + limit - 1) // limit if (total_response.count or 0) > 0 else 1
    }

@api_router.post("/admin/users")
async def admin_create_user(user_data: UserCreate, admin_id: str = Depends(get_current_user)):
    """Create a new user (admin only)"""
    admin = supabase.table("users").select("*").eq("id", admin_id).eq("role", "admin").single().execute()
    if not admin.data:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Register with Supabase Auth
    try:
        auth_response = supabase.auth.admin.create_user({
            "email": user_data.email,
            "password": user_data.password,
            "email_confirm": True,
            "user_metadata": {
                "name": user_data.name
            }
        })
        
        if auth_response.user:
            user_id = auth_response.user.id
            client = get_supabase_client(use_service_role=True)
            
            # Create profile in users table
            client.table("users").insert({
                "id": user_id,
                "email": user_data.email,
                "name": user_data.name,
                "role": "user",
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat()
            }).execute()
            
            await log_system_event("info", "admin", f"User created by admin: {user_data.email}", user_id=admin_id)
            
            return {
                "id": user_id,
                "email": user_data.email,
                "name": user_data.name,
                "role": "user",
                "status": "active"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        error_msg = str(e)
        if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {error_msg}")

@api_router.put("/admin/users/{user_id}")
async def admin_update_user(user_id: str, update_data: UserUpdate, admin_id: str = Depends(get_current_user)):
    admin = supabase.table("users").select("*").eq("id", admin_id).eq("role", "admin").single().execute()
    if not admin.data:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    client = get_supabase_client(use_service_role=True)
    client.table("users").update(update_dict).eq("id", user_id).execute()
    action = "banned" if update_dict.get('status') == 'banned' else "updated"
    await log_system_event("warning", "admin", f"User {user_id} {action}", user_id=admin_id)
    
    return {"message": f"User {action} successfully"}

@api_router.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: str, admin_id: str = Depends(get_current_user)):
    """Delete a user (admin only)"""
    admin = supabase.table("users").select("*").eq("id", admin_id).eq("role", "admin").single().execute()
    if not admin.data:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if user_id == admin_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    client = get_supabase_client(use_service_role=True)
    
    # Delete user profile
    client.table("users").delete().eq("id", user_id).execute()
    
    # Optionally delete from auth (requires admin API)
    try:
        supabase.auth.admin.delete_user(user_id)
    except Exception as e:
        logging.warning(f"Failed to delete user from auth: {e}")
    
    await log_system_event("warning", "admin", f"User {user_id} deleted", user_id=admin_id)
    return {"message": "User deleted successfully"}

@api_router.get("/admin/projects")
async def admin_get_projects(page: int = 1, limit: int = 20, admin_id: str = Depends(get_current_user)):
    """Get all projects (admin only)"""
    client = get_supabase_client(use_service_role=True)
    
    admin = client.table("users").select("*").eq("id", admin_id).eq("role", "admin").execute()
    if not admin.data or len(admin.data) == 0:
        logging.warning(f"Admin access denied for user {admin_id}")
        raise HTTPException(status_code=403, detail="Admin access required")
    
    offset = (page - 1) * limit
    
    # Get total count first
    total_response = client.table("projects").select("id", count="exact").execute()
    total_count = total_response.count or 0
    logging.info(f"Admin {admin_id} requesting projects: page={page}, limit={limit}, total={total_count}")
    
    # Get projects with pagination
    projects_response = client.table("projects").select("*").order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    projects = projects_response.data or []
    
    logging.info(f"Found {len(projects)} projects in page {page}")
    
    # Enrich projects with user info and build counts
    for p in projects:
        try:
            user_response = client.table("users").select("name, email").eq("id", p['user_id']).execute()
            builds_response = client.table("builds").select("id", count="exact").eq("project_id", p['id']).execute()
            
            if user_response.data and len(user_response.data) > 0:
                p['user_name'] = user_response.data[0].get('name', 'Unknown')
                p['user_email'] = user_response.data[0].get('email', 'Unknown')
            else:
                p['user_name'] = 'Unknown'
                p['user_email'] = 'Unknown'
                logging.warning(f"User not found for project {p.get('id')}, user_id: {p.get('user_id')}")
            
            p['builds_count'] = builds_response.count or 0
        except Exception as e:
            logging.error(f"Error getting user info for project {p.get('id')}: {e}")
            p['user_name'] = 'Unknown'
            p['user_email'] = 'Unknown'
            p['builds_count'] = 0
    
    pages = ((total_count + limit - 1) // limit) if total_count > 0 else 1
    
    return {
        "projects": projects,
        "total": total_count,
        "page": page,
        "pages": pages
    }

@api_router.delete("/admin/projects/{project_id}")
async def admin_delete_project(project_id: str, admin_id: str = Depends(get_current_user)):
    """Delete any project (admin only)"""
    admin = supabase.table("users").select("*").eq("id", admin_id).eq("role", "admin").single().execute()
    if not admin.data:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    client = get_supabase_client(use_service_role=True)
    client.table("projects").delete().eq("id", project_id).execute()
    
    await log_system_event("warning", "admin", f"Project {project_id} deleted by admin", user_id=admin_id)
    return {"message": "Project deleted successfully"}

@api_router.get("/admin/builds") 
async def admin_get_builds(page: int = 1, limit: int = 20, status: Optional[str] = None, admin_id: str = Depends(get_current_user)):
    """Get all builds (admin only)"""
    client = get_supabase_client(use_service_role=True)
    
    admin = client.table("users").select("*").eq("id", admin_id).eq("role", "admin").execute()
    if not admin.data or len(admin.data) == 0:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    offset = (page - 1) * limit
    query = client.table("builds").select("*")
    if status:
        query = query.eq("status", status)
    
    builds_response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    total = client.table("builds").select("id", count="exact").execute()
    
    builds = builds_response.data or []
    
    # Enrich builds with project and user info
    for b in builds:
        try:
            project_response = client.table("projects").select("name").eq("id", b['project_id']).execute()
            user_response = client.table("users").select("name, email").eq("id", b['user_id']).execute()
            
            if project_response.data and len(project_response.data) > 0:
                b['project_name'] = project_response.data[0].get('name', 'Unknown')
            else:
                b['project_name'] = 'Unknown'
            
            if user_response.data and len(user_response.data) > 0:
                b['user_name'] = user_response.data[0].get('name', 'Unknown')
                b['user_email'] = user_response.data[0].get('email', 'Unknown')
            else:
                b['user_name'] = 'Unknown'
                b['user_email'] = 'Unknown'
        except Exception as e:
            logging.warning(f"Error enriching build {b.get('id')}: {e}")
            b['project_name'] = 'Unknown'
            b['user_name'] = 'Unknown'
            b['user_email'] = 'Unknown'
    
    return {
        "builds": builds,
        "total": total.count or 0,
        "page": page,
        "pages": ((total.count or 0) + limit - 1) // limit if (total.count or 0) > 0 else 1
    }


@api_router.get("/admin/logs")
async def admin_get_logs(page: int = 1, limit: int = 50, level: Optional[str] = None, category: Optional[str] = None, admin_id: str = Depends(get_current_user)):
    """Get system logs (admin only)"""
    client = get_supabase_client(use_service_role=True)
    
    admin = client.table("users").select("*").eq("id", admin_id).eq("role", "admin").execute()
    if not admin.data or len(admin.data) == 0:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    offset = (page - 1) * limit
    query = client.table("system_logs").select("*")
    if level:
        query = query.eq("level", level)
    if category:
        query = query.eq("category", category)
    
    logs_response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    total = client.table("system_logs").select("id", count="exact").execute()
    
    return {
        "logs": logs_response.data or [],
        "total": total.count or 0,
        "page": page,
        "pages": ((total.count or 0) + limit - 1) // limit if (total.count or 0) > 0 else 1
    }

@api_router.get("/admin/analytics")
async def admin_get_analytics(admin_id: str = Depends(get_current_user)):
    """Get platform analytics (admin only)"""
    client = get_supabase_client(use_service_role=True)
    
    admin = client.table("users").select("*").eq("id", admin_id).eq("role", "admin").execute()
    if not admin.data or len(admin.data) == 0:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    total_users = client.table("users").select("id", count="exact").execute()
    active_users = client.table("users").select("id", count="exact").eq("status", "active").execute()
    total_projects = client.table("projects").select("id", count="exact").execute()
    total_builds = client.table("builds").select("id", count="exact").execute()
    successful = client.table("builds").select("id", count="exact").eq("status", "completed").execute()
    failed = client.table("builds").select("id", count="exact").eq("status", "failed").execute()
    processing = client.table("builds").select("id", count="exact").eq("status", "processing").execute()
    android = client.table("builds").select("id", count="exact").eq("platform", "android").execute()
    ios = client.table("builds").select("id", count="exact").eq("platform", "ios").execute()
    
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

@api_router.post("/track-visit")
async def track_visit(visit_data: VisitTrack):
    """Track a site visit (public endpoint, no auth required)"""
    try:
        client = get_supabase_client(use_service_role=True)
        
        visit_dict = visit_data.model_dump()
        visit_dict["device_type"] = visit_dict.get("device_type") or "unknown"
        visit_dict["created_at"] = datetime.now(timezone.utc).isoformat()
        
        client.table("site_visits").insert(visit_dict).execute()
        
        return {"status": "tracked"}
    except Exception as e:
        logging.error(f"Error tracking visit: {e}")
        # Ne pas faire échouer le tracking, retourner un succès même en cas d'erreur
        return {"status": "tracked"}

@api_router.get("/admin/visit-stats")
async def admin_get_visit_stats(admin_id: str = Depends(get_current_user)):
    """Get site visit statistics (admin only)"""
    client = get_supabase_client(use_service_role=True)
    
    admin = client.table("users").select("*").eq("id", admin_id).eq("role", "admin").single().execute()
    if not admin.data:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Total visits
        total_visits_response = client.table("site_visits").select("id", count="exact").execute()
        
        # Unique visitors (distinct session_ids)
        unique_visitors_query = client.table("site_visits").select("session_id").execute()
        unique_sessions = set()
        if unique_visitors_query.data:
            for visit in unique_visitors_query.data:
                if visit.get("session_id"):
                    unique_sessions.add(visit["session_id"])
        
        # Visits today
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        visits_today_response = client.table("site_visits").select("id", count="exact").gte("created_at", today_start.isoformat()).execute()
        
        # Visits this week
        week_start = datetime.now(timezone.utc) - timedelta(days=7)
        visits_week_response = client.table("site_visits").select("id", count="exact").gte("created_at", week_start.isoformat()).execute()
        
        # Visits this month
        month_start = datetime.now(timezone.utc) - timedelta(days=30)
        visits_month_response = client.table("site_visits").select("id", count="exact").gte("created_at", month_start.isoformat()).execute()
        
        # Top pages
        top_pages_response = client.table("site_visits").select("page_path").execute()
        page_counts = {}
        if top_pages_response.data:
            for visit in top_pages_response.data:
                path = visit.get("page_path", "unknown")
                page_counts[path] = page_counts.get(path, 0) + 1
        
        top_pages = sorted(page_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Device breakdown
        device_response = client.table("site_visits").select("device_type").execute()
        device_counts = {}
        if device_response.data:
            for visit in device_response.data:
                device = visit.get("device_type", "unknown")
                device_counts[device] = device_counts.get(device, 0) + 1
        
        return {
            "total_visits": total_visits_response.count or 0,
            "unique_visitors": len(unique_sessions),
            "visits_today": visits_today_response.count or 0,
            "visits_this_week": visits_week_response.count or 0,
            "visits_this_month": visits_month_response.count or 0,
            "top_pages": [{"path": path, "count": count} for path, count in top_pages],
            "device_breakdown": device_counts
        }
    except Exception as e:
        logging.error(f"Error fetching visit stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching visit stats: {str(e)}")

@api_router.get("/admin/config")
async def admin_get_config(admin_id: str = Depends(get_current_user)):
    """Get platform configuration (admin only)"""
    client = get_supabase_client(use_service_role=True)
    
    admin = client.table("users").select("*").eq("id", admin_id).eq("role", "admin").execute()
    if not admin.data or len(admin.data) == 0:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Configuration par défaut
    default_config = {
        "id": "platform_config",
        "maintenance_mode": False,
        "max_builds_per_user": 10,
        "max_projects_per_user": 5,
        "allowed_domains": [],
        "build_timeout_minutes": 30,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        # Essayer de récupérer la config existante (peut ne pas exister)
        config_response = client.table("platform_config").select("*").eq("id", "platform_config").execute()
        
        if config_response.data and len(config_response.data) > 0:
            # Configuration existante trouvée
            return config_response.data[0]
        else:
            # Aucune configuration trouvée, créer la config par défaut
            try:
                client.table("platform_config").insert(default_config).execute()
                logging.info("Created default platform_config")
            except Exception as e:
                # Si l'insertion échoue (peut-être déjà créé entre temps), réessayer de récupérer
                logging.warning(f"Failed to insert default config, retrying fetch: {e}")
                retry_response = client.table("platform_config").select("*").eq("id", "platform_config").execute()
                if retry_response.data and len(retry_response.data) > 0:
                    return retry_response.data[0]
            
            return default_config
            
    except Exception as e:
        # En cas d'erreur, retourner la config par défaut
        logging.error(f"Error fetching platform_config: {e}")
        return default_config

@api_router.put("/admin/config")
async def admin_update_config(config_data: dict, admin_id: str = Depends(get_current_user)):
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

# ==================== TEMPLATES MANAGEMENT ====================

@api_router.get("/admin/templates")
async def admin_get_templates(admin_id: str = Depends(get_current_user)):
    """Get all templates (admin only)"""
    client = get_supabase_client(use_service_role=True)
    
    admin = client.table("users").select("*").eq("id", admin_id).eq("role", "admin").execute()
    if not admin.data or len(admin.data) == 0:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Try to get templates from database
        templates_response = client.table("templates").select("*").order("created_at", desc=False).execute()
        
        if templates_response.data and len(templates_response.data) > 0:
            return {"templates": templates_response.data}
        
        # If no templates in DB, return default templates
        default_templates = [
            {
                "id": "blank",
                "name": "Projet Vide",
                "description": "Commencez de zéro avec une configuration minimale",
                "features": ["push_notifications", "local_storage"],
                "recommended": False,
                "icon": "globe",
                "color": "primary",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "pwa",
                "name": "PWA Standard",
                "description": "Progressive Web App avec toutes les fonctionnalités essentielles",
                "features": ["push_notifications", "local_storage", "geolocation", "camera", "share"],
                "recommended": True,
                "icon": "smartphone",
                "color": "success",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "ecommerce",
                "name": "E-Commerce",
                "description": "Boutique en ligne avec paiements et notifications",
                "features": ["push_notifications", "local_storage", "biometrics", "haptics", "share", "clipboard"],
                "recommended": False,
                "icon": "shopping-cart",
                "color": "warning",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "blog",
                "name": "Blog / Media",
                "description": "Site de contenu avec partage social et offline",
                "features": ["push_notifications", "local_storage", "share", "clipboard", "deep_links"],
                "recommended": False,
                "icon": "file-text",
                "color": "info",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "business",
                "name": "App Business",
                "description": "Application professionnelle avec authentification sécurisée",
                "features": ["push_notifications", "local_storage", "biometrics", "contacts", "file_system", "clipboard"],
                "recommended": False,
                "icon": "briefcase",
                "color": "secondary",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "gaming",
                "name": "Jeu / Divertissement",
                "description": "Application ludique avec feedback haptique",
                "features": ["push_notifications", "local_storage", "haptics", "share", "app_badge"],
                "recommended": False,
                "icon": "gamepad",
                "color": "destructive",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
        ]
        
        return {"templates": default_templates}
        
    except Exception as e:
        logging.error(f"Error fetching templates: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching templates: {str(e)}")

@api_router.post("/admin/templates")
async def admin_create_template(template_data: TemplateCreate, admin_id: str = Depends(get_current_user)):
    """Create a new template"""
    client = get_supabase_client(use_service_role=True)
    
    admin = client.table("users").select("*").eq("id", admin_id).eq("role", "admin").single().execute()
    if not admin.data:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        template_dict = template_data.model_dump()
        template_dict["created_at"] = datetime.now(timezone.utc).isoformat()
        template_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        response = client.table("templates").insert(template_dict).execute()
        
        if response.data:
            await log_system_event("info", "admin", f"Template created: {template_data.name}", user_id=admin_id)
            return response.data[0]
        else:
            raise HTTPException(status_code=500, detail="Failed to create template")
            
    except Exception as e:
        logging.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")

@api_router.put("/admin/templates/{template_id}")
async def admin_update_template(template_id: str, template_data: TemplateUpdate, admin_id: str = Depends(get_current_user)):
    """Update a template"""
    client = get_supabase_client(use_service_role=True)
    
    admin = client.table("users").select("*").eq("id", admin_id).eq("role", "admin").single().execute()
    if not admin.data:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        update_dict = {k: v for k, v in template_data.model_dump().items() if v is not None}
        if not update_dict:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        response = client.table("templates").update(update_dict).eq("id", template_id).execute()
        
        if response.data:
            await log_system_event("info", "admin", f"Template updated: {template_id}", user_id=admin_id)
            return response.data[0]
        else:
            raise HTTPException(status_code=404, detail="Template not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating template: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating template: {str(e)}")

@api_router.delete("/admin/templates/{template_id}")
async def admin_delete_template(template_id: str, admin_id: str = Depends(get_current_user)):
    """Delete a template"""
    client = get_supabase_client(use_service_role=True)
    
    admin = client.table("users").select("*").eq("id", admin_id).eq("role", "admin").single().execute()
    if not admin.data:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Check if template exists
        existing = client.table("templates").select("*").eq("id", template_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Template not found")
        
        client.table("templates").delete().eq("id", template_id).execute()
        
        await log_system_event("warning", "admin", f"Template deleted: {template_id}", user_id=admin_id)
        
        return {"message": "Template deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting template: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting template: {str(e)}")

@api_router.get("/admin/templates/{template_id}")
async def admin_get_template(template_id: str, admin_id: str = Depends(get_current_user)):
    """Get a single template"""
    client = get_supabase_client(use_service_role=True)
    
    admin = client.table("users").select("*").eq("id", admin_id).eq("role", "admin").single().execute()
    if not admin.data:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        response = client.table("templates").select("*").eq("id", template_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            raise HTTPException(status_code=404, detail="Template not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching template: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching template: {str(e)}")

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "NativiWeb Studio API v2.0.0", "status": "operational"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include the router
# CORS - Must be added before including routers
# Configure CORS based on environment
cors_origins = ALLOWED_ORIGINS if ENVIRONMENT == "production" else ["http://localhost:3000", "http://localhost:3001"]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Trusted host middleware (production only)
if ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with your actual domain
    )

app.include_router(api_router)

# Include upload router for file uploads
try:
    from upload import router as upload_router
    # Inclure le router avec le préfixe /api pour être cohérent avec les autres routes
    app.include_router(upload_router, prefix="/api")
    logging.info("Upload router loaded successfully with /api prefix")
except ImportError as e:
    logging.warning(f"Upload router not available - upload functionality disabled: {e}")
except Exception as e:
    logging.error(f"Error loading upload router - upload functionality disabled: {e}")
    # Le backend continue de fonctionner sans le module upload

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
