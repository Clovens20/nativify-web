"""
Système de build Android réel pour compiler les projets Android et générer des APKs fonctionnels
VERSION CORRIGÉE - Télécharge automatiquement gradle-wrapper.jar
"""
import os
import subprocess
import tempfile
import shutil
import zipfile
import io
import logging
import urllib.request
from pathlib import Path
from typing import Optional, Tuple
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


class AndroidBuilder:
    """Classe pour compiler des projets Android et générer des APKs fonctionnels"""
    
    def __init__(self):
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
            common_java_paths = [
                r"C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot",
                r"C:\Program Files\Java\jdk-17",
                r"C:\Program Files\Java\jdk-17.0.17.10-hotspot",
            ]
            adoptium_base = Path(r"C:\Program Files\Eclipse Adoptium")
            if adoptium_base.exists():
                for jdk_dir in adoptium_base.iterdir():
                    if jdk_dir.is_dir() and 'jdk' in jdk_dir.name.lower():
                        java_exe = jdk_dir / 'bin' / 'java.exe'
                        if java_exe.exists():
                            java_home = str(jdk_dir)
                            logger.info(f"🔍 Java trouvé automatiquement: {java_home}")
                            break
            
            if not java_home:
                for path_str in common_java_paths:
                    java_exe = Path(path_str) / 'bin' / 'java.exe'
                    if java_exe.exists():
                        java_home = path_str
                        logger.info(f"🔍 Java trouvé dans chemin commun: {java_home}")
                        break
        
        self.java_home = java_home
        
        # Auto-détection Android SDK
        android_home = (
            os.environ.get('ANDROID_HOME') or 
            os.environ.get('ANDROID_SDK_ROOT')
        )
        if not android_home:
            common_android_paths = [
                r"C:\Android",
                r"C:\Android\Sdk",
                Path.home() / "AppData" / "Local" / "Android" / "Sdk",
            ]
            for path in common_android_paths:
                android_path = Path(path) if isinstance(path, str) else path
                if android_path.exists():
                    android_home = str(android_path)
                    logger.info(f"🔍 Android SDK trouvé automatiquement: {android_home}")
                    break
        
        self.android_home = android_home
        
        logger.info(f"🔍 AndroidBuilder init - JAVA_HOME: {self.java_home}")
        logger.info(f"🔍 AndroidBuilder init - ANDROID_HOME: {self.android_home}")
        
        self.check_dependencies()
    
    def check_dependencies(self) -> Tuple[bool, Optional[str]]:
        """Vérifie que Java et Android SDK sont disponibles"""
        errors = []
        
        # Vérifier Java
        java_available = False
        if self.java_home:
            java_exe_name = 'java.exe' if os.name == 'nt' else 'java'
            java_exe = Path(self.java_home) / 'bin' / java_exe_name
            if java_exe.exists():
                try:
                    result = subprocess.run([str(java_exe), '-version'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        java_available = True
                        version_info = result.stderr.split('\n')[0] if result.stderr else 'Unknown'
                        logger.info(f"✅ Java trouvé: {version_info}")
                except Exception as e:
                    logger.warning(f"Erreur lors de la vérification de Java: {e}")
        else:
            try:
                result = subprocess.run(['java', '-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    java_available = True
                    self.java_home = shutil.which('java')
                    if self.java_home:
                        self.java_home = str(Path(self.java_home).parent.parent)
                    logger.info(f"Java trouvé dans PATH")
            except Exception:
                pass
        
        if not java_available:
            errors.append("Java JDK non trouvé. Installez Java JDK 17 ou supérieur.")
        
        # SDK optionnel
        if self.android_home and Path(self.android_home).exists():
            logger.info(f"✅ Android SDK trouvé: {self.android_home}")
        else:
            logger.info(f"ℹ️  Android SDK non trouvé (optionnel)")
        
        if errors:
            return False, "; ".join(errors)
        return True, None
    
    def download_gradle_wrapper_jar(self, project_dir: Path) -> bool:
        """Télécharge gradle-wrapper.jar si nécessaire"""
        gradle_wrapper_jar = project_dir / 'gradle' / 'wrapper' / 'gradle-wrapper.jar'
        
        if gradle_wrapper_jar.exists() and gradle_wrapper_jar.stat().st_size > 1000:
            logger.info(f"✓ gradle-wrapper.jar existe déjà: {gradle_wrapper_jar.stat().st_size} bytes")
            return True
        
        try:
            logger.info("📥 Téléchargement de gradle-wrapper.jar...")
            wrapper_url = "https://raw.githubusercontent.com/gradle/gradle/v8.2.0/gradle/wrapper/gradle-wrapper.jar"
            gradle_wrapper_jar.parent.mkdir(parents=True, exist_ok=True)
            
            urllib.request.urlretrieve(wrapper_url, str(gradle_wrapper_jar))
            
            if gradle_wrapper_jar.exists() and gradle_wrapper_jar.stat().st_size > 1000:
                logger.info(f"✅ gradle-wrapper.jar téléchargé avec succès: {gradle_wrapper_jar.stat().st_size} bytes")
                return True
            else:
                logger.error("❌ Le fichier téléchargé est trop petit ou invalide")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du téléchargement de gradle-wrapper.jar: {e}")
            return False
    
    def build_apk(self, project_zip: bytes, project_name: str) -> Tuple[bool, Optional[bytes], Optional[str]]:
        """Compile un projet Android depuis un ZIP et génère un APK fonctionnel"""
        temp_dir = None
        try:
            # Vérifier dépendances
            deps_ok, deps_error = self.check_dependencies()
            if not deps_ok:
                logger.warning(f"Dépendances manquantes: {deps_error}")
            
            # Créer répertoire temporaire
            temp_dir = tempfile.mkdtemp(prefix=f'nativiweb_build_{project_name}_')
            logger.info(f"📁 Répertoire temporaire: {temp_dir}")
            
            # Extraire projet
            with zipfile.ZipFile(io.BytesIO(project_zip), 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Trouver dossier projet
            extracted_dirs = [d for d in Path(temp_dir).iterdir() if d.is_dir()]
            if not extracted_dirs:
                raise Exception("Aucun dossier trouvé dans le ZIP")
            project_dir = extracted_dirs[0]
            
            logger.info(f"📂 Projet extrait: {project_dir}")
            
            # CRITIQUE: Télécharger gradle-wrapper.jar
            if not self.download_gradle_wrapper_jar(project_dir):
                raise Exception("Impossible de télécharger gradle-wrapper.jar. Le build ne peut pas continuer.")
            
            # Vérifier gradlew
            gradlew = project_dir / 'gradlew'
            gradlew_bat = project_dir / 'gradlew.bat'
            
            if not gradlew.exists() and not gradlew_bat.exists():
                raise Exception("Gradle wrapper (gradlew) non trouvé dans le projet")
            
            # Rendre gradlew exécutable
            if gradlew.exists():
                os.chmod(gradlew, 0o755)
            
            # Créer local.properties
            if self.android_home:
                local_properties = project_dir / 'local.properties'
                with open(local_properties, 'w') as f:
                    # Échapper les backslashes pour Windows
                    sdk_path = self.android_home.replace('\\', '\\\\')
                    f.write(f'sdk.dir={sdk_path}\n')
                logger.info(f"📝 local.properties créé")
            
            # Préparer environnement
            env = os.environ.copy()
            if self.java_home:
                env['JAVA_HOME'] = self.java_home
                java_bin = str(Path(self.java_home) / 'bin')
                env['PATH'] = f"{java_bin}{os.pathsep}{env.get('PATH', '')}"
            
            # Compiler APK
            logger.info("🔨 Compilation APK Debug...")
            
            if os.name == 'nt':
                gradle_cmd = [str(gradlew_bat)] if gradlew_bat.exists() else ['gradlew.bat']
            else:
                gradle_cmd = ['./gradlew']
            
            build_cmd = gradle_cmd + [
                'assembleDebug',
                '--no-daemon',
                '--stacktrace',
                '--warning-mode', 'all'
            ]
            
            logger.info(f"💻 Commande: {' '.join(build_cmd)}")
            
            # Sauvegarder CWD
            original_cwd = os.getcwd()
            
            try:
                os.chdir(str(project_dir))
                
                result = subprocess.run(
                    build_cmd,
                    cwd=str(project_dir),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=900,  # 15 minutes
                    shell=False
                )
            finally:
                try:
                    os.chdir(original_cwd)
                except Exception:
                    pass
            
            if result.returncode != 0:
                error_output = result.stderr or result.stdout or "Erreur inconnue"
                # Extraire erreurs pertinentes
                error_lines = []
                for line in error_output.split('\n'):
                    if 'error' in line.lower() or 'failed' in line.lower() or 'exception' in line.lower():
                        error_lines.append(line)
                
                relevant_error = '\n'.join(error_lines[-20:]) if error_lines else error_output[-2000:]
                error_msg = f"❌ Erreur de compilation:\n{relevant_error}"
                logger.error(error_msg)
                return False, None, error_msg
            
            logger.info("✅ Compilation réussie!")
            
            # Trouver APK
            apk_paths = [
                project_dir / 'app' / 'build' / 'outputs' / 'apk' / 'debug' / 'app-debug.apk',
                project_dir / 'build' / 'outputs' / 'apk' / 'debug' / 'app-debug.apk',
            ]
            
            apk_path = None
            for path in apk_paths:
                if path.exists():
                    apk_path = path
                    break
            
            if not apk_path:
                # Chercher récursivement
                for apk_file in project_dir.rglob('*.apk'):
                    if 'debug' in str(apk_file).lower():
                        apk_path = apk_file
                        break
            
            if not apk_path or not apk_path.exists():
                raise Exception(f"APK non trouvé après compilation dans {project_dir}")
            
            logger.info(f"📱 APK trouvé: {apk_path}")
            
            # Vérifier taille APK
            apk_size = apk_path.stat().st_size
            if apk_size < 100000:  # Moins de 100 KB = problème
                raise Exception(f"APK trop petit ({apk_size} bytes), probablement invalide")
            
            # Vérifier structure APK
            try:
                with zipfile.ZipFile(apk_path, 'r') as test_zip:
                    files = test_zip.namelist()
                    if 'AndroidManifest.xml' not in files:
                        raise Exception("APK invalide: AndroidManifest.xml manquant")
                    if not any('classes.dex' in f for f in files):
                        raise Exception("APK invalide: Aucun fichier .dex trouvé")
                    logger.info("✅ Structure APK validée")
            except zipfile.BadZipFile:
                raise Exception("APK corrompu: fichier ZIP invalide")
            
            # Lire APK
            with open(apk_path, 'rb') as f:
                apk_bytes = f.read()
            
            logger.info(f"🎉 APK généré avec succès!")
            logger.info(f"📊 Taille: {len(apk_bytes) / 1024 / 1024:.2f} MB")
            logger.info(f"📲 APK prêt à être installé")
            
            return True, apk_bytes, None
            
        except subprocess.TimeoutExpired:
            error_msg = "⏱️ Timeout: La compilation a pris trop de temps (15 minutes max)"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"❌ Erreur build: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, None, error_msg
        finally:
            # Nettoyer
            if temp_dir and Path(temp_dir).exists():
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"🧹 Nettoyage terminé")
                except Exception as e:
                    logger.warning(f"⚠️ Erreur nettoyage: {e}")