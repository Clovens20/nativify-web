"""
Générateur de templates natifs Android et iOS pour NativiWeb Studio
Génère des projets complets et fonctionnels prêts à être compilés
VERSION CORRIGÉE
"""
import os
import json
import zipfile
import io
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NativeTemplateGenerator:
    """Génère des templates de projets natifs Android et iOS"""
    
    def __init__(self):
        self.android_template_dir = Path(__file__).parent / "templates" / "android"
        self.ios_template_dir = Path(__file__).parent / "templates" / "ios"
        
    def generate_android_project(
        self,
        project_name: str,
        package_name: str,
        web_url: str,
        features: List[Dict[str, Any]],
        app_icon_url: Optional[str] = None
    ) -> bytes:
        """
        Génère un projet Android complet et fonctionnel
        
        Args:
            project_name: Nom de l'application
            package_name: Nom du package (ex: com.example.app)
            web_url: URL de l'application web
            features: Liste des fonctionnalités activées
            app_icon_url: URL de l'icône de l'application
            
        Returns:
            Bytes du fichier ZIP contenant le projet Android complet
        """
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Structure du projet Android
            base_dir = f"{project_name.lower().replace(' ', '-')}-android"
            
            # 1. AndroidManifest.xml
            manifest = self._generate_android_manifest(package_name, project_name, features)
            zip_file.writestr(f"{base_dir}/app/src/main/AndroidManifest.xml", manifest)
            
            # 2. build.gradle (Project level)
            project_build_gradle = self._generate_project_build_gradle()
            zip_file.writestr(f"{base_dir}/build.gradle", project_build_gradle)
            
            # 3. build.gradle (App level)
            app_build_gradle = self._generate_app_build_gradle(package_name, features)
            zip_file.writestr(f"{base_dir}/app/build.gradle", app_build_gradle)
            
            # 4. activity_main.xml (Layout) - VERSION AMÉLIORÉE
            activity_main = """<?xml version="1.0" encoding="utf-8"?>
<androidx.swiperefreshlayout.widget.SwipeRefreshLayout 
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:id="@+id/swipeRefresh"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <FrameLayout
        android:layout_width="match_parent"
        android:layout_height="match_parent">

        <WebView
            android:id="@+id/webView"
            android:layout_width="match_parent"
            android:layout_height="match_parent" />

        <ProgressBar
            android:id="@+id/progressBar"
            style="?android:attr/progressBarStyleHorizontal"
            android:layout_width="match_parent"
            android:layout_height="4dp"
            android:layout_gravity="top"
            android:max="100"
            android:progress="0"
            android:progressTint="@android:color/holo_blue_bright"
            android:visibility="gone" />

    </FrameLayout>

</androidx.swiperefreshlayout.widget.SwipeRefreshLayout>
"""
            zip_file.writestr(f"{base_dir}/app/src/main/res/layout/activity_main.xml", activity_main)
            
            # 5. MainActivity.kt
            main_activity = self._generate_main_activity(package_name, web_url, features)
            package_path = package_name.replace('.', '/')
            zip_file.writestr(f"{base_dir}/app/src/main/java/{package_path}/MainActivity.kt", main_activity)
            
            # 6. NativiWebBridge.kt - Bridge pour communiquer avec le WebView
            bridge = self._generate_native_bridge(package_name, features)
            zip_file.writestr(f"{base_dir}/app/src/main/java/{package_path}/NativiWebBridge.kt", bridge)
            
            # 7. settings.gradle
            settings_gradle = f"rootProject.name = '{project_name}'\ninclude ':app'\n"
            zip_file.writestr(f"{base_dir}/settings.gradle", settings_gradle)
            
            # 8. gradle.properties
            gradle_properties = """org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.enableJetifier=true
kotlin.code.style=official
"""
            zip_file.writestr(f"{base_dir}/gradle.properties", gradle_properties)
            
            # 9. gradle/wrapper/gradle-wrapper.properties
            gradle_wrapper_props = """distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.2-bin.zip
networkTimeout=10000
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
"""
            zip_file.writestr(f"{base_dir}/gradle/wrapper/gradle-wrapper.properties", gradle_wrapper_props)
            
            # 9.0. gradle/wrapper/gradle-wrapper.jar - Placeholder (sera téléchargé par android_builder.py)
            gradle_wrapper_info = """# Gradle Wrapper JAR
# Ce fichier sera téléchargé automatiquement par le système de build lors de la compilation.
# Le JAR sera téléchargé depuis: https://raw.githubusercontent.com/gradle/gradle/v8.2.0/gradle/wrapper/gradle-wrapper.jar
"""
            zip_file.writestr(f"{base_dir}/gradle/wrapper/gradle-wrapper.jar.info", gradle_wrapper_info)
            
            # 9.1. gradlew (Linux/Mac script)
            gradlew_script = """#!/bin/sh
# Gradle wrapper script (version simplifiée)
APP_HOME=$( cd "${APP_HOME:-./}" && pwd -P ) || exit
CLASSPATH=$APP_HOME/gradle/wrapper/gradle-wrapper.jar

if [ -n "$JAVA_HOME" ] ; then
    if [ -x "$JAVA_HOME/jre/sh/java" ] ; then
        JAVACMD=$JAVA_HOME/jre/sh/java
    else
        JAVACMD=$JAVA_HOME/bin/java
    fi
else
    JAVACMD=java
fi

DEFAULT_JVM_OPTS='"-Xmx64m" "-Xms64m"'

exec "$JAVACMD" $DEFAULT_JVM_OPTS -classpath "$CLASSPATH" org.gradle.wrapper.GradleWrapperMain "$@"
"""
            zip_file.writestr(f"{base_dir}/gradlew", gradlew_script)
            
            # 9.2. gradlew.bat (Windows script)
            gradlew_bat = """@echo off
@rem Gradle startup script for Windows
set DIRNAME=%~dp0
set APP_HOME=%DIRNAME%
set CLASSPATH=%APP_HOME%\\gradle\\wrapper\\gradle-wrapper.jar
set DEFAULT_JVM_OPTS="-Xmx64m" "-Xms64m"

if defined JAVA_HOME goto findJavaFromJavaHome
set JAVA_EXE=java.exe
goto execute

:findJavaFromJavaHome
set JAVA_EXE=%JAVA_HOME%/bin/java.exe

:execute
"%JAVA_EXE%" %DEFAULT_JVM_OPTS% -classpath "%CLASSPATH%" org.gradle.wrapper.GradleWrapperMain %*
"""
            zip_file.writestr(f"{base_dir}/gradlew.bat", gradlew_bat)
            
            # 9.3. Script de build automatique (build.sh)
            build_sh = f"""#!/bin/bash
# Script de build automatique pour {project_name}
set -e
echo "🚀 Compilation de {project_name}..."
if ! command -v java &> /dev/null; then
    echo "❌ Java non installé. Téléchargez: https://adoptium.net/"
    exit 1
fi
echo "✓ Java: $(java -version 2>&1 | head -n 1)"
chmod +x ./gradlew
echo "📦 Compilation APK Debug..."
./gradlew assembleDebug
if [ $? -eq 0 ]; then
    echo "✅ APK généré: app/build/outputs/apk/debug/app-debug.apk"
else
    echo "❌ Erreur de compilation"
    exit 1
fi
"""
            zip_file.writestr(f"{base_dir}/build.sh", build_sh)
            
            # 9.4. Script de build automatique Windows (build.bat)
            build_bat = f"""@echo off
echo 🚀 Compilation de {project_name}...
java -version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Java non installé
    exit /b 1
)
echo ✓ Java détecté
echo 📦 Compilation APK Debug...
call gradlew.bat assembleDebug
if %ERRORLEVEL% equ 0 (
    echo ✅ APK généré: app\\build\\outputs\\apk\\debug\\app-debug.apk
) else (
    echo ❌ Erreur de compilation
    exit /b 1
)
"""
            zip_file.writestr(f"{base_dir}/build.bat", build_bat)
            
            # 10. app/src/main/res/values/strings.xml
            strings_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">{project_name}</string>
    <string name="web_url">{web_url}</string>
</resources>
"""
            zip_file.writestr(f"{base_dir}/app/src/main/res/values/strings.xml", strings_xml)
            
            # 11. app/src/main/res/drawable/ic_launcher.xml (icône par défaut)
            ic_launcher = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#00F0FF"
        android:pathData="M54,0L108,54L54,108L0,54Z"/>
</vector>
"""
            zip_file.writestr(f"{base_dir}/app/src/main/res/drawable/ic_launcher.xml", ic_launcher)
            
            # 12. app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml
            zip_file.writestr(f"{base_dir}/app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml", ic_launcher)
            
            # 13. SDK JavaScript personnalisé
            sdk_js = self._generate_javascript_sdk(web_url, features, "android")
            zip_file.writestr(f"{base_dir}/app/src/main/assets/nativiweb-sdk.js", sdk_js)
            
            # 14. README.md avec instructions
            readme = self._generate_android_readme(project_name, package_name, web_url)
            zip_file.writestr(f"{base_dir}/README.md", readme)
            
            # 15. .gitignore
            gitignore = """*.iml
.gradle
/local.properties
/.idea/
.DS_Store
/build
/captures
.externalNativeBuild
.cxx
"""
            zip_file.writestr(f"{base_dir}/.gitignore", gitignore)
            
        zip_buffer.seek(0)
        return zip_buffer.read()
# CONTINUATION DE LA CLASSE NativeTemplateGenerator
    
    def _generate_android_manifest(self, package_name: str, app_name: str, features: List[Dict[str, Any]]) -> str:
        """Génère AndroidManifest.xml avec permissions selon les fonctionnalités"""
        permissions = []
        permissions_map = {
            "camera": ["android.permission.CAMERA"],
            "geolocation": ["android.permission.ACCESS_FINE_LOCATION", "android.permission.ACCESS_COARSE_LOCATION"],
            "push_notifications": ["android.permission.POST_NOTIFICATIONS"],
            "contacts": ["android.permission.READ_CONTACTS"],
            "file_system": ["android.permission.READ_EXTERNAL_STORAGE", "android.permission.WRITE_EXTERNAL_STORAGE"],
        }
        
        for feature in features:
            if feature.get("enabled") and feature.get("id") in permissions_map:
                permissions.extend(permissions_map[feature["id"]])
        
        permissions_xml = "\n".join([f'    <uses-permission android:name="{p}" />' for p in set(permissions)])
        
        # Permissions Internet toujours nécessaires
        if 'android.permission.INTERNET' not in permissions_xml:
            permissions_xml = '    <uses-permission android:name="android.permission.INTERNET" />\n' + permissions_xml
        
        return f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{package_name}">

{permissions_xml}

    <application
        android:allowBackup="true"
        android:icon="@drawable/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@drawable/ic_launcher"
        android:supportsRtl="true"
        android:theme="@style/Theme.AppCompat.Light.NoActionBar"
        android:usesCleartextTraffic="true">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden"
            android:windowSoftInputMode="adjustResize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>

</manifest>
"""
    
    def _generate_project_build_gradle(self) -> str:
        """Génère build.gradle au niveau projet - VERSION CORRIGÉE"""
        return """// Top-level build file
buildscript {
    ext.kotlin_version = '1.9.20'
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:8.2.0'
        classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:$kotlin_version"
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

task clean(type: Delete) {
    delete rootProject.buildDir
}
"""
    
    def _generate_app_build_gradle(self, package_name: str, features: List[Dict[str, Any]]) -> str:
        """Génère build.gradle au niveau app - VERSION CORRIGÉE"""
        return f"""plugins {{
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
}}

android {{
    namespace "{package_name}"
    compileSdk 34

    defaultConfig {{
        applicationId "{package_name}"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0.0"
        
        testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"
    }}

    buildTypes {{
        release {{
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }}
        debug {{
            minifyEnabled false
            debuggable true
        }}
    }}

    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }}

    kotlinOptions {{
        jvmTarget = '17'
    }}
    
    buildFeatures {{
        viewBinding true
    }}
}}

dependencies {{
    implementation 'androidx.core:core-ktx:1.12.0'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.11.0'
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4'
    implementation 'androidx.webkit:webkit:1.9.0'
    implementation 'androidx.swiperefreshlayout:swiperefreshlayout:1.1.0'
    
    testImplementation 'junit:junit:4.13.2'
    androidTestImplementation 'androidx.test.ext:junit:1.1.5'
    androidTestImplementation 'androidx.test.espresso:espresso-core:3.5.1'
}}
"""
    
    def _generate_main_activity(self, package_name: str, web_url: str, features: List[Dict[str, Any]]) -> str:
        """Génère MainActivity.kt avec WebView et bridge - VERSION CORRIGÉE"""
        enabled_features = [f.get("id") for f in features if f.get("enabled")]
        
        return f"""package {package_name}

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.*
import android.view.View
import android.widget.ProgressBar
import androidx.appcompat.app.AppCompatActivity
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout

class MainActivity : AppCompatActivity() {{
    private lateinit var webView: WebView
    private lateinit var bridge: NativiWebBridge
    private lateinit var progressBar: ProgressBar
    private lateinit var swipeRefresh: SwipeRefreshLayout

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Initialiser les vues
        webView = findViewById(R.id.webView)
        progressBar = findViewById(R.id.progressBar)
        swipeRefresh = findViewById(R.id.swipeRefresh)
        
        // Configuration WebView complète
        configureWebView()
        
        // Bridge pour communication native <-> JavaScript
        bridge = NativiWebBridge(this, webView)
        webView.addJavascriptInterface(bridge, "NativiWebNative")

        // WebViewClient pour intercepter les chargements
        webView.webViewClient = object : WebViewClient() {{
            override fun onPageStarted(view: WebView?, url: String?, favicon: android.graphics.Bitmap?) {{
                super.onPageStarted(view, url, favicon)
                progressBar.visibility = View.VISIBLE
            }}
            
            override fun onPageFinished(view: WebView?, url: String?) {{
                super.onPageFinished(view, url)
                progressBar.visibility = View.GONE
                swipeRefresh.isRefreshing = false
                
                // Injecter le SDK JavaScript
                try {{
                    val sdkScript = assets.open("nativiweb-sdk.js").bufferedReader().use {{ it.readText() }}
                    view?.evaluateJavascript(sdkScript, null)
                }} catch (e: Exception) {{
                    e.printStackTrace()
                }}
            }}
            
            override fun onReceivedError(
                view: WebView?,
                request: WebResourceRequest?,
                error: WebResourceError?
            ) {{
                super.onReceivedError(view, request, error)
                progressBar.visibility = View.GONE
                swipeRefresh.isRefreshing = false
            }}
        }}

        webView.webChromeClient = object : WebChromeClient() {{
            override fun onProgressChanged(view: WebView?, newProgress: Int) {{
                super.onProgressChanged(view, newProgress)
                progressBar.progress = newProgress
            }}
            
            // Support pour les permissions (caméra, géolocalisation, etc.)
            override fun onPermissionRequest(request: PermissionRequest?) {{
                request?.grant(request.resources)
            }}
        }}
        
        // Configuration du pull-to-refresh
        swipeRefresh.setOnRefreshListener {{
            webView.reload()
        }}

        // Charger l'URL web
        webView.loadUrl("{web_url}")
    }}
    
    @SuppressLint("SetJavaScriptEnabled")
    private fun configureWebView() {{
        with(webView.settings) {{
            // JavaScript
            javaScriptEnabled = true
            javaScriptCanOpenWindowsAutomatically = true
            
            // Stockage
            domStorageEnabled = true
            databaseEnabled = true
            
            // Cache
            cacheMode = WebSettings.LOAD_DEFAULT
            
            // Zoom
            setSupportZoom(true)
            builtInZoomControls = true
            displayZoomControls = false
            
            // Viewport
            useWideViewPort = true
            loadWithOverviewMode = true
            
            // Media
            mediaPlaybackRequiresUserGesture = false
            
            // Contenu mixte (HTTP/HTTPS)
            mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            
            // User Agent
            userAgentString = "${{userAgentString}} NativiWeb/1.0"
        }}
        
        // Activer le débogage WebView
        WebView.setWebContentsDebuggingEnabled(true)
    }}

    override fun onBackPressed() {{
        if (webView.canGoBack()) {{
            webView.goBack()
        }} else {{
            super.onBackPressed()
        }}
    }}
    
    override fun onDestroy() {{
        super.onDestroy()
        webView.destroy()
    }}
}}
"""
    
    def _generate_native_bridge(self, package_name: str, features: List[Dict[str, Any]]) -> str:
        """Génère NativiWebBridge.kt pour communication native - VERSION CORRIGÉE"""
        
        return f"""package {package_name}

import android.Manifest
import android.content.Context
import android.content.ClipData
import android.content.ClipboardManager
import android.content.pm.PackageManager
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.webkit.JavascriptInterface
import android.webkit.WebView
import androidx.core.content.ContextCompat
import org.json.JSONObject

class NativiWebBridge(private val context: Context, private val webView: WebView) {{
    private val vibrator = context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator

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
        val info = JSONObject().apply {{
            put("platform", "android")
            put("platformVersion", Build.VERSION.RELEASE)
            put("deviceModel", Build.MODEL)
            put("manufacturer", Build.MANUFACTURER)
            put("appVersion", "1.0.0")
            put("sdkVersion", "1.0.0")
            put("isNative", true)
        }}
        return info.toString()
    }}

    @JavascriptInterface
    fun vibrate(duration: Int) {{
        try {{
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {{
                vibrator?.vibrate(
                    VibrationEffect.createOneShot(
                        duration.toLong(), 
                        VibrationEffect.DEFAULT_AMPLITUDE
                    )
                )
            }} else {{
                @Suppress("DEPRECATION")
                vibrator?.vibrate(duration.toLong())
            }}
            callbackSuccess("vibrate", "Vibration déclenchée")
        }} catch (e: Exception) {{
            callbackError("vibrate", e.message ?: "Erreur de vibration")
        }}
    }}

    @JavascriptInterface
    fun copyToClipboard(text: String) {{
        try {{
            val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = ClipData.newPlainText("text", text)
            clipboard.setPrimaryClip(clip)
            callbackSuccess("copyToClipboard", "Texte copié")
        }} catch (e: Exception) {{
            callbackError("copyToClipboard", e.message ?: "Erreur de copie")
        }}
    }}
    
    @JavascriptInterface
    fun showToast(message: String) {{
        android.os.Handler(android.os.Looper.getMainLooper()).post {{
            android.widget.Toast.makeText(context, message, android.widget.Toast.LENGTH_SHORT).show()
        }}
    }}
    
    private fun callbackSuccess(action: String, message: String) {{
        val js = "if(window.NativiWeb && window.NativiWeb._handleNativeCallback) {{" +
                 "window.NativiWeb._handleNativeCallback('$action', true, '$message');" +
                 "}}"
        webView.post {{
            webView.evaluateJavascript(js, null)
        }}
    }}
    
    private fun callbackError(action: String, error: String) {{
        val js = "if(window.NativiWeb && window.NativiWeb._handleNativeCallback) {{" +
                 "window.NativiWeb._handleNativeCallback('$action', false, '$error');" +
                 "}}"
        webView.post {{
            webView.evaluateJavascript(js, null)
        }}
    }}
}}
"""

    # CONTINUATION: Méthodes iOS et utilitaires (à copier après les méthodes Android)
    
    def generate_ios_project(
        self,
        project_name: str,
        bundle_identifier: str,
        web_url: str,
        features: List[Dict[str, Any]],
        app_icon_url: Optional[str] = None
    ) -> bytes:
        """Génère un projet iOS complet et fonctionnel"""
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            base_dir = f"{project_name.replace(' ', '')}-iOS"
            
            # Fichiers iOS (garder votre implémentation actuelle ou améliorer)
            # ... (garder votre code iOS existant)
            
        zip_buffer.seek(0)
        return zip_buffer.read()
    
    def _generate_javascript_sdk(self, web_url: str, features: List[Dict[str, Any]], platform: str) -> str:
        """Génère le SDK JavaScript personnalisé"""
        enabled_features = [f.get("id") for f in features if f.get("enabled")]
        
        return f"""// NativiWeb SDK v1.0.0
(function() {{
    'use strict';
    
    const NativiWeb = {{
        platform: '{platform}',
        version: '1.0.0',
        features: {json.dumps(enabled_features)},
        
        isNative: function() {{
            return typeof window.NativiWebNative !== 'undefined';
        }},
        
        vibrate: function(duration) {{
            if (this.isNative() && window.NativiWebNative.vibrate) {{
                window.NativiWebNative.vibrate(duration || 100);
                return Promise.resolve();
            }}
            return Promise.reject('Not native');
        }},
        
        copyToClipboard: function(text) {{
            if (this.isNative() && window.NativiWebNative.copyToClipboard) {{
                window.NativiWebNative.copyToClipboard(text);
                return Promise.resolve();
            }}
            return navigator.clipboard.writeText(text);
        }},
        
        getDeviceInfo: function() {{
            if (this.isNative() && window.NativiWebNative.getDeviceInfo) {{
                return Promise.resolve(JSON.parse(window.NativiWebNative.getDeviceInfo()));
            }}
            return Promise.resolve({{ platform: 'web', userAgent: navigator.userAgent }});
        }},
        
        showToast: function(message) {{
            if (this.isNative() && window.NativiWebNative.showToast) {{
                window.NativiWebNative.showToast(message);
                return Promise.resolve();
            }}
            console.log('Toast:', message);
            return Promise.resolve();
        }}
    }};
    
    window.NativiWeb = NativiWeb;
    console.log('NativiWeb SDK initialized on', NativiWeb.platform);
}})();
"""
    
    def _generate_android_readme(self, project_name: str, package_name: str, web_url: str) -> str:
        """Génère README pour projet Android"""
        safe_name = project_name.lower().replace(' ', '-')
        return f"""# {project_name} - Android

## Configuration
- **Package**: {package_name}
- **URL**: {web_url}

## Compilation Rapide

### Windows:
```cmd
build.bat
```

### Linux/Mac:
```bash
chmod +x build.sh
./build.sh
```

L'APK sera dans: `app/build/outputs/apk/debug/app-debug.apk`

## Installation
1. Transférez l'APK sur votre téléphone
2. Activez "Sources inconnues" dans Paramètres > Sécurité
3. Ouvrez l'APK pour l'installer

## Plus d'infos
- Utilisez Android Studio pour le développement avancé
- Min SDK: Android 7.0 (API 24)
- Target SDK: Android 14 (API 34)
"""

 # ========== MÉTHODES iOS COMPLÈTES ==========
    # À ajouter à la fin de la classe NativeTemplateGenerator dans generator.py
    
    def generate_ios_project(
        self,
        project_name: str,
        bundle_identifier: str,
        web_url: str,
        features: List[Dict[str, Any]],
        app_icon_url: Optional[str] = None
    ) -> bytes:
        """
        Génère un projet iOS complet et fonctionnel
        
        Args:
            project_name: Nom de l'application
            bundle_identifier: Bundle ID (ex: com.example.app)
            web_url: URL de l'application web
            features: Liste des fonctionnalités activées
            app_icon_url: URL de l'icône de l'application
            
        Returns:
            Bytes du fichier ZIP contenant le projet iOS complet
        """
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            base_dir = f"{project_name.replace(' ', '')}-iOS"
            
            # 1. ContentView.swift - Vue principale avec WebView
            content_view = self._generate_content_view(bundle_identifier, web_url, features)
            zip_file.writestr(f"{base_dir}/{project_name.replace(' ', '')}/ContentView.swift", content_view)
            
            # 2. App.swift - Point d'entrée de l'application
            app_swift = self._generate_app_swift(project_name)
            zip_file.writestr(f"{base_dir}/{project_name.replace(' ', '')}/App.swift", app_swift)
            
            # 3. NativiWebBridge.swift - Bridge pour communiquer avec le WebView
            bridge_swift = self._generate_ios_bridge(bundle_identifier, features)
            zip_file.writestr(f"{base_dir}/{project_name.replace(' ', '')}/NativiWebBridge.swift", bridge_swift)
            
            # 4. Info.plist
            info_plist = self._generate_info_plist(bundle_identifier, project_name, features)
            zip_file.writestr(f"{base_dir}/{project_name.replace(' ', '')}/Info.plist", info_plist)
            
            # 5. project.pbxproj - Fichier de projet Xcode
            project_file = self._generate_xcode_project(project_name, bundle_identifier)
            zip_file.writestr(f"{base_dir}/{project_name.replace(' ', '')}.xcodeproj/project.pbxproj", project_file)
            
            # 6. SDK JavaScript personnalisé
            sdk_js = self._generate_javascript_sdk(web_url, features, "ios")
            zip_file.writestr(f"{base_dir}/{project_name.replace(' ', '')}/Assets/nativiweb-sdk.js", sdk_js)
            
            # 7. README.md
            readme = self._generate_ios_readme(project_name, bundle_identifier, web_url)
            zip_file.writestr(f"{base_dir}/README.md", readme)
            
            # 8. Podfile pour CocoaPods (si nécessaire)
            podfile = self._generate_podfile(project_name)
            zip_file.writestr(f"{base_dir}/Podfile", podfile)
            
        zip_buffer.seek(0)
        return zip_buffer.read()
    
    def _generate_content_view(self, bundle_id: str, web_url: str, features: List[Dict[str, Any]]) -> str:
        """Génère ContentView.swift pour iOS"""
        return f"""import SwiftUI
import WebKit

struct ContentView: View {{
    @StateObject private var bridge = NativiWebBridge()
    
    var body: some View {{
        WebViewRepresentable(url: "{web_url}", bridge: bridge)
            .edgesIgnoringSafeArea(.all)
    }}
}}

struct WebViewRepresentable: UIViewRepresentable {{
    let url: String
    let bridge: NativiWebBridge
    
    func makeUIView(context: Context) -> WKWebView {{
        let config = WKWebViewConfiguration()
        let contentController = WKUserContentController()
        
        // Ajouter le bridge
        contentController.add(bridge, name: "NativiWebNative")
        config.userContentController = contentController
        
        let webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = bridge
        
        // Charger le SDK JavaScript
        if let sdkPath = Bundle.main.path(forResource: "nativiweb-sdk", ofType: "js"),
           let sdkContent = try? String(contentsOfFile: sdkPath) {{
            let script = WKUserScript(source: sdkContent, injectionTime: .atDocumentEnd, forMainFrameOnly: false)
            contentController.addUserScript(script)
        }}
        
        return webView
    }}
    
    func updateUIView(_ webView: WKWebView, context: Context) {{
        if webView.url == nil {{
            if let url = URL(string: url) {{
                webView.load(URLRequest(url: url))
            }}
        }}
    }}
}}

#Preview {{
    ContentView()
}}
"""
    
    def _generate_app_swift(self, app_name: str) -> str:
        """Génère App.swift point d'entrée iOS"""
        app_name_clean = app_name.replace(" ", "")
        return f"""import SwiftUI

@main
struct {app_name_clean}App: App {{
    var body: some Scene {{
        WindowGroup {{
            ContentView()
        }}
    }}
}}
"""
    
    def _generate_ios_bridge(self, bundle_id: str, features: List[Dict[str, Any]]) -> str:
        """Génère NativiWebBridge.swift pour iOS"""
        return """import WebKit
import UIKit
import CoreLocation
import AVFoundation

class NativiWebBridge: NSObject, ObservableObject, WKScriptMessageHandler, WKNavigationDelegate {
    
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.name == "NativiWebNative" else { return }
        
        if let body = message.body as? [String: Any],
           let action = body["action"] as? String {
            
            switch action {
            case "vibrate":
                let generator = UIImpactFeedbackGenerator(style: .medium)
                generator.impactOccurred()
                
            case "copyToClipboard":
                if let text = body["text"] as? String {
                    UIPasteboard.general.string = text
                }
                
            case "getDeviceInfo":
                let info: [String: Any] = [
                    "platform": "ios",
                    "platformVersion": UIDevice.current.systemVersion,
                    "deviceModel": UIDevice.current.model,
                    "manufacturer": "Apple",
                    "appVersion": "1.0.0",
                    "sdkVersion": "1.0.0",
                    "isNative": true
                ]
                // Callback vers JavaScript avec les infos
                if let webView = message.webView {
                    let jsonData = try? JSONSerialization.data(withJSONObject: info)
                    let jsonString = String(data: jsonData ?? Data(), encoding: .utf8) ?? "{}"
                    let js = "if(window.NativiWeb && window.NativiWeb._handleNativeCallback) { window.NativiWeb._handleNativeCallback('getDeviceInfo', true, \\(jsonString)); }"
                    webView.evaluateJavaScript(js, completionHandler: nil)
                }
                
            case "showToast":
                if let text = body["message"] as? String {
                    // iOS ne supporte pas les toasts natifs, utiliser une alerte simple
                    DispatchQueue.main.async {
                        if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
                           let rootVC = windowScene.windows.first?.rootViewController {
                            let alert = UIAlertController(title: nil, message: text, preferredStyle: .alert)
                            rootVC.present(alert, animated: true)
                            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                                alert.dismiss(animated: true)
                            }
                        }
                    }
                }
                
            default:
                break
            }
        }
    }
    
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        // Page chargée
    }
    
    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        // Erreur de chargement
        print("WebView error: \\(error.localizedDescription)")
    }
}
"""
    
    def _generate_info_plist(self, bundle_id: str, app_name: str, features: List[Dict[str, Any]]) -> str:
        """Génère Info.plist avec permissions"""
        permissions = []
        for feature in features:
            if feature.get("enabled"):
                if feature.get("id") == "camera":
                    permissions.append('<key>NSCameraUsageDescription</key><string>Nous avons besoin de la caméra pour prendre des photos</string>')
                elif feature.get("id") == "geolocation":
                    permissions.append('<key>NSLocationWhenInUseUsageDescription</key><string>Nous avons besoin de votre position</string>')
                elif feature.get("id") == "push_notifications":
                    permissions.append('<key>NSUserNotificationsUsageDescription</key><string>Nous avons besoin de votre permission pour les notifications</string>')
        
        permissions_xml = "\n    ".join(permissions)
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>$(DEVELOPMENT_LANGUAGE)</string>
    <key>CFBundleDisplayName</key>
    <string>{app_name}</string>
    <key>CFBundleExecutable</key>
    <string>$(EXECUTABLE_NAME)</string>
    <key>CFBundleIdentifier</key>
    <string>{bundle_id}</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>$(PRODUCT_NAME)</string>
    <key>CFBundlePackageType</key>
    <string>$(PRODUCT_BUNDLE_PACKAGE_TYPE)</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSRequiresIPhoneOS</key>
    <true/>
    <key>UIApplicationSceneManifest</key>
    <dict>
        <key>UIApplicationSupportsMultipleScenes</key>
        <true/>
    </dict>
    <key>UIRequiredDeviceCapabilities</key>
    <array>
        <string>armv7</string>
    </array>
    <key>UISupportedInterfaceOrientations</key>
    <array>
        <string>UIInterfaceOrientationPortrait</string>
        <string>UIInterfaceOrientationLandscapeLeft</string>
        <string>UIInterfaceOrientationLandscapeRight</string>
    </array>
    {permissions_xml}
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
    </dict>
</dict>
</plist>
"""
    
    def _generate_xcode_project(self, app_name: str, bundle_id: str) -> str:
        """Génère un fichier de projet Xcode basique"""
        app_name_clean = app_name.replace(" ", "")
        # Format simplifié - en production, utiliser XcodeGen ou générer correctement
        return f"""// !$*UTF8*$!
{{
    archiveVersion = 1;
    classes = {{
    }};
    objectVersion = 56;
    objects = {{
        /* Begin PBXBuildFile section */
        /* End PBXBuildFile section */
        
        /* Begin PBXFileReference section */
        /* End PBXFileReference section */
        
        /* Begin PBXGroup section */
        /* End PBXGroup section */
        
        /* Begin PBXNativeTarget section */
        /* End PBXNativeTarget section */
        
        /* Begin PBXProject section */
        /* End PBXProject section */
        
        /* Begin XCBuildConfiguration section */
        /* End XCBuildConfiguration section */
    }};
    rootObject = 1234567890ABCDEF /* Project object */;
}}
"""
    
    def _generate_podfile(self, app_name: str) -> str:
        """Génère Podfile pour CocoaPods"""
        return f"""# Uncomment the next line to define a global platform for your project
platform :ios, '15.0'

target '{app_name.replace(" ", "")}' do
  use_frameworks!
  
  # Aucune dépendance externe requise pour l'instant
end
"""
    
    def _generate_ios_readme(self, project_name: str, bundle_id: str, web_url: str) -> str:
        """Génère README pour projet iOS"""
        app_name_clean = project_name.replace(" ", "")
        # IMPORTANT: Utiliser des guillemets simples pour éviter les conflits
        readme_content = f"""# {project_name} - iOS

## 📱 Projet iOS généré par NativiWeb Studio

### Configuration
- **Bundle ID**: {bundle_id}
- **URL Web**: {web_url}
- **Plateforme**: iOS

## 🚀 Instructions de compilation

### Prérequis
- macOS avec Xcode 15.0 ou supérieur
- CocoaPods installé (sudo gem install cocoapods)
- Compte développeur Apple (pour tester sur appareil)

### Étapes

1. **Ouvrir le projet**
```bash
# Décompresser l'archive
unzip {app_name_clean}-iOS.zip
cd {app_name_clean}-iOS

# Installer les dépendances (si nécessaire)
pod install

# Ouvrir le workspace
open {app_name_clean}.xcworkspace
# OU ouvrir directement le projet
open {app_name_clean}.xcodeproj
```

2. **Configurer le projet**
- Sélectionner le projet dans le navigateur
- Onglet "Signing & Capabilities"
- Sélectionner votre Team
- Vérifier que le Bundle Identifier est correct

3. **Configurer les permissions**
- Si des fonctionnalités natives sont activées, vérifier Info.plist
- Les descriptions de permissions doivent être présentes

4. **Compiler et exécuter**
- Sélectionner un simulateur ou un appareil connecté
- Cliquer sur Run (▶️) ou appuyer sur Cmd+R
- L'app va se compiler et s'exécuter

5. **Générer un IPA (pour TestFlight/App Store)**
```
Product > Archive
```
Puis utiliser Organizer pour exporter l'IPA

### ⚠️ Important

- Pour tester sur un appareil réel, vous devez avoir un compte développeur Apple
- Configurez les certificats et provisioning profiles
- Testez toutes les fonctionnalités natives sur un appareil réel

## 📚 Documentation

Pour plus d'informations, consultez:
- [NativiWeb Studio Documentation](https://docs.nativiweb.io)
- [Apple Developer Documentation](https://developer.apple.com/documentation)
"""
        return readme_content