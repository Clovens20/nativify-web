"""
Module pour synchroniser les utilisateurs de auth.users vers public.users
"""

import logging
from datetime import datetime, timezone
from supabase import Client

def sync_missing_user(client: Client, user_id: str) -> dict:
    """
    Synchronise un utilisateur spécifique de auth.users vers public.users
    """
    try:
        # Vérifier si l'utilisateur existe dans auth.users
        auth_user_response = client.auth.admin.get_user_by_id(user_id)
        auth_user = auth_user_response.user
        
        if not auth_user:
            return {"success": False, "error": "User not found in auth.users"}
        
        # Préparer les données utilisateur
        user_data = {
            "id": auth_user.id,
            "email": auth_user.email or "",
            "name": (
                auth_user.user_metadata.get("name", "") 
                if auth_user.user_metadata 
                else auth_user.email.split("@")[0] if auth_user.email else "Utilisateur"
            ),
            "role": "user",
            "status": "active",
            "created_at": auth_user.created_at or datetime.now(timezone.utc).isoformat()
        }
        
        # Upsert dans public.users
        response = client.table("users").upsert(user_data, on_conflict="id").execute()
        
        if response.data:
            return {"success": True, "user": response.data[0]}
        else:
            return {"success": False, "error": "Failed to insert user"}
            
    except Exception as e:
        logging.error(f"Error syncing user {user_id}: {e}")
        return {"success": False, "error": str(e)}

