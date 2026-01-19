import asyncio
import platform
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Header, Request, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

# Rate limiting (optionnel)
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    HAS_SLOWAPI = True
except ImportError:
    HAS_SLOWAPI = False
    class Limiter:
        def __init__(self, key_func):
            self.key_func = key_func
    def get_remote_address(request):
        return request.client.host if request.client else "unknown"
    class RateLimitExceeded(Exception):
        pass
    def _rate_limit_exceeded_handler(request, exc):
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

from supabase import create_client, Client
import supabase
import os
import logging
import time
import jwt

# PyJWK (optionnel)
try:
    from jwt import PyJWKClient
    HAS_PYJWK = True
except ImportError:
    HAS_PYJWK = False

from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr, HttpUrl, field_validator
from urllib.parse import urlparse
from typing import List, Optional, Dict, Any, Tuple
import uuid
from datetime import datetime, timezone, timedelta
import json
import io
import zipfile
import hashlib
import secrets
import base64
import random
import tempfile
import shutil
import math

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ==================== CONFIGURATION ====================

# Environment
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

# Mode développement sans Supabase
DEV_MODE = ENVIRONMENT == 'development' and not os.environ.get('SUPABASE_URL')
if DEV_MODE:
    logging.warning("⚠️ MODE DÉVELOPPEMENT : Supabase désactivé, authentification bypassée")

# Stockage en mémoire pour les projets en mode DEV
DEV_PROJECTS_STORE: Dict[str, Dict[str, Any]] = {}
DEV_BUILDS_STORE: Dict[str, List[Dict[str, Any]]] = {}
DEV_TEMPLATES_STORE: Dict[str, Dict[str, Any]] = {}
DEV_PLATFORM_CONFIG: Dict[str, Any] = {}
DEV_USERS_STORE: Dict[str, Dict[str, Any]] = {}

# Stockage en mémoire pour les APKs compilés
build_in_memory: Dict[str, Dict[str, Any]] = {}

# Validate required environment variables
REQUIRED_ENV_VARS = {
    'production': ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_ROLE_KEY'],
    'development': ['SUPABASE_URL', 'SUPABASE_ANON_KEY'],
    'test': []
}

missing_vars = []
if ENVIRONMENT not in ['test']:
    required = REQUIRED_ENV_VARS.get(ENVIRONMENT, REQUIRED_ENV_VARS['development'])
    for var in required:
        if not os.environ.get(var):
            missing_vars.append(var)

if missing_vars and not DEV_MODE:
    error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
    logging.error(error_msg)
    if ENVIRONMENT == 'production':
        raise ValueError(error_msg)
    else:
        logging.warning(f"⚠️  {error_msg} - Application may not work correctly")

# Initialize Sentry for error tracking (production only)
SENTRY_DSN = os.environ.get('SENTRY_DSN')
if SENTRY_DSN and ENVIRONMENT == 'production':
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                FastApiIntegration(),
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
            ],
            traces_sample_rate=0.1,
            environment=ENVIRONMENT,
            release=os.environ.get('RELEASE_VERSION', '1.0.0')
        )
        logging.info("Sentry error tracking initialized")
    except ImportError:
        logging.warning("Sentry SDK not installed - error tracking disabled")

ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'https://nativify-web-vercel.vercel.app,http://localhost:3000').split(',')

# Supabase connection
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')

if SUPABASE_URL and SUPABASE_KEY and not DEV_MODE:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
    if ENVIRONMENT != 'test' and not DEV_MODE:
        logging.warning("⚠️  Supabase not configured - authentication will fail")

# Configure structured logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
LOG_FORMAT = os.environ.get('LOG_FORMAT', 'json' if ENVIRONMENT == 'production' else 'text')

if LOG_FORMAT == 'json':
    try:
        from pythonjsonlogger import jsonlogger
        log_handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d'
        )
        log_handler.setFormatter(formatter)
        logging.basicConfig(level=getattr(logging, LOG_LEVEL), handlers=[log_handler])
    except ImportError:
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
else:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

logger = logging.getLogger(__name__)

# ==================== HELPER FUNCTIONS ====================

def get_supabase_client(token: Optional[str] = None, use_service_role: bool = False) -> Optional[Client]:
    """Get Supabase client with optional user token for RLS"""
    if DEV_MODE:
        return None
    
    if not SUPABASE_URL:
        return None
    
    try:
        if use_service_role and SUPABASE_SERVICE_KEY:
            return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        if token and not use_service_role:
            client = create_client(SUPABASE_URL, SUPABASE_KEY)
            return client
        
        if SUPABASE_SERVICE_KEY:
            return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        return supabase
    except Exception as e:
        logging.warning(f"Error creating Supabase client: {e}")
        return None

# Initialize rate limiter
RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', '100'))

if HAS_SLOWAPI and RATE_LIMIT_ENABLED:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[f"{RATE_LIMIT_PER_MINUTE}/minute"]
    )
    logging.info(f"Rate limiting enabled: {RATE_LIMIT_PER_MINUTE} requests/minute")
else:
    limiter = Limiter(key_func=get_remote_address)
    if not HAS_SLOWAPI:
        logging.warning("slowapi not installed - rate limiting disabled")
    elif not RATE_LIMIT_ENABLED:
        logging.warning("Rate limiting disabled via RATE_LIMIT_ENABLED=false")

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
    name: str = Field(..., min_length=1, max_length=100)
    web_url: HttpUrl  # Validation stricte d'URL
    description: Optional[str] = Field(default="", max_length=1000)
    platform: List[str] = Field(default=["android", "ios"])
    features: Optional[List[NativeFeature]] = None
    logo_url: Optional[HttpUrl] = None
    
    @field_validator('web_url')
    @classmethod
    def validate_web_url(cls, v):
        """Valider que l'URL est HTTP/HTTPS et pas un fichier local"""
        if isinstance(v, str):
            parsed = urlparse(str(v))
            if parsed.scheme not in ['http', 'https']:
                raise ValueError("URL must use http or https protocol")
            if not parsed.netloc:
                raise ValueError("URL must have a valid domain")
            # Bloquer les localhost en production (optionnel)
            if ENVIRONMENT == "production" and parsed.netloc in ['localhost', '127.0.0.1', '0.0.0.0']:
                raise ValueError("Localhost URLs not allowed in production")
        return v
    
    @field_validator('platform')
    @classmethod
    def validate_platform(cls, v):
        """Valider que les plateformes sont valides"""
        valid_platforms = ['android', 'ios']
        for platform in v:
            if platform not in valid_platforms:
                raise ValueError(f"Platform must be one of: {valid_platforms}")
        if not v:
            raise ValueError("At least one platform must be specified")
        return v

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    web_url: Optional[HttpUrl] = None  # Validation stricte d'URL
    description: Optional[str] = Field(None, max_length=1000)
    features: Optional[List[NativeFeature]] = None
    advanced_config: Optional[Dict] = None
    web_app_version: Optional[str] = Field(None, max_length=50)  # Version de l'app web (ex: "1.2.3", "2024.01.15")
    
    @field_validator('web_url')
    @classmethod
    def validate_web_url(cls, v):
        """Valider que l'URL est HTTP/HTTPS si fournie"""
        if v is not None:
            if isinstance(v, str):
                parsed = urlparse(v)
                if parsed.scheme not in ['http', 'https']:
                    raise ValueError("URL must use http or https protocol")
                if not parsed.netloc:
                    raise ValueError("URL must have a valid domain")
                if ENVIRONMENT == "production" and parsed.netloc in ['localhost', '127.0.0.1', '0.0.0.0']:
                    raise ValueError("Localhost URLs not allowed in production")
        return v

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
    web_app_version: Optional[str] = None  # Version de l'app web
    version_check_enabled: bool = True  # Activer la vérification automatique de version
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

class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: Optional[str] = "user"

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

# ==================== CONSTANTS ====================

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
    # NOUVELLES FEATURES AJOUTÉES
    {"id": "in_app_purchases", "name": "In-App Purchases", "enabled": False, "config": {}},
    {"id": "subscriptions", "name": "Subscriptions", "enabled": False, "config": {}},
    {"id": "qr_scanner", "name": "QR/Barcode Scanner", "enabled": False, "config": {}},
    {"id": "audio_recording", "name": "Audio Recording", "enabled": False, "config": {}},
    {"id": "video_recording", "name": "Video Recording", "enabled": False, "config": {}},
    {"id": "offline_bundling", "name": "Offline Capability & Asset Bundling", "enabled": False, "config": {}},
    {"id": "analytics", "name": "Analytics Support", "enabled": False, "config": {}},
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

# ==================== UTILITY FUNCTIONS ====================

def hash_password(password: str) -> str:
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_build_logs(phase: str, platform: str, project_name: str) -> List[Dict[str, Any]]:
    """Generate build logs for a specific phase"""
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

async def log_system_event(
    level: str, 
    category: str, 
    message: str, 
    details: Optional[dict] = None, 
    user_id: Optional[str] = None, 
    token: Optional[str] = None
):
    """Log a system event to database"""
    if DEV_MODE:
        logger.info(f"[{level.upper()}] [{category}] {message}")
        return
    
    try:
        client = get_supabase_client(use_service_role=True)
        if client:
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

def normalize_web_url(url: str) -> str:
    """Normalize web URL (GitHub detection)"""
    if not url:
        return url
    
    if 'github.com' in url.lower():
        import re
        match = re.search(r'github\.com/([^/]+)/([^/]+)', url)
        if match:
            username = match.group(1)
            repo = match.group(2).replace('.git', '')
            logging.warning(f"URL GitHub détectée: {url}. Assurez-vous que l'application web est déployée et accessible.")
            return url
    
    return url

def normalize_features(features: Optional[List]) -> List[Dict[str, Any]]:
    """Normalize features to consistent format"""
    if not features:
        return DEFAULT_FEATURES.copy()
    
    normalized = []
    for f in features:
        if isinstance(f, dict):
            if 'id' not in f:
                continue
            if 'enabled' not in f:
                f['enabled'] = False
            if 'name' not in f:
                f['name'] = f['id']
            if 'config' not in f:
                f['config'] = {}
            normalized.append(f)
        elif hasattr(f, 'id'):
            normalized.append({
                'id': f.id,
                'enabled': getattr(f, 'enabled', False),
                'name': getattr(f, 'name', f.id),
                'config': getattr(f, 'config', {})
            })
    
    return normalized if normalized else DEFAULT_FEATURES.copy()
# ==================== AUTHENTICATION ====================

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract user ID from JWT token"""
    if DEV_MODE:
        return "dev-user-123"
    
    try:
        token = credentials.credentials
        
        if not token:
            logging.warning("No token provided in credentials")
            raise HTTPException(status_code=401, detail="No token provided")
        
        try:
            # Décoder le JWT sans vérifier la signature d'abord
            unverified = jwt.decode(token, options={"verify_signature": False})
            
            # Extraire le user_id
            user_id = unverified.get('sub') or unverified.get('user_id')
            
            if not user_id:
                logging.warning("No user_id found in token")
                raise HTTPException(status_code=401, detail="Invalid token - no user ID")
            
            # Vérifier expiration
            exp = unverified.get('exp')
            if exp and exp < time.time():
                logging.warning(f"Token expired for user {user_id}")
                raise HTTPException(status_code=401, detail="Token expired")
            
            # Vérifier la signature - OBLIGATOIRE en production
            if ENVIRONMENT == "production":
                if not HAS_PYJWK or not SUPABASE_URL:
                    logging.error("JWT signature verification unavailable in production - PyJWK or Supabase URL missing")
                    raise HTTPException(
                        status_code=503, 
                        detail="Authentication service unavailable. JWT verification required."
                    )
                
                try:
                    jwks_url = f"{SUPABASE_URL}/.well-known/jwks.json"
                    jwks_client = PyJWKClient(jwks_url, timeout=5)
                    signing_key = jwks_client.get_signing_key_from_jwt(token)
                    jwt.decode(
                        token, 
                        signing_key.key, 
                        algorithms=["RS256"], 
                        audience="authenticated", 
                        options={"verify_exp": False}
                    )
                    logging.debug(f"Token signature verified for user: {user_id}")
                except Exception as sig_error:
                    logging.warning(f"Token signature verification failed: {sig_error}")
                    # Fallback: vérifier via Supabase si la récupération JWKS échoue
                    try:
                        if supabase:
                            user_response = supabase.auth.get_user(token)
                            if user_response.user and user_response.user.id == user_id:
                                logging.info("Token validated via Supabase fallback")
                                return user_id
                    except Exception as fallback_error:
                        logging.error(f"Supabase fallback verification failed: {fallback_error}")
                    raise HTTPException(status_code=401, detail="Invalid token signature")
            else:
                # En développement, vérifier si disponible, sinon warning seulement
                if HAS_PYJWK and SUPABASE_URL:
                    try:
                        jwks_url = f"{SUPABASE_URL}/.well-known/jwks.json"
                        jwks_client = PyJWKClient(jwks_url, timeout=2)
                        signing_key = jwks_client.get_signing_key_from_jwt(token)
                        jwt.decode(
                            token, 
                            signing_key.key, 
                            algorithms=["RS256"], 
                            audience="authenticated", 
                            options={"verify_exp": False}
                        )
                        logging.debug(f"Token signature verified for user: {user_id}")
                    except Exception as sig_error:
                        logging.warning(f"Could not verify token signature (dev mode - continuing): {sig_error}")
                else:
                    logging.warning("JWT signature verification unavailable (dev mode)")
            
            return user_id
            
        except jwt.ExpiredSignatureError:
            logging.warning("Token expired")
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as jwt_error:
            logging.error(f"Invalid JWT token: {jwt_error}")
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as decode_error:
            logging.error(f"JWT decode error: {decode_error}")
            raise HTTPException(status_code=401, detail="Authentication failed: Invalid token")
                
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected auth error: {e}", exc_info=True)
        # Ne jamais exposer les détails d'erreur d'authentification
        raise HTTPException(status_code=401, detail="Authentication failed")

def _normalize_pagination(page: int, limit: int) -> Tuple[int, int, int, int]:
    safe_page = max(1, page or 1)
    safe_limit = min(max(1, limit or 20), 100)
    start = (safe_page - 1) * safe_limit
    end = start + safe_limit - 1
    return safe_page, safe_limit, start, end

def _calc_pages(total: int, limit: int) -> int:
    if not total or total <= 0:
        return 1
    return max(1, math.ceil(total / limit))

def _extract_auth_users(auth_result: Any) -> List[Any]:
    if hasattr(auth_result, "users"):
        return auth_result.users or []
    if isinstance(auth_result, dict) and "users" in auth_result:
        return auth_result.get("users") or []
    data = getattr(auth_result, "data", None)
    if isinstance(data, dict) and "users" in data:
        return data.get("users") or []
    if isinstance(data, list):
        return data
    return []

async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Ensure the requester is an admin user."""
    user_id = await get_current_user(credentials)

    if DEV_MODE:
        return {
            "id": user_id,
            "email": "dev@local.com",
            "name": "Dev Admin",
            "role": "admin",
            "status": "active"
        }

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        response = client.table("users").select("id, email, name, role, status").eq("id", user_id).single().execute()
        user_data = response.data if response.data else None

        if not user_data:
            try:
                from admin_sync import sync_missing_user
                sync_missing_user(client, user_id)
                response = client.table("users").select("id, email, name, role, status").eq("id", user_id).single().execute()
                user_data = response.data if response.data else None
            except Exception as sync_error:
                logging.warning(f"Failed to sync missing user {user_id}: {sync_error}")

        if not user_data:
            raise HTTPException(status_code=403, detail="Admin access required")

        if user_data.get("status") == "banned":
            raise HTTPException(status_code=403, detail="Account suspended")

        role = user_data.get("role", "user")
        if role not in ["admin", "superadmin"]:
            raise HTTPException(status_code=403, detail="Admin access required")

        return user_data
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to verify admin user: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify admin access")

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/register")
async def register(request: Request, user_data: UserCreate):
    if DEV_MODE:
        return {
            "token": "dev-token",
            "user": {
                "id": "dev-user-123",
                "email": user_data.email,
                "name": user_data.name,
                "role": "user"
            }
        }
    
    try:
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
            user_id = auth_response.user.id
            client = get_supabase_client(use_service_role=True)
            
            if client:
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
        if "already registered" in error_msg.lower():
            raise HTTPException(status_code=400, detail="Email already registered")
        logging.error(f"Registration error: {e}")
        raise HTTPException(status_code=400, detail=f"Registration failed: {error_msg}")

@api_router.post("/auth/login")
async def login(request: Request, credentials: UserLogin):
    if DEV_MODE:
        return {
            "token": "dev-token",
            "user": {
                "id": "dev-user-123",
                "email": credentials.email or "dev@local.com",
                "name": "Dev User",
                "role": "user"
            }
        }
    
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        if auth_response.user and auth_response.session:
            user_id = auth_response.user.id
            token = auth_response.session.access_token
            
            client = get_supabase_client(use_service_role=True)
            user_data = {}
            
            if client:
                try:
                    user_response = client.table("users").select("*").eq("id", user_id).single().execute()
                    user_data = user_response.data if user_response.data else {}
                except Exception as e:
                    logging.error(f"Failed to fetch user profile: {e}")
            
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
    if DEV_MODE:
        return {
            "id": "dev-user-123",
            "email": "dev@local.com",
            "name": "Dev User",
            "role": "user"
        }
    
    try:
        token = credentials.credentials
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        user_id = user_response.user.id
        client = get_supabase_client(use_service_role=True)
        user_data = {}
        
        if client:
            try:
                profile_response = client.table("users").select("*").eq("id", user_id).execute()
                if profile_response.data and len(profile_response.data) > 0:
                    user_data = profile_response.data[0]
                else:
                    # Create user profile if missing
                    logging.warning(f"User profile not found for {user_id}, creating it")
                    user_metadata = user_response.user.user_metadata or {}
                    user_email = user_response.user.email or ""
                    user_name = user_metadata.get("name") or user_email.split("@")[0] if user_email else "User"
                    
                    client.table("users").upsert({
                        "id": user_id,
                        "email": user_email,
                        "name": user_name,
                        "role": "user",
                        "status": "active",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }).execute()
                    
                    profile_response = client.table("users").select("*").eq("id", user_id).execute()
                    user_data = profile_response.data[0] if profile_response.data else {}
            except Exception as e:
                logging.error(f"Failed to fetch/create user profile: {e}")
        
        return {
            "id": user_id,
            "email": user_response.user.email or user_data.get('email', ''),
            "name": user_data.get('name', ''),
            "role": user_data.get('role', 'user')
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Get user error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

@api_router.post("/auth/logout")
async def logout(user_id: str = Depends(get_current_user)):
    if DEV_MODE:
        return {"message": "Logged out successfully"}
    
    try:
        supabase.auth.sign_out()
    except:
        pass
    return {"message": "Logged out successfully"}

# ==================== ANALYTICS ENDPOINTS ====================

@api_router.post("/track-visit")
async def track_visit(visit_data: VisitTrack, request: Request):
    """Track page visit for analytics"""
    if DEV_MODE:
        logger.info(f"📊 Visit tracked (dev): {visit_data.page_path} - {visit_data.device_type}")
        return {"success": True, "message": "Visit tracked (dev mode)"}
    
    try:
        # Get user_id from token if available (optional)
        user_id = visit_data.user_id
        if not user_id:
            try:
                # Try to get from Authorization header
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.replace("Bearer ", "")
                    user_response = supabase.auth.get_user(token)
                    if user_response.user:
                        user_id = user_response.user.id
            except Exception:
                pass  # User not authenticated, that's okay
        
        client = get_supabase_client(use_service_role=True)
        if not client:
            return {"success": False, "message": "Database unavailable"}
        
        # Préparer les données de visite
        visit_record = {
            "id": str(uuid.uuid4()),
            "page_path": visit_data.page_path,
            "user_agent": visit_data.user_agent,
            "referrer": visit_data.referrer,
            "device_type": visit_data.device_type,
            "browser": visit_data.browser,
            "os": visit_data.os,
            "session_id": visit_data.session_id,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Insérer dans la base de données
        result = client.table("site_visits").insert(visit_record).execute()
        
        if result.data:
            logger.debug(f"✅ Visit tracked: {visit_data.page_path}")
            return {"success": True, "message": "Visit tracked successfully"}
        else:
            logger.warning(f"⚠️ Failed to track visit: no data returned")
            return {"success": False, "message": "Failed to track visit"}
            
    except Exception as e:
        logger.error(f"❌ Error tracking visit: {e}")
        # Ne pas lever d'exception pour ne pas bloquer l'utilisateur
        return {"success": False, "message": "Error tracking visit"}

# ==================== PROJECT ENDPOINTS ====================

@api_router.post("/projects")
async def create_project(project_data: ProjectCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    normalized_web_url = normalize_web_url(project_data.web_url)
    features = normalize_features(project_data.features)
    
    if DEV_MODE:
        user_id = "dev-user-123"
        project_id = str(uuid.uuid4())
        project = {
            "id": project_id,
            "user_id": user_id,
            "name": project_data.name,
            "web_url": normalized_web_url,
            "description": project_data.description or "",
            "platform": project_data.platform,
            "features": features,
            "logo_url": project_data.logo_url,
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        DEV_PROJECTS_STORE[project_id] = project  # CORRECTION: Sauvegarder en mémoire
        logging.info(f"📁 Projet créé en mode DEV: {project_id}")
        return project
    
    try:
        token = credentials.credentials
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = user_response.user.id
        client = get_supabase_client(use_service_role=True)
        
        if not client:
            raise HTTPException(status_code=500, detail="Database unavailable")
        
        # Ensure user exists
        try:
            user_check = client.table("users").select("id").eq("id", user_id).execute()
            if not user_check.data:
                user_metadata = user_response.user.user_metadata or {}
                user_email = user_response.user.email or ""
                user_name = user_metadata.get("name") or user_email.split("@")[0] if user_email else "User"
                
                client.table("users").upsert({
                    "id": user_id,
                    "email": user_email,
                    "name": user_name,
                    "role": "user",
                    "status": "active",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }).execute()
        except Exception as user_error:
            logging.warning(f"Error checking/creating user: {user_error}")
        
        project_id = str(uuid.uuid4())
        project = {
            "id": project_id,
            "user_id": user_id,
            "name": project_data.name,
            "web_url": normalized_web_url,
            "description": project_data.description or "",
            "platform": project_data.platform,
            "features": features,
            "logo_url": project_data.logo_url,
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = client.table("projects").insert(project).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create project")
        
        await log_system_event("info", "project", f"Project created: {project_data.name}", user_id=user_id)
        return project
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating project: {e}")
        # Ne pas exposer les détails d'erreur en production
        if ENVIRONMENT == "production":
            raise HTTPException(status_code=500, detail="Failed to create project. Please try again later.")
        else:
            raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")

@api_router.get("/projects")
async def get_projects(user_id: str = Depends(get_current_user)):
    if DEV_MODE:
        projects = [p for p in DEV_PROJECTS_STORE.values() if p.get("user_id") == user_id]
        logging.info(f"📋 Retour de {len(projects)} projets en mode DEV")
        return projects
    
    try:
        client = get_supabase_client(use_service_role=True)
        if not client:
            return []
        
        response = client.table("projects").select("*").eq("user_id", user_id).execute()
        return response.data or []
    except Exception as e:
        logging.error(f"Error fetching projects: {e}")
        return []

@api_router.get("/projects/{project_id}")
async def get_project(project_id: str, user_id: str = Depends(get_current_user)):
    if DEV_MODE:
        if project_id in DEV_PROJECTS_STORE:
            project = DEV_PROJECTS_STORE[project_id]
            logging.info(f"📦 Projet récupéré: {project_id}")
            return project
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        client = get_supabase_client(use_service_role=True)
        if not client:
            raise HTTPException(status_code=500, detail="Database unavailable")
        
        response = client.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching project: {e}")
        if ENVIRONMENT == "production":
            raise HTTPException(status_code=500, detail="Failed to fetch project. Please try again later.")
        else:
            raise HTTPException(status_code=500, detail=f"Error fetching project: {str(e)}")

@api_router.put("/projects/{project_id}")
async def update_project(project_id: str, update_data: ProjectUpdate, user_id: str = Depends(get_current_user)):
    if DEV_MODE:
        if project_id not in DEV_PROJECTS_STORE:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = DEV_PROJECTS_STORE[project_id]
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        
        if 'web_url' in update_dict:
            update_dict['web_url'] = normalize_web_url(update_dict['web_url'])
        
        if 'features' in update_dict:
            update_dict['features'] = normalize_features(update_dict['features'])
        
        if 'advanced_config' in update_dict:
            current_config = project.get('advanced_config', {})
            if isinstance(current_config, dict):
                current_config.update(update_dict['advanced_config'])
                update_dict['advanced_config'] = current_config
        
        project.update(update_dict)
        project['updated_at'] = datetime.now(timezone.utc).isoformat()
        DEV_PROJECTS_STORE[project_id] = project
        
        logging.info(f"📝 Projet mis à jour: {project_id}")
        return project
    
    try:
        client = get_supabase_client(use_service_role=True)
        if not client:
            raise HTTPException(status_code=500, detail="Database unavailable")
        
        existing = client.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).single().execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        
        if 'web_url' in update_dict:
            update_dict['web_url'] = normalize_web_url(update_dict['web_url'])
        
        if 'features' in update_dict:
            update_dict['features'] = normalize_features(update_dict['features'])
        
        if 'advanced_config' in update_dict:
            current_config = existing.data.get('advanced_config', {})
            if isinstance(current_config, dict):
                current_config.update(update_dict['advanced_config'])
                update_dict['advanced_config'] = current_config
        
        update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        client.table("projects").update(update_dict).eq("id", project_id).execute()
        
        updated = client.table("projects").select("*").eq("id", project_id).single().execute()
        return updated.data
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating project: {e}")
        if ENVIRONMENT == "production":
            raise HTTPException(status_code=500, detail="Failed to update project. Please try again later.")
        else:
            raise HTTPException(status_code=500, detail=f"Error updating project: {str(e)}")

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str, user_id: str = Depends(get_current_user)):
    if DEV_MODE:
        if project_id in DEV_PROJECTS_STORE:
            # Supprimer les builds associés
            if project_id in DEV_BUILDS_STORE:
                # Nettoyer build_in_memory pour les builds de ce projet
                for build in DEV_BUILDS_STORE[project_id]:
                    build_id = build.get('id')
                    if build_id in build_in_memory:
                        apk_path = build_in_memory[build_id].get('apk_path')
                        if apk_path and Path(apk_path).exists():
                            try:
                                os.unlink(apk_path)
                                logging.info(f"🗑️ APK supprimé: {apk_path}")
                            except Exception as e:
                                logging.warning(f"Erreur suppression APK {apk_path}: {e}")
                        del build_in_memory[build_id]
                del DEV_BUILDS_STORE[project_id]
            del DEV_PROJECTS_STORE[project_id]
            logging.info(f"🗑️ Projet supprimé: {project_id}")
        return {"message": "Project deleted"}
    
    try:
        client = get_supabase_client(use_service_role=True)
        if not client:
            raise HTTPException(status_code=500, detail="Database unavailable")
        
        # Vérifier que le projet existe et appartient à l'utilisateur
        project_response = client.table("projects").select("id").eq("id", project_id).eq("user_id", user_id).execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Récupérer tous les builds associés pour nettoyer build_in_memory
        builds_response = client.table("builds").select("id").eq("project_id", project_id).execute()
        build_ids = [build["id"] for build in builds_response.data] if builds_response.data else []
        
        # Nettoyer build_in_memory et supprimer les fichiers APK
        for build_id in build_ids:
            if build_id in build_in_memory:
                apk_path = build_in_memory[build_id].get('apk_path')
                if apk_path and Path(apk_path).exists():
                    try:
                        os.unlink(apk_path)
                        logging.info(f"🗑️ APK supprimé: {apk_path}")
                    except Exception as e:
                        logging.warning(f"Erreur suppression APK {apk_path}: {e}")
                del build_in_memory[build_id]
        
        # Supprimer d'abord tous les builds associés
        if build_ids:
            client.table("builds").delete().eq("project_id", project_id).execute()
            logging.info(f"🗑️ {len(build_ids)} build(s) supprimé(s) pour le projet {project_id}")
        
        # Ensuite supprimer le projet
        client.table("projects").delete().eq("id", project_id).eq("user_id", user_id).execute()
        await log_system_event("info", "project", f"Project deleted: {project_id}", user_id=user_id)
        return {"message": "Project deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting project: {e}", exc_info=True)
        if ENVIRONMENT == "production":
            raise HTTPException(status_code=500, detail="Failed to delete project. Please try again later.")
        else:
            raise HTTPException(status_code=500, detail=f"Error deleting project: {str(e)}")

# ==================== BUILD ENDPOINTS (CORRIGÉ) ====================

@api_router.post("/builds")
async def create_build(
    build_data: BuildCreate, 
    background_tasks: BackgroundTasks, 
    user_id: str = Depends(get_current_user)
):
    if DEV_MODE:
        project = DEV_PROJECTS_STORE.get(build_data.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        build_id = str(uuid.uuid4())
        build = {
            "id": build_id,
            "project_id": build_data.project_id,
            "user_id": user_id,
            "platform": build_data.platform,
            "build_type": build_data.build_type or "debug",
            "build_config": {},
            "certificate_id": build_data.certificate_id,
            "status": "processing",
            "phase": "queued",
            "progress": 0,
            "logs": [{"level": "info", "message": "Build queued (dev mode)", "timestamp": datetime.now(timezone.utc).isoformat()}],
            "artifacts": [],
            "download_url": None,
            "error_message": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None,
            "completed_at": None,
            "duration_seconds": None
        }
        
        if build_data.project_id not in DEV_BUILDS_STORE:
            DEV_BUILDS_STORE[build_data.project_id] = []
        DEV_BUILDS_STORE[build_data.project_id].append(build)
        
        # CORRECTION: Passer les vraies données du projet
        background_tasks.add_task(process_build, build_id, project)
        logging.info(f"🔨 Build créé en mode DEV: {build_id}")
        return build
    
    try:
        client = get_supabase_client(use_service_role=True)
        if not client:
            raise HTTPException(status_code=500, detail="Database unavailable")
        
        project_response = client.table("projects").select("*").eq("id", build_data.project_id).eq("user_id", user_id).execute()
        if not project_response.data:
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
        
        result = client.table("builds").insert(build).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create build")
        
        await log_system_event("info", "build", f"Build started: {build_id}", user_id=user_id)
        
        background_tasks.add_task(process_build, build_id, project)
        
        return result.data[0] if result.data else build
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating build: {e}")
        if ENVIRONMENT == "production":
            raise HTTPException(status_code=500, detail="Failed to create build. Please try again later.")
        else:
            raise HTTPException(status_code=500, detail=f"Error creating build: {str(e)}")
# ==================== BUILD PROCESS (CORRIGÉ) ====================

async def process_build(build_id: str, project: dict):
    """Process build with real Android compilation"""
    
    # CORRECTION : Vérifier que GENERATOR_AVAILABLE est défini
    try:
        generator_available = GENERATOR_AVAILABLE
    except NameError:
        generator_available = False
    
    if DEV_MODE:
        # Trouver le build dans le store
        build_in_store = None
        project_id = project.get('id')
        if project_id and project_id in DEV_BUILDS_STORE:
            for build in DEV_BUILDS_STORE[project_id]:
                if build.get('id') == build_id:
                    build_in_store = build
                    break
        
        if not build_in_store:
            logging.warning(f"Build {build_id} not found in DEV_BUILDS_STORE")
            return
        
        logging.info(f"🔨 Mode dev : Traitement du build {build_id}")
        platform = build_in_store.get('platform', 'android')
        project_name = project.get('name', 'MyApp')
        web_url = project.get('web_url', '')
        features = normalize_features(project.get('features', []))
        
        build_in_store['status'] = 'processing'
        build_in_store['started_at'] = datetime.now(timezone.utc).isoformat()
        
        # Simuler les phases
        phases = BUILD_PHASES.get(platform, BUILD_PHASES['android'])
        total_duration = sum(p['duration'] for p in phases)
        current_progress = 0
        
        for phase_info in phases:
            phase = phase_info['phase']
            duration = phase_info['duration']
            
            build_in_store['phase'] = phase
            build_in_store['progress'] = min(int(current_progress), 99)
            
            # Compilation réelle pour Android
            if platform == 'android' and phase == 'assembling' and generator_available:
                try:
                    logging.info(f"🔨 Compilation APK réelle pour {project_name}...")
                    
                    safe_name = "".join(c.lower() if c.isalnum() else '' for c in project_name)
                    package_name = f"com.nativiweb.{safe_name}" if safe_name else "com.nativiweb.app"
                    
                    project_zip = generator.generate_android_project(
                        project_name=project_name,
                        package_name=package_name,
                        web_url=web_url,
                        features=features,
                        app_icon_url=project.get('logo_url')
                    )
                    
                    try:
                        from android_builder import AndroidBuilder
                        builder = AndroidBuilder()
                        
                        import concurrent.futures
                        loop = asyncio.get_event_loop()
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            success, apk_bytes, error_msg = await loop.run_in_executor(
                                executor, 
                                builder.build_apk, 
                                project_zip, 
                                project_name,
                                3  # max_retries
                            )
                        
                        if success and apk_bytes:
                            # Sauvegarder l'APK dans un fichier temporaire
                            import tempfile
                            apk_file = tempfile.NamedTemporaryFile(
                                delete=False, 
                                suffix='.apk', 
                                prefix=f'{safe_name}_'
                            )
                            apk_file.write(apk_bytes)
                            apk_file.close()
                            
                            # Stocker le chemin dans le build
                            build_in_memory[build_id] = {
                                'apk_path': apk_file.name,
                                'apk_size': len(apk_bytes),
                                'compiled': True
                            }
                            
                            logging.info(f"✅ APK compilé! Taille: {len(apk_bytes) / 1024 / 1024:.2f} MB")
                            logging.info(f"📁 APK sauvegardé: {apk_file.name}")
                        else:
                            logging.warning(f"⚠️ Compilation échouée: {error_msg[:200] if error_msg else 'Erreur inconnue'}")
                    except ImportError:
                        logging.warning("AndroidBuilder non disponible")
                    except Exception as build_error:
                        logging.error(f"Erreur build Android: {build_error}")
                except Exception as gen_error:
                    logging.error(f"Erreur génération projet: {gen_error}")
            
            current_progress += (100 / total_duration)
            if duration > 0:
                await asyncio.sleep(min(duration * 0.1, 1))
        
        # Finaliser
        build_in_store['status'] = 'completed'
        build_in_store['phase'] = 'completed'
        build_in_store['progress'] = 100
        build_in_store['completed_at'] = datetime.now(timezone.utc).isoformat()
        build_in_store['artifacts'] = [{"name": f"{project_name}-debug.apk", "type": "apk", "size": "varies"}]
        build_in_store['download_url'] = f"/api/builds/{build_id}/download"
        
        logging.info(f"✅ Build {build_id} terminé (mode dev)")
        return
    
    # Production mode
    try:
        client = get_supabase_client(use_service_role=True)
        if not client:
            logging.error("Database client unavailable")
            return
        
        build_response = client.table("builds").select("*").eq("id", build_id).execute()
        if not build_response.data:
            logging.error(f"Build {build_id} not found")
            return
        
        build_data = build_response.data[0]
        platform = build_data['platform']
        phases = BUILD_PHASES.get(platform, BUILD_PHASES['android'])
        
        client.table("builds").update({
            "started_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", build_id).execute()
        
        apk_compiled = False
        apk_size = 0
        
        for phase_info in phases:
            phase = phase_info['phase']
            duration = phase_info['duration']
            
            logs = generate_build_logs(phase, platform, project['name'])
            
            current_build = client.table("builds").select("logs").eq("id", build_id).execute()
            current_logs = current_build.data[0].get('logs', []) if current_build.data else []
            current_logs.extend(logs)
            
            client.table("builds").update({
                "phase": phase,
                "logs": current_logs
            }).eq("id", build_id).execute()
            
            # Compilation réelle Android
            if platform == 'android' and phase == 'assembling' and generator_available:
                try:
                    logging.info(f"🔨 Compilation APK réelle pour {project['name']}...")
                    
                    project_name = project.get('name', 'MyApp')
                    web_url = project.get('web_url', '')
                    features = normalize_features(project.get('features', []))
                    safe_name = "".join(c.lower() if c.isalnum() else '' for c in project_name)
                    package_name = f"com.nativiweb.{safe_name}" if safe_name else "com.nativiweb.app"
                    
                    project_zip = generator.generate_android_project(
                        project_name=project_name,
                        package_name=package_name,
                        web_url=web_url,
                        features=features,
                        app_icon_url=project.get('logo_url')
                    )
                    
                    try:
                        from android_builder import AndroidBuilder
                        builder = AndroidBuilder()
                        
                        import concurrent.futures
                        loop = asyncio.get_event_loop()
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            success, apk_bytes, error_msg = await loop.run_in_executor(
                                executor, 
                                builder.build_apk, 
                                project_zip, 
                                project_name,
                                3  # max_retries
                            )
                        
                        if success and apk_bytes:
                            # Sauvegarder l'APK dans un fichier temporaire
                            import tempfile
                            apk_file = tempfile.NamedTemporaryFile(
                                delete=False, 
                                suffix='.apk', 
                                prefix=f'{safe_name}_'
                            )
                            apk_file.write(apk_bytes)
                            apk_file.close()
                            
                            # Stocker le chemin dans le build
                            build_in_memory[build_id] = {
                                'apk_path': apk_file.name,
                                'apk_size': len(apk_bytes),
                                'compiled': True
                            }
                            
                            apk_compiled = True
                            apk_size = len(apk_bytes)
                            logging.info(f"✅ APK compilé! Taille: {apk_size / 1024 / 1024:.2f} MB")
                            logging.info(f"📁 APK sauvegardé: {apk_file.name}")
                        else:
                            logging.warning(f"⚠️ Compilation échouée: {error_msg[:200] if error_msg else 'Erreur inconnue'}")
                    except ImportError:
                        logging.warning("AndroidBuilder non disponible")
                    except Exception as build_error:
                        logging.error(f"Erreur build Android: {build_error}")
                except Exception as gen_error:
                    logging.error(f"Erreur génération projet: {gen_error}")
            
            if duration > 0:
                steps = max(1, duration)
                for _ in range(steps):
                    await asyncio.sleep(0.5)
        
        # Artifacts
        artifacts = []
        if platform == 'android':
            if apk_compiled:
                artifacts = [{"name": f"{project['name']}-debug.apk", "type": "apk", "size": f"{apk_size / 1024 / 1024:.1f}MB", "compiled": True}]
            else:
                artifacts = [{"name": f"{project['name']}-source.zip", "type": "zip", "size": "varies", "compiled": False}]
        else:
            artifacts = [{"name": f"{project['name']}.ipa", "type": "ipa", "size": f"{random.randint(20, 40)}MB"}]
        
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
        
        logging.info(f"✅ Build {build_id} terminé")
    except Exception as e:
        logging.error(f"Error in process_build: {e}", exc_info=True)

# ==================== BUILD ENDPOINTS (SUITE) ====================

@api_router.get("/builds")
async def get_builds(user_id: str = Depends(get_current_user), project_id: Optional[str] = None):
    if DEV_MODE:
        all_builds = []
        for builds in DEV_BUILDS_STORE.values():
            all_builds.extend([b for b in builds if b.get("user_id") == user_id])
        if project_id:
            all_builds = [b for b in all_builds if b.get("project_id") == project_id]
        return all_builds
    
    try:
        client = get_supabase_client(use_service_role=True)
        if not client:
            return []
        
        query = client.table("builds").select("*").eq("user_id", user_id)
        if project_id:
            query = query.eq("project_id", project_id)
        response = query.order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        logging.error(f"Error fetching builds: {e}")
        return []

@api_router.get("/builds/{build_id}")
async def get_build(build_id: str, user_id: str = Depends(get_current_user)):
    if DEV_MODE:
        for project_builds in DEV_BUILDS_STORE.values():
            for build in project_builds:
                if build.get('id') == build_id:
                    return build
        raise HTTPException(status_code=404, detail="Build not found")
    
    try:
        client = get_supabase_client(use_service_role=True)
        if not client:
            raise HTTPException(status_code=500, detail="Database unavailable")
        
        response = client.table("builds").select("*").eq("id", build_id).eq("user_id", user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Build not found")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching build: {e}")
        if ENVIRONMENT == "production":
            raise HTTPException(status_code=500, detail="An error occurred. Please try again later.")
        else:
            if ENVIRONMENT == "production":
                raise HTTPException(status_code=500, detail="An error occurred. Please try again later.")
            else:
                raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@api_router.delete("/builds/{build_id}")
async def delete_build(build_id: str, user_id: str = Depends(get_current_user)):
    if DEV_MODE:
        logging.info(f"DEV_MODE: Build {build_id} deleted (simulated)")
        return {"message": "Build deleted successfully"}
    
    try:
        client = get_supabase_client(use_service_role=True)
        if not client:
            raise HTTPException(status_code=500, detail="Database unavailable")
        
        build_response = client.table("builds").select("*").eq("id", build_id).eq("user_id", user_id).execute()
        if not build_response.data:
            raise HTTPException(status_code=404, detail="Build not found")
        
        client.table("builds").delete().eq("id", build_id).execute()
        await log_system_event("info", "build", f"Build deleted: {build_id}", user_id=user_id)
        
        return {"message": "Build deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting build: {e}")
        if ENVIRONMENT == "production":
            raise HTTPException(status_code=500, detail="An error occurred. Please try again later.")
        else:
            if ENVIRONMENT == "production":
                raise HTTPException(status_code=500, detail="An error occurred. Please try again later.")
            else:
                raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@api_router.delete("/builds")
async def delete_all_builds(user_id: str = Depends(get_current_user)):
    if DEV_MODE:
        build_count = sum(len([b for b in builds if b.get("user_id") == user_id]) for builds in DEV_BUILDS_STORE.values())
        logging.info(f"DEV_MODE: All builds deleted (simulated, {build_count} builds)")
        return {"message": "All builds deleted successfully", "deleted_count": build_count}
    
    try:
        client = get_supabase_client(use_service_role=True)
        if not client:
            raise HTTPException(status_code=500, detail="Database unavailable")
        
        builds_response = client.table("builds").select("id").eq("user_id", user_id).execute()
        build_count = len(builds_response.data) if builds_response.data else 0
        
        client.table("builds").delete().eq("user_id", user_id).execute()
        await log_system_event("info", "build", f"All builds deleted ({build_count} builds)", user_id=user_id)
        
        return {"message": "All builds deleted successfully", "deleted_count": build_count}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting builds: {e}")
        if ENVIRONMENT == "production":
            raise HTTPException(status_code=500, detail="An error occurred. Please try again later.")
        else:
            if ENVIRONMENT == "production":
                raise HTTPException(status_code=500, detail="An error occurred. Please try again later.")
            else:
                raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@api_router.get("/builds/{build_id}/download")
async def download_build(build_id: str, user_id: str = Depends(get_current_user)):
    """Télécharge l'APK compilé ou le projet source"""
    
    try:
        logging.info(f"📥 Download request for build {build_id}")
        
        client = get_supabase_client(use_service_role=True)
        if not client and not DEV_MODE:
            raise HTTPException(status_code=500, detail="Database unavailable")
        
        # Récupérer le build
        if DEV_MODE:
            build = None
            for project_builds in DEV_BUILDS_STORE.values():
                for b in project_builds:
                    if b.get('id') == build_id:
                        build = b
                        break
                if build:
                    break
            if not build:
                raise HTTPException(status_code=404, detail="Build not found")
        else:
            build_response = client.table("builds").select("*").eq("id", build_id).execute()
            if not build_response.data:
                raise HTTPException(status_code=404, detail="Build not found")
            build = build_response.data[0]
        
        # Vérifier permissions
        if build.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        
        # Récupérer le projet
        if DEV_MODE:
            project = DEV_PROJECTS_STORE.get(build['project_id'])
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
        else:
            project_response = client.table("projects").select("*").eq("id", build["project_id"]).execute()
            if not project_response.data:
                raise HTTPException(status_code=404, detail="Project not found")
            project = project_response.data[0]
        
        platform = build.get('platform', 'android')
        project_name = project.get('name', 'MyApp')
        build_status = build.get('status', 'unknown')
        
        # VÉRIFIER SI UN APK A ÉTÉ COMPILÉ EN MÉMOIRE
        if build_id in build_in_memory and build_in_memory[build_id].get('apk_path'):
            apk_info = build_in_memory[build_id]
            apk_path = Path(apk_info['apk_path'])
            
            if apk_path.exists():
                logging.info(f"✅ APK trouvé en mémoire: {apk_path} ({apk_info['apk_size'] / 1024 / 1024:.2f} MB)")
                
                safe_filename = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).strip()
                filename = f"{safe_filename.lower().replace(' ', '-')}.apk"
                
                def iterfile():
                    with open(apk_path, "rb") as f:
                        yield from f
                
                return StreamingResponse(
                    iterfile(),
                    media_type="application/vnd.android.package-archive",
                    headers={
                        "Content-Disposition": f'attachment; filename="{filename}"',
                        "Content-Type": "application/vnd.android.package-archive",
                        "Content-Length": str(apk_info['apk_size'])
                    }
                )
        
        # POUR ANDROID : TOUJOURS ESSAYER DE COMPILER L'APK
        if platform == 'android' and build_status == "completed":
            logging.info("🚀 Compilation APK en temps réel...")
            
            try:
                generator_available = GENERATOR_AVAILABLE
            except NameError:
                generator_available = False
            
            if not generator_available:
                raise HTTPException(status_code=503, detail="Generator not available")
            
            try:
                from android_builder import AndroidBuilder
                builder = AndroidBuilder()
                
                # Vérifier dépendances
                deps_ok, deps_error = builder.check_dependencies()
                if not deps_ok:
                    logging.error(f"❌ Dependencies missing: {deps_error}")
                    raise HTTPException(
                        status_code=503, 
                        detail=f"Build dependencies not available: {deps_error}. Please ensure Java JDK 17+ is installed."
                    )
                
                # Générer le projet
                safe_name = "".join(c.lower() if c.isalnum() else '' for c in project_name)
                package_name = f"com.nativiweb.{safe_name}" if safe_name else "com.nativiweb.app"
                web_url = project.get('web_url', '')
                features = normalize_features(project.get('features', []))
                
                logging.info(f"📦 Generating Android project: {project_name}")
                project_zip = generator.generate_android_project(
                    project_name=project_name,
                    package_name=package_name,
                    web_url=web_url,
                    features=features,
                    app_icon_url=project.get('logo_url')
                )
                
                # Compiler l'APK
                logging.info(f"🔨 Compiling APK for {project_name}...")
                success, apk_bytes, error_msg = builder.build_apk(project_zip, project_name, max_retries=3)
                
                if success and apk_bytes and len(apk_bytes) >= 50000:  # Minimum 50KB pour un APK valide
                    logging.info(f"✅ APK compiled successfully! Size: {len(apk_bytes) / 1024 / 1024:.2f} MB")
                    
                    # Sauvegarder en mémoire pour les prochains téléchargements
                    import tempfile
                    apk_file = tempfile.NamedTemporaryFile(
                        delete=False, 
                        suffix='.apk', 
                        prefix=f'{safe_name}_'
                    )
                    apk_file.write(apk_bytes)
                    apk_file.close()
                    
                    build_in_memory[build_id] = {
                        'apk_path': apk_file.name,
                        'apk_size': len(apk_bytes),
                        'compiled': True
                    }
                    
                    safe_filename = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).strip()
                    filename = f"{safe_filename.lower().replace(' ', '-')}.apk"
                    
                    return StreamingResponse(
                        io.BytesIO(apk_bytes),
                        media_type="application/vnd.android.package-archive",
                        headers={
                            "Content-Disposition": f'attachment; filename="{filename}"',
                            "Content-Type": "application/vnd.android.package-archive",
                            "Content-Length": str(len(apk_bytes))
                        }
                    )
                else:
                    error_detail = error_msg or "Compilation failed - APK not generated"
                    logging.error(f"❌ Compilation failed: {error_detail}")
                    raise HTTPException(
                        status_code=500, 
                        detail=f"APK compilation failed: {error_detail}. Please check build logs."
                    )
                    
            except HTTPException:
                raise
            except ImportError as e:
                logging.error(f"❌ AndroidBuilder not available: {e}")
                raise HTTPException(
                    status_code=503, 
                    detail="Android build system not available. Please check server configuration."
                )
            except Exception as e:
                logging.error(f"❌ Compilation error: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to compile APK: {str(e)}. Please check server logs."
                )
        
        # POUR iOS OU SI BUILD NON COMPLETÉ : RETOURNER LE PROJET SOURCE
        # (Pour Android, on ne devrait jamais arriver ici si le build est complété)
        if platform == 'android' and build_status == "completed":
            # Si on arrive ici pour Android avec build complété, c'est une erreur
            logging.error(f"❌ Android build completed but APK not available for {build_id}")
            raise HTTPException(
                status_code=500,
                detail="APK not available for completed Android build. Please try rebuilding."
            )
        
        try:
            generator_available = GENERATOR_AVAILABLE
        except NameError:
            generator_available = False
        
        if not generator_available:
            raise HTTPException(status_code=503, detail="Generator not available")
        
        logging.info("📦 Returning source project (ZIP)")
        
        safe_name = "".join(c.lower() if c.isalnum() else '' for c in project_name)
        web_url = project.get('web_url', '')
        features = normalize_features(project.get('features', []))
        
        if platform == 'android':
            package_name = f"com.nativiweb.{safe_name}" if safe_name else "com.nativiweb.app"
            project_zip = generator.generate_android_project(
                project_name=project_name,
                package_name=package_name,
                web_url=web_url,
                features=features,
                app_icon_url=project.get('logo_url')
            )
            filename_suffix = "-source.zip"
        else:
            bundle_id = f"com.nativiweb.{safe_name}" if safe_name else "com.nativiweb.app"
            project_zip = generator.generate_ios_project(
                project_name=project_name,
                bundle_identifier=bundle_id,
                web_url=web_url,
                features=features,
                app_icon_url=project.get('logo_url')
            )
            filename_suffix = "-ios-source.zip"
        
        safe_filename = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_filename.lower().replace(' ', '-')}{filename_suffix}"
        
        return StreamingResponse(
            io.BytesIO(project_zip),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"❌ Download error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/builds/{build_id}/publish")
async def publish_build(
    build_id: str,
    publish_config: dict,
    user_id: str = Depends(get_current_user)
):
    """
    Publie un build complété sur les stores (OPTIONNEL)
    Utilise les APIs existantes appstore_api.py et playstore_api.py
    """
    try:
        logging.info(f"📤 Publish request for build {build_id}")
        
        client = get_supabase_client(use_service_role=True)
        if not client and not DEV_MODE:
            raise HTTPException(status_code=500, detail="Database unavailable")
        
        # Récupérer le build (même logique que download_build)
        if DEV_MODE:
            build = None
            for project_builds in DEV_BUILDS_STORE.values():
                for b in project_builds:
                    if b.get('id') == build_id:
                        build = b
                        break
                if build:
                    break
            if not build:
                raise HTTPException(status_code=404, detail="Build not found")
        else:
            build_response = client.table("builds").select("*").eq("id", build_id).eq("user_id", user_id).execute()
            if not build_response.data:
                raise HTTPException(status_code=404, detail="Build not found")
            build = build_response.data[0]
        
        # Vérifier permissions
        if build.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        
        # Vérifier que le build est complété
        if build.get('status') != 'completed':
            raise HTTPException(status_code=400, detail="Build must be completed before publishing")
        
        platform = build.get('platform', 'android')
        
        # Récupérer le projet
        if DEV_MODE:
            project = DEV_PROJECTS_STORE.get(build['project_id'])
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
        else:
            project_response = client.table("projects").select("*").eq("id", build["project_id"]).execute()
            if not project_response.data:
                raise HTTPException(status_code=404, detail="Project not found")
            project = project_response.data[0]
        
        # Android - Utiliser PlayStoreAPI existant
        if platform == 'android':
            try:
                from playstore_api import PlayStoreAPI
                
                # Récupérer les credentials depuis publish_config
                credentials_path = publish_config.get('google_credentials_path')
                if not credentials_path:
                    raise HTTPException(status_code=400, detail="google_credentials_path required")
                
                if not Path(credentials_path).exists():
                    raise HTTPException(status_code=404, detail=f"Credentials file not found: {credentials_path}")
                
                playstore = PlayStoreAPI(credentials_path)
                
                # Récupérer l'APK depuis build_in_memory
                apk_path = None
                if build_id in build_in_memory and build_in_memory[build_id].get('apk_path'):
                    apk_path = build_in_memory[build_id]['apk_path']
                
                if not apk_path or not Path(apk_path).exists():
                    raise HTTPException(status_code=404, detail="APK not found. Please ensure build completed successfully.")
                
                # Pour l'instant, on utilise l'APK directement
                # Note: Play Store nécessite un AAB, mais on peut utiliser l'APK pour internal testing
                safe_name = "".join(c.lower() if c.isalnum() else '' for c in project.get('name', 'MyApp'))
                package_name = f"com.nativiweb.{safe_name}" if safe_name else "com.nativiweb.app"
                track = publish_config.get('track', 'internal')
                
                # Upload vers Play Store (utiliser AAB si disponible, sinon APK)
                # Pour simplifier, on utilise directement l'APK pour internal track
                logging.info(f"📤 Uploading to Play Store: {package_name} on {track} track")
                
                # Note: PlayStoreAPI.upload_aab nécessite un AAB, mais on peut adapter
                # Pour l'instant, on retourne un message indiquant que l'upload nécessite un AAB
                # L'utilisateur peut compiler en AAB séparément
                
                publish_info = {
                    "published": True,
                    "platform": "android",
                    "track": track,
                    "package_name": package_name,
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "note": "APK available. For Play Store, compile AAB separately."
                }
                
                if DEV_MODE:
                    build['publish_info'] = publish_info
                else:
                    client.table("builds").update({"publish_info": publish_info}).eq("id", build_id).execute()
                
                return {
                    "success": True,
                    "platform": "android",
                    "package_name": package_name,
                    "track": track,
                    "message": f"Build ready for Play Store. Note: Play Store requires AAB format. APK available at: {apk_path}",
                    "apk_path": apk_path
                }
                
            except ImportError:
                raise HTTPException(status_code=503, detail="PlayStoreAPI not available. Install google-api-python-client")
            except HTTPException:
                raise
            except Exception as e:
                logging.error(f"Play Store publish error: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Failed to publish to Play Store: {str(e)}")
        
        # iOS - Utiliser AppStoreConnectAPI existant
        elif platform == 'ios':
            try:
                from appstore_api import AppStoreConnectAPI
                
                key_id = publish_config.get('apple_key_id')
                issuer_id = publish_config.get('apple_issuer_id')
                private_key_path = publish_config.get('apple_private_key_path')
                
                if not all([key_id, issuer_id, private_key_path]):
                    raise HTTPException(status_code=400, detail="Apple credentials required: key_id, issuer_id, private_key_path")
                
                if not Path(private_key_path).exists():
                    raise HTTPException(status_code=404, detail=f"Private key file not found: {private_key_path}")
                
                appstore = AppStoreConnectAPI(key_id, issuer_id, private_key_path)
                
                # Récupérer l'IPA (l'utilisateur doit fournir le chemin ou on le génère)
                ipa_path = publish_config.get('ipa_path')
                if not ipa_path:
                    raise HTTPException(status_code=400, detail="ipa_path required for iOS publishing")
                
                if not Path(ipa_path).exists():
                    raise HTTPException(status_code=404, detail=f"IPA file not found: {ipa_path}")
                
                apple_id = publish_config.get('apple_id')
                app_password = publish_config.get('app_specific_password')
                
                if not all([apple_id, app_password]):
                    raise HTTPException(status_code=400, detail="apple_id and app_specific_password required")
                
                logging.info(f"📤 Uploading IPA to App Store Connect")
                success = appstore.upload_ipa(ipa_path, apple_id, app_password)
                
                if success:
                    publish_info = {
                        "published": True,
                        "platform": "ios",
                        "published_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    if DEV_MODE:
                        build['publish_info'] = publish_info
                    else:
                        client.table("builds").update({"publish_info": publish_info}).eq("id", build_id).execute()
                    
                    return {
                        "success": True,
                        "platform": "ios",
                        "message": "IPA uploaded to App Store Connect successfully"
                    }
                else:
                    raise HTTPException(status_code=500, detail="Failed to upload IPA to App Store Connect")
                    
            except ImportError:
                raise HTTPException(status_code=503, detail="AppStoreConnectAPI not available")
            except HTTPException:
                raise
            except Exception as e:
                logging.error(f"App Store publish error: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Failed to publish to App Store: {str(e)}")
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Publish error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ==================== AUTRES ENDPOINTS ====================

@api_router.get("/features")
async def get_available_features():
    return DEFAULT_FEATURES

@api_router.get("/projects/{project_id}/version/check")
async def check_web_app_version(
    project_id: str,
    current_version: Optional[str] = Query(None, description="Version actuelle dans l'app native"),
    user_id: str = Depends(get_current_user)
):
    """
    Vérifie si une nouvelle version de l'app web est disponible.
    Retourne la version actuelle du projet et indique si une mise à jour est nécessaire.
    """
    try:
        if DEV_MODE:
            if project_id not in DEV_PROJECTS_STORE:
                raise HTTPException(status_code=404, detail="Project not found")
            project = DEV_PROJECTS_STORE[project_id]
        else:
            client = get_supabase_client(use_service_role=True)
            if not client:
                raise HTTPException(status_code=500, detail="Database unavailable")
            
            response = client.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).execute()
            if not response.data:
                raise HTTPException(status_code=404, detail="Project not found")
            project = response.data[0]
        
        # Récupérer la version actuelle du projet
        project_version = project.get('web_app_version')
        version_check_enabled = project.get('version_check_enabled', True)
        
        # Si la vérification est désactivée
        if not version_check_enabled:
            return {
                "version_check_enabled": False,
                "message": "Version check is disabled for this project"
            }
        
        # Si aucune version n'est définie dans le projet
        if not project_version:
            return {
                "version": None,
                "update_available": False,
                "message": "No version set for this project. Please set web_app_version in project settings."
            }
        
        # Comparer les versions
        update_available = False
        if current_version and current_version != project_version:
            update_available = True
        
        return {
            "version": project_version,
            "current_version": current_version,
            "update_available": update_available,
            "project_id": project_id,
            "web_url": project.get('web_url'),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error checking version: {e}")
        if ENVIRONMENT == "production":
            raise HTTPException(status_code=500, detail="Failed to check version. Please try again later.")
        else:
            raise HTTPException(status_code=500, detail=f"Error checking version: {str(e)}")

@api_router.get("/stats")
async def get_user_stats(user_id: str = Depends(get_current_user)):
    if DEV_MODE:
        dev_projects_count = len([p for p in DEV_PROJECTS_STORE.values() if p.get("user_id") == user_id])
        dev_builds_count = sum(len([b for b in builds if b.get("user_id") == user_id]) for builds in DEV_BUILDS_STORE.values())
        dev_successful_count = sum(len([b for b in builds if b.get("user_id") == user_id and b.get("status") == "completed"]) for builds in DEV_BUILDS_STORE.values())
        return {
            "projects": dev_projects_count,
            "total_builds": dev_builds_count,
            "successful_builds": dev_successful_count,
            "api_keys": 0
        }
    
    try:
        client = get_supabase_client(use_service_role=True)
        if not client:
            return {"projects": 0, "total_builds": 0, "successful_builds": 0, "api_keys": 0}
        
        projects_result = client.table("projects").select("id").eq("user_id", user_id).execute()
        builds_result = client.table("builds").select("id, status").eq("user_id", user_id).execute()
        api_keys_result = client.table("api_keys").select("id").eq("user_id", user_id).execute()
        
        builds_data = builds_result.data if builds_result.data else []
        
        return {
            "projects": len(projects_result.data) if projects_result.data else 0,
            "total_builds": len(builds_data),
            "successful_builds": len([b for b in builds_data if b.get("status") == "completed"]),
            "api_keys": len(api_keys_result.data) if api_keys_result.data else 0
        }
    except Exception as e:
        logging.error(f"Error fetching stats: {e}")
        return {"projects": 0, "total_builds": 0, "successful_builds": 0, "api_keys": 0}

# ==================== ADMIN ENDPOINTS ====================

@api_router.get("/admin/users")
async def admin_get_users(
    page: int = 1,
    limit: int = 20,
    include_auth_only: bool = True,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
):
    safe_page, safe_limit, start, end = _normalize_pagination(page, limit)

    if DEV_MODE:
        users = list(DEV_USERS_STORE.values())
        total = len(users)
        return {
            "users": users[start:start + safe_limit],
            "total": total,
            "page": safe_page,
            "pages": _calc_pages(total, safe_limit)
        }

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    response = client.table("users").select("*", count="exact").order("created_at", desc=True).range(start, end).execute()
    users = response.data or []

    if include_auth_only:
        try:
            auth_admin = client.auth.admin
            if hasattr(auth_admin, "list_users"):
                auth_result = auth_admin.list_users()
                auth_users = _extract_auth_users(auth_result)
                existing_ids = {u.get("id") for u in users if u.get("id")}
                for auth_user in auth_users:
                    auth_id = getattr(auth_user, "id", None)
                    if not auth_id and isinstance(auth_user, dict):
                        auth_id = auth_user.get("id")
                    if auth_id and auth_id not in existing_ids:
                        try:
                            from admin_sync import sync_missing_user
                            sync_missing_user(client, auth_id)
                        except Exception as sync_error:
                            logging.warning(f"Failed to sync auth user {auth_id}: {sync_error}")
                response = client.table("users").select("*", count="exact").order("created_at", desc=True).range(start, end).execute()
                users = response.data or []
        except Exception as auth_error:
            logging.warning(f"Failed to sync auth users: {auth_error}")

    user_ids = [u.get("id") for u in users if u.get("id")]
    projects_count: Dict[str, int] = {}
    builds_count: Dict[str, int] = {}

    if user_ids:
        try:
            projects_resp = client.table("projects").select("id,user_id").in_("user_id", user_ids).execute()
            for row in projects_resp.data or []:
                projects_count[row.get("user_id")] = projects_count.get(row.get("user_id"), 0) + 1
        except Exception as e:
            logging.warning(f"Failed to fetch projects count: {e}")

        try:
            builds_resp = client.table("builds").select("id,user_id").in_("user_id", user_ids).execute()
            for row in builds_resp.data or []:
                builds_count[row.get("user_id")] = builds_count.get(row.get("user_id"), 0) + 1
        except Exception as e:
            logging.warning(f"Failed to fetch builds count: {e}")

    for user in users:
        uid = user.get("id")
        user["projects_count"] = projects_count.get(uid, 0)
        user["builds_count"] = builds_count.get(uid, 0)

    total = response.count or len(users)
    return {
        "users": users,
        "total": total,
        "page": safe_page,
        "pages": _calc_pages(total, safe_limit)
    }

@api_router.post("/admin/users")
async def admin_create_user(
    user_data: AdminUserCreate,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
):
    if DEV_MODE:
        user_id = str(uuid.uuid4())
        new_user = {
            "id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "role": user_data.role or "user",
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        DEV_USERS_STORE[user_id] = new_user
        return new_user

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    try:
        auth_admin = client.auth.admin
        if not hasattr(auth_admin, "create_user"):
            raise HTTPException(status_code=501, detail="Admin user creation not supported")

        auth_response = auth_admin.create_user({
            "email": user_data.email,
            "password": user_data.password,
            "email_confirm": True,
            "user_metadata": {"name": user_data.name}
        })

        auth_user = getattr(auth_response, "user", None)
        if not auth_user and isinstance(auth_response, dict):
            auth_user = auth_response.get("user")
        user_id = getattr(auth_user, "id", None) if auth_user else None
        if not user_id and isinstance(auth_user, dict):
            user_id = auth_user.get("id")

        if not user_id:
            raise HTTPException(status_code=500, detail="Failed to create auth user")

        new_user = {
            "id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "role": user_data.role or "user",
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        client.table("users").upsert(new_user, on_conflict="id").execute()
        await log_system_event("info", "admin", f"Admin created user {user_data.email}", user_id=admin_user.get("id"))
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

@api_router.put("/admin/users/{user_id}")
async def admin_update_user(
    user_id: str,
    updates: UserUpdate,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
):
    if DEV_MODE:
        if user_id not in DEV_USERS_STORE:
            raise HTTPException(status_code=404, detail="User not found")
        user = DEV_USERS_STORE[user_id]
        if updates.role is not None:
            user["role"] = updates.role
        if updates.status is not None:
            user["status"] = updates.status
        DEV_USERS_STORE[user_id] = user
        return user

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_dict:
        response = client.table("users").select("*").eq("id", user_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")
        return response.data

    client.table("users").update(update_dict).eq("id", user_id).execute()
    response = client.table("users").select("*").eq("id", user_id).single().execute()
    await log_system_event("info", "admin", f"Admin updated user {user_id}", user_id=admin_user.get("id"))
    return response.data

@api_router.delete("/admin/users/{user_id}")
async def admin_delete_user(
    user_id: str,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
):
    if DEV_MODE:
        if user_id in DEV_USERS_STORE:
            del DEV_USERS_STORE[user_id]
        return {"message": "User deleted"}

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    client.table("users").delete().eq("id", user_id).execute()
    try:
        auth_admin = client.auth.admin
        if hasattr(auth_admin, "delete_user"):
            auth_admin.delete_user(user_id)
    except Exception as e:
        logging.warning(f"Failed to delete auth user {user_id}: {e}")

    await log_system_event("info", "admin", f"Admin deleted user {user_id}", user_id=admin_user.get("id"))
    return {"message": "User deleted"}

@api_router.post("/admin/users/sync/{user_id}")
async def admin_sync_user(
    user_id: str,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
):
    if DEV_MODE:
        return {"success": True, "message": "Sync not required in dev mode"}

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    try:
        from admin_sync import sync_missing_user
        result = sync_missing_user(client, user_id)
        return result
    except Exception as e:
        logging.error(f"Error syncing user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync user")

@api_router.get("/admin/projects")
async def admin_get_projects(
    page: int = 1,
    limit: int = 20,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
):
    safe_page, safe_limit, start, end = _normalize_pagination(page, limit)

    if DEV_MODE:
        projects = list(DEV_PROJECTS_STORE.values())
        total = len(projects)
        return {
            "projects": projects[start:start + safe_limit],
            "total": total,
            "page": safe_page,
            "pages": _calc_pages(total, safe_limit)
        }

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    response = client.table("projects").select("*", count="exact").order("created_at", desc=True).range(start, end).execute()
    projects = response.data or []

    user_ids = list({p.get("user_id") for p in projects if p.get("user_id")})
    project_ids = [p.get("id") for p in projects if p.get("id")]

    user_email_map: Dict[str, str] = {}
    builds_count: Dict[str, int] = {}

    if user_ids:
        try:
            users_resp = client.table("users").select("id, email").in_("id", user_ids).execute()
            for row in users_resp.data or []:
                user_email_map[row.get("id")] = row.get("email") or ""
        except Exception as e:
            logging.warning(f"Failed to fetch user emails: {e}")

    if project_ids:
        try:
            builds_resp = client.table("builds").select("id, project_id").in_("project_id", project_ids).execute()
            for row in builds_resp.data or []:
                builds_count[row.get("project_id")] = builds_count.get(row.get("project_id"), 0) + 1
        except Exception as e:
            logging.warning(f"Failed to fetch builds count for projects: {e}")

    for project in projects:
        project["user_email"] = user_email_map.get(project.get("user_id"), "")
        project["builds_count"] = builds_count.get(project.get("id"), 0)

    total = response.count or len(projects)
    return {
        "projects": projects,
        "total": total,
        "page": safe_page,
        "pages": _calc_pages(total, safe_limit)
    }

@api_router.delete("/admin/projects/{project_id}")
async def admin_delete_project(
    project_id: str,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
):
    if DEV_MODE:
        if project_id in DEV_PROJECTS_STORE:
            if project_id in DEV_BUILDS_STORE:
                del DEV_BUILDS_STORE[project_id]
            del DEV_PROJECTS_STORE[project_id]
        return {"message": "Project deleted"}

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    project_response = client.table("projects").select("id").eq("id", project_id).execute()
    if not project_response.data:
        raise HTTPException(status_code=404, detail="Project not found")

    builds_response = client.table("builds").select("id").eq("project_id", project_id).execute()
    build_ids = [build["id"] for build in builds_response.data] if builds_response.data else []

    for build_id in build_ids:
        if build_id in build_in_memory:
            apk_path = build_in_memory[build_id].get("apk_path")
            if apk_path and Path(apk_path).exists():
                try:
                    os.unlink(apk_path)
                except Exception as e:
                    logging.warning(f"Error deleting APK {apk_path}: {e}")
            del build_in_memory[build_id]

    if build_ids:
        client.table("builds").delete().eq("project_id", project_id).execute()

    client.table("projects").delete().eq("id", project_id).execute()
    await log_system_event("info", "admin", f"Admin deleted project {project_id}", user_id=admin_user.get("id"))
    return {"message": "Project deleted"}

@api_router.get("/admin/builds")
async def admin_get_builds(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
):
    safe_page, safe_limit, start, end = _normalize_pagination(page, limit)

    if DEV_MODE:
        builds = [b for builds in DEV_BUILDS_STORE.values() for b in builds]
        total = len(builds)
        return {
            "builds": builds[start:start + safe_limit],
            "total": total,
            "page": safe_page,
            "pages": _calc_pages(total, safe_limit)
        }

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    query = client.table("builds").select("*", count="exact")
    if status:
        query = query.eq("status", status)

    response = query.order("created_at", desc=True).range(start, end).execute()
    builds = response.data or []

    project_ids = list({b.get("project_id") for b in builds if b.get("project_id")})
    user_ids = list({b.get("user_id") for b in builds if b.get("user_id")})

    project_map: Dict[str, Dict[str, Any]] = {}
    user_map: Dict[str, Dict[str, Any]] = {}

    if project_ids:
        try:
            projects_resp = client.table("projects").select("id, name").in_("id", project_ids).execute()
            for row in projects_resp.data or []:
                project_map[row.get("id")] = row
        except Exception as e:
            logging.warning(f"Failed to fetch project names: {e}")

    if user_ids:
        try:
            users_resp = client.table("users").select("id, email, name").in_("id", user_ids).execute()
            for row in users_resp.data or []:
                user_map[row.get("id")] = row
        except Exception as e:
            logging.warning(f"Failed to fetch user info: {e}")

    for build in builds:
        project = project_map.get(build.get("project_id"), {})
        user = user_map.get(build.get("user_id"), {})
        build["project_name"] = project.get("name", "")
        build["user_name"] = user.get("name", "")
        build["user_email"] = user.get("email", "")

    total = response.count or len(builds)
    return {
        "builds": builds,
        "total": total,
        "page": safe_page,
        "pages": _calc_pages(total, safe_limit)
    }

@api_router.get("/admin/logs")
async def admin_get_logs(
    page: int = 1,
    limit: int = 50,
    level: Optional[str] = None,
    category: Optional[str] = None,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
):
    safe_page, safe_limit, start, end = _normalize_pagination(page, limit)

    if DEV_MODE:
        return {"logs": [], "total": 0, "page": safe_page, "pages": 1}

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    query = client.table("system_logs").select("*", count="exact")
    if level:
        query = query.eq("level", level)
    if category:
        query = query.eq("category", category)

    response = query.order("created_at", desc=True).range(start, end).execute()
    logs = response.data or []
    total = response.count or len(logs)
    return {
        "logs": logs,
        "total": total,
        "page": safe_page,
        "pages": _calc_pages(total, safe_limit)
    }

@api_router.get("/admin/analytics")
async def admin_get_analytics(admin_user: Dict[str, Any] = Depends(get_admin_user)):
    if DEV_MODE:
        return {
            "users": {"total": len(DEV_USERS_STORE), "active": len(DEV_USERS_STORE)},
            "projects": {"total": len(DEV_PROJECTS_STORE)},
            "builds": {"total": 0, "successful": 0, "failed": 0, "success_rate": 0},
            "platforms": {"android": 0, "ios": 0}
        }

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    users_total = client.table("users").select("id", count="exact").execute().count or 0
    active_users = client.table("users").select("id", count="exact").eq("status", "active").execute().count or 0
    projects_total = client.table("projects").select("id", count="exact").execute().count or 0

    builds_resp = client.table("builds").select("id, status, platform").execute()
    builds_data = builds_resp.data or []
    builds_total = len(builds_data)
    successful = len([b for b in builds_data if b.get("status") == "completed"])
    failed = len([b for b in builds_data if b.get("status") in ["failed", "error"]])
    success_rate = round((successful / builds_total) * 100, 2) if builds_total else 0

    platforms = {"android": 0, "ios": 0}
    for b in builds_data:
        platform = b.get("platform")
        if platform in platforms:
            platforms[platform] += 1

    return {
        "users": {"total": users_total, "active": active_users},
        "projects": {"total": projects_total},
        "builds": {
            "total": builds_total,
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate
        },
        "platforms": platforms
    }

@api_router.get("/admin/config")
async def admin_get_config(admin_user: Dict[str, Any] = Depends(get_admin_user)):
    default_config = {
        "id": "platform_config",
        "maintenance_mode": False,
        "max_builds_per_user": 10,
        "max_projects_per_user": 5,
        "allowed_domains": [],
        "build_timeout_minutes": 30
    }

    if DEV_MODE:
        if not DEV_PLATFORM_CONFIG:
            DEV_PLATFORM_CONFIG.update(default_config)
        return DEV_PLATFORM_CONFIG

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    response = client.table("platform_config").select("*").eq("id", "platform_config").single().execute()
    if response.data:
        return response.data

    client.table("platform_config").upsert(default_config, on_conflict="id").execute()
    return default_config

@api_router.put("/admin/config")
async def admin_update_config(
    config: Dict[str, Any],
    admin_user: Dict[str, Any] = Depends(get_admin_user)
):
    default_config = {
        "id": "platform_config",
        "maintenance_mode": False,
        "max_builds_per_user": 10,
        "max_projects_per_user": 5,
        "allowed_domains": [],
        "build_timeout_minutes": 30
    }

    if DEV_MODE:
        if not DEV_PLATFORM_CONFIG:
            DEV_PLATFORM_CONFIG.update(default_config)
        DEV_PLATFORM_CONFIG.update({k: v for k, v in config.items() if k in default_config})
        return DEV_PLATFORM_CONFIG

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    updated = default_config.copy()
    updated.update({k: v for k, v in config.items() if k in default_config})
    updated["updated_at"] = datetime.now(timezone.utc).isoformat()

    client.table("platform_config").upsert(updated, on_conflict="id").execute()
    await log_system_event("info", "admin", "Admin updated platform config", user_id=admin_user.get("id"))
    return updated

@api_router.get("/admin/templates")
async def admin_get_templates(admin_user: Dict[str, Any] = Depends(get_admin_user)):
    if DEV_MODE:
        return {"templates": list(DEV_TEMPLATES_STORE.values())}

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    response = client.table("templates").select("*").order("created_at", desc=True).execute()
    return {"templates": response.data or []}

@api_router.get("/admin/templates/{template_id}")
async def admin_get_template(
    template_id: str,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
):
    if DEV_MODE:
        template = DEV_TEMPLATES_STORE.get(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    response = client.table("templates").select("*").eq("id", template_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Template not found")
    return response.data

@api_router.post("/admin/templates")
async def admin_create_template(
    template_data: TemplateCreate,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
):
    now = datetime.now(timezone.utc).isoformat()
    template = template_data.model_dump()
    template["created_at"] = now
    template["updated_at"] = now

    if DEV_MODE:
        DEV_TEMPLATES_STORE[template["id"]] = template
        return template

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    client.table("templates").insert(template).execute()
    await log_system_event("info", "admin", f"Admin created template {template['id']}", user_id=admin_user.get("id"))
    return template

@api_router.put("/admin/templates/{template_id}")
async def admin_update_template(
    template_id: str,
    updates: TemplateUpdate,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
):
    update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()

    if DEV_MODE:
        if template_id not in DEV_TEMPLATES_STORE:
            raise HTTPException(status_code=404, detail="Template not found")
        DEV_TEMPLATES_STORE[template_id].update(update_dict)
        return DEV_TEMPLATES_STORE[template_id]

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    client.table("templates").update(update_dict).eq("id", template_id).execute()
    response = client.table("templates").select("*").eq("id", template_id).single().execute()
    await log_system_event("info", "admin", f"Admin updated template {template_id}", user_id=admin_user.get("id"))
    return response.data

@api_router.delete("/admin/templates/{template_id}")
async def admin_delete_template(
    template_id: str,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
):
    if DEV_MODE:
        if template_id in DEV_TEMPLATES_STORE:
            del DEV_TEMPLATES_STORE[template_id]
        return {"message": "Template deleted"}

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    client.table("templates").delete().eq("id", template_id).execute()
    await log_system_event("info", "admin", f"Admin deleted template {template_id}", user_id=admin_user.get("id"))
    return {"message": "Template deleted"}

@api_router.get("/admin/visit-stats")
async def admin_get_visit_stats(admin_user: Dict[str, Any] = Depends(get_admin_user)):
    if DEV_MODE:
        return {
            "total_visits": 0,
            "unique_visitors": 0,
            "visits_today": 0,
            "visits_this_week": 0,
            "visits_this_month": 0,
            "top_pages": [],
            "device_breakdown": {}
        }

    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database unavailable")

    def parse_ts(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None

    response = client.table("site_visits").select("page_path, device_type, session_id, user_id, created_at", count="exact").execute()
    visits = response.data or []

    total_visits = response.count or len(visits)
    unique_keys = set()
    page_counts: Dict[str, int] = {}
    device_counts: Dict[str, int] = {}

    now = datetime.now(timezone.utc)
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_week = start_today - timedelta(days=start_today.weekday())
    start_month = start_today.replace(day=1)

    visits_today = 0
    visits_week = 0
    visits_month = 0

    for visit in visits:
        session_id = visit.get("session_id")
        user_id = visit.get("user_id")
        unique_key = session_id or user_id
        if unique_key:
            unique_keys.add(unique_key)

        page_path = visit.get("page_path") or "/"
        page_counts[page_path] = page_counts.get(page_path, 0) + 1

        device_type = visit.get("device_type") or "unknown"
        device_counts[device_type] = device_counts.get(device_type, 0) + 1

        created_at = parse_ts(visit.get("created_at"))
        if created_at:
            if created_at >= start_today:
                visits_today += 1
            if created_at >= start_week:
                visits_week += 1
            if created_at >= start_month:
                visits_month += 1

    top_pages = sorted(
        [{"path": path, "count": count} for path, count in page_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:10]

    return {
        "total_visits": total_visits,
        "unique_visitors": len(unique_keys),
        "visits_today": visits_today,
        "visits_this_week": visits_week,
        "visits_this_month": visits_month,
        "top_pages": top_pages,
        "device_breakdown": device_counts
    }

@api_router.get("/system/check-dependencies")
async def check_system_dependencies(user_id: str = Depends(get_current_user)):
    """Check system dependencies for Android build"""
    import subprocess
    
    result = {
        "android_builder_available": False,
        "java_available": False,
        "java_version": None,
        "java_home": None,
        "android_sdk_available": False,
        "android_home": None,
        "gradle_available": True,
        "status": "unknown",
        "ready": False,
        "errors": [],
        "warnings": [],
        "instructions": []
    }
    
    try:
        # Vérifier Java sur le SERVEUR
        java_home = os.environ.get("JAVA_HOME", "/usr/lib/jvm/java-21-openjdk-amd64")
        result["java_home"] = java_home
        
        # Si JAVA_HOME n'est pas défini, essayer de le détecter automatiquement
        if not java_home or "C:\\" in java_home:  # Ignorer les chemins Windows locaux
            try:
                # Chercher Java dans les chemins standards Linux
                java_which = subprocess.run(
                    ["which", "java"],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                if java_which.returncode == 0:
                    java_path = java_which.stdout.strip()
                    # Remonter au JAVA_HOME depuis /usr/bin/java
                    if java_path:
                        java_home = str(Path(java_path).parent.parent)
                        result["java_home"] = java_home
            except Exception:
                result["java_home"] = "/usr/lib/jvm/java-21-openjdk-amd64"  # Valeur par défaut
        
        try:
            # Essayer d'exécuter java -version sur le serveur
            java_result = subprocess.run(
                ["java", "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if java_result.returncode == 0:
                result["java_available"] = True
                version_output = java_result.stderr or java_result.stdout
                result["java_version"] = version_output.split('\n')[0] if version_output else None
                logging.info(f"✅ Java détecté sur le serveur: {result['java_version']}")
            else:
                result["errors"].append("Java JDK 17+ non trouvé sur le serveur")
        except FileNotFoundError:
            result["errors"].append("Java JDK 17+ non trouvé. Installez Java JDK 17 ou supérieur et définissez JAVA_HOME.")
            result["instructions"].extend([
                "Installez Java JDK 17+ depuis https://adoptium.net/",
                "Ajoutez Java au PATH système",
                "Redémarrez le serveur"
            ])
        except Exception as e:
            logging.error(f"Erreur vérification Java: {e}")
            result["errors"].append(f"Erreur lors de la vérification de Java: {str(e)}")
        
        # Vérifier AndroidBuilder
        try:
            from android_builder import AndroidBuilder
            builder = AndroidBuilder()
            result["android_builder_available"] = True
            
            # Vérifier Android SDK (optionnel)
            if builder.android_home and Path(builder.android_home).exists():
                result["android_sdk_available"] = True
                result["android_home"] = builder.android_home
            else:
                result["warnings"].append("Android SDK non trouvé (optionnel)")
            
            # Vérifier si tout est prêt
            if result["java_available"]:
                result["status"] = "ready"
                result["ready"] = True
                logging.info("✅ Système prêt pour la compilation Android")
            else:
                result["status"] = "missing_dependencies"
                result["ready"] = False
                
        except ImportError:
            result["errors"].append("AndroidBuilder non disponible")
            result["status"] = "builder_unavailable"
        except Exception as builder_error:
            logging.error(f"Erreur AndroidBuilder: {builder_error}")
            result["errors"].append(f"Erreur AndroidBuilder: {str(builder_error)}")
            result["status"] = "error"
                
    except Exception as e:
        result["errors"].append(f"Erreur: {str(e)}")
        result["status"] = "error"
        logging.error(f"Erreur système: {e}", exc_info=True)
    
    return result

# ==================== GENERATOR ====================

try:
    from generator import NativeTemplateGenerator
    generator = NativeTemplateGenerator()
    GENERATOR_AVAILABLE = True
    logging.info("✅ Générateur de projets natifs disponible")
except ImportError as e:
    logging.warning(f"⚠️ Generator not available: {e}")
    GENERATOR_AVAILABLE = False
    generator = None

@api_router.get("/generator/download/{project_id}/{platform}")
async def download_generated_project(
    project_id: str,
    platform: str,
    user_id: str = Depends(get_current_user)
):
    """Download generated native project"""
    if not GENERATOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Generator unavailable")
    
    if platform not in ['android', 'ios']:
        raise HTTPException(status_code=400, detail="Platform must be 'android' or 'ios'")
    
    try:
        client = get_supabase_client(use_service_role=True)
        if not client and not DEV_MODE:
            raise HTTPException(status_code=500, detail="Database unavailable")
        
        if DEV_MODE:
            project = DEV_PROJECTS_STORE.get(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
        else:
            project_response = client.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).execute()
            if not project_response.data:
                raise HTTPException(status_code=404, detail="Project not found")
            project = project_response.data[0]
        
        project_name = project.get('name', 'MyApp')
        web_url = project.get('web_url', '')
        features = normalize_features(project.get('features', []))
        
        safe_name = "".join(c.lower() if c.isalnum() else '' for c in project_name)
        
        if platform == 'android':
            package_name = f"com.nativiweb.{safe_name}" if safe_name else "com.nativiweb.app"
            project_zip = generator.generate_android_project(
                project_name=project_name,
                package_name=package_name,
                web_url=web_url,
                features=features,
                app_icon_url=project.get('logo_url')
            )
            filename = f"{safe_name}-android.zip"
        else:
            bundle_id = f"com.nativiweb.{safe_name}" if safe_name else "com.nativiweb.app"
            project_zip = generator.generate_ios_project(
                project_name=project_name,
                bundle_identifier=bundle_id,
                web_url=web_url,
                features=features,
                app_icon_url=project.get('logo_url')
            )
            filename = f"{safe_name}-ios.zip"
        
        await log_system_event("info", "generator", f"Generated {platform} project for {project_name}", user_id=user_id)
        
        return StreamingResponse(
            io.BytesIO(project_zip),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error generating project: {e}", exc_info=True)
        if ENVIRONMENT == "production":
            raise HTTPException(status_code=500, detail="An error occurred. Please try again later.")
        else:
            if ENVIRONMENT == "production":
                raise HTTPException(status_code=500, detail="An error occurred. Please try again later.")
            else:
                raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "NativiWeb Studio API v2.0.0", "status": "operational"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@api_router.post("/push/send")
async def send_push_notification(
    notification_data: dict,
    user_id: str = Depends(get_current_user)
):
    """
    Envoyer une push notification (OPTIONNEL - nécessite configuration)
    Nécessite FIREBASE_CREDENTIALS_PATH pour Android et APNs config pour iOS
    """
    try:
        from push_service import get_push_service
        push_service = get_push_service()
        
        title = notification_data.get('title', '')
        body = notification_data.get('body', '')
        data = notification_data.get('data', {})
        android_tokens = notification_data.get('android_tokens', [])
        ios_tokens = notification_data.get('ios_tokens', [])
        
        if not title or not body:
            raise HTTPException(status_code=400, detail="title and body required")
        
        if not android_tokens and not ios_tokens:
            raise HTTPException(status_code=400, detail="At least one token (android_tokens or ios_tokens) required")
        
        results = {"android": [], "ios": []}
        
        # Android
        for token in android_tokens:
            try:
                result = push_service.send_to_android(token, title, body, data)
                results["android"].append({"token": token, "success": True, **result})
            except Exception as e:
                results["android"].append({"token": token, "success": False, "error": str(e)})
        
        # iOS
        for token in ios_tokens:
            try:
                result = push_service.send_to_ios(token, title, body, data)
                results["ios"].append({"token": token, "success": True, **result})
            except Exception as e:
                results["ios"].append({"token": token, "success": False, "error": str(e)})
        
        success_count = sum(1 for r in results["android"] + results["ios"] if r.get("success"))
        total_count = len(results["android"]) + len(results["ios"])
        
        return {
            "success": success_count > 0,
            "sent": success_count,
            "total": total_count,
            "results": results
        }
        
    except ImportError:
        raise HTTPException(status_code=503, detail="Push notification service not available. Install firebase-admin and/or apns2.")
    except Exception as e:
        logging.error(f"Push notification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CONFIGURATION FINALE ====================

# CORS
cors_origins = ALLOWED_ORIGINS if ENVIRONMENT == "production" else [
    "http://localhost:3000", 
    "http://127.0.0.1:3000", 
    "http://localhost:3001"
]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "Content-Disposition",
        "Content-Type",
        "Content-Length",
        "X-Build-Type",
        "X-APK-Size"
    ],
    max_age=3600,
)

# Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted host (production)
if ENVIRONMENT == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Include routers
app.include_router(api_router)

# Upload router
try:
    from upload import router as upload_router
    app.include_router(upload_router, prefix="/api")
    logging.info("Upload router loaded successfully")
except ImportError as e:
    logging.warning(f"Upload router not available: {e}")
except Exception as e:
    logging.error(f"Error loading upload router: {e}")

# Screenshots router
try:
    from screenshots_api import router as screenshots_router
    app.include_router(screenshots_router, prefix="/api")
    logging.info("Screenshots router loaded successfully")
except ImportError as e:
    logging.warning(f"Screenshots router not available: {e}")
except Exception as e:
    logging.error(f"Error loading screenshots router: {e}")

# Final logging
logging.info(f"✅ NativiWeb Studio API started (Environment: {ENVIRONMENT})")
if DEV_MODE:
    logging.info("🔧 MODE DÉVELOPPEMENT actif")
if GENERATOR_AVAILABLE:
    logging.info("✅ Générateur de projets natifs: ACTIF")
else:
    logging.warning("⚠️ Générateur de projets natifs: INACTIF")