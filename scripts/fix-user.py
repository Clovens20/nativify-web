#!/usr/bin/env python3
"""
Script pour créer un utilisateur dans la table users s'il n'existe pas
Usage: python scripts/fix-user.py USER_ID
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Charger les variables d'environnement
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / 'backend' / '.env')

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Erreur: SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY doivent être définis dans backend/.env")
    sys.exit(1)

def fix_user(user_id: str):
    """Créer l'utilisateur dans la table users s'il n'existe pas"""
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Vérifier si l'utilisateur existe dans users
    try:
        result = client.table("users").select("id, email, role").eq("id", user_id).single().execute()
        if result.data:
            print(f"✅ L'utilisateur {user_id} existe déjà dans la table users")
            print(f"   Email: {result.data.get('email')}")
            print(f"   Role: {result.data.get('role')}")
            return True
    except Exception as e:
        if "No rows" in str(e) or "not found" in str(e).lower():
            print(f"⚠️  L'utilisateur {user_id} n'existe pas dans la table users")
        else:
            print(f"❌ Erreur lors de la vérification: {e}")
            return False
    
    # Essayer de récupérer depuis auth.users (nécessite admin API)
    # Note: Cette partie nécessite l'API Admin de Supabase
    print(f"🔄 Tentative de récupération depuis auth.users...")
    
    try:
        # On ne peut pas directement accéder à auth.users via le client Python
        # Il faut utiliser l'API Admin ou créer manuellement
        print("❌ Impossible de récupérer depuis auth.users automatiquement")
        print("   Veuillez utiliser le script SQL sync-users.sql dans Supabase SQL Editor")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/fix-user.py USER_ID")
        print(f"\nExemple: python scripts/fix-user.py 6488b320-b39f-411d-849e-4d36a5145f70")
        sys.exit(1)
    
    user_id = sys.argv[1]
    print(f"🔍 Vérification de l'utilisateur: {user_id}\n")
    
    if fix_user(user_id):
        print("\n✅ Opération réussie!")
    else:
        print("\n❌ Opération échouée")
        print("\n💡 Solution alternative:")
        print("   1. Allez dans Supabase SQL Editor")
        print("   2. Exécutez le script scripts/sync-users.sql")
        sys.exit(1)

