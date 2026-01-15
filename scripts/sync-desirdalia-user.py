#!/usr/bin/env python3
"""
Script pour synchroniser l'utilisateur desirdalia@gmail.com
de auth.users vers public.users dans Supabase
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Charger les variables d'environnement
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / 'backend' / '.env')

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Erreur: SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY doivent être définis dans backend/.env")
    sys.exit(1)

# Créer le client Supabase avec service role key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

USER_ID = 'fd599f98-56cf-445f-93d6-abdde48f959c'
USER_EMAIL = 'desirdalia@gmail.com'

def sync_user():
    """Synchroniser l'utilisateur depuis auth.users vers public.users"""
    
    print(f"🔄 Synchronisation de l'utilisateur {USER_EMAIL} (ID: {USER_ID})...")
    
    try:
        # 1. Vérifier si l'utilisateur existe dans auth.users
        print("\n1. Vérification dans auth.users...")
        
        # Utiliser l'Admin API pour récupérer l'utilisateur
        try:
            auth_users = supabase.auth.admin.list_users()
            auth_user = None
            
            if hasattr(auth_users, 'users'):
                for user in auth_users.users:
                    if user.id == USER_ID or user.email == USER_EMAIL:
                        auth_user = user
                        break
            
            if not auth_user:
                print(f"❌ Utilisateur non trouvé dans auth.users avec ID {USER_ID} ou email {USER_EMAIL}")
                return False
            
            print(f"✅ Utilisateur trouvé dans auth.users:")
            print(f"   - ID: {auth_user.id}")
            print(f"   - Email: {auth_user.email}")
            print(f"   - Créé le: {auth_user.created_at}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération depuis auth.users: {e}")
            # Continuer avec les données que nous avons
            auth_user = None
        
        # 2. Vérifier si l'utilisateur existe déjà dans public.users
        print("\n2. Vérification dans public.users...")
        existing_user = supabase.table("users").select("*").eq("id", USER_ID).execute()
        
        if existing_user.data and len(existing_user.data) > 0:
            print(f"✅ Utilisateur existe déjà dans public.users:")
            for key, value in existing_user.data[0].items():
                print(f"   - {key}: {value}")
            print("\n✅ Utilisateur déjà synchronisé!")
            return True
        
        # 3. Créer l'utilisateur dans public.users
        print("\n3. Création dans public.users...")
        
        user_metadata = auth_user.user_metadata if auth_user and hasattr(auth_user, 'user_metadata') else {}
        user_name = (
            user_metadata.get('name') 
            or (USER_EMAIL.split('@')[0] if USER_EMAIL else 'User')
        )
        
        user_data = {
            "id": USER_ID,
            "email": USER_EMAIL,
            "name": user_name,
            "role": "user",
            "status": "active"
        }
        
        if auth_user and hasattr(auth_user, 'created_at') and auth_user.created_at:
            user_data["created_at"] = auth_user.created_at
        
        result = supabase.table("users").upsert(user_data).execute()
        
        if result.data:
            print(f"✅ Utilisateur créé avec succès dans public.users!")
            print("\n📋 Détails de l'utilisateur créé:")
            for key, value in result.data[0].items():
                print(f"   - {key}: {value}")
            return True
        else:
            print("❌ Échec de la création de l'utilisateur")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la synchronisation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = sync_user()
    sys.exit(0 if success else 1)

