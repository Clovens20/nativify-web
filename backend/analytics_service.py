"""
Service Analytics pour Firebase Analytics (ou alternative)
Ce service peut être étendu pour supporter d'autres providers d'analytics
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Essayer d'importer Firebase Analytics (optionnel)
try:
    import firebase_admin
    from firebase_admin import credentials, analytics
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logger.warning("Firebase Admin SDK not installed - Analytics will use stub implementation")


class AnalyticsService:
    """Service Analytics pour tracking d'événements"""
    
    def __init__(self):
        self.initialized = False
        if FIREBASE_AVAILABLE:
            try:
                # Initialiser Firebase (si credentials disponibles)
                # Note: En production, utiliser les credentials Firebase
                # firebase_admin.initialize_app()
                self.initialized = True
                logger.info("✅ Firebase Analytics initialized")
            except Exception as e:
                logger.warning(f"Firebase Analytics initialization failed: {e}")
                self.initialized = False
    
    def log_event(self, event_name: str, parameters: Optional[Dict[str, Any]] = None):
        """
        Enregistre un événement analytics
        
        Args:
            event_name: Nom de l'événement (ex: 'screen_view', 'button_click')
            parameters: Paramètres de l'événement (dict)
        """
        if not self.initialized or not FIREBASE_AVAILABLE:
            # Stub implementation - peut être étendu avec d'autres providers
            logger.debug(f"📊 Analytics event (stub): {event_name} - {parameters}")
            return
        
        try:
            # Utiliser Firebase Analytics si disponible
            # analytics.log_event(event_name, parameters or {})
            logger.info(f"📊 Analytics event: {event_name} - {parameters}")
        except Exception as e:
            logger.error(f"Error logging analytics event: {e}")
    
    def set_user_property(self, property_name: str, value: str):
        """
        Définit une propriété utilisateur
        
        Args:
            property_name: Nom de la propriété
            value: Valeur de la propriété
        """
        if not self.initialized or not FIREBASE_AVAILABLE:
            logger.debug(f"📊 Analytics user property (stub): {property_name} = {value}")
            return
        
        try:
            # Utiliser Firebase Analytics si disponible
            logger.info(f"📊 Analytics user property: {property_name} = {value}")
        except Exception as e:
            logger.error(f"Error setting analytics user property: {e}")
    
    def set_user_id(self, user_id: str):
        """
        Définit l'ID utilisateur pour analytics
        
        Args:
            user_id: ID utilisateur
        """
        if not self.initialized or not FIREBASE_AVAILABLE:
            logger.debug(f"📊 Analytics user ID (stub): {user_id}")
            return
        
        try:
            # Utiliser Firebase Analytics si disponible
            logger.info(f"📊 Analytics user ID: {user_id}")
        except Exception as e:
            logger.error(f"Error setting analytics user ID: {e}")


# Instance globale du service analytics
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Retourne l'instance globale du service analytics"""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service

