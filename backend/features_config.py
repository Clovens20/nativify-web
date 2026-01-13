"""
Configuration centralisée pour toutes les fonctionnalités natives
"""
FEATURES_CONFIG = {
    'in_app_purchases': {
        'android_permissions': ['com.android.vending.BILLING'],
        'android_dependencies': [
            'com.android.billingclient:billing-ktx:6.1.0',
            'com.android.billingclient:billing:6.1.0'
        ],
        'ios_frameworks': ['StoreKit'],
        'requires_config': True,
        'category': 'payments'
    },
    'qr_scanner': {
        'android_permissions': ['android.permission.CAMERA'],
        'android_dependencies': [
            'com.google.mlkit:barcode-scanning:17.2.0',
            'androidx.camera:camera-camera2:1.3.0',
            'androidx.camera:camera-lifecycle:1.3.0',
            'androidx.camera:camera-view:1.3.0'
        ],
        'ios_frameworks': ['AVFoundation', 'Vision'],
        'requires_config': False,
        'category': 'device'
    },
    'audio_recording': {
        'android_permissions': ['android.permission.RECORD_AUDIO'],
        'android_dependencies': [],
        'ios_frameworks': ['AVFoundation'],
        'requires_config': False,
        'category': 'media'
    },
    'video_recording': {
        'android_permissions': ['android.permission.RECORD_AUDIO', 'android.permission.CAMERA'],
        'android_dependencies': [],
        'ios_frameworks': ['AVFoundation', 'UIKit'],
        'requires_config': False,
        'category': 'media'
    },
    'offline_bundling': {
        'android_permissions': [],
        'android_dependencies': [],
        'ios_frameworks': [],
        'requires_config': False,
        'category': 'system'
    },
    'camera': {
        'android_permissions': ['android.permission.CAMERA'],
        'android_dependencies': [],
        'ios_frameworks': ['AVFoundation'],
        'requires_config': False,
        'category': 'device'
    },
    'geolocation': {
        'android_permissions': [
            'android.permission.ACCESS_FINE_LOCATION',
            'android.permission.ACCESS_COARSE_LOCATION'
        ],
        'android_dependencies': [],
        'ios_frameworks': ['CoreLocation'],
        'requires_config': False,
        'category': 'device'
    },
    'push_notifications': {
        'android_permissions': ['android.permission.POST_NOTIFICATIONS'],
        'android_dependencies': [],
        'ios_frameworks': ['UserNotifications'],
        'requires_config': True,
        'category': 'notifications'
    },
    'contacts': {
        'android_permissions': ['android.permission.READ_CONTACTS'],
        'android_dependencies': [],
        'ios_frameworks': ['Contacts'],
        'requires_config': False,
        'category': 'device'
    },
    'file_system': {
        'android_permissions': [
            'android.permission.READ_EXTERNAL_STORAGE',
            'android.permission.WRITE_EXTERNAL_STORAGE'
        ],
        'android_dependencies': [],
        'ios_frameworks': [],
        'requires_config': False,
        'category': 'system'
    },
    'biometrics': {
        'android_permissions': [],
        'android_dependencies': [
            'androidx.biometric:biometric:1.1.0'
        ],
        'ios_frameworks': ['LocalAuthentication'],
        'requires_config': False,
        'category': 'security'
    }
}

def get_android_permissions(features: list) -> list:
    """Récupère toutes les permissions Android nécessaires pour les features activées"""
    permissions = set()
    for feature in features:
        if isinstance(feature, dict):
            feature_id = feature.get('id', '')
        else:
            feature_id = feature
        
        if feature_id in FEATURES_CONFIG:
            permissions.update(FEATURES_CONFIG[feature_id]['android_permissions'])
    
    return sorted(list(permissions))

def get_android_dependencies(features: list) -> list:
    """Récupère toutes les dépendances Android nécessaires pour les features activées"""
    dependencies = set()
    for feature in features:
        if isinstance(feature, dict):
            feature_id = feature.get('id', '')
        else:
            feature_id = feature
        
        if feature_id in FEATURES_CONFIG:
            dependencies.update(FEATURES_CONFIG[feature_id]['android_dependencies'])
    
    return sorted(list(dependencies))

def get_ios_frameworks(features: list) -> list:
    """Récupère tous les frameworks iOS nécessaires pour les features activées"""
    frameworks = set()
    for feature in features:
        if isinstance(feature, dict):
            feature_id = feature.get('id', '')
        else:
            feature_id = feature
        
        if feature_id in FEATURES_CONFIG:
            frameworks.update(FEATURES_CONFIG[feature_id]['ios_frameworks'])
    
    return sorted(list(frameworks))

