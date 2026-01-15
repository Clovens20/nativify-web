#!/usr/bin/env python3
"""
Script Python pour synchroniser un utilisateur spécifique de auth.users vers public.users
Usage: python scripts/sync-user.py <user_id>
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
load_dotenv('.env')

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Erreur: SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY doivent être définis dans .env")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def sync_user(user_id: str):
    print(f"\n🔍 Synchronisation de l'utilisateur: {user_id}\n")
    
    try:
        # 1. Vérifier si l'utilisateur existe dans auth.users
        print("1. Vérification dans auth.users...")
        auth_user_response = supabase.auth.admin.get_user_by_id(user_id)
        auth_user = auth_user_response.user
        
        if not auth_user:
            print(f"❌ Utilisateur {user_id} non trouvé dans auth.users")
            return False
        
        print(f"✅ Utilisateur trouvé dans auth.users:")
        print(f"   - Email: {auth_user.email}")
        print(f"   - Créé le: {auth_user.created_at}")
        
        # 2. Vérifier si l'utilisateur existe déjà dans public.users
        print("\n2. Vérification dans public.users...")
        existing_user = supabase.table("users").select("*").eq("id", user_id).execute()
        
        if existing_user.data:
            print(f"⚠️  Utilisateur existe déjà dans public.users:")
            print(f"   - Email: {existing_user.data[0].get('email')}")
            print(f"   - Nom: {existing_user.data[0].get('name')}")
            print(f"   - Rôle: {existing_user.data[0].get('role')}")
            print("\n🔄 Mise à jour de l'utilisateur...")
        else:
            print("ℹ️  Utilisateur non trouvé dans public.users, création...")
        
        # 3. Synchroniser/Insérer dans public.users
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
        
        # Utiliser upsert pour créer ou mettre à jour
        response = supabase.table("users").upsert(user_data, on_conflict="id").execute()
        
        if response.data:
            print("\n✅ Utilisateur synchronisé avec succès!")
            print(f"\n📋 Données de l'utilisateur:")
            user_info = response.data[0]
            print(f"   - ID: {user_info.get('id')}")
            print(f"   - Email: {user_info.get('email')}")
            print(f"   - Nom: {user_info.get('name')}")
            print(f"   - Rôle: {user_info.get('role')}")
            print(f"   - Statut: {user_info.get('status')}")
            print(f"   - Créé le: {user_info.get('created_at')}")
            return True
        else:
            print("❌ Erreur: Aucune donnée retournée après synchronisation")
            return False
            
    except Exception as e:
        print(f"\n❌ Erreur lors de la synchronisation: {e}")
        import traceback
        traceback.print_exc()
        return False

def sync_user_by_email(email: str):
    """Synchroniser un utilisateur par son email"""
    print(f"\n🔍 Recherche de l'utilisateur par email: {email}\n")
    
    try:
        # Rechercher l'utilisateur dans auth.users par email
        auth_users_response = supabase.auth.admin.list_users()
        auth_user = None
        
        if auth_users_response and hasattr(auth_users_response, 'users'):
            for user in auth_users_response.users:
                if user.email == email:
                    auth_user = user
                    break
        
        if not auth_user:
            print(f"❌ Utilisateur avec l'email {email} non trouvé dans auth.users")
            return False
        
        # Utiliser la fonction existante avec l'ID trouvé
        return sync_user(auth_user.id)
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la recherche par email: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Erreur: ID utilisateur ou email requis")
        print("\nUsage:")
        print("  python scripts/sync-user.py <user_id>")
        print("  python scripts/sync-user.py --email <email>")
        print("\nExemples:")
        print("  python scripts/sync-user.py fd599f98-56cf-445f-93d6-abdde48f959c")
        print("  python scripts/sync-user.py --email desirdalia@gmail.com")
        sys.exit(1)
    
    if sys.argv[1] == '--email' or sys.argv[1] == '-e':
        if len(sys.argv) < 3:
            print("❌ Erreur: Email requis après --email")
            sys.exit(1)
        email = sys.argv[2]
        success = sync_user_by_email(email)
    else:
        user_id = sys.argv[1]
        success = sync_user(user_id)
    
    if success:
        print("\n✨ Synchronisation terminée! L'utilisateur devrait maintenant apparaître dans l'interface admin.")
    else:
        print("\n⚠️  La synchronisation a échoué. Vérifiez les erreurs ci-dessus.")
        sys.exit(1)

