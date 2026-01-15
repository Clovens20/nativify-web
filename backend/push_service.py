"""
Service de push notifications (FCM pour Android, APNs pour iOS)
OPTIONNEL - Ne casse rien si non configuré
"""
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class PushNotificationService:
    """Service pour envoyer des push notifications"""
    
    def __init__(self):
        self.fcm_available = False
        self.apns_available = False
        self.fcm_messaging = None
        
        # Vérifier Firebase (optionnel)
        firebase_creds_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
        if firebase_creds_path and os.path.exists(firebase_creds_path):
            try:
                from firebase_admin import credentials, messaging, initialize_app
                cred = credentials.Certificate(firebase_creds_path)
                initialize_app(cred)
                self.fcm_available = True
                self.fcm_messaging = messaging
                logger.info("✅ Firebase Cloud Messaging initialized")
            except ImportError:
                logger.warning("⚠️ firebase-admin not installed - FCM disabled. Install with: pip install firebase-admin")
            except Exception as e:
                logger.warning(f"⚠️ FCM initialization failed: {e}")
        else:
            logger.info("ℹ️ FIREBASE_CREDENTIALS_PATH not set - FCM disabled")
        
        # Vérifier APNs (optionnel)
        self.apns_key_path = os.environ.get('APNS_KEY_PATH')
        self.apns_key_id = os.environ.get('APNS_KEY_ID')
        self.apns_team_id = os.environ.get('APNS_TEAM_ID')
        self.apns_bundle_id = os.environ.get('APNS_BUNDLE_ID')
        
        if all([self.apns_key_path, self.apns_key_id, self.apns_team_id]):
            try:
                # Vérifier que apns2 est disponible
                import apns2
                self.apns_available = True
                logger.info("✅ APNs configuration found")
            except ImportError:
                logger.warning("⚠️ apns2 not installed - iOS push disabled. Install with: pip install apns2")
        else:
            logger.info("ℹ️ APNs credentials not configured - iOS push disabled")
    
    def send_to_android(self, token: str, title: str, body: str, data: Optional[Dict] = None):
        """Envoyer à Android via FCM"""
        if not self.fcm_available:
            raise Exception("FCM not configured. Set FIREBASE_CREDENTIALS_PATH environment variable and install firebase-admin.")
        
        message = self.fcm_messaging.Message(
            notification=self.fcm_messaging.Notification(title=title, body=body),
            data={str(k): str(v) for k, v in (data or {}).items()},  # FCM data must be strings
            token=token
        )
        
        try:
            response = self.fcm_messaging.send(message)
            logger.info(f"✅ FCM message sent: {response}")
            return {"success": True, "message_id": response}
        except Exception as e:
            logger.error(f"❌ FCM error: {e}")
            raise
    
    def send_to_ios(self, token: str, title: str, body: str, data: Optional[Dict] = None):
        """Envoyer à iOS via APNs"""
        if not self.apns_available:
            raise Exception("APNs not configured. Set APNS_KEY_PATH, APNS_KEY_ID, APNS_TEAM_ID environment variables and install apns2.")
        
        try:
            from apns2.client import APNsClient
            from apns2.payload import Payload
            
            client = APNsClient(
                self.apns_key_path,
                use_sandbox=True,  # Utiliser production=False pour dev
                use_alternative_port=False
            )
            
            payload = Payload(
                alert={"title": title, "body": body},
                sound="default",
                badge=1,
                custom=data or {}
            )
            
            client.send_notification(token, payload, topic=self.apns_bundle_id)
            logger.info(f"✅ APNs message sent to {token[:20]}...")
            return {"success": True}
        except Exception as e:
            logger.error(f"❌ APNs error: {e}")
            raise
    
    def send_to_multiple(self, android_tokens: List[str], ios_tokens: List[str], 
                        title: str, body: str, data: Optional[Dict] = None):
        """Envoyer à plusieurs appareils"""
        results = {"android": [], "ios": []}
        
        for token in android_tokens:
            try:
                result = self.send_to_android(token, title, body, data)
                results["android"].append({"token": token, "success": True, **result})
            except Exception as e:
                results["android"].append({"token": token, "success": False, "error": str(e)})
        
        for token in ios_tokens:
            try:
                result = self.send_to_ios(token, title, body, data)
                results["ios"].append({"token": token, "success": True, **result})
            except Exception as e:
                results["ios"].append({"token": token, "success": False, "error": str(e)})
        
        return results

# Instance globale (optionnelle)
_push_service = None

def get_push_service():
    """Récupère l'instance du service push (singleton)"""
    global _push_service
    if _push_service is None:
        _push_service = PushNotificationService()
    return _push_service

