"""
Système de build Android réel pour compiler les projets Android et générer des APKs fonctionnels
VERSION CORRIGÉE - Meilleure gestion des erreurs et téléchargement automatique
"""
import os
import platform
import subprocess
import tempfile
import shutil
import zipfile
import io
import logging
import urllib.request
import time
import re
from pathlib import Path
from typing import Optional, Tuple, List
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _setup_java_environment():
    """Configure JAVA_HOME automatiquement selon l'OS"""
    # Si JAVA_HOME existe déjà et est valide, ne rien faire
    java_home = os.environ.get('JAVA_HOME')
    if java_home:
        java_exe = os.path.join(java_home, 'bin', 'java.exe' if os.name == 'nt' else 'java')
        if os.path.exists(java_exe):
            return  # JAVA_HOME déjà configuré correctement
    
    # Auto-détection selon l'OS
    system = platform.system()
    
    if system == 'Linux':
        # Chemins courants sur Linux/Docker
        possible_paths = [
            '/usr/lib/jvm/java-21-openjdk-amd64',
            '/usr/lib/jvm/java-17-openjdk-amd64',
            '/usr/lib/jvm/default-java',
        ]
        for path in possible_paths:
            if os.path.exists(path):
                os.environ['JAVA_HOME'] = path
                logger.info(f"✅ JAVA_HOME auto-détecté: {path}")
                return
                
    elif system == 'Windows':
        # Chemins courants sur Windows
        possible_paths = [
            r'C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot',
            r'C:\Program Files\Java\jdk-17',
            r'C:\Program Files\Java\jdk-21',
        ]
        for path in possible_paths:
            if os.path.exists(path):
                os.environ['JAVA_HOME'] = path
                logger.info(f"✅ JAVA_HOME auto-détecté: {path}")
                return
    
    logger.warning("⚠️ JAVA_HOME non trouvé automatiquement")


class AndroidBuilderErrorHandler:
    """Gère les erreurs de compilation Android et tente de les corriger"""
    
    @staticmethod
    def extract_kotlin_errors(log_content: str) -> List[dict]:
        """Extrait les erreurs Kotlin du log"""
        errors = []
        lines = log_content.split('\n')
        
        for i, line in enumerate(lines):
            if 'e: file:///' in line and '.kt:' in line:
                error_info = {
                    'file': line.split('file:///')[1].split(':')[0] if 'file:///' in line else '',
                    'line': '',
                    'message': ''
                }
                
                # Chercher le message d'erreur sur les lignes suivantes
                for j in range(i+1, min(i+5, len(lines))):
                    if lines[j].strip() and not lines[j].startswith('e:'):
                        error_info['message'] = lines[j].strip()
                        break
                
                errors.append(error_info)
        
        return errors
    
    @staticmethod
    def _extract_package_name(bridge_path: Path) -> str:
        """Extrait le package name depuis le fichier ou le chemin"""
        try:
            # Essayer d'extraire depuis le fichier existant
            content = bridge_path.read_text(encoding='utf-8')
            package_match = re.search(r'package\s+([a-zA-Z0-9_.]+)', content)
            if package_match:
                return package_match.group(1)
            
            # Sinon, extraire depuis le chemin du fichier
            parts = bridge_path.parts
            if 'java' in parts:
                java_idx = parts.index('java')
                if java_idx + 1 < len(parts):
                    package_parts = parts[java_idx + 1:-1]  # Exclure le nom du fichier
                    return '.'.join(package_parts)
        except Exception as e:
            logger.warning(f"⚠️ Impossible d'extraire le package: {e}")
        
        # Fallback
        return "com.nativiweb.app"
    
    @staticmethod
    def fix_nativiweb_bridge_advanced(project_path: Path) -> bool:
        """Correction avancée du fichier NativiWebBridge.kt avec template validé"""
        bridge_path = None
        
        # Chercher le fichier récursivement
        for kt_file in project_path.rglob("NativiWebBridge.kt"):
            bridge_path = kt_file
            break
        
        if not bridge_path or not bridge_path.exists():
            logger.error("❌ NativiWebBridge.kt non trouvé")
            return False
        
        try:
            # Extraire le package name
            package_name = AndroidBuilderErrorHandler._extract_package_name(bridge_path)
            logger.info(f"📦 Package name détecté: {package_name}")
            
            # Template de fichier NativiWebBridge.kt corrigé (compatible avec MainActivity.kt)
            fixed_content = f'''package {package_name}

import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.widget.Toast
import android.content.Context
import org.json.JSONObject

class NativiWebBridge(private val context: Context, private val webView: WebView) {{
    
    @JavascriptInterface
    fun showToast(message: String) {{
        android.os.Handler(android.os.Looper.getMainLooper()).post {{
            Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
        }}
    }}
    
    @JavascriptInterface
    fun getPlatform(): String {{
        return "android"
    }}
    
    @JavascriptInterface
    fun isNative(): Boolean {{
        return true
    }}
    
    @JavascriptInterface
    fun getDeviceInfo(): String {{
        val deviceInfo = JSONObject()
        try {{
            deviceInfo.put("platform", "Android")
            deviceInfo.put("platformVersion", android.os.Build.VERSION.RELEASE)
            deviceInfo.put("deviceModel", android.os.Build.MODEL)
            deviceInfo.put("manufacturer", android.os.Build.MANUFACTURER)
            deviceInfo.put("appVersion", "1.0.0")
            deviceInfo.put("sdkVersion", "1.0.0")
            deviceInfo.put("isNative", true)
        }} catch (e: Exception) {{
            e.printStackTrace()
        }}
        return deviceInfo.toString()
    }}
    
    @JavascriptInterface
    fun vibrate(duration: Int) {{
        try {{
            val vibrator = context.getSystemService(Context.VIBRATOR_SERVICE) as? android.os.Vibrator
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {{
                vibrator?.vibrate(android.os.VibrationEffect.createOneShot(duration.toLong(), android.os.VibrationEffect.DEFAULT_AMPLITUDE))
            }} else {{
                @Suppress("DEPRECATION")
                vibrator?.vibrate(duration.toLong())
            }}
        }} catch (e: Exception) {{
            e.printStackTrace()
        }}
    }}
    
    @JavascriptInterface
    fun copyToClipboard(text: String) {{
        try {{
            val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as android.content.ClipboardManager
            val clip = android.content.ClipData.newPlainText("text", text)
            clipboard.setPrimaryClip(clip)
        }} catch (e: Exception) {{
            e.printStackTrace()
        }}
    }}
}}
'''
            
            # Écrire le contenu corrigé
            bridge_path.write_text(fixed_content, encoding='utf-8')
            logger.info(f"✅ NativiWebBridge.kt corrigé : {bridge_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la correction : {str(e)}")
            return False
    
    @staticmethod
    def fix_kotlin_syntax_errors(log: str, project_path: Path) -> bool:
        """Correction spécifique des erreurs Kotlin détectées dans les logs"""
        kotlin_errors = [
            "'return' is not allowed here",
            "Expecting a top level declaration",
            "A 'return' expression required in a function",
            "Unresolved reference",
            "Type mismatch"
        ]
        
        has_kotlin_errors = any(err in log for err in kotlin_errors)
        
        if has_kotlin_errors:
            logger.info("🔧 Détection d'erreurs Kotlin, application du correctif...")
            return AndroidBuilderErrorHandler.fix_nativiweb_bridge_advanced(project_path)
        
        return False
    
    @staticmethod
    def fix_nativiweb_bridge_errors(project_path: Path) -> bool:
        """Corrige les erreurs courantes dans NativiWebBridge.kt (méthode de fallback)"""
        # Utiliser la méthode avancée
        return AndroidBuilderErrorHandler.fix_nativiweb_bridge_advanced(project_path)
    
    @staticmethod
    def fix_gradle_build_errors(project_path: Path, error_log: str) -> bool:
        """Tente de corriger les erreurs Gradle"""
        fixed = False
        
        # Corriger build.gradle si nécessaire
        build_gradle = project_path / "app" / "build.gradle"
        
        if build_gradle.exists():
            try:
                content = build_gradle.read_text(encoding='utf-8')
                original = content
                
                # Ajouter les dépendances manquantes
                if 'androidx.webkit:webkit' not in content:
                    dependencies_section = content.find('dependencies {')
                    if dependencies_section != -1:
                        insert_pos = content.find('\n', dependencies_section) + 1
                        if insert_pos > 0:
                            content = content[:insert_pos] + \
                                    '    implementation "androidx.webkit:webkit:1.8.0"\n' + \
                                    content[insert_pos:]
                
                if content != original:
                    build_gradle.write_text(content, encoding='utf-8')
                    logger.info("✅ build.gradle corrigé")
                    fixed = True
                    
            except Exception as e:
                logger.error(f"❌ Erreur correction build.gradle: {e}")
        
        return fixed
    
    @staticmethod
    def clean_project(project_path: Path):
        """Nettoie le projet pour forcer une recompilation"""
        try:
            # Supprimer les dossiers de build
            for folder in ['build', '.gradle', 'app/build', '.gradle']:
                folder_path = project_path / folder
                if folder_path.exists():
                    shutil.rmtree(folder_path, ignore_errors=True)
                    logger.info(f"🧹 Nettoyé: {folder}")
        except Exception as e:
            logger.warning(f"⚠️ Erreur nettoyage: {e}")
    
    @staticmethod
    def attempt_auto_fix(project_path: Path, error_log: str, attempt: int) -> bool:
        """Tente de corriger automatiquement les erreurs"""
        logger.info(f"🔧 Tentative de correction automatique {attempt}/3")
        
        fixed = False
        
        # PRIORITÉ 1: Corriger les erreurs Kotlin avec la nouvelle méthode
        if AndroidBuilderErrorHandler.fix_kotlin_syntax_errors(error_log, project_path):
            logger.info("✅ Erreurs Kotlin corrigées")
            fixed = True
        
        # Extraire les erreurs (fallback)
        if not fixed:
            kotlin_errors = AndroidBuilderErrorHandler.extract_kotlin_errors(error_log)
            
            if kotlin_errors:
                logger.info(f"📋 {len(kotlin_errors)} erreurs Kotlin détectées")
                
                # Corriger NativiWebBridge.kt
                if AndroidBuilderErrorHandler.fix_nativiweb_bridge_errors(project_path):
                    fixed = True
        
        # Corriger les erreurs Gradle
        if AndroidBuilderErrorHandler.fix_gradle_build_errors(project_path, error_log):
            fixed = True
        
        # Nettoyer le projet pour forcer une recompilation complète
        if fixed:
            AndroidBuilderErrorHandler.clean_project(project_path)
        
        return fixed


class AndroidBuilder:
    """Classe pour compiler des projets Android et générer des APKs fonctionnels"""
    
    def __init__(self):
        # Configurer Java automatiquement
        _setup_java_environment()
        
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"🔍 .env chargé depuis: {env_path}")
        else:
            root_env = Path(__file__).parent.parent / '.env'
            if root_env.exists():
                load_dotenv(root_env)
                logger.info(f"🔍 .env chargé depuis: {root_env}")
        
        # Auto-détection Java
        java_home = os.environ.get('JAVA_HOME')
        if not java_home:
            java_home = self._find_java_home()
        
        self.java_home = java_home
        
        # Auto-détection Android SDK
        android_home = (
            os.environ.get('ANDROID_HOME') or 
            os.environ.get('ANDROID_SDK_ROOT')
        )
        if not android_home:
            android_home = self._find_android_sdk()
        
        self.android_home = android_home
        
        logger.info(f"🔍 AndroidBuilder init - JAVA_HOME: {self.java_home}")
        logger.info(f"🔍 AndroidBuilder init - ANDROID_HOME: {self.android_home}")
        
        self.check_dependencies()
    
    def _find_java_home(self) -> Optional[str]:
        """Trouve automatiquement JAVA_HOME"""
        common_java_paths = [
            r"C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot",
            r"C:\Program Files\Java\jdk-17",
            r"C:\Program Files\Java\jdk-17.0.17.10-hotspot",
            r"C:\Program Files\OpenJDK\jdk-17",
            r"C:\Program Files\Temurin\jdk-17",
        ]
        
        # Chercher dans Eclipse Adoptium
        adoptium_base = Path(r"C:\Program Files\Eclipse Adoptium")
        if adoptium_base.exists():
            for jdk_dir in sorted(adoptium_base.iterdir(), reverse=True):
                if jdk_dir.is_dir() and 'jdk' in jdk_dir.name.lower():
                    java_exe = jdk_dir / 'bin' / 'java.exe'
                    if java_exe.exists():
                        logger.info(f"🔍 Java trouvé automatiquement: {jdk_dir}")
                        return str(jdk_dir)
        
        # Chercher dans les chemins communs
        for path_str in common_java_paths:
            java_path = Path(path_str)
            java_exe = java_path / 'bin' / ('java.exe' if os.name == 'nt' else 'java')
            if java_exe.exists():
                logger.info(f"🔍 Java trouvé dans chemin commun: {java_path}")
                return str(java_path)
        
        # Chercher dans PATH
        try:
            java_cmd = 'java.exe' if os.name == 'nt' else 'java'
            java_in_path = shutil.which(java_cmd)
            if java_in_path:
                java_home = Path(java_in_path).parent.parent
                logger.info(f"🔍 Java trouvé dans PATH: {java_home}")
                return str(java_home)
        except Exception:
            pass
        
        return None
    
    def _find_android_sdk(self) -> Optional[str]:
        """Trouve automatiquement Android SDK"""
        common_android_paths = [
            r"C:\Android\Sdk",
            r"C:\Android",
            Path.home() / "AppData" / "Local" / "Android" / "Sdk",
            Path.home() / "Android" / "Sdk",
        ]
        
        for path in common_android_paths:
            android_path = Path(path) if isinstance(path, str) else path
            # Vérifier que le SDK est valide (contient platform-tools)
            if android_path.exists() and (android_path / "platform-tools").exists():
                logger.info(f"🔍 Android SDK trouvé automatiquement: {android_path}")
                return str(android_path)
        
        return None
    
    def check_dependencies(self) -> Tuple[bool, Optional[str]]:
        """Vérifie que Java et Android SDK sont disponibles"""
        errors = []
        
        # Vérifier Java
        java_available = False
        java_version = None
        
        if self.java_home:
            java_exe_name = 'java.exe' if os.name == 'nt' else 'java'
            java_exe = Path(self.java_home) / 'bin' / java_exe_name
            if java_exe.exists():
                try:
                    result = subprocess.run(
                        [str(java_exe), '-version'], 
                        capture_output=True, 
                        text=True, 
                        timeout=10
                    )
                    if result.returncode == 0:
                        java_available = True
                        # Extraire la version
                        version_output = result.stderr or result.stdout
                        version_match = re.search(r'version "(\d+)', version_output)
                        if version_match:
                            java_version = int(version_match.group(1))
                            logger.info(f"✅ Java {java_version} trouvé: {version_output.split(chr(10))[0]}")
                            
                            # Vérifier version minimale (Java 17+)
                            if java_version < 17:
                                errors.append(f"Java {java_version} détecté, mais Java 17+ est requis pour Android")
                                java_available = False
                        else:
                            logger.info(f"✅ Java trouvé: {version_output.split(chr(10))[0]}")
                except Exception as e:
                    logger.warning(f"Erreur lors de la vérification de Java: {e}")
        
        if not java_available:
            errors.append("Java JDK 17+ non trouvé. Installez Java JDK 17 ou supérieur et définissez JAVA_HOME.")
        
        # SDK optionnel mais recommandé
        if self.android_home and Path(self.android_home).exists():
            logger.info(f"✅ Android SDK trouvé: {self.android_home}")
        else:
            logger.info(f"ℹ️  Android SDK non trouvé (les dépendances seront téléchargées par Gradle)")
        
        if errors:
            return False, "; ".join(errors)
        return True, None
    
    def download_gradle_wrapper_jar(self, project_dir: Path, max_retries: int = 3) -> bool:
        """Télécharge gradle-wrapper.jar si nécessaire avec retry"""
        gradle_wrapper_jar = project_dir / 'gradle' / 'wrapper' / 'gradle-wrapper.jar'
        
        # Vérifier si existe déjà et est valide
        if gradle_wrapper_jar.exists() and gradle_wrapper_jar.stat().st_size > 50000:
            logger.info(f"✓ gradle-wrapper.jar existe déjà: {gradle_wrapper_jar.stat().st_size} bytes")
            return True
        
        # URLs de fallback
        wrapper_urls = [
            "https://raw.githubusercontent.com/gradle/gradle/v8.2.0/gradle/wrapper/gradle-wrapper.jar",
            "https://raw.githubusercontent.com/gradle/gradle/v8.5.0/gradle/wrapper/gradle-wrapper.jar",
            "https://raw.githubusercontent.com/gradle/gradle/v8.1.1/gradle/wrapper/gradle-wrapper.jar",
        ]
        
        gradle_wrapper_jar.parent.mkdir(parents=True, exist_ok=True)
        
        for attempt in range(max_retries):
            for url in wrapper_urls:
                try:
                    logger.info(f"📥 Tentative {attempt + 1}/{max_retries} - Téléchargement depuis: {url}")
                    
                    # Télécharger avec timeout
                    req = urllib.request.Request(
                        url,
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    
                    with urllib.request.urlopen(req, timeout=30) as response:
                        data = response.read()
                        
                        # Vérifier la taille
                        if len(data) < 50000:
                            logger.warning(f"⚠️ Fichier trop petit: {len(data)} bytes")
                            continue
                        
                        # Écrire le fichier
                        with open(gradle_wrapper_jar, 'wb') as f:
                            f.write(data)
                        
                        # Vérifier que le fichier est valide
                        if gradle_wrapper_jar.exists() and gradle_wrapper_jar.stat().st_size > 50000:
                            logger.info(f"✅ gradle-wrapper.jar téléchargé: {gradle_wrapper_jar.stat().st_size} bytes")
                            return True
                        
                except Exception as e:
                    logger.warning(f"⚠️ Échec téléchargement depuis {url}: {e}")
                    continue
            
            # Attendre avant de réessayer
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Backoff exponentiel: 1s, 2s, 4s
        
        logger.error("❌ Impossible de télécharger gradle-wrapper.jar après toutes les tentatives")
        return False
    
    def _extract_compilation_errors(self, full_output: str) -> List[str]:
        """Extrait intelligemment les erreurs de compilation du log Gradle"""
        errors = []
        lines = full_output.split('\n')
        
        # Patterns d'erreurs Kotlin/Java
        error_patterns = [
            r'e:\s+file://.*\.kt:\d+:\d+:.*',  # Erreurs Kotlin
            r'.*\.kt:\d+:\d+:\s+error:.*',
            r'Unresolved reference:.*',
            r'Type mismatch:.*',
            r'Expecting.*but.*found',
            r'Cannot access.*',
            r'.*error:\s+cannot find symbol.*',
        ]
        
        compiled_patterns = [re.compile(p, re.IGNORECASE) for p in error_patterns]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Vérifier si la ligne correspond à un pattern d'erreur
            is_error = any(pattern.search(line) for pattern in compiled_patterns)
            
            if is_error:
                # Capturer le contexte (5 lignes avant, ligne actuelle, 10 lignes après)
                start = max(0, i - 5)
                end = min(len(lines), i + 11)
                context = '\n'.join(lines[start:end])
                errors.append(context)
                i = end  # Sauter les lignes déjà capturées
            else:
                i += 1
        
        # Si aucune erreur spécifique trouvée, chercher "BUILD FAILED"
        if not errors:
            for i, line in enumerate(lines):
                if 'BUILD FAILED' in line or 'FAILURE:' in line:
                    start = max(0, i - 10)
                    end = min(len(lines), i + 50)
                    context = '\n'.join(lines[start:end])
                    errors.append(context)
                    break
        
        return errors[:5]  # Limiter à 5 erreurs pour éviter surcharge
    
    def build_apk(self, project_zip: bytes, project_name: str, max_retries: int = 2) -> Tuple[bool, Optional[bytes], Optional[str]]:
        """
        Compile un projet Android depuis un ZIP et génère un APK fonctionnel
        
        Args:
            project_zip: Bytes du ZIP contenant le projet Android
            project_name: Nom du projet
            max_retries: Nombre maximum de tentatives
        
        Returns:
            Tuple (success, apk_bytes, error_msg)
        """
        last_error = None
        
        # Vérifier dépendances AVANT toute tentative
        deps_ok, deps_error = self.check_dependencies()
        if not deps_ok:
            error_msg = f"Dépendances manquantes: {deps_error}"
            logger.error(error_msg)
            return False, None, error_msg
        
        temp_dir = None
        project_dir = None
        
        try:
            # Créer répertoire temporaire (une seule fois pour toutes les tentatives)
            temp_dir = tempfile.mkdtemp(prefix=f'nativiweb_{project_name}_')
            logger.info(f"📁 Répertoire temporaire: {temp_dir}")
            
            # Extraire projet (une seule fois)
            with zipfile.ZipFile(io.BytesIO(project_zip), 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Trouver dossier projet
            extracted_dirs = [d for d in Path(temp_dir).iterdir() if d.is_dir()]
            if not extracted_dirs:
                raise Exception("Aucun dossier trouvé dans le ZIP")
            project_dir = extracted_dirs[0]
            
            logger.info(f"📂 Projet extrait: {project_dir.name}")
            
            # CRITIQUE: Télécharger gradle-wrapper.jar (une seule fois)
            if not self.download_gradle_wrapper_jar(project_dir):
                raise Exception("Impossible de télécharger gradle-wrapper.jar. Vérifiez votre connexion internet.")
            
            # Vérifier gradlew
            gradlew = project_dir / 'gradlew'
            gradlew_bat = project_dir / 'gradlew.bat'
            
            if not gradlew.exists() and not gradlew_bat.exists():
                raise Exception("Gradle wrapper (gradlew/gradlew.bat) non trouvé dans le projet")
            
            # Rendre gradlew exécutable (Unix)
            if gradlew.exists() and os.name != 'nt':
                os.chmod(gradlew, 0o755)
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        logger.info(f"🔄 Nouvelle tentative {attempt + 1}/{max_retries + 1}...")
                        time.sleep(3 * attempt)  # Attente progressive: 3s, 6s, 9s
                    
                    # Créer local.properties avec Android SDK si disponible
                    if self.android_home:
                        local_properties = project_dir / 'local.properties'
                        sdk_path = self.android_home.replace('\\', '\\\\') if os.name == 'nt' else self.android_home
                        with open(local_properties, 'w', encoding='utf-8') as f:
                            f.write(f'sdk.dir={sdk_path}\n')
                        logger.info(f"📝 local.properties créé")
                    
                    # Préparer environnement
                    env = os.environ.copy()
                    if self.java_home:
                        env['JAVA_HOME'] = self.java_home
                        java_bin = str(Path(self.java_home) / 'bin')
                        # Mettre Java en premier dans le PATH pour éviter les conflits
                        env['PATH'] = f"{java_bin}{os.pathsep}{env.get('PATH', '')}"
                    
                    # Nettoyer les builds précédents (en cas de retry)
                    build_dir = project_dir / 'app' / 'build'
                    if build_dir.exists() and attempt > 0:
                        logger.info("🧹 Nettoyage du build précédent...")
                        try:
                            shutil.rmtree(build_dir)
                        except Exception as e:
                            logger.warning(f"⚠️ Impossible de nettoyer: {e}")
                    
                    # Compiler APK
                    logger.info("🔨 Lancement de la compilation...")
                    
                    if os.name == 'nt':
                        gradle_cmd = str(gradlew_bat) if gradlew_bat.exists() else 'gradlew.bat'
                    else:
                        gradle_cmd = './gradlew'
                    
                    build_cmd = [
                        gradle_cmd,
                        'assembleDebug',
                        '--no-daemon',
                        '--stacktrace',
                        '--warning-mode', 'all',
                        '--no-build-cache',  # Éviter les problèmes de cache
                    ]
                    
                    logger.info(f"💻 Commande: {' '.join(build_cmd)}")
                    
                    # Fichier de log
                    log_file = project_dir / 'gradle_build.log'
                    
                    # Exécuter la compilation
                    start_time = time.time()
                    
                    with open(log_file, 'w', encoding='utf-8') as log_f:
                        process = subprocess.Popen(
                            build_cmd,
                            cwd=str(project_dir),
                            env=env,
                            stdout=log_f,
                            stderr=subprocess.STDOUT,
                            text=True,
                            shell=False
                        )
                        
                        # Attendre avec timeout de 20 minutes (augmenté)
                        try:
                            process.wait(timeout=1200)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            raise Exception("Timeout: compilation trop longue (20 minutes max)")
                    
                    build_time = time.time() - start_time
                    logger.info(f"⏱️ Temps de compilation: {build_time:.1f}s")
                    
                    # Lire le log complet
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        full_output = f.read()
                    
                    if process.returncode != 0:
                        # Extraire les erreurs
                        errors = self._extract_compilation_errors(full_output)
                        
                        if errors:
                            error_msg = "❌ Erreurs de compilation:\n\n" + "\n\n---\n\n".join(errors)
                        else:
                            # Fallback: dernières lignes
                            last_lines = '\n'.join(full_output.split('\n')[-100:])
                            error_msg = f"❌ Compilation échouée:\n{last_lines}"
                        
                        # Logger pour debug
                        logger.error(f"📋 Log complet ({len(full_output)} chars) sauvegardé dans: {log_file}")
                        
                        # Tenter une correction automatique si ce n'est pas la dernière tentative
                        if attempt < max_retries:
                            logger.info(f"🔧 Tentative de correction automatique avant retry {attempt + 2}/{max_retries + 1}")
                            if AndroidBuilderErrorHandler.attempt_auto_fix(project_dir, full_output, attempt + 1):
                                logger.info("✅ Corrections appliquées, nouvelle tentative...")
                                # Sauvegarder l'erreur mais continuer la boucle pour réessayer
                                last_error = error_msg
                                continue
                            else:
                                logger.warning("⚠️ Aucune correction automatique possible")
                        
                        # Si c'est la dernière tentative ou aucune correction possible, lever l'exception
                        last_error = error_msg
                        if attempt >= max_retries:
                            raise Exception(error_msg)
                        continue
                    
                    logger.info("✅ Compilation réussie!")
                    
                    # Trouver APK (plusieurs emplacements possibles)
                    apk_candidates = [
                        project_dir / 'app' / 'build' / 'outputs' / 'apk' / 'debug' / 'app-debug.apk',
                        project_dir / 'build' / 'outputs' / 'apk' / 'debug' / 'app-debug.apk',
                    ]
                    
                    apk_path = None
                    for candidate in apk_candidates:
                        if candidate.exists():
                            apk_path = candidate
                            break
                    
                    # Recherche récursive si non trouvé
                    if not apk_path:
                        for apk_file in project_dir.rglob('*.apk'):
                            if 'debug' in str(apk_file).lower() and 'unsigned' not in str(apk_file).lower():
                                apk_path = apk_file
                                break
                    
                    if not apk_path or not apk_path.exists():
                        raise Exception(f"APK non trouvé après compilation. Vérifiez {log_file}")
                    
                    logger.info(f"📱 APK trouvé: {apk_path.name}")
                    
                    # Vérifier taille APK (seuil réduit à 50KB pour plus de flexibilité)
                    apk_size = apk_path.stat().st_size
                    if apk_size < 50000:
                        raise Exception(f"APK trop petit ({apk_size} bytes), probablement corrompu")
                    
                    # Vérifier structure APK
                    try:
                        with zipfile.ZipFile(apk_path, 'r') as apk_zip:
                            files = apk_zip.namelist()
                            has_manifest = 'AndroidManifest.xml' in files
                            has_dex = any('classes' in f and '.dex' in f for f in files)
                            has_resources = any('resources.arsc' in f for f in files)
                            
                            if not has_manifest:
                                raise Exception("APK invalide: AndroidManifest.xml manquant")
                            if not has_dex:
                                raise Exception("APK invalide: fichiers .dex manquants")
                            
                            logger.info(f"✅ APK valide (manifest: ✓, dex: ✓, resources: {'✓' if has_resources else '✗'})")
                            
                    except zipfile.BadZipFile:
                        raise Exception("APK corrompu: structure ZIP invalide")
                    
                    # Lire APK
                    with open(apk_path, 'rb') as f:
                        apk_bytes = f.read()
                    
                    logger.info(f"🎉 APK généré avec succès!")
                    logger.info(f"📊 Taille: {len(apk_bytes) / 1024 / 1024:.2f} MB")
                    logger.info(f"📲 Prêt pour installation")
                    
                    return True, apk_bytes, None
                    
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"❌ Tentative {attempt + 1} échouée: {last_error[:200]}")
                    
                    # Ne pas réessayer pour certaines erreurs
                    no_retry_keywords = [
                        "Dépendances manquantes",
                        "gradle-wrapper.jar",
                        "Gradle wrapper",
                        "Aucun dossier trouvé",
                        "Java",
                        "Timeout",
                    ]
                    
                    if any(keyword in last_error for keyword in no_retry_keywords):
                        logger.error(f"Erreur non-récupérable, abandon")
                        break
                    
                    # Si c'est la dernière tentative, lever l'exception
                    if attempt >= max_retries:
                        raise
                    
                    # Sinon, continuer la boucle pour réessayer
                    continue
                    
        except Exception as e:
            last_error = str(e)
            logger.error(f"❌ Erreur lors de la compilation: {last_error[:200]}")
        
        finally:
            # Nettoyer à la fin de toutes les tentatives
            if temp_dir and Path(temp_dir).exists():
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.info(f"🧹 Nettoyage effectué")
                except Exception as e:
                    logger.warning(f"⚠️ Erreur nettoyage: {e}")
        
        # Échec final
        final_error = last_error or "Erreur inconnue lors de la compilation"
        logger.error(f"❌ Échec après {max_retries + 1} tentatives")
        return False, None, final_error