"""
Générateur automatique de screenshots pour App Store et Play Store
Utilise Playwright pour capturer les pages dans les résolutions exactes requises
"""
import sys
import os
import asyncio
import logging
import zipfile
import io
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Fix Python 3.13 Windows - DOIT être appliqué AVANT toute utilisation de Playwright
if sys.platform == "win32" and sys.version_info >= (3, 13):
    try:
        # Forcer l'utilisation de WindowsProactorEventLoopPolicy pour supporter les subprocess
        current_policy = asyncio.get_event_loop_policy()
        if not isinstance(current_policy, asyncio.WindowsProactorEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            logger.info("✅ Fix Python 3.13 Windows appliqué dans screenshot_generator")
        
        # Vérifier le loop actuel et le recréer si nécessaire
        try:
            loop = asyncio.get_running_loop()
            # Si le loop actuel n'est pas un ProactorEventLoop, on ne peut pas le changer
            # Il faudra créer un nouveau loop dans un thread séparé
            if not isinstance(loop, asyncio.ProactorEventLoop):
                logger.warning("⚠️ Le loop d'événements actuel n'est pas compatible avec Playwright sur Python 3.13 Windows")
        except RuntimeError:
            # Pas de loop en cours, c'est bon
            pass
    except Exception as e:
        logger.warning(f"⚠️ Impossible de vérifier la policy asyncio: {e}")

try:
    from playwright.async_api import async_playwright, Browser, Page, Error as PlaywrightError
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    logging.warning("Playwright not installed. Screenshot generation will not work.")

logger = logging.getLogger(__name__)

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

# Résolutions requises par Play Store
PLAY_STORE_RESOLUTIONS = {
    "phone": {
        "name": "Phone",
        "width": 1080,
        "height": 1920,
        "device": "Pixel 5"
    },
    "tablet_7": {
        "name": "7\" Tablet",
        "width": 800,
        "height": 1280,
        "device": "Nexus 7"
    },
    "tablet_10": {
        "name": "10\" Tablet",
        "width": 1200,
        "height": 1920,
        "device": "Nexus 10"
    },
    "tv": {
        "name": "TV",
        "width": 1280,
        "height": 720,
        "device": "TV"
    },
    "wear": {
        "name": "Wear",
        "width": 400,
        "height": 400,
        "device": "Wear"
    }
}


class ScreenshotGenerator:
    """Générateur de screenshots pour les stores"""
    
    def __init__(self):
        if not HAS_PLAYWRIGHT:
            raise ImportError("Playwright is required. Install with: pip install playwright && playwright install chromium")
        self.browser: Optional[Browser] = None
        self.playwright = None
    
    async def initialize(self):
        """Initialise le navigateur Playwright"""
        # S'assurer que la policy est correcte avant d'initialiser Playwright
        if sys.platform == "win32" and sys.version_info >= (3, 13):
            try:
                current_policy = asyncio.get_event_loop_policy()
                if not isinstance(current_policy, asyncio.WindowsProactorEventLoopPolicy):
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                    logger.info("✅ Fix Python 3.13 Windows appliqué avant l'initialisation de Playwright")
            except Exception as e:
                logger.warning(f"⚠️ Erreur lors de la vérification de la policy: {e}")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        logger.info("Playwright browser initialized")
    
    async def close(self):
        """Ferme le navigateur"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Playwright browser closed")
    
    async def discover_pages(self, base_url: str, max_pages: int = 10) -> List[str]:
        """
        Découvre automatiquement les pages importantes d'une web app
        
        Args:
            base_url: URL de base de l'application
            max_pages: Nombre maximum de pages à découvrir
        
        Returns:
            Liste des URLs des pages importantes
        """
        pages = [base_url]  # Toujours inclure la page d'accueil
        
        try:
            context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            # Aller sur la page d'accueil
            await page.goto(base_url, wait_until="networkidle", timeout=30000)
            
            # Attendre que la page soit chargée
            await asyncio.sleep(2)
            
            # Trouver tous les liens internes
            links = await page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href]'));
                    const baseUrl = window.location.origin;
                    const internalLinks = new Set();
                    
                    links.forEach(link => {
                        const href = link.getAttribute('href');
                        if (!href) return;
                        
                        // Convertir les liens relatifs en absolus
                        let fullUrl;
                        try {
                            fullUrl = new URL(href, baseUrl).href;
                        } catch (e) {
                            return;
                        }
                        
                        // Ne garder que les liens internes
                        if (fullUrl.startsWith(baseUrl) && 
                            !fullUrl.includes('#') && 
                            !fullUrl.includes('mailto:') &&
                            !fullUrl.includes('tel:') &&
                            !fullUrl.includes('javascript:') &&
                            fullUrl !== baseUrl &&
                            fullUrl !== baseUrl + '/') {
                            internalLinks.add(fullUrl);
                        }
                    });
                    
                    return Array.from(internalLinks).slice(0, 10);
                }
            """)
            
            pages.extend(links[:max_pages - 1])
            
            await context.close()
            logger.info(f"Discovered {len(pages)} pages: {pages}")
            
        except Exception as e:
            logger.error(f"Error discovering pages: {e}")
        
        return list(set(pages))  # Supprimer les doublons
    
    async def capture_screenshot(
        self,
        url: str,
        width: int,
        height: int,
        device: Optional[str] = None,
        wait_time: int = 3
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
            
            # Attendre que la page soit complètement chargée
            await asyncio.sleep(wait_time)
            
            # Scroll pour charger le contenu lazy
            await page.evaluate("""
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
            """)
            
            # Attendre un peu après le scroll
            await asyncio.sleep(1)
            
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
            pages: Liste des pages à capturer (si None, auto-découverte)
            store: Store cible ("ios", "android", "both")
            auto_discover: Si True, découvre automatiquement les pages
        
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
        return f"""NativiWeb Screenshot Generator
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Pages captured: {len(pages)}
Total screenshots: {count}
Store: {store}

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

- android/ : Screenshots pour Play Store
  - phone/ : Phone (1080x1920)
  - tablet_7/ : 7" Tablet (800x1280)
  - tablet_10/ : 10" Tablet (1200x1920)
  - tv/ : TV (1280x720)
  - wear/ : Wear (400x400)

Instructions:
1. Extrayez ce ZIP
2. Utilisez les screenshots dans les dossiers correspondants
3. Pour App Store: Upload via App Store Connect
4. Pour Play Store: Upload via Google Play Console

Note: Les screenshots sont optimisés pour chaque résolution requise.
"""


# Fonction helper pour utilisation synchrone
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
        pages: Pages à capturer (None = auto-découverte)
        store: "ios", "android", ou "both"
        auto_discover: Découvrir automatiquement les pages
    
    Returns:
        Bytes du ZIP contenant les screenshots
    """
    # Fix Python 3.13 Windows - Le loop d'événements doit être un ProactorEventLoop
    # pour supporter les subprocess de Playwright
    if sys.platform == "win32" and sys.version_info >= (3, 13):
        try:
            loop = asyncio.get_running_loop()
            # Vérifier si le loop actuel est compatible
            if not isinstance(loop, asyncio.ProactorEventLoop):
                # Le loop actuel n'est pas compatible, utiliser un thread séparé
                import concurrent.futures
                logger.info("⚠️ Loop d'événements non compatible avec Playwright, utilisation d'un thread séparé")
                
                # Définir la fonction async interne avant de la passer au thread
                async def _generate_in_loop():
                    generator = ScreenshotGenerator()
                    try:
                        await generator.initialize()
                        result = await generator.generate_all_screenshots(
                            base_url, pages, store, auto_discover
                        )
                        return result
                    finally:
                        await generator.close()
                
                def run_in_new_loop():
                    """Exécute la génération dans un nouveau loop avec la bonne policy"""
                    # Forcer la policy Proactor pour Windows Python 3.13
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(_generate_in_loop())
                    finally:
                        new_loop.close()
                        asyncio.set_event_loop(None)
                
                # Exécuter dans un thread séparé avec un nouveau loop
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_new_loop)
                    try:
                        return future.result(timeout=300)  # Timeout de 5 minutes
                    except concurrent.futures.TimeoutError:
                        logger.error("Timeout lors de la génération de screenshots")
                        raise TimeoutError("Timeout lors de la génération de screenshots")
                    except Exception as e:
                        logger.error(f"Erreur dans le thread de génération: {e}")
                        raise
        except RuntimeError:
            # Pas de loop en cours d'exécution, on peut utiliser le code normal
            # Mais on s'assure que la policy est correcte
            current_policy = asyncio.get_event_loop_policy()
            if not isinstance(current_policy, asyncio.WindowsProactorEventLoopPolicy):
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                logger.info("✅ Fix Python 3.13 Windows appliqué dans generate_screenshots_async")
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors du fix Python 3.13: {e}")
    
    # Exécution normale
    generator = ScreenshotGenerator()
    try:
        await generator.initialize()
        result = await generator.generate_all_screenshots(
            base_url, pages, store, auto_discover
        )
        return result
    finally:
        await generator.close()

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
        pages: Pages à capturer (None = auto-découverte)
        store: "ios", "android", ou "both"
        auto_discover: Découvrir automatiquement les pages
    
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

