"""
Endpoint pour l'upload de fichiers (logos de projets)
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from supabase import create_client
import os
import uuid
from pathlib import Path
import logging
from datetime import datetime, timezone
from typing import Optional

security = HTTPBearer(auto_error=False)

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Get current user ID from JWT token (optional)"""
    if not credentials:
        return None
    try:
        from main import supabase
        token = credentials.credentials
        user_response = supabase.auth.get_user(token)
        if user_response.user:
            return user_response.user.id
        return None
    except Exception as e:
        logging.warning(f"Auth error in upload endpoint: {e}")
        return None

router = APIRouter()

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')

# Configuration du bucket
LOGO_BUCKET = "project-logos"

# Fonction pour obtenir le client Supabase (initialisation paresseuse)
def get_supabase_storage():
    """Crée et retourne le client Supabase pour le storage"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise HTTPException(
            status_code=500,
            detail="Configuration Supabase manquante. Vérifiez SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY dans .env"
        )
    try:
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    except Exception as e:
        logging.error(f"Erreur lors de la création du client Supabase: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Impossible de se connecter à Supabase: {str(e)}"
        )

@router.post("/upload/logo")
async def upload_logo(
    file: UploadFile = File(...),
    user_id: Optional[str] = Depends(get_current_user_optional)
):
    """
    Upload un logo de projet vers Supabase Storage
    """
    try:
        # Vérifier le type de fichier
        allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp", "image/svg+xml"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Type de fichier non autorisé. Types acceptés: {', '.join(allowed_types)}"
            )
        
        # Vérifier la taille (max 5MB)
        file_content = await file.read()
        if len(file_content) > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(status_code=400, detail="Le fichier est trop volumineux (max 5MB)")
        
        # Générer un nom de fichier unique
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        storage_path = f"{user_id or 'public'}/{unique_filename}"
        
        # Obtenir le client Supabase
        supabase_storage = get_supabase_storage()
        
        # Vérifier que le bucket existe, sinon le créer
        bucket_exists = False
        try:
            buckets_response = supabase_storage.storage.list_buckets()
            # La réponse peut être une liste ou un objet avec une propriété
            if isinstance(buckets_response, list):
                buckets = buckets_response
            elif hasattr(buckets_response, 'data'):
                buckets = buckets_response.data or []
            else:
                buckets = []
            
            bucket_exists = any(
                (bucket.name == LOGO_BUCKET if hasattr(bucket, 'name') else bucket.get('name') == LOGO_BUCKET if isinstance(bucket, dict) else str(bucket) == LOGO_BUCKET)
                for bucket in buckets
            )
            
            logging.info(f"Bucket '{LOGO_BUCKET}' exists: {bucket_exists}")
            
        except Exception as bucket_check_error:
            logging.warning(f"Error checking bucket existence: {bucket_check_error}")
            # On continue quand même, on essaiera de créer le bucket
        
        if not bucket_exists:
            try:
                logging.info(f"Creating bucket '{LOGO_BUCKET}'...")
                # Créer le bucket s'il n'existe pas
                create_response = supabase_storage.storage.create_bucket(
                    LOGO_BUCKET,
                    {
                        "public": True,
                        "file_size_limit": 5242880,  # 5MB
                        "allowed_mime_types": allowed_types
                    }
                )
                logging.info(f"Bucket '{LOGO_BUCKET}' created successfully: {create_response}")
            except Exception as bucket_create_error:
                error_msg = str(bucket_create_error)
                logging.error(f"Error creating bucket: {error_msg}")
                
                # Si l'erreur indique que le bucket existe déjà, on continue
                if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                    logging.info(f"Bucket '{LOGO_BUCKET}' already exists, continuing...")
                    bucket_exists = True
                else:
                    # Si on ne peut pas créer le bucket, on essaie quand même d'uploader
                    # (peut-être que les permissions permettent l'upload même si list_buckets ne fonctionne pas)
                    logging.warning(f"Cannot create bucket, but attempting upload anyway...")
        
        # Upload vers Supabase Storage
        try:
            logging.info(f"Attempting upload to bucket '{LOGO_BUCKET}' with path '{storage_path}'")
            result = supabase_storage.storage.from_(LOGO_BUCKET).upload(
                storage_path,
                file_content,
                file_options={
                    "content-type": file.content_type,
                    "upsert": "false"
                }
            )
            
            logging.info(f"Upload successful: {result}")
            
            # Obtenir l'URL publique du fichier
            public_url = supabase_storage.storage.from_(LOGO_BUCKET).get_public_url(storage_path)
            logging.info(f"Public URL generated: {public_url}")
            
            return {
                "success": True,
                "url": public_url,
                "path": storage_path,
                "filename": unique_filename
            }
        except Exception as upload_error:
            error_msg = str(upload_error)
            logging.error(f"Upload error: {error_msg}", exc_info=True)
            
            # Messages d'erreur plus spécifiques
            if "bucket" in error_msg.lower() or "not found" in error_msg.lower():
                detail = f"Le bucket '{LOGO_BUCKET}' n'existe pas. Veuillez le créer dans Supabase Storage."
            elif "permission" in error_msg.lower() or "forbidden" in error_msg.lower():
                detail = "Permissions insuffisantes pour uploader le fichier. Vérifiez les politiques RLS du bucket."
            elif "duplicate" in error_msg.lower() or "already exists" in error_msg.lower():
                detail = "Un fichier avec ce nom existe déjà."
            else:
                detail = f"Erreur lors de l'upload: {error_msg}"
            
            raise HTTPException(status_code=500, detail=detail)
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error uploading logo: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

@router.delete("/upload/logo/{path:path}")
async def delete_logo(path: str):
    """
    Supprimer un logo de projet
    """
    try:
        supabase_storage = get_supabase_storage()
        supabase_storage.storage.from_(LOGO_BUCKET).remove([path])
        return {"success": True, "message": "Logo supprimé"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting logo: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")

