"""
API pour la soumission automatique à Google Play Store
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import logging

logger = logging.getLogger(__name__)


class PlayStoreAPI:
    """Classe pour gérer la soumission automatique à Google Play Store"""
    
    def __init__(self, credentials_path: str):
        """
        Initialise l'API Play Store
        
        Args:
            credentials_path: Chemin vers le fichier JSON de credentials Google Service Account
        """
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Credentials file not found: {credentials_path}")
        
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/androidpublisher']
        )
        self.service = build('androidpublisher', 'v3', credentials=self.credentials)
        logger.info("Play Store API initialized")
    
    def upload_aab(self, package_name: str, aab_path: str, track: str = 'internal'):
        """
        Upload un AAB (Android App Bundle) vers Google Play Store
        
        Args:
            package_name: Nom du package de l'application (ex: com.example.app)
            aab_path: Chemin vers le fichier AAB
            track: Piste de publication ('internal', 'alpha', 'beta', 'production')
        
        Returns:
            versionCode du bundle uploadé
        """
        if not os.path.exists(aab_path):
            raise FileNotFoundError(f"AAB file not found: {aab_path}")
        
        try:
            # Créer un nouvel edit
            edit = self.service.edits().insert(
                packageName=package_name,
                body={}
            ).execute()
            
            edit_id = edit['id']
            logger.info(f"Created edit: {edit_id}")
            
            # Upload le bundle
            logger.info(f"Uploading AAB: {aab_path}")
            media = MediaFileUpload(
                aab_path,
                mimetype='application/octet-stream',
                resumable=True
            )
            
            bundle = self.service.edits().bundles().upload(
                packageName=package_name,
                editId=edit_id,
                media_body=media
            ).execute()
            
            version_code = bundle['versionCode']
            logger.info(f"Bundle uploaded successfully. Version code: {version_code}")
            
            # Assigner à la piste
            self.service.edits().tracks().update(
                packageName=package_name,
                editId=edit_id,
                track=track,
                body={
                    'releases': [{
                        'versionCodes': [str(version_code)],
                        'status': 'completed'
                    }]
                }
            ).execute()
            
            logger.info(f"Bundle assigned to track: {track}")
            
            # Commit l'edit
            self.service.edits().commit(
                packageName=package_name,
                editId=edit_id
            ).execute()
            
            logger.info("Edit committed successfully")
            return version_code
            
        except Exception as e:
            logger.error(f"Error uploading AAB: {e}")
            raise
    
    def get_app_info(self, package_name: str):
        """
        Récupère les informations de l'application
        
        Args:
            package_name: Nom du package
        
        Returns:
            Informations de l'application
        """
        try:
            app = self.service.edits().get(packageName=package_name).execute()
            return app
        except Exception as e:
            logger.error(f"Error getting app info: {e}")
            raise

