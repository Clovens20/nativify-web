"""
API pour la soumission automatique à Apple App Store Connect
"""
import jwt
import time
import requests
import subprocess
import os
import logging

logger = logging.getLogger(__name__)


class AppStoreConnectAPI:
    """Classe pour gérer la soumission automatique à Apple App Store"""
    
    def __init__(self, key_id: str, issuer_id: str, private_key_path: str):
        """
        Initialise l'API App Store Connect
        
        Args:
            key_id: Key ID de la clé API App Store Connect
            issuer_id: Issuer ID de votre compte développeur
            private_key_path: Chemin vers le fichier .p8 de la clé privée
        """
        self.key_id = key_id
        self.issuer_id = issuer_id
        
        if not os.path.exists(private_key_path):
            raise FileNotFoundError(f"Private key file not found: {private_key_path}")
        
        with open(private_key_path, 'r') as f:
            self.private_key = f.read()
        
        logger.info("App Store Connect API initialized")
    
    def _generate_token(self):
        """
        Génère un token JWT pour l'API App Store Connect
        
        Returns:
            Token JWT
        """
        header = {
            'alg': 'ES256',
            'kid': self.key_id,
            'typ': 'JWT'
        }
        
        payload = {
            'iss': self.issuer_id,
            'iat': int(time.time()),
            'exp': int(time.time()) + 1200,  # 20 minutes
            'aud': 'appstoreconnect-v1'
        }
        
        return jwt.encode(payload, self.private_key, algorithm='ES256', headers=header)
    
    def upload_ipa(self, ipa_path: str, apple_id: str, app_specific_password: str):
        """
        Upload un IPA vers App Store Connect en utilisant Transporter (altool)
        
        Args:
            ipa_path: Chemin vers le fichier IPA
            apple_id: Apple ID du compte développeur
            app_specific_password: Mot de passe spécifique à l'application
        
        Returns:
            True si succès, False sinon
        """
        if not os.path.exists(ipa_path):
            raise FileNotFoundError(f"IPA file not found: {ipa_path}")
        
        try:
            # Utiliser xcrun altool (méthode recommandée)
            logger.info(f"Uploading IPA: {ipa_path}")
            
            result = subprocess.run([
                'xcrun', 'altool', '--upload-app',
                '-f', ipa_path,
                '-t', 'ios',
                '-u', apple_id,
                '-p', app_specific_password
            ], capture_output=True, text=True, timeout=3600)  # 1 heure timeout
            
            if result.returncode == 0:
                logger.info("IPA uploaded successfully")
                logger.info(result.stdout)
                return True
            else:
                logger.error(f"Error uploading IPA: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Upload timeout after 1 hour")
            return False
        except Exception as e:
            logger.error(f"Error uploading IPA: {e}")
            return False
    
    def upload_ipa_transporter(self, ipa_path: str, api_key_id: str, api_issuer_id: str):
        """
        Upload un IPA en utilisant Transporter avec API Key (méthode moderne)
        
        Args:
            ipa_path: Chemin vers le fichier IPA
            api_key_id: Key ID de l'API
            api_issuer_id: Issuer ID
        
        Returns:
            True si succès, False sinon
        """
        if not os.path.exists(ipa_path):
            raise FileNotFoundError(f"IPA file not found: {ipa_path}")
        
        try:
            logger.info(f"Uploading IPA with Transporter: {ipa_path}")
            
            # Utiliser Transporter CLI
            result = subprocess.run([
                'xcrun', 'transporter',
                '-f', ipa_path,
                '-t', 'signIn',
                '-u', api_key_id,
                '-p', api_issuer_id
            ], capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                logger.info("IPA uploaded successfully with Transporter")
                return True
            else:
                logger.error(f"Error uploading IPA: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading IPA with Transporter: {e}")
            return False
    
    def get_app_info(self, app_id: str):
        """
        Récupère les informations de l'application via l'API App Store Connect
        
        Args:
            app_id: ID de l'application dans App Store Connect
        
        Returns:
            Informations de l'application
        """
        try:
            token = self._generate_token()
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            url = f'https://api.appstoreconnect.apple.com/v1/apps/{app_id}'
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error getting app info: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting app info: {e}")
            return None

