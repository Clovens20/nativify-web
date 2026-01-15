import asyncio
import nest_asyncio
import logging
import os
import zipfile
import io
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Maintenant on peut importer Playwright
try:
    from playwright.async_api import async_playwright, Browser, Page, Error as PlaywrightError
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    logging.warning("Playwright not installed. Screenshot generation will not work.")

# Résolutions requises par App Store
APP_STORE_RESOLUTIONS = {
    "iphone_6_7": {
        "name": "iPhone 6.7\" (14 Pro Max)",
        "width": 1290,
        "height": 2796,
        "device": "iPhone 14 Pro Max"
    },
    "iphone_6_5": {
        "name": "iPhone 6.5\" (11 Pro Max)",
        "width": 1242,
        "height": 2688,
        "device": "iPhone 11 Pro Max"
    },
    "iphone_5_5": {
        "name": "iPhone 5.5\" (8 Plus)",
        "width": 1242,
        "height": 2208,
        "device": "iPhone 8 Plus"
    },
    "ipad_pro_12_9": {
        "name": "iPad Pro 12.9\"",
        "width": 2048,
        "height": 2732,
        "device": "iPad Pro 12.9-inch"
    },
    "ipad_pro_11": {
        "name": "iPad Pro 11\"",
        "width": 1668,
        "height": 2388,
        "device": "iPad Pro 11-inch"
    },
    "ipad_10_5": {
        "name": "iPad 10.5\"",
        "width": 1668,
        "height": 2224,
        "device": "iPad Air"
    }
}

# 🚀 RÉSOLUTIONS OPTIMISÉES - Seulement les 2 plus importantes
PLAY_STORE_RESOLUTIONS = {
    "phone": {
        "name": "Phone",
        "width": 1080,
        "height": 1920,
        "device": "Pixel 5"
    },
    "tablet_10": {
        "name": "10\" Tablet",
        "width": 1200,
        "height": 1920,
        "device": "Nexus 10"
    }
}


class ScreenshotGenerator:
    """Générateur de screenshots pour les stores - VERSION OPTIMISÉE"""
    
    def __init__(self):
        if not HAS_PLAYWRIGHT:
            raise ImportError("Playwright is required. Install with: pip install playwright && playwright install chromium")
        self.browser: Optional[Browser] = None
        self.playwright = None
    
    async def initialize(self):
        """Initialize Playwright browser"""
        try:
            import sys

            # Appliquer nest_asyncio pour Python 3.13 Windows
            if sys.platform == 'win32' and sys.version_info >= (3, 13):
                nest_asyncio.apply()
                logger.info("✅ nest_asyncio appliqué pour Playwright")

            logger.info("Initializing Playwright browser...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            logger.info("✅ Browser launched successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Playwright: {e}")
            await self.close()
            raise
    
    async def close(self):
        """Ferme le navigateur"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Playwright browser closed")
    
    async def discover_pages(self, base_url: str, max_pages: int = 10) -> List[str]:
        """
        Découvre et vérifie les pages essentielles de l'application
        Ne garde QUE les pages qui existent (pas d'erreur 404)
        
        Args:
            base_url: URL de base de l'application
            max_pages: Non utilisé (gardé pour compatibilité)
        
        Returns:
            Liste des URLs des pages qui existent réellement
        """
        # 🎯 PAGES POTENTIELLES À VÉRIFIER
        # Le système vérifiera automatiquement lesquelles existent
        potential_pages = [
            {"url": base_url, "name": "Accueil"},
            {"url": f"{base_url}/auth", "name": "Connexion"},
            {"url": f"{base_url}/login", "name": "Login"},
            {"url": f"{base_url}/register", "name": "Inscription"},
            {"url": f"{base_url}/signup", "name": "Sign Up"},
            {"url": f"{base_url}/products", "name": "Produits"},
            {"url": f"{base_url}/produits", "name": "Produits (FR)"},
            {"url": f"{base_url}/shop", "name": "Boutique"},
            {"url": f"{base_url}/about", "name": "À propos"},
            {"url": f"{base_url}/contact", "name": "Contact"},
        ]
        
        # 🔍 Vérification : tester quelles pages existent vraiment
        verified_pages = []
        verified_urls = set()  # Pour éviter les doublons
        
        try:
            context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            for page_info in potential_pages:
                url = page_info["url"]
                name = page_info["name"]
                
                # Éviter les doublons (ex: si base_url et base_url/ sont identiques)
                if url in verified_urls:
                    continue
                
                try:
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                    
                    if response and response.status < 400:
                        verified_pages.append(url)
                        verified_urls.add(url)
                        logger.info(f"✅ Page trouvée: {name} ({url}) - Status {response.status}")
                    else:
                        logger.info(f"❌ Page ignorée: {name} ({url}) - Status {response.status}")
                        
                except Exception as e:
                    logger.info(f"❌ Page ignorée: {name} ({url}) - Erreur: {str(e)[:50]}")
            
            await context.close()
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des pages: {e}")
            # En cas d'erreur, au minimum on garde la page d'accueil
            verified_pages = [base_url]
        
        # 🛡️ Garantie : toujours avoir au moins la page d'accueil
        if not verified_pages:
            logger.warning("Aucune page vérifiée, utilisation de la page d'accueil par défaut")
            verified_pages = [base_url]
        
        logger.info(f"📸 {len(verified_pages)} page(s) seront capturées: {verified_pages}")
        
        return verified_pages
    
    async def capture_screenshot(
        self,
        url: str,
        width: int,
        height: int,
        device: Optional[str] = None,
        wait_time: int = 1  # 🚀 RÉDUIT de 3 à 1 seconde
    ) -> bytes:
        """
        Capture un screenshot d'une URL dans une résolution spécifique
        
        Args:
            url: URL à capturer
            width: Largeur en pixels
            height: Hauteur en pixels
            device: Nom du device Playwright (optionnel)
            wait_time: Temps d'attente avant capture (secondes)
        
        Returns:
            Bytes de l'image PNG
        """
        context = await self.browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=1,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        page = await context.new_page()
        
        try:
            # Naviguer vers l'URL
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # 🚀 Attente réduite à 1 seconde
            await asyncio.sleep(wait_time)
            
            # 🚀 SCROLL DÉSACTIVÉ pour plus de vitesse
            # Si vous avez besoin du scroll (lazy loading), décommentez ci-dessous :
            """
            await page.evaluate('''
                async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 100;
                        const timer = setInterval(() => {
                            const scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            
                            if(totalHeight >= scrollHeight){
                                clearInterval(timer);
                                window.scrollTo(0, 0);
                                resolve();
                            }
                        }, 100);
                    });
                }
            ''')
            await asyncio.sleep(1)
            """
            
            # Capturer le screenshot
            screenshot = await page.screenshot(
                type="png",
                full_page=False,  # Capturer seulement la viewport
            )
            
            await context.close()
            return screenshot
            
        except Exception as e:
            await context.close()
            logger.error(f"Error capturing screenshot of {url}: {e}")
            raise
    
    async def generate_all_screenshots(
        self,
        base_url: str,
        pages: Optional[List[str]] = None,
        store: str = "both",  # "ios", "android", "both"
        auto_discover: bool = True
    ) -> bytes:
        """
        Génère tous les screenshots nécessaires pour les stores
        
        Args:
            base_url: URL de base de l'application
            pages: Liste des pages à capturer (si None, pages essentielles)
            store: Store cible ("ios", "android", "both")
            auto_discover: Si True, utilise les pages essentielles définies
        
        Returns:
            Bytes du fichier ZIP contenant tous les screenshots
        """
        if pages is None and auto_discover:
            pages = await self.discover_pages(base_url)
        elif pages is None:
            pages = [base_url]
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            screenshots_generated = 0
            
            # Générer screenshots iOS si demandé
            if store in ["ios", "both"]:
                for resolution_id, resolution in APP_STORE_RESOLUTIONS.items():
                    for page_url in pages:
                        try:
                            page_name = self._get_page_name(page_url, base_url)
                            screenshot = await self.capture_screenshot(
                                page_url,
                                resolution["width"],
                                resolution["height"],
                                resolution.get("device")
                            )
                            
                            filename = f"ios/{resolution_id}/{page_name}.png"
                            zip_file.writestr(filename, screenshot)
                            screenshots_generated += 1
                            logger.info(f"Generated: {filename}")
                            
                        except Exception as e:
                            logger.error(f"Failed to generate {resolution_id} for {page_url}: {e}")
            
            # Générer screenshots Android si demandé
            if store in ["android", "both"]:
                for resolution_id, resolution in PLAY_STORE_RESOLUTIONS.items():
                    for page_url in pages:
                        try:
                            page_name = self._get_page_name(page_url, base_url)
                            screenshot = await self.capture_screenshot(
                                page_url,
                                resolution["width"],
                                resolution["height"],
                                resolution.get("device")
                            )
                            
                            filename = f"android/{resolution_id}/{page_name}.png"
                            zip_file.writestr(filename, screenshot)
                            screenshots_generated += 1
                            logger.info(f"Generated: {filename}")
                            
                        except Exception as e:
                            logger.error(f"Failed to generate {resolution_id} for {page_url}: {e}")
            
            # Ajouter un fichier README avec les instructions
            readme = self._generate_readme(pages, store, screenshots_generated)
            zip_file.writestr("README.txt", readme)
        
        zip_buffer.seek(0)
        return zip_buffer.read()
    
    def _get_page_name(self, url: str, base_url: str) -> str:
        """Extrait un nom de fichier propre depuis l'URL"""
        # Enlever le protocole et le domaine
        path = url.replace(base_url, "").strip("/")
        if not path:
            return "home"
        
        # Nettoyer le nom
        name = path.replace("/", "_").replace("?", "_").replace("&", "_").replace("=", "_")
        # Limiter la longueur
        if len(name) > 50:
            name = name[:50]
        
        return name or "page"
    
    def _generate_readme(self, pages: List[str], store: str, count: int) -> str:
        """Génère un fichier README avec les instructions"""
        return f"""NativiWeb Screenshot Generator - VERSION OPTIMISÉE
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Pages captured: {len(pages)}
Total screenshots: {count}
Store: {store}

🚀 OPTIMISATIONS ACTIVÉES:
- Seulement 2 résolutions Android (Phone + Tablet 10")
- Temps d'attente réduit à 1 seconde
- Scroll désactivé pour vitesse maximale
- 4 pages essentielles seulement

Pages:
{chr(10).join(f'  - {page}' for page in pages)}

Structure:
- ios/ : Screenshots pour App Store
  - iphone_6_7/ : iPhone 14 Pro Max (1290x2796)
  - iphone_6_5/ : iPhone 11 Pro Max (1242x2688)
  - iphone_5_5/ : iPhone 8 Plus (1242x2208)
  - ipad_pro_12_9/ : iPad Pro 12.9" (2048x2732)
  - ipad_pro_11/ : iPad Pro 11" (1668x2388)
  - ipad_10_5/ : iPad 10.5" (1668x2224)

- android/ : Screenshots pour Play Store (OPTIMISÉ)
  - phone/ : Phone (1080x1920) ✅
  - tablet_10/ : 10" Tablet (1200x1920) ✅

Instructions:
1. Extrayez ce ZIP
2. Utilisez les screenshots dans les dossiers correspondants
3. Pour App Store: Upload via App Store Connect
4. Pour Play Store: Upload via Google Play Console

Note: Version optimisée pour génération rapide (30-45 secondes au lieu de 8 minutes).
"""


# Fonction helper pour utilisation synchrone
async def _generate_screenshots_async_internal(
    base_url: str,
    pages: Optional[List[str]] = None,
    store: str = "both",
    auto_discover: bool = True
) -> bytes:
    """
    Version asynchrone du générateur de screenshots (pour FastAPI)
    
    Args:
        base_url: URL de base
        pages: Pages à capturer (None = pages essentielles)
        store: "ios", "android", ou "both"
        auto_discover: Utiliser les pages essentielles prédéfinies
    
    Returns:
        Bytes du ZIP contenant les screenshots
    """
    generator = ScreenshotGenerator()
    try:
        await generator.initialize()
        result = await generator.generate_all_screenshots(
            base_url, pages, store, auto_discover
        )
        return result
    finally:
        await generator.close()


async def generate_screenshots_async(
    base_url: str,
    pages: Optional[List[str]] = None,
    store: str = "both",
    auto_discover: bool = True
) -> bytes:
    """
    Version asynchrone du générateur de screenshots (pour FastAPI)
    
    Args:
        base_url: URL de base
        pages: Pages à capturer (None = pages essentielles)
        store: "ios", "android", ou "both"
        auto_discover: Utiliser les pages essentielles prédéfinies
    
    Returns:
        Bytes du ZIP contenant les screenshots
    """
    import sys

    # Sur Windows, Playwright doit tourner sur un event loop Proactor
    if sys.platform == "win32":
        try:
            loop = asyncio.get_running_loop()
            loop_name = type(loop).__name__
        except RuntimeError:
            loop = None
            loop_name = ""

        if loop is not None and "Proactor" not in loop_name:
            def _run_in_thread():
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                return asyncio.run(
                    _generate_screenshots_async_internal(
                        base_url, pages, store, auto_discover
                    )
                )

            return await asyncio.to_thread(_run_in_thread)

    return await _generate_screenshots_async_internal(
        base_url, pages, store, auto_discover
    )

def generate_screenshots_sync(
    base_url: str,
    pages: Optional[List[str]] = None,
    store: str = "both",
    auto_discover: bool = True
) -> bytes:
    """
    Version synchrone du générateur de screenshots (pour usage hors FastAPI)
    
    Args:
        base_url: URL de base
        pages: Pages à capturer (None = pages essentielles)
        store: "ios", "android", ou "both"
        auto_discover: Utiliser les pages essentielles prédéfinies
    
    Returns:
        Bytes du ZIP contenant les screenshots
    """
    # Vérifier si on est déjà dans un event loop
    try:
        loop = asyncio.get_running_loop()
        # Si on est dans un event loop, on ne peut pas utiliser asyncio.run()
        raise RuntimeError(
            "Cannot use generate_screenshots_sync() from within an async context. "
            "Use generate_screenshots_async() instead."
        )
    except RuntimeError:
        # Si l'erreur est celle qu'on a levée, la propager
        if "Cannot use generate_screenshots_sync" in str(RuntimeError):
            raise
        # Sinon, on n'est pas dans un event loop, on peut utiliser asyncio.run()
        pass
    
    async def _generate():
        generator = ScreenshotGenerator()
        try:
            await generator.initialize()
            result = await generator.generate_all_screenshots(
                base_url, pages, store, auto_discover
            )
            return result
        finally:
            await generator.close()
    
    return asyncio.run(_generate())