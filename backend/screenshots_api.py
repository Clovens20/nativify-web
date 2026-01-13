"""
API Router pour la génération de screenshots pour les stores
Utilise screenshot_generator.py pour la génération
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from typing import Literal, List, Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/projects/{project_id}/screenshots/generate")
async def generate_screenshots(
    project_id: str,
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
        # Import lazy pour éviter les imports circulaires
        from main import get_supabase_client, DEV_MODE
        
        # Récupérer le projet depuis Supabase
        client = get_supabase_client(use_service_role=True)
        
        if not client:
            if DEV_MODE:
                # Mode dev : utiliser un projet fictif
                base_url = "https://example.com"
                project_name = "Dev Project"
            else:
                raise HTTPException(status_code=500, detail="Database unavailable")
        else:
            # Vérifier que le projet existe
            project_response = client.table("projects").select("*").eq("id", project_id).execute()
            
            if not project_response.data:
                raise HTTPException(status_code=404, detail="Projet non trouvé")
            
            project = project_response.data[0]
            base_url = project.get("web_url")
            project_name = project.get("name", "Project")
            
            if not base_url:
                raise HTTPException(status_code=400, detail="URL du projet non définie")
        
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
                    detail="Aucun screenshot généré. Vérifiez que l'URL est accessible et que Playwright est correctement installé."
                )
            
            logger.info(f"Screenshots générés avec succès ({len(zip_bytes)} bytes)")
            
            # Retourner le ZIP
            return Response(
                content=zip_bytes,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename=screenshots_{project_id}_{store}.zip"
                }
            )
            
        except ImportError as e:
            logger.error(f"Import error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Playwright n'est pas installé. Installez-le avec: pip install playwright && playwright install chromium"
            )
        except Exception as e:
            logger.error(f"Erreur lors de la génération de screenshots: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la génération: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur génération screenshots: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/screenshots/status")
async def get_screenshot_status(project_id: str):
    """Retourne le statut de génération des screenshots"""
    try:
        # Import lazy pour éviter les imports circulaires
        from main import get_supabase_client, DEV_MODE
        
        client = get_supabase_client(use_service_role=True)
        
        if not client:
            if DEV_MODE:
                return {
                    "status": "ready",
                    "project_id": project_id,
                    "available_stores": ["android", "ios"]
                }
            raise HTTPException(status_code=500, detail="Database unavailable")
        
        # Vérifier que le projet existe
        project_response = client.table("projects").select("id").eq("id", project_id).execute()
        
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        
        # Vérifier si Playwright est disponible
        try:
            from playwright.async_api import async_playwright
            playwright_available = True
        except ImportError:
            playwright_available = False
        
        return {
            "status": "ready" if playwright_available else "unavailable",
            "project_id": project_id,
            "available_stores": ["android", "ios"],
            "playwright_installed": playwright_available
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération statut screenshots: {e}")
        raise HTTPException(status_code=500, detail=str(e))
