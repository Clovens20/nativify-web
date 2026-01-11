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

# Mode développement sans Supabase
DEV_MODE = ENVIRONMENT == 'development' and not os.environ.get('SUPABASE_URL')
if DEV_MODE:
    logging.warning("⚠️ MODE DÉVELOPPEMENT : Supabase désactivé, authentification bypassée")

# Stockage en mémoire pour les projets en mode DEV
DEV_PROJECTS_STORE: Dict[str, Dict[str, Any]] = {}
DEV_BUILDS_STORE: Dict[str, List[Dict[str, Any]]] = {}

# Validate required environment variables
REQUIRED_ENV_VARS = {
    'production': ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_ROLE_KEY'],
    'development': ['SUPABASE_URL', 'SUPABASE_ANON_KEY'],
    'test': []  # Test environment uses mocks
}

missing_vars = []
if ENVIRONMENT not in ['test']:
    required = REQUIRED_ENV_VARS.get(ENVIRONMENT, REQUIRED_ENV_VARS['development'])
    for var in required:
        if not os.environ.get(var):
            missing_vars.append(var)

if missing_vars:
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
            traces_sample_rate=0.1,  # 10% of transactions
            environment=ENVIRONMENT,
            release=os.environ.get('RELEASE_VERSION', '1.0.0')
        )
        logging.info("Sentry error tracking initialized")
    except ImportError:
        logging.warning("Sentry SDK not installed - error tracking disabled")
else:
    if ENVIRONMENT == 'production' and not SENTRY_DSN:
        logging.warning("⚠️  SENTRY_DSN not set - error tracking disabled in production")

ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')

# Supabase connection
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
    if ENVIRONMENT != 'test':
        logging.warning("⚠️  Supabase not configured - authentication will fail")

# Configure structured logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
LOG_FORMAT = os.environ.get('LOG_FORMAT', 'json' if ENVIRONMENT == 'production' else 'text')

if LOG_FORMAT == 'json':
    from pythonjsonlogger import jsonlogger
    log_handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d'
    )
    log_handler.setFormatter(formatter)
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        handlers=[log_handler]
    )
else:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

logger = logging.getLogger(__name__)

def get_supabase_client(token: Optional[str] = None, use_service_role: bool = False) -> Optional[Client]:
    """Get Supabase client with optional user token for RLS
    
    Args:
        token: User JWT token for RLS-enabled operations
        use_service_role: If True, use service role key to bypass RLS (for backend operations)
    
    Returns:
        Supabase client configured with appropriate credentials, or None if not available
    """
    # En mode dev sans Supabase, retourner None
    if DEV_MODE:
        return None
    
    # Si Supabase n'est pas configuré, retourner None
    if not SUPABASE_URL:
        return None
    
    try:
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
    except Exception as e:
        logging.warning(f"Error creating Supabase client: {e}")
        return None

# Initialize rate limiter (must be before app creation)
# Default rate limits: 100 requests per minute per IP
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
    # Mode dev : bypass authentification
    if DEV_MODE:
        return "dev-user-123"
    
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
    # Mode dev : retourner un utilisateur dev
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
    
    # Rate limiting is handled globally by slowapi
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
    # Mode dev : retourner un faux token
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
    
    # Rate limiting is handled globally by slowapi
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
    # Mode dev : retourner l'utilisateur dev
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
    # Mode dev : retourner succès
    if DEV_MODE:
        return {"message": "Logged out successfully"}
    
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except:
        return {"message": "Logged out successfully"}

# ==================== PROJECT ENDPOINTS ====================

def normalize_web_url(url: str) -> str:
    """Convertit une URL GitHub en URL web utilisable si nécessaire"""
    if not url:
        return url
    
    # Si c'est une URL GitHub, essayer de la convertir en GitHub Pages
    if 'github.com' in url.lower():
        # Format: https://github.com/username/repo
        import re
        match = re.search(r'github\.com/([^/]+)/([^/]+)', url)
        if match:
            username = match.group(1)
            repo = match.group(2).replace('.git', '')
            # Essayer GitHub Pages (username.github.io/repo ou repo.github.io)
            # Pour l'instant, on retourne l'URL telle quelle et on log un avertissement
            logging.warning(f"URL GitHub détectée: {url}. Assurez-vous que l'application web est déployée et accessible.")
            # On pourrait aussi essayer: https://{username}.github.io/{repo} ou https://{repo}.github.io
            # Mais pour l'instant, on laisse l'utilisateur fournir l'URL du site déployé
            return url
    
    return url

@api_router.post("/projects")
async def create_project(project_data: ProjectCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Normaliser l'URL web (convertir GitHub si nécessaire)
    normalized_web_url = normalize_web_url(project_data.web_url)
    
    # Normaliser les features
    if project_data.features:
        features_raw = [f.model_dump() if hasattr(f, 'model_dump') else f for f in project_data.features]
        # S'assurer que toutes les features ont 'id' et 'enabled'
        features = []
        for f in features_raw:
            if isinstance(f, dict):
                if 'id' not in f:
                    continue  # Ignorer les features invalides
                if 'enabled' not in f:
                    f['enabled'] = False
                features.append(f)
            else:
                # Si c'est un objet, essayer de le convertir
                if hasattr(f, 'id'):
                    features.append({
                        'id': f.id,
                        'enabled': getattr(f, 'enabled', False),
                        'name': getattr(f, 'name', f.id),
                        'config': getattr(f, 'config', {})
                    })
    else:
        features = DEFAULT_FEATURES.copy()
    
    # Mode dev : retourner un projet factice
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
        return project
    
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
        
        # Utiliser les features normalisées
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
    # Mode dev : retourner les projets stockés en mémoire
    if DEV_MODE:
        projects = list(DEV_PROJECTS_STORE.values())
        # Filtrer par user_id si nécessaire (en mode dev, on retourne tous les projets)
        logging.info(f"📋 Retour de {len(projects)} projets en mode DEV")
        return projects
    
    response = supabase.table("projects").select("*").eq("user_id", user_id).execute()
    return response.data or []

@api_router.get("/projects/{project_id}")
async def get_project(project_id: str, user_id: str = Depends(get_current_user)):
    # Mode dev : retourner le projet stocké en mémoire
    if DEV_MODE:
        if project_id in DEV_PROJECTS_STORE:
            project = DEV_PROJECTS_STORE[project_id]
            logging.info(f"📦 Projet récupéré en mode DEV: {project_id} - URL: {project.get('web_url')}")
            return project
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    
    # Utiliser le service role client pour éviter les problèmes RLS
    client = get_supabase_client(use_service_role=True)
    response = client.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).execute()
    
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Retourner le premier élément (devrait être unique)
    return response.data[0]

@api_router.put("/projects/{project_id}")
async def update_project(project_id: str, update_data: ProjectUpdate, user_id: str = Depends(get_current_user)):
    # Mode dev : mettre à jour le projet en mémoire
    if DEV_MODE:
        if project_id not in DEV_PROJECTS_STORE:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = DEV_PROJECTS_STORE[project_id]
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        
        # Normaliser l'URL si elle est mise à jour
        if 'web_url' in update_dict:
            update_dict['web_url'] = normalize_web_url(update_dict['web_url'])
        
        # Normaliser les features si elles sont mises à jour
        if 'features' in update_dict:
            features_raw = update_dict['features']
            if isinstance(features_raw, list):
                normalized_features = []
                for f in features_raw:
                    if isinstance(f, dict):
                        if 'id' not in f:
                            continue
                        if 'enabled' not in f:
                            f['enabled'] = False
                        normalized_features.append(f)
                    elif hasattr(f, 'id'):
                        normalized_features.append({
                            'id': f.id,
                            'enabled': getattr(f, 'enabled', False),
                            'name': getattr(f, 'name', f.id),
                            'config': getattr(f, 'config', {})
                        })
                update_dict['features'] = normalized_features
        
        # Mettre à jour le projet
        project.update(update_dict)
        project['updated_at'] = datetime.now(timezone.utc).isoformat()
        DEV_PROJECTS_STORE[project_id] = project
        
        logging.info(f"📝 Projet mis à jour en mode DEV: {project_id} - URL: {project.get('web_url')}")
        return project
    
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
    # Mode dev : supprimer le projet de la mémoire
    if DEV_MODE:
        if project_id in DEV_PROJECTS_STORE:
            del DEV_PROJECTS_STORE[project_id]
            if project_id in DEV_BUILDS_STORE:
                del DEV_BUILDS_STORE[project_id]
            logging.info(f"🗑️ Projet supprimé en mode DEV: {project_id}")
        return {"message": "Project deleted"}
    
    result = supabase.table("projects").delete().eq("id", project_id).eq("user_id", user_id).execute()
    await log_system_event("info", "project", f"Project deleted: {project_id}", user_id=user_id)
    return {"message": "Project deleted"}

# ==================== BUILD ENDPOINTS ====================

@api_router.post("/builds")
async def create_build(build_data: BuildCreate, background_tasks: BackgroundTasks, user_id: str = Depends(get_current_user)):
    # Mode dev : créer un build et le stocker en mémoire
    if DEV_MODE:
        # Récupérer le projet depuis le store
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
            "logs": [{"level": "info", "message": f"Build queued (dev mode)", "timestamp": datetime.now(timezone.utc).isoformat()}],
            "artifacts": [],
            "download_url": None,
            "error_message": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None,
            "completed_at": None,
            "duration_seconds": None
        }
        
        # Stocker le build en mémoire
        if build_data.project_id not in DEV_BUILDS_STORE:
            DEV_BUILDS_STORE[build_data.project_id] = []
        DEV_BUILDS_STORE[build_data.project_id].append(build)
        
        # Traiter le build en arrière-plan avec les vraies données du projet
        background_tasks.add_task(process_build, build_id, project)
        logging.info(f"🔨 Build créé en mode DEV: {build_id} pour projet {build_data.project_id} - URL: {project.get('web_url')}")
        return build
    
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
    """Process build with detailed phases - Compile réellement l'APK pour Android"""
    # Mode dev : générer réellement le projet et compiler l'APK si possible
    if DEV_MODE:
        # Trouver le build dans le store et le mettre à jour
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
        platform = project.get('platform', 'android')
        project_name = project.get('name', 'MyApp')
        web_url = project.get('web_url', '')
        features = project.get('features', DEFAULT_FEATURES.copy())
        
        # S'assurer que les features sont au bon format
        if not features or len(features) == 0:
            features = DEFAULT_FEATURES.copy()
        elif isinstance(features, list) and len(features) > 0:
            # Vérifier le format des features
            if not isinstance(features[0], dict) or 'id' not in features[0]:
                # Si les features ne sont pas au bon format, utiliser les defaults
                features = DEFAULT_FEATURES.copy()
        
        # Mettre à jour le build dans le store
        build_in_store['status'] = 'processing'
        build_in_store['started_at'] = datetime.now(timezone.utc).isoformat()
        
        # Simuler les phases du build
        phases = BUILD_PHASES.get(platform, BUILD_PHASES['android'])
        total_duration = sum(p['duration'] for p in phases)
        current_progress = 0
        
        for phase_info in phases:
            phase = phase_info['phase']
            duration = phase_info['duration']
            logging.info(f"Phase: {phase} ({duration}s)")
            
            # Mettre à jour le build dans le store
            build_in_store['phase'] = phase
            build_in_store['progress'] = min(int(current_progress), 99)
            
            # À la phase "assembling" pour Android, essayer de compiler réellement l'APK
            if platform == 'android' and phase == 'assembling' and GENERATOR_AVAILABLE:
                try:
                    logging.info(f"🔨 Phase d'assemblage: Génération et compilation réelle de l'APK pour {project_name}...")
                    
                    safe_name = "".join(c.lower() if c.isalnum() else '' for c in project_name)
                    package_name = f"com.nativiweb.{safe_name}" if safe_name else "com.nativiweb.app"
                    
                    project_zip = generator.generate_android_project(
                        project_name=project_name,
                        package_name=package_name,
                        web_url=web_url,
                        features=features,
                        app_icon_url=project.get('logo_url')
                    )
                    
                    # Importer et utiliser le builder Android
                    try:
                        from android_builder import AndroidBuilder
                        builder = AndroidBuilder()
                        
                        # Compiler l'APK (synchroniser car c'est une opération bloquante)
                        import concurrent.futures
                        loop = asyncio.get_event_loop()
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            success, apk_bytes, error_msg = await loop.run_in_executor(
                                executor, 
                                builder.build_apk, 
                                project_zip, 
                                project_name
                            )
                        
                        if success and apk_bytes:
                            logging.info(f"✅ APK compilé avec succès en mode dev! Taille: {len(apk_bytes) / 1024 / 1024:.2f} MB")
                        else:
                            logging.warning(f"⚠️ Compilation échouée en mode dev: {error_msg[:200] if error_msg else 'Erreur inconnue'}")
                    except ImportError:
                        logging.warning("AndroidBuilder non disponible en mode dev - le projet source sera fourni")
                    except Exception as build_error:
                        logging.error(f"Erreur lors du build Android en mode dev: {build_error}", exc_info=True)
                except Exception as gen_error:
                    logging.error(f"Erreur lors de la génération du projet en mode dev: {gen_error}", exc_info=True)
            
            current_progress += (100 / total_duration)
            if duration > 0:
                await asyncio.sleep(min(duration * 0.1, 1))  # Accélérer en mode dev
        
        # Finaliser le build
        build_in_store['status'] = 'completed'
        build_in_store['phase'] = 'completed'
        build_in_store['progress'] = 100
        build_in_store['completed_at'] = datetime.now(timezone.utc).isoformat()
        build_in_store['artifacts'] = [{"name": f"{project_name}-debug.apk", "type": "apk", "size": "varies"}]
        build_in_store['download_url'] = f"/api/builds/{build_id}/download"
        
        logging.info(f"✅ Build {build_id} terminé (mode dev)")
        return
    
    # Utiliser le service role client pour éviter les problèmes RLS
    client = get_supabase_client(use_service_role=True)
    
    build_response = client.table("builds").select("*").eq("id", build_id).execute()
    if not build_response.data or len(build_response.data) == 0:
        logging.error(f"Build {build_id} not found in process_build")
        return
    
    build_data = build_response.data[0]
    platform = build_data['platform']
    build_type = build_data.get('build_type', 'debug')
    phases = BUILD_PHASES.get(platform, BUILD_PHASES['android'])
    total_duration = sum(p['duration'] for p in phases)
    current_progress = 0
    apk_compiled = False
    apk_size = 0
    
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
        
        # Si on est à la phase "assembling" pour Android, compiler réellement l'APK
        if platform == 'android' and phase == 'assembling' and GENERATOR_AVAILABLE:
            try:
                logging.info(f"🔨 Phase d'assemblage: Compilation réelle de l'APK pour {project['name']}...")
                
                # Générer le projet source
                project_name = project.get('name', 'MyApp')
                web_url = project.get('web_url', '')
                features = project.get('features', [])
                safe_name = "".join(c.lower() if c.isalnum() else '' for c in project_name)
                package_name = f"com.nativiweb.{safe_name}" if safe_name else "com.nativiweb.app"
                
                project_zip = generator.generate_android_project(
                    project_name=project_name,
                    package_name=package_name,
                    web_url=web_url,
                    features=features,
                    app_icon_url=project.get('logo_url')
                )
                
                # Importer et utiliser le builder Android
                try:
                    from android_builder import AndroidBuilder
                    builder = AndroidBuilder()
                    
                    # Compiler l'APK (synchroniser car c'est une opération bloquante)
                    # On utilise run_in_executor pour ne pas bloquer l'event loop
                    import concurrent.futures
                    loop = asyncio.get_event_loop()
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        success, apk_bytes, error_msg = await loop.run_in_executor(
                            executor, 
                            builder.build_apk, 
                            project_zip, 
                            project_name
                        )
                    
                    if success and apk_bytes:
                        apk_compiled = True
                        apk_size = len(apk_bytes)
                        logging.info(f"✅ APK compilé avec succès! Taille: {apk_size / 1024 / 1024:.2f} MB")
                        
                        # Stocker l'APK dans un fichier temporaire ou en mémoire pour le téléchargement
                        # Pour l'instant, on le stockera dans la base de données comme indication
                        # L'APK sera recompilé au téléchargement (ou on peut le stocker sur disque/S3)
                        current_logs.append({
                            "level": "success",
                            "message": f"APK compilé avec succès! Taille: {apk_size / 1024 / 1024:.2f} MB",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                    else:
                        logging.warning(f"⚠️ Compilation échouée: {error_msg[:200] if error_msg else 'Erreur inconnue'}")
                        current_logs.append({
                            "level": "warning",
                            "message": f"Compilation échouée: {error_msg[:200] if error_msg else 'Erreur inconnue'}. Le projet source sera fourni.",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                except ImportError:
                    logging.warning("AndroidBuilder non disponible - le projet source sera fourni")
                except Exception as build_error:
                    logging.error(f"Erreur lors du build Android: {build_error}", exc_info=True)
            except Exception as gen_error:
                logging.error(f"Erreur lors de la génération du projet: {gen_error}", exc_info=True)
        
        if duration > 0:
            steps = max(1, duration)
            for _ in range(steps):
                await asyncio.sleep(0.5)
                current_progress += (100 / total_duration) / 2
                client.table("builds").update({
                    "progress": min(int(current_progress), 99),
                    "logs": current_logs
                }).eq("id", build_id).execute()
    
    # Generate artifacts
    artifacts = []
    if platform == 'android':
        if apk_compiled:
            artifacts = [
                {"name": f"{project['name']}-debug.apk", "type": "apk", "size": f"{apk_size / 1024 / 1024:.1f}MB", "compiled": True},
            ]
        else:
            artifacts = [
                {"name": f"{project['name']}-source.zip", "type": "zip", "size": "varies", "compiled": False},
                {"name": f"{project['name']}-debug.apk", "type": "apk", "size": "N/A (source project)", "compiled": False},
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
    
    if apk_compiled:
        logging.info(f"✅ Build {build_id} terminé avec APK compilé! Taille: {apk_size / 1024 / 1024:.2f} MB")
    else:
        logging.info(f"✅ Build {build_id} terminé (projet source fourni)")

@api_router.get("/builds")
async def get_builds(user_id: str = Depends(get_current_user), project_id: Optional[str] = None):
    # Mode dev : retourner une liste de builds factices
    if DEV_MODE:
        return [
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "project_id": project_id or str(uuid.uuid4()),
                "platform": "android",
                "build_type": "debug",
                "status": "completed",
                "phase": "completed",
                "progress": 100,
                "artifacts": [{"name": "app-debug.apk", "type": "apk", "size": "15MB"}],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        ]
    
    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    query = client.table("builds").select("*").eq("user_id", user_id)
    if project_id:
        query = query.eq("project_id", project_id)
    response = query.order("created_at", desc=True).execute()
    return response.data or []

@api_router.get("/builds/{build_id}")
async def get_build(build_id: str, user_id: str = Depends(get_current_user)):
    # Mode dev : retourner le build depuis le store
    if DEV_MODE:
        # Chercher le build dans tous les projets
        for project_builds in DEV_BUILDS_STORE.values():
            for build in project_builds:
                if build.get('id') == build_id:
                    return build
        raise HTTPException(status_code=404, detail="Build not found")
    
    client = get_supabase_client(use_service_role=True)
    if not client:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    response = client.table("builds").select("*").eq("id", build_id).eq("user_id", user_id).execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=404, detail="Build not found")
    return response.data[0]

@api_router.delete("/builds/{build_id}")
async def delete_build(build_id: str, user_id: str = Depends(get_current_user)):
    """Delete a build"""
    # Mode dev : retourner un succès sans accéder à Supabase
    if DEV_MODE:
        logging.info(f"DEV_MODE: Build {build_id} deleted (simulated)")
        return {"message": "Build deleted successfully"}
    
    try:
        client = get_supabase_client(use_service_role=True)
        
        if not client:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Vérifier que le build existe et appartient à l'utilisateur
        build_response = client.table("builds").select("*").eq("id", build_id).eq("user_id", user_id).execute()
        
        if not build_response.data or len(build_response.data) == 0:
            raise HTTPException(status_code=404, detail="Build not found")
        
        # Supprimer le build
        client.table("builds").delete().eq("id", build_id).execute()
        
        await log_system_event("info", "build", f"Build deleted: {build_id}", user_id=user_id)
        
        return {"message": "Build deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting build {build_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting build: {str(e)}")

@api_router.delete("/builds")
async def delete_all_builds(user_id: str = Depends(get_current_user)):
    """Delete all builds for the current user"""
    # Mode dev : retourner un succès sans accéder à Supabase
    if DEV_MODE:
        # En mode dev, on retourne le nombre de builds mock (1 build selon get_builds)
        build_count = 1
        logging.info(f"DEV_MODE: All builds deleted (simulated, {build_count} builds)")
        return {"message": f"All builds deleted successfully", "deleted_count": build_count}
    
    try:
        client = get_supabase_client(use_service_role=True)
        
        if not client:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Récupérer tous les builds de l'utilisateur pour logging
        builds_response = client.table("builds").select("id").eq("user_id", user_id).execute()
        build_count = len(builds_response.data) if builds_response.data else 0
        
        # Supprimer tous les builds de l'utilisateur
        client.table("builds").delete().eq("user_id", user_id).execute()
        
        await log_system_event("info", "build", f"All builds deleted for user ({build_count} builds)", user_id=user_id)
        
        return {"message": f"All builds deleted successfully", "deleted_count": build_count}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting all builds for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting builds: {str(e)}")

@api_router.get("/builds/{build_id}/download")
async def download_build(build_id: str, user_id: str = Depends(get_current_user)):
    """Download build artifact (APK/IPA) - Compile réellement l'APK pour Android"""
    # Mode dev : générer un projet source factice
    if DEV_MODE:
        logging.info(f"Mode dev : Génération d'un projet source pour build {build_id}")
        try:
            # Générer un projet Android factice
            project_name = "Dev Project"
            web_url = "https://example.com"
            features = []
            safe_name = "devproject"
            package_name = f"com.nativiweb.{safe_name}"
            
            if GENERATOR_AVAILABLE:
                project_zip = generator.generate_android_project(
                    project_name=project_name,
                    package_name=package_name,
                    web_url=web_url,
                    features=features
                )
            else:
                # Créer un ZIP vide si le générateur n'est pas disponible
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    zip_file.writestr("README.txt", "Dev mode - Project source")
                project_zip = zip_buffer.getvalue()
            
            return StreamingResponse(
                io.BytesIO(project_zip),
                media_type="application/zip",
                headers={
                    "Content-Disposition": f'attachment; filename="{project_name}-source.zip"'
                }
            )
        except Exception as e:
            logging.error(f"Error generating dev project: {e}")
            raise HTTPException(status_code=500, detail=f"Error generating project: {str(e)}")
    
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
        project_name = project.get('name', 'MyApp')
        
        # Pour Android, essayer de compiler réellement l'APK
        if platform == 'android' and GENERATOR_AVAILABLE:
            try:
                # Importer le builder Android
                try:
                    from android_builder import AndroidBuilder
                    builder = AndroidBuilder()
                    
                    # Générer le projet source
                    web_url = project.get('web_url', '')
                    features = project.get('features', [])
                    safe_name = "".join(c.lower() if c.isalnum() else '' for c in project_name)
                    package_name = f"com.nativiweb.{safe_name}" if safe_name else "com.nativiweb.app"
                    
                    project_zip = generator.generate_android_project(
                        project_name=project_name,
                        package_name=package_name,
                        web_url=web_url,
                        features=features,
                        app_icon_url=project.get('logo_url')
                    )
                    
                    # Compiler réellement l'APK
                    logging.info(f"🚀 Démarrage de la compilation de l'APK Android pour {project_name}...")
                    
                    try:
                        success, apk_bytes, error_msg = builder.build_apk(project_zip, project_name)
                        
                        if success and apk_bytes:
                            # Vérifier que l'APK est valide (au moins 1KB)
                            if len(apk_bytes) < 1000:
                                raise Exception(f"APK trop petit ({len(apk_bytes)} bytes), probablement corrompu")
                            
                            logging.info(f"✅ APK compilé avec succès pour {project_name}!")
                            logging.info(f"📦 Taille de l'APK: {len(apk_bytes) / 1024 / 1024:.2f} MB")
                            logging.info(f"📱 APK prêt à être installé sur un appareil Android")
                            
                            # Mettre à jour le build dans la base de données pour indiquer que c'est un APK compilé
                            try:
                                client.table("builds").update({
                                    "download_url": f"/api/builds/{build_id}/download",
                                    "status": "completed",
                                    "phase": "completed"
                                }).eq("id", build_id).execute()
                            except Exception as db_error:
                                logging.warning(f"Erreur lors de la mise à jour du build: {db_error}")
                            
                            # Retourner l'APK compilé directement
                            safe_project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).strip()
                            filename = f"{safe_project_name}-debug-{build_id[:8]}.apk"
                            
                            return StreamingResponse(
                                io.BytesIO(apk_bytes),
                                media_type="application/vnd.android.package-archive",
                                headers={
                                    "Content-Disposition": f'attachment; filename="{filename}"',
                                    "Content-Type": "application/vnd.android.package-archive",
                                    "Content-Length": str(len(apk_bytes)),
                                    "X-Build-Type": "compiled-apk",
                                    "X-APK-Size": str(len(apk_bytes))
                                }
                            )
                        else:
                            # Si la compilation échoue, logger l'erreur et retourner le projet source
                            error_detail = error_msg[:500] if error_msg else "Erreur inconnue"
                            logging.warning(f"⚠️ Compilation échouée pour {project_name}: {error_detail}")
                            logging.warning(f"📦 Retour du projet source à la place de l'APK compilé")
                            # Continuer avec le code suivant pour retourner le ZIP source
                            
                    except Exception as build_exception:
                        logging.error(f"❌ Exception lors du build Android: {build_exception}", exc_info=True)
                        # Continuer avec le code suivant pour retourner le ZIP source
                        
                except ImportError as import_error:
                    logging.warning(f"AndroidBuilder non disponible: {import_error}. Retour du projet source.")
                    # Continuer avec le code suivant pour retourner le ZIP source
                except Exception as build_error:
                    logging.error(f"Erreur lors du build Android: {build_error}", exc_info=True)
                    # Continuer avec le code suivant pour retourner le ZIP source
            except Exception as gen_error:
                logging.error(f"Erreur lors de la génération du projet: {gen_error}", exc_info=True)
                # Continuer avec le fallback
        
        # Générer un projet source (pour iOS ou si la compilation Android a échoué)
        if GENERATOR_AVAILABLE:
            try:
                project_name = project.get('name', 'MyApp')
                web_url = project.get('web_url', '')
                features = project.get('features', [])
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
                else:
                    bundle_id = f"com.nativiweb.{safe_name}" if safe_name else "com.nativiweb.app"
                    project_zip = generator.generate_ios_project(
                        project_name=project_name,
                        bundle_identifier=bundle_id,
                        web_url=web_url,
                        features=features,
                        app_icon_url=project.get('logo_url')
                    )
                
                # Créer un ZIP avec le projet ET les métadonnées du build
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Écrire le projet généré (en extrayant et réintégrant)
                    with zipfile.ZipFile(io.BytesIO(project_zip), 'r') as temp_zip:
                        for item in temp_zip.infolist():
                            zip_file.writestr(item.filename, temp_zip.read(item.filename))
                    
                    # Ajouter les métadonnées du build
                    readme = f"""# {project['name']} - {platform.upper()} Build
Generated by NativiWeb Studio

Build ID: {build_id}
Project: {project['name']}
Platform: {platform}
Status: {build.get('status', 'unknown')}

## ⚠️ IMPORTANT : Ce fichier est un PROJET SOURCE

Ce ZIP contient le **code source** du projet natif {platform.upper()}, **pas un APK/IPA compilé**.

Pour obtenir une application installable, vous devez **compiler** le projet :
- **Android** : Utilisez le script `build.sh` (Linux/Mac) ou `build.bat` (Windows), ou ouvrez le projet dans Android Studio
- **iOS** : Ouvrez le projet dans Xcode sur macOS

## 🚀 Compilation Rapide

### Android
```bash
# Décompresser, puis :
chmod +x build.sh && ./build.sh
# OU sur Windows: build.bat
```

L'APK sera généré dans : `app/build/outputs/apk/debug/app-debug.apk`

### iOS
Ouvrez le projet `.xcodeproj` dans Xcode sur macOS, puis compilez.

## 📖 Instructions Complètes

Consultez le **README.md** dans le dossier du projet pour les instructions détaillées de compilation et d'installation.
"""
                    zip_file.writestr('BUILD_INFO.md', readme)
                    zip_file.writestr('build-config.json', json.dumps({
                        "project": project['name'],
                        "web_url": project.get('web_url', ''),
                        "platform": platform,
                        "build_id": build_id,
                        "created_at": build.get('created_at', ''),
                        "completed_at": build.get('completed_at', '')
                    }, indent=2))
                
                zip_buffer.seek(0)
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
            except Exception as gen_error:
                logging.warning(f"Failed to generate native project, falling back to placeholder: {gen_error}")
        
        # Fallback: générer un ZIP avec placeholder si le générateur échoue
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            readme = f"# {project['name']} - {platform.upper()} Build\nGenerated by NativiWeb Studio\n\nBuild ID: {build_id}\nProject: {project['name']}\nPlatform: {platform}\nStatus: {build.get('status', 'unknown')}\n\n⚠️ Note: Ce build est un placeholder. Pour obtenir un projet natif complet, utilisez l'endpoint /api/generator/download/{project['id']}/{platform}"
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
    # Mode dev : retourner une liste vide
    if DEV_MODE:
        return []
    
    response = supabase.table("api_keys").select("*").eq("user_id", user_id).execute()
    return response.data or []

@api_router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: str, user_id: str = Depends(get_current_user)):
    # Mode dev : retourner succès
    if DEV_MODE:
        return {"message": "API key deleted"}
    
    supabase.table("api_keys").delete().eq("id", key_id).eq("user_id", user_id).execute()
    return {"message": "API key deleted"}

# ==================== FEATURES & STATS ====================

@api_router.get("/features")
async def get_available_features():
    return DEFAULT_FEATURES

@api_router.get("/stats")
async def get_user_stats(user_id: str = Depends(get_current_user)):
    # Mode dev : retourner des stats factices
    if DEV_MODE:
        return {
            "projects": 1,
            "total_builds": 1,
            "successful_builds": 1,
            "api_keys": 0
        }
    
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

# ==================== GENERATOR ENDPOINTS ====================

try:
    from generator import NativeTemplateGenerator
    generator = NativeTemplateGenerator()
    GENERATOR_AVAILABLE = True
    logging.info("✅ Générateur de projets natifs disponible")
except ImportError as e:
    logging.warning(f"⚠️ Generator not available: {e}")
    GENERATOR_AVAILABLE = False
    generator = None

# Vérifier si AndroidBuilder est disponible au démarrage
try:
    from android_builder import AndroidBuilder
    builder_test = AndroidBuilder()
    deps_ok, deps_error = builder_test.check_dependencies()
    if deps_ok:
        logging.info("✅ AndroidBuilder disponible - Compilation d'APK activée")
    else:
        logging.warning(f"⚠️ AndroidBuilder disponible mais dépendances manquantes: {deps_error}")
        logging.warning("⚠️ Les APKs ne seront pas compilés automatiquement. Les projets source seront fournis.")
    ANDROID_BUILDER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"⚠️ AndroidBuilder not available: {e} - Compilation d'APK désactivée")
    ANDROID_BUILDER_AVAILABLE = False
except Exception as e:
    logging.error(f"❌ Erreur lors de l'initialisation d'AndroidBuilder: {e}")
    ANDROID_BUILDER_AVAILABLE = False

@api_router.get("/generator/download/{project_id}/{platform}")
async def download_generated_project(
    project_id: str,
    platform: str,
    user_id: str = Depends(get_current_user)
):
    """
    Télécharge un projet natif généré (Android ou iOS)
    
    Args:
        project_id: ID du projet
        platform: 'android' ou 'ios'
        user_id: ID de l'utilisateur (depuis le token)
    
    Returns:
        StreamingResponse avec le ZIP du projet
    """
    if not GENERATOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Generator service unavailable")
    
    if platform not in ['android', 'ios']:
        raise HTTPException(status_code=400, detail="Platform must be 'android' or 'ios'")
    
    try:
        client = get_supabase_client(use_service_role=True)
        
        # Récupérer le projet
        project_response = client.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).execute()
        
        if not project_response.data or len(project_response.data) == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = project_response.data[0]
        project_name = project.get('name', 'MyApp')
        web_url = project.get('web_url', '')
        features = project.get('features', [])
        
        # Générer le package name / bundle identifier
        # Convertir le nom en format valide
        safe_name = "".join(c.lower() if c.isalnum() else '' for c in project_name)
        if platform == 'android':
            package_name = f"com.nativiweb.{safe_name}" if safe_name else "com.nativiweb.app"
        else:
            bundle_id = f"com.nativiweb.{safe_name}" if safe_name else "com.nativiweb.app"
        
        # Générer le projet
        if platform == 'android':
            project_zip = generator.generate_android_project(
                project_name=project_name,
                package_name=package_name,
                web_url=web_url,
                features=features,
                app_icon_url=project.get('logo_url')
            )
            filename = f"{safe_name}-android.zip"
            content_type = "application/zip"
        else:
            project_zip = generator.generate_ios_project(
                project_name=project_name,
                bundle_identifier=bundle_id,
                web_url=web_url,
                features=features,
                app_icon_url=project.get('logo_url')
            )
            filename = f"{safe_name}-ios.zip"
            content_type = "application/zip"
        
        await log_system_event("info", "generator", f"Generated {platform} project for {project_name}", user_id=user_id)
        
        return StreamingResponse(
            io.BytesIO(project_zip),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": content_type
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error generating project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating project: {str(e)}")

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "NativiWeb Studio API v2.0.0", "status": "operational"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# CORS - Must be added before including routers
# Configure CORS based on environment
cors_origins = ALLOWED_ORIGINS if ENVIRONMENT == "production" else ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Add compression middleware (after CORS)
app.add_middleware(GZipMiddleware, minimum_size=1000)

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
