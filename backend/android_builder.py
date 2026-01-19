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
    
    def __init__(self, project_root: Path):
        """Initialise le builder Android"""
        
        # ÉTAPE 1: Auto-détecter Java AVANT tout
        logger.info("🔍 Détection de Java...")
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
        
        # ÉTAPE 2: Récupérer les variables
        self.project_root = project_root
        self.java_home = os.environ.get('JAVA_HOME', '')
        self.android_home = os.environ.get('ANDROID_HOME', 'C:\\Android')
        
        # ÉTAPE 3: Logs de debug
        logger.info(f"🔍 AndroidBuilder init - JAVA_HOME: {self.java_home}")
        logger.info(f"🔍 AndroidBuilder init - ANDROID_HOME: {self.android_home}")
        
        # ÉTAPE 4: CRITIQUE - Vérifier que JAVA_HOME existe
        if not self.java_home:
            logger.error("❌ JAVA_HOME est vide après auto-détection!")
            raise ValueError("JAVA_HOME non trouvé. Java JDK 17+ requis.")
        
        if not os.path.exists(self.java_home):
            logger.error(f"❌ JAVA_HOME pointe vers un chemin inexistant: {self.java_home}")
            raise ValueError(f"JAVA_HOME invalide: {self.java_home}")
        
        # Vérifier que java existe
        java_exe = os.path.join(self.java_home, 'bin', 'java.exe' if os.name == 'nt' else 'java')
        if not os.path.exists(java_exe):
            logger.error(f"❌ Exécutable Java non trouvé: {java_exe}")
            raise ValueError(f"Java non trouvé dans JAVA_HOME: {self.java_home}")
        
        logger.info(f"✅ Java trouvé: {java_exe}")
        
        # Reste de l'initialisation...
        self.android_dir = None
        self.build_config = None

    def _create_local_properties(self) -> None:
        """Crée le fichier local.properties avec le SDK Android si disponible"""
        if not self.android_home:
            return
        local_properties = self.android_dir / 'local.properties'
        sdk_path = self.android_home.replace('\\', '\\\\') if os.name == 'nt' else self.android_home
        local_properties.write_text(f'sdk.dir={sdk_path}\n', encoding='utf-8')
        logger.info("📝 local.properties créé")

    def _create_gradle_properties(self) -> None:
        """Crée le fichier gradle.properties avec les bonnes options JVM"""
        gradle_props_path = self.android_dir / "gradle.properties"
        gradle_props_content = """# Gradle Properties
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
org.gradle.parallel=true
org.gradle.caching=true
org.gradle.daemon=false

# Android Properties
android.useAndroidX=true
android.enableJetifier=true

# Kotlin
kotlin.code.style=official

# Build optimizations
android.defaults.buildfeatures.buildconfig=true
android.nonTransitiveRClass=false
android.nonFinalResIds=false
"""
        gradle_props_path.write_text(gradle_props_content, encoding='utf-8')
        logger.info("📝 gradle.properties créé")

    def _fix_gradle_wrapper_properties(self) -> None:
        """Corrige le fichier gradle-wrapper.properties pour éviter les erreurs JVM"""
        wrapper_props_path = self.android_dir / "gradle" / "wrapper" / "gradle-wrapper.properties"
        
        if not wrapper_props_path.exists():
            logger.warning(f"⚠️ gradle-wrapper.properties non trouvé: {wrapper_props_path}")
            return
        
        # Lire le contenu actuel
        content = wrapper_props_path.read_text(encoding='utf-8')
        
        # S'assurer que la distribution Gradle est correcte
        if 'distributionUrl' not in content:
            content += '\ndistributionUrl=https\\://services.gradle.org/distributions/gradle-8.2-all.zip\n'
        
        # Écrire le contenu corrigé
        wrapper_props_path.write_text(content, encoding='utf-8')
        logger.info("📝 gradle-wrapper.properties vérifié")

    def _create_gradle_wrapper_script(self) -> None:
        """Crée un wrapper Gradle sans options JVM problématiques"""
        gradlew_path = self.android_dir / "gradlew"
        
        if gradlew_path.exists():
            # Lire le script existant
            content = gradlew_path.read_text(encoding='utf-8', errors='ignore')
            
            # Remplacer les options JVM problématiques
            if 'DEFAULT_JVM_OPTS=' in content:
                content = content.replace(
                    'DEFAULT_JVM_OPTS="-Xmx64m" "-Xms64m"',
                    'DEFAULT_JVM_OPTS=""'
                )
                content = content.replace(
                    'DEFAULT_JVM_OPTS="-Xmx64m"',
                    'DEFAULT_JVM_OPTS=""'
                )
                
                gradlew_path.write_text(content, encoding='utf-8')
                logger.info("🔧 Script gradlew corrigé (options JVM retirées)")
            else:
                logger.info("ℹ️ Script gradlew ne contient pas DEFAULT_JVM_OPTS")
        else:
            logger.warning(f"⚠️ Script gradlew non trouvé: {gradlew_path}")

    def _compile_with_retry(self, max_retries: int = 4) -> Path:
        """Compile avec système de retry et auto-correction"""
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔄 Nouvelle tentative {attempt}/{max_retries}...")
                
                # Attendre avant retry (sauf première tentative)
                if attempt > 1:
                    time.sleep(min(attempt * 3, 10))
                
                # Créer les fichiers de configuration
                self._create_local_properties()
                self._create_gradle_properties()
                
                # NOUVEAU: Corriger les scripts Gradle
                self._fix_gradle_wrapper_properties()
                self._create_gradle_wrapper_script()
                
                # Permissions gradlew
                gradlew_path = self.android_dir / "gradlew"
                if gradlew_path.exists() and os.name != 'nt':
                    os.chmod(gradlew_path, 0o755)
                
                return self._run_gradle_build()
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"❌ Tentative {attempt} échouée: {last_error}")
        
                if attempt < max_retries:
                    logger.info(f"🔧 Tentative de correction automatique avant retry {attempt + 1}/{max_retries}")
                    try:
                        self._auto_fix_errors(last_error, attempt)
                    except Exception as fix_error:
                        logger.warning(f"⚠️ Correction automatique impossible: {fix_error}")
        
        raise Exception(f"❌ Échec après {max_retries} tentatives: {last_error}")

    def _run_gradle_build(self) -> Path:
        """Lance la compilation Gradle en contournant le wrapper problématique"""
        logger.info("🔨 Lancement de la compilation...")
        
        # Vérifier JAVA_HOME
        if not self.java_home or not os.path.exists(self.java_home):
            raise ValueError(f"JAVA_HOME invalide: {self.java_home}")
        
        # Trouver le JAR Gradle wrapper
        gradle_jar = self.android_dir / "gradle" / "wrapper" / "gradle-wrapper.jar"
        if not gradle_jar.exists():
            raise FileNotFoundError(f"gradle-wrapper.jar non trouvé: {gradle_jar}")
        
        # Construire la commande Java directement (bypass du script gradlew)
        java_exe = os.path.join(self.java_home, 'bin', 'java.exe' if os.name == 'nt' else 'java')
        
        cmd = [
            java_exe,
            '-Xmx2048m',
            '-Dfile.encoding=UTF-8',
            '-Dorg.gradle.daemon=false',
            '-classpath',
            str(gradle_jar),
            'org.gradle.wrapper.GradleWrapperMain',
            'assembleDebug',
            '--stacktrace',
            '--warning-mode', 'all',
        ]
        
        if os.name != 'nt':
            cmd.append('--no-build-cache')
        
        logger.info(f"💻 Commande: {' '.join(cmd)}")
        
        # Variables d'environnement
        env = os.environ.copy()
        env['JAVA_HOME'] = str(self.java_home)
        env['ANDROID_HOME'] = str(self.android_home)
        
        logger.info(f"🔧 JAVA_HOME utilisé: {env['JAVA_HOME']}")
        logger.info(f"🔧 ANDROID_HOME utilisé: {env['ANDROID_HOME']}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.android_dir),
                capture_output=True,
                text=True,
                timeout=600,
                env=env,
                check=False
            )
            
            build_time = time.time() - start_time
            logger.info(f"⏱️ Temps de compilation: {build_time:.1f}s")
            
            # Logs
            log_file = self.android_dir / "gradle_build.log"
            full_output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            log_file.write_text(full_output, encoding='utf-8')
            
            logger.info(f"📋 Log complet ({len(full_output)} chars) sauvegardé dans: {log_file}")
            
            if result.returncode != 0:
                error_msg = self._parse_gradle_error(result.stdout, result.stderr)
                raise Exception(f"❌ Compilation échouée:\n{error_msg}")
            
            # Vérifier APK
            apk_path = self.android_dir / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
            if not apk_path.exists():
                raise FileNotFoundError(f"APK non trouvé: {apk_path}")
            
            logger.info(f"✅ Compilation réussie: {apk_path}")
            return apk_path
            
        except subprocess.TimeoutExpired:
            raise Exception("⏱️ Timeout: La compilation a pris plus de 10 minutes")
    
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

    def _auto_fix_errors(self, error_message: str, attempt: int) -> None:
        """Tente de corriger automatiquement les erreurs Gradle connues"""
        if not hasattr(self, "android_dir"):
            return
        
        gradle_log = self.android_dir / "gradle_build.log"
        if not gradle_log.exists():
            return
        
        try:
            full_output = gradle_log.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            full_output = ""
        
        if full_output:
            AndroidBuilderErrorHandler.attempt_auto_fix(self.android_dir, full_output, attempt + 1)

    def _parse_gradle_error(self, stdout: str, stderr: str) -> str:
        """Parse les erreurs Gradle pour un message plus lisible"""
        full_output = f"{stdout}\n{stderr}"
        errors = self._extract_compilation_errors(full_output)
        if errors:
            return "\n\n---\n\n".join(errors)
        last_lines = '\n'.join(full_output.split('\n')[-100:])
        return last_lines or "Erreur de compilation inconnue"
    
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
            self.android_dir = project_dir
            
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
                    self._create_local_properties()
                    self._create_gradle_properties()
                    
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
                    
                    log_file = project_dir / 'gradle_build.log'
                    apk_path = self._run_gradle_build()
                    logger.info("✅ Compilation réussie!")
                    
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
                    
                    full_output = ""
                    log_file = project_dir / 'gradle_build.log'
                    if log_file.exists():
                        try:
                            full_output = log_file.read_text(encoding='utf-8', errors='ignore')
                        except Exception:
                            full_output = ""
                    
                    # Tenter une correction automatique si ce n'est pas la dernière tentative
                    if full_output and attempt < max_retries:
                        logger.info(f"🔧 Tentative de correction automatique avant retry {attempt + 2}/{max_retries + 1}")
                        if AndroidBuilderErrorHandler.attempt_auto_fix(project_dir, full_output, attempt + 1):
                            logger.info("✅ Corrections appliquées, nouvelle tentative...")
                            continue
                        else:
                            logger.warning("⚠️ Aucune correction automatique possible")
                    
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