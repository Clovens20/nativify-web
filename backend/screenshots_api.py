import logging

# ✅ Définir le logger
logger = logging.getLogger(__name__)

# Maintenant on peut importer les autres modules
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Literal, List, Optional

router = APIRouter()
security = HTTPBearer(auto_error=False)

async def get_user_id_from_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Extract user ID from JWT token"""
    try:
        from main import DEV_MODE
        
        if DEV_MODE:
            return "dev-user-123"
        
        if not credentials:
            return None
        
        token = credentials.credentials
        
        if not token:
            return None
        
        import jwt
        import time
        
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
            user_id = unverified.get('sub') or unverified.get('user_id')
            
            if not user_id:
                return None
            
            exp = unverified.get('exp')
            if exp and exp < time.time():
                logger.warning(f"Token expired for user {user_id}")
                return None
            
            return user_id
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            logger.warning(f"Error decoding token: {e}")
            return None
    except Exception as e:
        logger.warning(f"Error in get_user_id_from_token: {e}")
        return None

@router.post("/projects/{project_id}/screenshots/generate")
async def generate_screenshots(
    project_id: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    store: Literal["android", "ios", "both"] = Query("both"),
    auto_discover: bool = Query(True),
    urls: Optional[List[str]] = Query(None)
):
    """
    Génère les screenshots pour les stores
    
    Args:
        project_id: ID du projet
        store: Store cible (android, ios, both)
        auto_discover: Découvrir automatiquement les pages
        urls: Liste d'URLs spécifiques (optionnel)
    """
    try:
        from main import get_supabase_client, DEV_MODE
        
        # Récupérer l'utilisateur depuis le token
        user_id = await get_user_id_from_token(credentials)
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Récupérer le projet depuis Supabase
        client = get_supabase_client(use_service_role=True)
        
        if not client:
            if DEV_MODE:
                base_url = "https://example.com"
                project_name = "Dev Project"
            else:
                raise HTTPException(status_code=500, detail="Database unavailable")
        else:
            project_response = client.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).execute()
            
            if not project_response.data:
                raise HTTPException(status_code=404, detail="Projet non trouvé ou accès non autorisé")
            
            project = project_response.data[0]
            base_url = project.get("web_url")
            project_name = project.get("name", "Project")
            
            if not base_url:
                raise HTTPException(status_code=400, detail="URL du projet non définie")
        
        # Vérifier que Playwright est installé
        try:
            from screenshot_generator import HAS_PLAYWRIGHT
            if not HAS_PLAYWRIGHT:
                raise HTTPException(
                    status_code=500,
                    detail="Playwright n'est pas installé. Installez-le avec: pip install playwright && playwright install chromium"
                )
        except ImportError as e:
            logger.error(f"Import error de screenshot_generator: {e}")
            raise HTTPException(
                status_code=500,
                detail="Module screenshot_generator introuvable. Vérifiez que le fichier existe."
            )
        
        # Utiliser le générateur de screenshots
        try:
            from screenshot_generator import generate_screenshots_async
            
            logger.info(f"Génération de screenshots pour {base_url} (store: {store})")
            
            # Générer les screenshots
            zip_bytes = await generate_screenshots_async(
                base_url=base_url,
                pages=urls,
                store=store,
                auto_discover=auto_discover
            )
            
            if not zip_bytes or len(zip_bytes) == 0:
                logger.error("Le ZIP généré est vide")
                raise HTTPException(
                    status_code=500,
                    detail="Aucun screenshot généré. Vérifiez que l'URL est accessible."
                )
            
            logger.info(f"Screenshots générés avec succès ({len(zip_bytes)} bytes)")
            
            # Retourner le ZIP
            return Response(
                content=zip_bytes,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename=screenshots_{project_name.replace(' ', '_')}_{store}.zip"
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la génération de screenshots: {e}", exc_info=True)
            
            # Messages d'erreur plus détaillés
            error_message = str(e)
            
            if "Playwright" in error_message or "chromium" in error_message:
                raise HTTPException(
                    status_code=500,
                    detail="Playwright non configuré. Exécutez: playwright install chromium"
                )
            elif "timeout" in error_message.lower():
                raise HTTPException(
                    status_code=500,
                    detail=f"Timeout lors de l'accès à {base_url}. Vérifiez que l'URL est accessible."
                )
            elif "connect" in error_message.lower() or "network" in error_message.lower():
                raise HTTPException(
                    status_code=500,
                    detail=f"Impossible de se connecter à {base_url}. Vérifiez que l'URL est correcte et accessible."
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Erreur lors de la génération: {error_message}"
                )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur génération screenshots: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/screenshots/status")
async def get_screenshot_status(
    project_id: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Retourne le statut de génération des screenshots"""
    try:
        from main import get_supabase_client, DEV_MODE
        
        user_id = await get_user_id_from_token(credentials)
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        client = get_supabase_client(use_service_role=True)
        
        if not client:
            if DEV_MODE:
                return {
                    "status": "ready",
                    "project_id": project_id,
                    "available_stores": ["android", "ios"],
                    "playwright_installed": False
                }
            raise HTTPException(status_code=500, detail="Database unavailable")
        
        project_response = client.table("projects").select("id").eq("id", project_id).eq("user_id", user_id).execute()
        
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Projet non trouvé ou accès non autorisé")
        
        # Vérifier si Playwright est disponible
        try:
            from screenshot_generator import HAS_PLAYWRIGHT
            playwright_available = HAS_PLAYWRIGHT
        except ImportError:
            playwright_available = False
        
        return {
            "status": "ready" if playwright_available else "unavailable",
            "project_id": project_id,
            "available_stores": ["android", "ios"],
            "playwright_installed": playwright_available,
            "message": "Playwright est installé et prêt" if playwright_available else "Installez Playwright avec: pip install playwright && playwright install chromium"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération statut screenshots: {e}")
        raise HTTPException(status_code=500, detail=str(e))