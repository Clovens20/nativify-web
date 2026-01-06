from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import json
import io
import zipfile
import hashlib
import secrets
import base64
import asyncio
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(
    title="NativiWeb Studio API",
    description="API pour transformer des web apps en applications natives",
    version="2.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ==================== MODELS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: str = "user"
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NativeFeature(BaseModel):
    id: str
    name: str
    enabled: bool = False
    config: Dict[str, Any] = {}

class ProjectCreate(BaseModel):
    name: str
    web_url: str
    description: Optional[str] = ""
    platform: List[str] = ["android", "ios"]

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    web_url: Optional[str] = None
    description: Optional[str] = None
    features: Optional[List[NativeFeature]] = None

class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    web_url: str
    description: str = ""
    platform: List[str] = ["android", "ios"]
    features: List[NativeFeature] = []
    status: str = "draft"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Certificate Models
class CertificateUpload(BaseModel):
    platform: str  # android or ios
    cert_type: str  # keystore, p12, provisioning_profile, etc.
    name: str
    password: Optional[str] = None

class Certificate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    project_id: str
    platform: str
    cert_type: str
    name: str
    filename: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    status: str = "valid"

# Build Models
class BuildCreate(BaseModel):
    project_id: str
    platform: str
    build_type: str = "debug"
    certificate_id: Optional[str] = None

class BuildConfig(BaseModel):
    version_name: str = "1.0.0"
    version_code: int = 1
    min_sdk: int = 24
    target_sdk: int = 34
    bundle_id: str = ""

class Build(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    user_id: str
    platform: str
    build_type: str
    build_config: Dict[str, Any] = {}
    certificate_id: Optional[str] = None
    status: str = "pending"
    phase: str = "queued"
    progress: int = 0
    logs: List[Dict[str, Any]] = []
    artifacts: List[Dict[str, str]] = []
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

class APIKeyCreate(BaseModel):
    name: str
    permissions: List[str] = ["read"]

class APIKey(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    key: str = Field(default_factory=lambda: f"nw_{secrets.token_hex(24)}")
    permissions: List[str] = ["read"]
    last_used: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Admin Models
class SystemLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    level: str  # info, warning, error
    category: str  # auth, build, system, api
    message: str
    details: Dict[str, Any] = {}
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PlatformConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "platform_config"
    maintenance_mode: bool = False
    max_builds_per_user: int = 10
    max_projects_per_user: int = 5
    allowed_domains: List[str] = []
    build_timeout_minutes: int = 30
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserUpdate(BaseModel):
    status: Optional[str] = None
    role: Optional[str] = None

# Default native features
DEFAULT_FEATURES = [
    {"id": "push_notifications", "name": "Push Notifications", "enabled": False, "config": {}},
    {"id": "camera", "name": "Camera", "enabled": False, "config": {}},
    {"id": "geolocation", "name": "Geolocation (GPS)", "enabled": False, "config": {}},
    {"id": "local_storage", "name": "Local Storage", "enabled": False, "config": {}},
    {"id": "biometrics", "name": "Biometric Auth", "enabled": False, "config": {}},
    {"id": "contacts", "name": "Contacts", "enabled": False, "config": {}},
    {"id": "file_system", "name": "File System", "enabled": False, "config": {}},
    {"id": "share", "name": "Native Share", "enabled": False, "config": {}},
    {"id": "haptics", "name": "Haptic Feedback", "enabled": False, "config": {}},
    {"id": "deep_links", "name": "Deep Links", "enabled": False, "config": {}},
    {"id": "app_badge", "name": "App Badge", "enabled": False, "config": {}},
    {"id": "clipboard", "name": "Clipboard", "enabled": False, "config": {}},
]

# Build phases for detailed progress
BUILD_PHASES = {
    "android": [
        {"phase": "queued", "name": "Queued", "duration": 2},
        {"phase": "preparing", "name": "Preparing Environment", "duration": 3},
        {"phase": "fetching", "name": "Fetching Web App", "duration": 4},
        {"phase": "generating", "name": "Generating Native Project", "duration": 5},
        {"phase": "configuring", "name": "Configuring Features", "duration": 3},
        {"phase": "gradle_sync", "name": "Gradle Sync", "duration": 8},
        {"phase": "compiling", "name": "Compiling Resources", "duration": 10},
        {"phase": "assembling", "name": "Assembling APK/AAB", "duration": 8},
        {"phase": "signing", "name": "Signing Package", "duration": 3},
        {"phase": "optimizing", "name": "Optimizing", "duration": 2},
        {"phase": "uploading", "name": "Uploading Artifacts", "duration": 2},
        {"phase": "completed", "name": "Completed", "duration": 0},
    ],
    "ios": [
        {"phase": "queued", "name": "Queued", "duration": 2},
        {"phase": "preparing", "name": "Preparing Environment", "duration": 4},
        {"phase": "fetching", "name": "Fetching Web App", "duration": 4},
        {"phase": "generating", "name": "Generating Xcode Project", "duration": 6},
        {"phase": "configuring", "name": "Configuring Capabilities", "duration": 4},
        {"phase": "pod_install", "name": "Installing CocoaPods", "duration": 8},
        {"phase": "compiling", "name": "Compiling Swift Code", "duration": 12},
        {"phase": "linking", "name": "Linking Frameworks", "duration": 6},
        {"phase": "archiving", "name": "Creating Archive", "duration": 8},
        {"phase": "signing", "name": "Code Signing", "duration": 4},
        {"phase": "exporting", "name": "Exporting IPA", "duration": 3},
        {"phase": "uploading", "name": "Uploading Artifacts", "duration": 2},
        {"phase": "completed", "name": "Completed", "duration": 0},
    ]
}

# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

async def log_system_event(level: str, category: str, message: str, details: dict = None, user_id: str = None):
    """Log system events to database"""
    log = SystemLog(
        level=level,
        category=category,
        message=message,
        details=details or {},
        user_id=user_id
    )
    log_dict = log.model_dump()
    log_dict['created_at'] = log_dict['created_at'].isoformat()
    await db.system_logs.insert_one(log_dict)

def generate_build_logs(phase: str, platform: str, project_name: str) -> List[Dict[str, Any]]:
    """Generate realistic build logs for each phase"""
    timestamp = datetime.now(timezone.utc).isoformat()
    
    log_templates = {
        "queued": [
            {"level": "info", "message": f"Build queued for {project_name}", "timestamp": timestamp},
            {"level": "info", "message": f"Target platform: {platform.upper()}", "timestamp": timestamp},
        ],
        "preparing": [
            {"level": "info", "message": "Initializing build environment...", "timestamp": timestamp},
            {"level": "info", "message": f"Setting up {platform.upper()} SDK...", "timestamp": timestamp},
            {"level": "info", "message": "Checking dependencies...", "timestamp": timestamp},
        ],
        "fetching": [
            {"level": "info", "message": "Fetching web application content...", "timestamp": timestamp},
            {"level": "info", "message": "Analyzing web app structure...", "timestamp": timestamp},
            {"level": "info", "message": "Caching static assets...", "timestamp": timestamp},
        ],
        "generating": [
            {"level": "info", "message": "Generating native project structure...", "timestamp": timestamp},
            {"level": "info", "message": "Creating main activity/view controller...", "timestamp": timestamp},
            {"level": "info", "message": "Setting up WebView bridge...", "timestamp": timestamp},
        ],
        "configuring": [
            {"level": "info", "message": "Configuring native features...", "timestamp": timestamp},
            {"level": "info", "message": "Setting up permissions...", "timestamp": timestamp},
            {"level": "info", "message": "Generating feature bridges...", "timestamp": timestamp},
        ],
        "gradle_sync": [
            {"level": "info", "message": "Starting Gradle sync...", "timestamp": timestamp},
            {"level": "info", "message": "Resolving dependencies...", "timestamp": timestamp},
            {"level": "info", "message": "BUILD SUCCESSFUL in 8s", "timestamp": timestamp},
        ],
        "pod_install": [
            {"level": "info", "message": "Running pod install...", "timestamp": timestamp},
            {"level": "info", "message": "Installing pods (15 dependencies)...", "timestamp": timestamp},
            {"level": "info", "message": "Pod installation complete!", "timestamp": timestamp},
        ],
        "compiling": [
            {"level": "info", "message": "Compiling source files...", "timestamp": timestamp},
            {"level": "info", "message": "Processing resources...", "timestamp": timestamp},
            {"level": "info", "message": "Compilation successful", "timestamp": timestamp},
        ],
        "linking": [
            {"level": "info", "message": "Linking frameworks...", "timestamp": timestamp},
            {"level": "info", "message": "Linking UIKit, WebKit, CoreLocation...", "timestamp": timestamp},
        ],
        "assembling": [
            {"level": "info", "message": "Assembling debug APK...", "timestamp": timestamp},
            {"level": "info", "message": "Merging DEX files...", "timestamp": timestamp},
            {"level": "info", "message": "APK assembly complete", "timestamp": timestamp},
        ],
        "archiving": [
            {"level": "info", "message": "Creating Xcode archive...", "timestamp": timestamp},
            {"level": "info", "message": "Archive created successfully", "timestamp": timestamp},
        ],
        "signing": [
            {"level": "info", "message": "Signing application package...", "timestamp": timestamp},
            {"level": "info", "message": "Verifying signature...", "timestamp": timestamp},
            {"level": "success", "message": "Package signed successfully", "timestamp": timestamp},
        ],
        "optimizing": [
            {"level": "info", "message": "Optimizing APK size...", "timestamp": timestamp},
            {"level": "info", "message": "Removing unused resources...", "timestamp": timestamp},
        ],
        "exporting": [
            {"level": "info", "message": "Exporting IPA file...", "timestamp": timestamp},
            {"level": "info", "message": "IPA exported successfully", "timestamp": timestamp},
        ],
        "uploading": [
            {"level": "info", "message": "Uploading build artifacts...", "timestamp": timestamp},
            {"level": "success", "message": "Artifacts uploaded successfully", "timestamp": timestamp},
        ],
        "completed": [
            {"level": "success", "message": f"Build completed successfully!", "timestamp": timestamp},
            {"level": "info", "message": "Artifacts ready for download", "timestamp": timestamp},
        ],
    }
    
    return log_templates.get(phase, [{"level": "info", "message": f"Phase: {phase}", "timestamp": timestamp}])

def generate_android_template(project: dict, features: list) -> str:
    """Generate Android project structure as string"""
    enabled_features = [f for f in features if f.get('enabled', False)]
    feature_permissions = {
        "push_notifications": "INTERNET",
        "camera": "CAMERA",
        "geolocation": "ACCESS_FINE_LOCATION",
        "contacts": "READ_CONTACTS",
        "file_system": "READ_EXTERNAL_STORAGE",
    }
    
    permissions = ["INTERNET"]
    for f in enabled_features:
        if f['id'] in feature_permissions:
            permissions.append(feature_permissions[f['id']])
    
    manifest_permissions = "\n".join([f'    <uses-permission android:name="android.permission.{p}" />' for p in set(permissions)])
    
    return f'''// ============================================
// NativiWeb Android Project Template
// Project: {project['name']}
// Generated: {datetime.now(timezone.utc).isoformat()}
// ============================================

// === AndroidManifest.xml ===
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.nativiweb.{project['name'].lower().replace(' ', '_').replace('-', '_')}">
    
{manifest_permissions}
    
    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="{project['name']}"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.NativiWeb"
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

// === build.gradle (Module: app) ===
plugins {{
    id 'com.android.application'
    id 'kotlin-android'
}}

android {{
    namespace "com.nativiweb.{project['name'].lower().replace(' ', '_').replace('-', '_')}"
    compileSdk 34
    
    defaultConfig {{
        applicationId "com.nativiweb.{project['name'].lower().replace(' ', '_').replace('-', '_')}"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0.0"
        
        testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"
    }}
    
    buildTypes {{
        release {{
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }}
        debug {{
            applicationIdSuffix ".debug"
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
    
    // Testing
    testImplementation 'junit:junit:4.13.2'
    androidTestImplementation 'androidx.test.ext:junit:1.1.5'
    androidTestImplementation 'androidx.test.espresso:espresso-core:3.5.1'
}}

// === MainActivity.kt ===
package com.nativiweb.{project['name'].lower().replace(' ', '_').replace('-', '_')}

import android.os.Bundle
import android.webkit.*
import androidx.appcompat.app.AppCompatActivity
import com.nativiweb.{project['name'].lower().replace(' ', '_').replace('-', '_')}.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {{
    
    private lateinit var binding: ActivityMainBinding
    private lateinit var webView: WebView
    
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupWebView()
    }}
    
    private fun setupWebView() {{
        webView = binding.webView
        
        webView.settings.apply {{
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = true
            allowContentAccess = true
            mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            cacheMode = WebSettings.LOAD_DEFAULT
            setSupportZoom(false)
            builtInZoomControls = false
            displayZoomControls = false
        }}
        
        webView.webViewClient = NativiWebViewClient()
        webView.webChromeClient = NativiWebChromeClient()
        
        // Add JavaScript interface for native features
        webView.addJavascriptInterface(NativiWebBridge(this), "NativiWebNative")
        
        // Load the web app
        webView.loadUrl("{project['web_url']}")
    }}
    
    override fun onBackPressed() {{
        if (webView.canGoBack()) {{
            webView.goBack()
        }} else {{
            super.onBackPressed()
        }}
    }}
    
    override fun onDestroy() {{
        webView.destroy()
        super.onDestroy()
    }}
}}

// === NativiWebBridge.kt ===
package com.nativiweb.{project['name'].lower().replace(' ', '_').replace('-', '_')}

import android.content.Context
import android.os.Build
import android.webkit.JavascriptInterface
import org.json.JSONObject

class NativiWebBridge(private val context: Context) {{
    
    @JavascriptInterface
    fun getDeviceInfo(): String {{
        return JSONObject().apply {{
            put("platform", "android")
            put("version", Build.VERSION.RELEASE)
            put("sdk", Build.VERSION.SDK_INT)
            put("manufacturer", Build.MANUFACTURER)
            put("model", Build.MODEL)
        }}.toString()
    }}
    
    @JavascriptInterface
    fun vibrate(duration: Long) {{
        val vibrator = context.getSystemService(Context.VIBRATOR_SERVICE) as? android.os.Vibrator
        vibrator?.vibrate(duration)
    }}
    
    @JavascriptInterface
    fun showNotification(title: String, body: String) {{
        // Notification implementation
        android.util.Log.d("NativiWeb", "Notification: $title - $body")
    }}
    
    @JavascriptInterface
    fun getCurrentPosition(): String {{
        // Location implementation (requires LocationManager)
        return JSONObject().apply {{
            put("latitude", 0.0)
            put("longitude", 0.0)
            put("accuracy", 0.0)
        }}.toString()
    }}
    
    @JavascriptInterface
    fun copyToClipboard(text: String) {{
        val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as android.content.ClipboardManager
        val clip = android.content.ClipData.newPlainText("NativiWeb", text)
        clipboard.setPrimaryClip(clip)
    }}
}}

// === activity_main.xml ===
<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout 
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <WebView
        android:id="@+id/webView"
        android:layout_width="0dp"
        android:layout_height="0dp"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toTopOf="parent" />

</androidx.constraintlayout.widget.ConstraintLayout>
'''

def generate_ios_template(project: dict, features: list) -> str:
    """Generate iOS project structure as string"""
    enabled_features = [f for f in features if f.get('enabled', False)]
    
    privacy_keys = []
    for f in enabled_features:
        if f['id'] == 'camera':
            privacy_keys.append('    <key>NSCameraUsageDescription</key>\n    <string>This app needs camera access for taking photos</string>')
        if f['id'] == 'geolocation':
            privacy_keys.append('    <key>NSLocationWhenInUseUsageDescription</key>\n    <string>This app needs location access</string>')
        if f['id'] == 'contacts':
            privacy_keys.append('    <key>NSContactsUsageDescription</key>\n    <string>This app needs contacts access</string>')
    
    privacy_section = "\n".join(privacy_keys) if privacy_keys else "    <!-- No special permissions required -->"
    bundle_id = f"com.nativiweb.{project['name'].lower().replace(' ', '-').replace('_', '-')}"
    
    return f'''// ============================================
// NativiWeb iOS Project Template
// Project: {project['name']}
// Generated: {datetime.now(timezone.utc).isoformat()}
// ============================================

// === Info.plist ===
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>$(DEVELOPMENT_LANGUAGE)</string>
    <key>CFBundleDisplayName</key>
    <string>{project['name']}</string>
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
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSRequiresIPhoneOS</key>
    <true/>
    <key>UILaunchStoryboardName</key>
    <string>LaunchScreen</string>
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
    <key>ITSAppUsesNonExemptEncryption</key>
    <false/>
{privacy_section}
</dict>
</plist>

// === NativiWebApp.swift ===
import SwiftUI

@main
struct NativiWebApp: App {{
    var body: some Scene {{
        WindowGroup {{
            ContentView()
                .preferredColorScheme(.light)
        }}
    }}
}}

// === ContentView.swift ===
import SwiftUI
import WebKit

struct ContentView: View {{
    @StateObject private var webViewModel = WebViewModel()
    
    var body: some View {{
        WebView(viewModel: webViewModel)
            .edgesIgnoringSafeArea(.all)
            .onAppear {{
                webViewModel.loadURL("{project['web_url']}")
            }}
    }}
}}

// === WebViewModel.swift ===
import Foundation
import WebKit

class WebViewModel: ObservableObject {{
    @Published var isLoading: Bool = true
    @Published var canGoBack: Bool = false
    @Published var canGoForward: Bool = false
    
    var webView: WKWebView?
    
    func loadURL(_ urlString: String) {{
        guard let url = URL(string: urlString) else {{ return }}
        webView?.load(URLRequest(url: url))
    }}
    
    func goBack() {{
        webView?.goBack()
    }}
    
    func goForward() {{
        webView?.goForward()
    }}
    
    func reload() {{
        webView?.reload()
    }}
}}

// === WebView.swift ===
import SwiftUI
import WebKit

struct WebView: UIViewRepresentable {{
    @ObservedObject var viewModel: WebViewModel
    
    func makeCoordinator() -> Coordinator {{
        Coordinator(viewModel: viewModel)
    }}
    
    func makeUIView(context: Context) -> WKWebView {{
        let configuration = WKWebViewConfiguration()
        configuration.allowsInlineMediaPlayback = true
        configuration.mediaTypesRequiringUserActionForPlayback = []
        
        // Add script message handler for native bridge
        let contentController = WKUserContentController()
        contentController.add(context.coordinator, name: "NativiWebNative")
        configuration.userContentController = contentController
        
        // Inject JavaScript bridge
        let bridgeScript = WKUserScript(
            source: NativiWebBridge.bridgeScript,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: true
        )
        contentController.addUserScript(bridgeScript)
        
        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = context.coordinator
        webView.uiDelegate = context.coordinator
        webView.allowsBackForwardNavigationGestures = true
        
        viewModel.webView = webView
        return webView
    }}
    
    func updateUIView(_ webView: WKWebView, context: Context) {{}}
    
    class Coordinator: NSObject, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler {{
        var viewModel: WebViewModel
        
        init(viewModel: WebViewModel) {{
            self.viewModel = viewModel
        }}
        
        func webView(_ webView: WKWebView, didStartProvisionalNavigation navigation: WKNavigation!) {{
            viewModel.isLoading = true
        }}
        
        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {{
            viewModel.isLoading = false
            viewModel.canGoBack = webView.canGoBack
            viewModel.canGoForward = webView.canGoForward
        }}
        
        func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {{
            NativiWebBridge.handleMessage(message)
        }}
    }}
}}

// === NativiWebBridge.swift ===
import Foundation
import WebKit
import UIKit

class NativiWebBridge {{
    
    static let bridgeScript = """
    window.NativiWebNative = {{
        postMessage: function(data) {{
            window.webkit.messageHandlers.NativiWebNative.postMessage(data);
        }}
    }};
    """
    
    static func handleMessage(_ message: WKScriptMessage) {{
        guard let body = message.body as? [String: Any],
              let method = body["method"] as? String else {{ return }}
        
        switch method {{
        case "getDeviceInfo":
            handleGetDeviceInfo(message.webView)
        case "vibrate":
            handleVibrate(body)
        case "showNotification":
            handleNotification(body)
        case "getCurrentPosition":
            handleGetLocation(message.webView)
        default:
            print("Unknown method: \\(method)")
        }}
    }}
    
    private static func handleGetDeviceInfo(_ webView: WKWebView?) {{
        let info: [String: Any] = [
            "platform": "ios",
            "version": UIDevice.current.systemVersion,
            "model": UIDevice.current.model,
            "name": UIDevice.current.name
        ]
        
        if let jsonData = try? JSONSerialization.data(withJSONObject: info),
           let jsonString = String(data: jsonData, encoding: .utf8) {{
            let js = "window.NativiWeb._onDeviceInfo(\\(jsonString))"
            webView?.evaluateJavaScript(js, completionHandler: nil)
        }}
    }}
    
    private static func handleVibrate(_ body: [String: Any]) {{
        let generator = UIImpactFeedbackGenerator(style: .medium)
        generator.impactOccurred()
    }}
    
    private static func handleNotification(_ body: [String: Any]) {{
        guard let title = body["title"] as? String else {{ return }}
        let bodyText = body["body"] as? String ?? ""
        print("Notification: \\(title) - \\(bodyText)")
        // Implement UNUserNotificationCenter for real notifications
    }}
    
    private static func handleGetLocation(_ webView: WKWebView?) {{
        // Implement CLLocationManager for real location
        let location: [String: Any] = [
            "latitude": 0.0,
            "longitude": 0.0,
            "accuracy": 0.0
        ]
        
        if let jsonData = try? JSONSerialization.data(withJSONObject: location),
           let jsonString = String(data: jsonData, encoding: .utf8) {{
            let js = "window.NativiWeb._onLocation(\\(jsonString))"
            webView?.evaluateJavaScript(js, completionHandler: nil)
        }}
    }}
}}

// === Podfile ===
platform :ios, '15.0'

target '{project['name'].replace(' ', '')}' do
  use_frameworks!
  
  # Add pods for additional features here
  # pod 'Firebase/Messaging' # For push notifications
  # pod 'GoogleMaps' # For maps
  
end

post_install do |installer|
  installer.pods_project.targets.each do |target|
    target.build_configurations.each do |config|
      config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'] = '15.0'
    end
  end
end
'''

def generate_sdk_js(project: dict, features: list) -> str:
    """Generate the NativiWeb JavaScript SDK"""
    enabled_features = [f for f in features if f.get('enabled', False)]
    feature_ids = [f['id'] for f in enabled_features]
    
    return f'''/**
 * NativiWeb SDK v1.0.0
 * Project: {project['name']}
 * Generated: {datetime.now(timezone.utc).isoformat()}
 * 
 * This SDK provides a bridge between your web app and native device features.
 * Include this script in your web app to access native capabilities.
 */

(function(global) {{
  'use strict';

  const ENABLED_FEATURES = {json.dumps(feature_ids)};
  const SDK_VERSION = '1.0.0';
  
  class NativiWebSDK {{
    constructor() {{
      this.platform = this._detectPlatform();
      this.isNative = this._checkNativeEnvironment();
      this.version = SDK_VERSION;
      this._eventHandlers = {{}};
      this._callbacks = {{}};
      this._callbackId = 0;
      
      if (this.isNative) {{
        this._initBridge();
      }}
      
      console.log('[NativiWeb] SDK initialized', {{
        platform: this.platform,
        isNative: this.isNative,
        version: this.version,
        features: ENABLED_FEATURES
      }});
    }}
    
    _detectPlatform() {{
      const ua = navigator.userAgent.toLowerCase();
      if (/android/.test(ua)) return 'android';
      if (/iphone|ipad|ipod/.test(ua)) return 'ios';
      return 'web';
    }}
    
    _checkNativeEnvironment() {{
      return typeof window.NativiWebNative !== 'undefined' || 
             typeof window.webkit?.messageHandlers?.NativiWebNative !== 'undefined';
    }}
    
    _initBridge() {{
      console.log('[NativiWeb] Initializing native bridge for', this.platform);
      
      // Set up callback handlers
      window.NativiWeb = window.NativiWeb || {{}};
      window.NativiWeb._onDeviceInfo = (data) => this._handleCallback('deviceInfo', data);
      window.NativiWeb._onLocation = (data) => this._handleCallback('location', data);
      window.NativiWeb._onNotification = (data) => this._handleCallback('notification', data);
      
      // Listen for native events
      window.addEventListener('NativiWebEvent', (e) => {{
        const {{ type, data }} = e.detail;
        if (this._eventHandlers[type]) {{
          this._eventHandlers[type].forEach(handler => handler(data));
        }}
      }});
    }}
    
    _handleCallback(type, data) {{
      const handlers = this._callbacks[type] || [];
      handlers.forEach({{ resolve }} => resolve(data));
      this._callbacks[type] = [];
    }}
    
    _callNative(method, params = {{}}) {{
      return new Promise((resolve, reject) => {{
        if (!this.isNative) {{
          reject(new Error('Not running in native environment'));
          return;
        }}
        
        const callbackId = ++this._callbackId;
        
        try {{
          if (this.platform === 'android' && window.NativiWebNative) {{
            const result = window.NativiWebNative[method](JSON.stringify(params));
            resolve(result ? JSON.parse(result) : {{}});
          }} else if (this.platform === 'ios' && window.webkit?.messageHandlers?.NativiWebNative) {{
            // Store callback for async response
            if (!this._callbacks[method]) this._callbacks[method] = [];
            this._callbacks[method].push({{ resolve, reject, callbackId }});
            
            window.webkit.messageHandlers.NativiWebNative.postMessage({{
              method,
              params,
              callbackId
            }});
            
            // Timeout after 30 seconds
            setTimeout(() => {{
              this._callbacks[method] = this._callbacks[method]?.filter(c => c.callbackId !== callbackId) || [];
              reject(new Error('Native call timeout'));
            }}, 30000);
          }}
        }} catch (error) {{
          reject(error);
        }}
      }});
    }}
    
    // Event handling
    on(event, handler) {{
      if (!this._eventHandlers[event]) {{
        this._eventHandlers[event] = [];
      }}
      this._eventHandlers[event].push(handler);
      return () => this.off(event, handler);
    }}
    
    off(event, handler) {{
      if (this._eventHandlers[event]) {{
        this._eventHandlers[event] = this._eventHandlers[event].filter(h => h !== handler);
      }}
    }}
    
    // ==================== DEVICE INFO ====================
    async getDeviceInfo() {{
      if (this.isNative) {{
        return this._callNative('getDeviceInfo');
      }}
      return {{
        platform: this.platform,
        userAgent: navigator.userAgent,
        language: navigator.language,
        online: navigator.onLine,
        screenWidth: window.screen.width,
        screenHeight: window.screen.height
      }};
    }}
    
    // ==================== PUSH NOTIFICATIONS ====================
    async requestNotificationPermission() {{
      if (!ENABLED_FEATURES.includes('push_notifications')) {{
        throw new Error('Push notifications feature not enabled');
      }}
      if (this.isNative) {{
        return this._callNative('requestNotificationPermission');
      }}
      return Notification.requestPermission();
    }}
    
    async showNotification(title, options = {{}}) {{
      if (!ENABLED_FEATURES.includes('push_notifications')) {{
        throw new Error('Push notifications feature not enabled');
      }}
      if (this.isNative) {{
        return this._callNative('showNotification', {{ title, ...options }});
      }}
      if (Notification.permission === 'granted') {{
        return new Notification(title, options);
      }}
      throw new Error('Notification permission not granted');
    }}
    
    // ==================== CAMERA ====================
    async openCamera(options = {{}}) {{
      if (!ENABLED_FEATURES.includes('camera')) {{
        throw new Error('Camera feature not enabled');
      }}
      if (this.isNative) {{
        return this._callNative('openCamera', options);
      }}
      return navigator.mediaDevices.getUserMedia({{ video: options.facingMode ? {{ facingMode: options.facingMode }} : true }});
    }}
    
    async takePhoto(options = {{}}) {{
      if (!ENABLED_FEATURES.includes('camera')) {{
        throw new Error('Camera feature not enabled');
      }}
      if (this.isNative) {{
        return this._callNative('takePhoto', options);
      }}
      throw new Error('takePhoto requires native environment');
    }}
    
    // ==================== GEOLOCATION ====================
    async getCurrentPosition(options = {{}}) {{
      if (!ENABLED_FEATURES.includes('geolocation')) {{
        throw new Error('Geolocation feature not enabled');
      }}
      if (this.isNative) {{
        return this._callNative('getCurrentPosition', options);
      }}
      return new Promise((resolve, reject) => {{
        navigator.geolocation.getCurrentPosition(
          (position) => resolve({{
            coords: {{
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
              accuracy: position.coords.accuracy,
              altitude: position.coords.altitude,
              altitudeAccuracy: position.coords.altitudeAccuracy,
              heading: position.coords.heading,
              speed: position.coords.speed
            }},
            timestamp: position.timestamp
          }}),
          reject,
          options
        );
      }});
    }}
    
    watchPosition(callback, options = {{}}) {{
      if (!ENABLED_FEATURES.includes('geolocation')) {{
        throw new Error('Geolocation feature not enabled');
      }}
      return navigator.geolocation.watchPosition(callback, console.error, options);
    }}
    
    clearWatch(watchId) {{
      navigator.geolocation.clearWatch(watchId);
    }}
    
    // ==================== LOCAL STORAGE ====================
    async setItem(key, value) {{
      if (!ENABLED_FEATURES.includes('local_storage')) {{
        throw new Error('Local storage feature not enabled');
      }}
      const serialized = JSON.stringify(value);
      if (this.isNative) {{
        return this._callNative('setStorageItem', {{ key, value: serialized }});
      }}
      localStorage.setItem(key, serialized);
    }}
    
    async getItem(key) {{
      if (!ENABLED_FEATURES.includes('local_storage')) {{
        throw new Error('Local storage feature not enabled');
      }}
      if (this.isNative) {{
        const result = await this._callNative('getStorageItem', {{ key }});
        return result.value ? JSON.parse(result.value) : null;
      }}
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    }}
    
    async removeItem(key) {{
      if (!ENABLED_FEATURES.includes('local_storage')) {{
        throw new Error('Local storage feature not enabled');
      }}
      if (this.isNative) {{
        return this._callNative('removeStorageItem', {{ key }});
      }}
      localStorage.removeItem(key);
    }}
    
    // ==================== HAPTICS ====================
    async vibrate(pattern = 100) {{
      if (!ENABLED_FEATURES.includes('haptics')) {{
        throw new Error('Haptics feature not enabled');
      }}
      if (this.isNative) {{
        return this._callNative('vibrate', {{ pattern }});
      }}
      navigator.vibrate?.(pattern);
    }}
    
    // ==================== SHARE ====================
    async share(data) {{
      if (!ENABLED_FEATURES.includes('share')) {{
        throw new Error('Share feature not enabled');
      }}
      if (this.isNative) {{
        return this._callNative('share', data);
      }}
      if (navigator.share) {{
        return navigator.share(data);
      }}
      throw new Error('Share not supported on this platform');
    }}
    
    // ==================== BIOMETRICS ====================
    async authenticateWithBiometrics(reason = 'Authenticate') {{
      if (!ENABLED_FEATURES.includes('biometrics')) {{
        throw new Error('Biometrics feature not enabled');
      }}
      if (!this.isNative) {{
        throw new Error('Biometrics requires native environment');
      }}
      return this._callNative('authenticateBiometric', {{ reason }});
    }}
    
    async isBiometricsAvailable() {{
      if (!ENABLED_FEATURES.includes('biometrics')) {{
        return false;
      }}
      if (!this.isNative) {{
        return false;
      }}
      const result = await this._callNative('checkBiometrics');
      return result.available || false;
    }}
    
    // ==================== CLIPBOARD ====================
    async copyToClipboard(text) {{
      if (!ENABLED_FEATURES.includes('clipboard')) {{
        throw new Error('Clipboard feature not enabled');
      }}
      if (this.isNative) {{
        return this._callNative('copyToClipboard', {{ text }});
      }}
      return navigator.clipboard.writeText(text);
    }}
    
    async readFromClipboard() {{
      if (!ENABLED_FEATURES.includes('clipboard')) {{
        throw new Error('Clipboard feature not enabled');
      }}
      if (this.isNative) {{
        const result = await this._callNative('readFromClipboard');
        return result.text;
      }}
      return navigator.clipboard.readText();
    }}
    
    // ==================== APP BADGE ====================
    async setBadgeCount(count) {{
      if (!ENABLED_FEATURES.includes('app_badge')) {{
        throw new Error('App badge feature not enabled');
      }}
      if (this.isNative) {{
        return this._callNative('setBadgeCount', {{ count }});
      }}
      if ('setAppBadge' in navigator) {{
        return navigator.setAppBadge(count);
      }}
    }}
    
    async clearBadge() {{
      if (!ENABLED_FEATURES.includes('app_badge')) {{
        throw new Error('App badge feature not enabled');
      }}
      if (this.isNative) {{
        return this._callNative('clearBadge');
      }}
      if ('clearAppBadge' in navigator) {{
        return navigator.clearAppBadge();
      }}
    }}
    
    // ==================== UTILITY ====================
    getEnabledFeatures() {{
      return ENABLED_FEATURES;
    }}
    
    isFeatureEnabled(featureId) {{
      return ENABLED_FEATURES.includes(featureId);
    }}
  }}
  
  // Create singleton instance
  const instance = new NativiWebSDK();
  
  // Export
  global.NativiWeb = instance;
  
  if (typeof module !== 'undefined' && module.exports) {{
    module.exports = instance;
  }}
  
}})(typeof window !== 'undefined' ? window : this);
'''

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_data.email,
        name=user_data.name,
        role="user",
        status="active"
    )
    user_dict = user.model_dump()
    user_dict['password_hash'] = hash_password(user_data.password)
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    await log_system_event("info", "auth", f"New user registered: {user_data.email}", user_id=user.id)
    return user

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        await log_system_event("warning", "auth", f"Failed login attempt for {credentials.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if user.get('status') == 'banned':
        raise HTTPException(status_code=403, detail="Account suspended")
    
    if user.get('password_hash') != hash_password(credentials.password):
        await log_system_event("warning", "auth", f"Failed login attempt for {credentials.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = secrets.token_hex(32)
    await db.sessions.insert_one({
        "token": token,
        "user_id": user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    await log_system_event("info", "auth", f"User logged in: {credentials.email}", user_id=user['id'])
    
    return {
        "token": token,
        "user": {
            "id": user['id'],
            "email": user['email'],
            "name": user['name'],
            "role": user.get('role', 'user')
        }
    }

@api_router.get("/auth/me")
async def get_current_user(token: str):
    session = await db.sessions.find_one({"token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.users.find_one({"id": session['user_id']}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@api_router.post("/auth/logout")
async def logout(token: str):
    await db.sessions.delete_one({"token": token})
    return {"message": "Logged out successfully"}

# ==================== PROJECT ENDPOINTS ====================

@api_router.post("/projects", response_model=Project)
async def create_project(project_data: ProjectCreate, user_id: str):
    project = Project(
        user_id=user_id,
        name=project_data.name,
        web_url=project_data.web_url,
        description=project_data.description or "",
        platform=project_data.platform,
        features=[NativeFeature(**f) for f in DEFAULT_FEATURES]
    )
    
    project_dict = project.model_dump()
    project_dict['created_at'] = project_dict['created_at'].isoformat()
    project_dict['updated_at'] = project_dict['updated_at'].isoformat()
    
    await db.projects.insert_one(project_dict)
    await log_system_event("info", "project", f"Project created: {project.name}", user_id=user_id)
    return project

@api_router.get("/projects", response_model=List[Project])
async def get_projects(user_id: str):
    projects = await db.projects.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    for p in projects:
        if isinstance(p.get('created_at'), str):
            p['created_at'] = datetime.fromisoformat(p['created_at'])
        if isinstance(p.get('updated_at'), str):
            p['updated_at'] = datetime.fromisoformat(p['updated_at'])
    return projects

@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str, user_id: str):
    project = await db.projects.find_one({"id": project_id, "user_id": user_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if isinstance(project.get('created_at'), str):
        project['created_at'] = datetime.fromisoformat(project['created_at'])
    if isinstance(project.get('updated_at'), str):
        project['updated_at'] = datetime.fromisoformat(project['updated_at'])
    
    return project

@api_router.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, user_id: str, update_data: ProjectUpdate):
    project = await db.projects.find_one({"id": project_id, "user_id": user_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if 'features' in update_dict:
        update_dict['features'] = [f.model_dump() if hasattr(f, 'model_dump') else f for f in update_dict['features']]
    
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.projects.update_one({"id": project_id}, {"$set": update_dict})
    
    updated = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    
    return updated

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str, user_id: str):
    result = await db.projects.delete_one({"id": project_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    await log_system_event("info", "project", f"Project deleted: {project_id}", user_id=user_id)
    return {"message": "Project deleted"}

# ==================== CERTIFICATE ENDPOINTS ====================

@api_router.post("/certificates")
async def upload_certificate(
    project_id: str,
    user_id: str,
    platform: str,
    cert_type: str,
    name: str,
    file: UploadFile = File(...)
):
    # Validate project ownership
    project = await db.projects.find_one({"id": project_id, "user_id": user_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Read and encode file
    content = await file.read()
    encoded = base64.b64encode(content).decode('utf-8')
    
    cert = Certificate(
        user_id=user_id,
        project_id=project_id,
        platform=platform,
        cert_type=cert_type,
        name=name,
        filename=file.filename
    )
    
    cert_dict = cert.model_dump()
    cert_dict['uploaded_at'] = cert_dict['uploaded_at'].isoformat()
    cert_dict['content'] = encoded  # Store encoded content
    
    await db.certificates.insert_one(cert_dict)
    await log_system_event("info", "certificate", f"Certificate uploaded: {name}", user_id=user_id)
    
    return {"id": cert.id, "name": name, "platform": platform, "cert_type": cert_type}

@api_router.get("/certificates")
async def get_certificates(project_id: str, user_id: str):
    certs = await db.certificates.find(
        {"project_id": project_id, "user_id": user_id},
        {"_id": 0, "content": 0}  # Exclude content from response
    ).to_list(100)
    
    for c in certs:
        if isinstance(c.get('uploaded_at'), str):
            c['uploaded_at'] = datetime.fromisoformat(c['uploaded_at'])
    
    return certs

@api_router.delete("/certificates/{cert_id}")
async def delete_certificate(cert_id: str, user_id: str):
    result = await db.certificates.delete_one({"id": cert_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return {"message": "Certificate deleted"}

# ==================== BUILD ENDPOINTS ====================

@api_router.post("/builds", response_model=Build)
async def create_build(build_data: BuildCreate, user_id: str, background_tasks: BackgroundTasks):
    project = await db.projects.find_one({"id": build_data.project_id, "user_id": user_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    build = Build(
        project_id=build_data.project_id,
        user_id=user_id,
        platform=build_data.platform,
        build_type=build_data.build_type,
        certificate_id=build_data.certificate_id,
        status="processing",
        phase="queued",
        logs=[{
            "level": "info",
            "message": f"Build queued for {project['name']}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]
    )
    
    build_dict = build.model_dump()
    build_dict['created_at'] = build_dict['created_at'].isoformat()
    
    await db.builds.insert_one(build_dict)
    await log_system_event("info", "build", f"Build started: {build.id}", user_id=user_id)
    
    # Start build process in background
    background_tasks.add_task(process_build_advanced, build.id, project)
    
    return build

async def process_build_advanced(build_id: str, project: dict):
    """Advanced build processing with detailed phases and logs"""
    platform = (await db.builds.find_one({"id": build_id}, {"_id": 0}))['platform']
    phases = BUILD_PHASES.get(platform, BUILD_PHASES['android'])
    
    total_duration = sum(p['duration'] for p in phases)
    current_progress = 0
    
    await db.builds.update_one(
        {"id": build_id},
        {"$set": {"started_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    for phase_info in phases:
        phase = phase_info['phase']
        phase_name = phase_info['name']
        duration = phase_info['duration']
        
        # Update phase
        await db.builds.update_one(
            {"id": build_id},
            {"$set": {"phase": phase}}
        )
        
        # Generate and add logs
        logs = generate_build_logs(phase, platform, project['name'])
        for log in logs:
            await db.builds.update_one(
                {"id": build_id},
                {"$push": {"logs": log}}
            )
        
        # Simulate phase duration
        if duration > 0:
            steps = max(1, duration)
            for _ in range(steps):
                await asyncio.sleep(0.5)  # 0.5s per step
                current_progress += (100 / total_duration) / 2
                await db.builds.update_one(
                    {"id": build_id},
                    {"$set": {"progress": min(int(current_progress), 99)}}
                )
    
    # Generate artifacts
    artifacts = []
    if platform == 'android':
        artifacts = [
            {"name": f"{project['name']}-debug.apk", "type": "apk", "size": f"{random.randint(15, 30)}MB"},
            {"name": f"{project['name']}-release.aab", "type": "aab", "size": f"{random.randint(12, 25)}MB"},
        ]
    else:
        artifacts = [
            {"name": f"{project['name']}.ipa", "type": "ipa", "size": f"{random.randint(20, 40)}MB"},
            {"name": f"{project['name']}.xcarchive", "type": "archive", "size": f"{random.randint(50, 80)}MB"},
        ]
    
    # Complete build
    completed_at = datetime.now(timezone.utc)
    started_at = await db.builds.find_one({"id": build_id}, {"_id": 0, "started_at": 1})
    started = datetime.fromisoformat(started_at['started_at']) if started_at.get('started_at') else completed_at
    duration = int((completed_at - started).total_seconds())
    
    await db.builds.update_one(
        {"id": build_id},
        {"$set": {
            "status": "completed",
            "phase": "completed",
            "progress": 100,
            "artifacts": artifacts,
            "completed_at": completed_at.isoformat(),
            "duration_seconds": duration,
            "download_url": f"/api/builds/{build_id}/download"
        }}
    )

@api_router.get("/builds", response_model=List[Build])
async def get_builds(user_id: str, project_id: Optional[str] = None):
    query = {"user_id": user_id}
    if project_id:
        query["project_id"] = project_id
    
    builds = await db.builds.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    for b in builds:
        if isinstance(b.get('created_at'), str):
            b['created_at'] = datetime.fromisoformat(b['created_at'])
        if isinstance(b.get('completed_at'), str):
            b['completed_at'] = datetime.fromisoformat(b['completed_at'])
        if isinstance(b.get('started_at'), str):
            b['started_at'] = datetime.fromisoformat(b['started_at'])
    return builds

@api_router.get("/builds/{build_id}", response_model=Build)
async def get_build(build_id: str, user_id: str):
    build = await db.builds.find_one({"id": build_id, "user_id": user_id}, {"_id": 0})
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    
    if isinstance(build.get('created_at'), str):
        build['created_at'] = datetime.fromisoformat(build['created_at'])
    if isinstance(build.get('completed_at'), str):
        build['completed_at'] = datetime.fromisoformat(build['completed_at'])
    
    return build

@api_router.get("/builds/{build_id}/download")
async def download_build(build_id: str, user_id: str):
    build = await db.builds.find_one({"id": build_id, "user_id": user_id}, {"_id": 0})
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    
    if build['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Build not completed")
    
    project = await db.projects.find_one({"id": build['project_id']}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        features = project.get('features', [])
        platform = build['platform']
        
        # Add README
        readme = f"""# {project['name']} - {platform.upper()} Build

Generated by NativiWeb Studio
Build ID: {build_id}
Created: {build.get('created_at', 'N/A')}
Duration: {build.get('duration_seconds', 0)} seconds

## Contents
- /template/ - Native project template
- /sdk/ - NativiWeb JavaScript SDK
- /config/ - Configuration files

## Next Steps
1. Open the template in {'Android Studio' if platform == 'android' else 'Xcode'}
2. Configure signing certificates
3. Build and test on device
4. Publish to {'Google Play' if platform == 'android' else 'App Store'}

For documentation, visit: https://nativiweb.io/docs
"""
        zip_file.writestr('README.md', readme)
        
        # Add template
        if platform == 'android':
            zip_file.writestr('template/android-project.txt', generate_android_template(project, features))
        else:
            zip_file.writestr('template/ios-project.txt', generate_ios_template(project, features))
        
        # Add SDK
        zip_file.writestr('sdk/nativiweb-sdk.js', generate_sdk_js(project, features))
        
        # Add config
        config = {
            "project": project['name'],
            "web_url": project['web_url'],
            "platform": platform,
            "build_type": build['build_type'],
            "build_id": build_id,
            "features": [f['id'] for f in features if f.get('enabled')],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        zip_file.writestr('config/app-config.json', json.dumps(config, indent=2))
        
        # Add simulated binary placeholder
        binary_info = f"""# Simulated Build Artifact

This is a placeholder for the actual build artifact.
In production, this would be the compiled {'APK/AAB' if platform == 'android' else 'IPA'} file.

To generate real builds, you would need:
- {'Android SDK and Gradle' if platform == 'android' else 'macOS with Xcode'}
- Signing certificates
- CI/CD infrastructure (like GitHub Actions or Codemagic)

See /docs/ARCHITECTURE.md for production setup guide.
"""
        zip_file.writestr(f'artifacts/{project["name"]}.{"apk" if platform == "android" else "ipa"}.txt', binary_info)
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={project['name']}_{platform}_{build_id[:8]}.zip"}
    )

# ==================== API KEYS ENDPOINTS ====================

@api_router.post("/api-keys", response_model=APIKey)
async def create_api_key(key_data: APIKeyCreate, user_id: str):
    api_key = APIKey(
        user_id=user_id,
        name=key_data.name,
        permissions=key_data.permissions
    )
    
    key_dict = api_key.model_dump()
    key_dict['created_at'] = key_dict['created_at'].isoformat()
    
    await db.api_keys.insert_one(key_dict)
    await log_system_event("info", "api", f"API key created: {key_data.name}", user_id=user_id)
    return api_key

@api_router.get("/api-keys", response_model=List[APIKey])
async def get_api_keys(user_id: str):
    keys = await db.api_keys.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    for k in keys:
        if isinstance(k.get('created_at'), str):
            k['created_at'] = datetime.fromisoformat(k['created_at'])
        if isinstance(k.get('last_used'), str):
            k['last_used'] = datetime.fromisoformat(k['last_used'])
    return keys

@api_router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: str, user_id: str):
    result = await db.api_keys.delete_one({"id": key_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "API key deleted"}

# ==================== GENERATOR ENDPOINTS ====================

@api_router.get("/generator/sdk/{project_id}")
async def generate_sdk(project_id: str, user_id: str):
    project = await db.projects.find_one({"id": project_id, "user_id": user_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    sdk_content = generate_sdk_js(project, project.get('features', []))
    
    return StreamingResponse(
        io.BytesIO(sdk_content.encode()),
        media_type="application/javascript",
        headers={"Content-Disposition": f"attachment; filename=nativiweb-sdk.js"}
    )

@api_router.get("/generator/template/{project_id}/{platform}")
async def generate_template(project_id: str, platform: str, user_id: str):
    if platform not in ['android', 'ios']:
        raise HTTPException(status_code=400, detail="Invalid platform")
    
    project = await db.projects.find_one({"id": project_id, "user_id": user_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    features = project.get('features', [])
    
    if platform == 'android':
        content = generate_android_template(project, features)
    else:
        content = generate_ios_template(project, features)
    
    return {"template": content, "platform": platform, "project": project['name']}

# ==================== FEATURES ENDPOINT ====================

@api_router.get("/features")
async def get_available_features():
    return DEFAULT_FEATURES

# ==================== STATS ENDPOINT ====================

@api_router.get("/stats")
async def get_user_stats(user_id: str):
    projects_count = await db.projects.count_documents({"user_id": user_id})
    builds_count = await db.builds.count_documents({"user_id": user_id})
    successful_builds = await db.builds.count_documents({"user_id": user_id, "status": "completed"})
    api_keys_count = await db.api_keys.count_documents({"user_id": user_id})
    
    return {
        "projects": projects_count,
        "total_builds": builds_count,
        "successful_builds": successful_builds,
        "api_keys": api_keys_count
    }

# ==================== ADMIN ENDPOINTS ====================

@api_router.get("/admin/users")
async def admin_get_users(admin_id: str, page: int = 1, limit: int = 20):
    # Verify admin
    admin = await db.users.find_one({"id": admin_id, "role": "admin"}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    skip = (page - 1) * limit
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.users.count_documents({})
    
    for u in users:
        if isinstance(u.get('created_at'), str):
            u['created_at'] = datetime.fromisoformat(u['created_at'])
        # Add stats
        u['projects_count'] = await db.projects.count_documents({"user_id": u['id']})
        u['builds_count'] = await db.builds.count_documents({"user_id": u['id']})
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@api_router.put("/admin/users/{user_id}")
async def admin_update_user(user_id: str, admin_id: str, update_data: UserUpdate):
    # Verify admin
    admin = await db.users.find_one({"id": admin_id, "role": "admin"}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    result = await db.users.update_one({"id": user_id}, {"$set": update_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    action = "banned" if update_dict.get('status') == 'banned' else "updated"
    await log_system_event("warning", "admin", f"User {user_id} {action} by admin", user_id=admin_id)
    
    return {"message": f"User {action} successfully"}

@api_router.get("/admin/builds")
async def admin_get_builds(admin_id: str, page: int = 1, limit: int = 20, status: Optional[str] = None):
    # Verify admin
    admin = await db.users.find_one({"id": admin_id, "role": "admin"}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = {}
    if status:
        query["status"] = status
    
    skip = (page - 1) * limit
    builds = await db.builds.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.builds.count_documents(query)
    
    # Enrich with project and user info
    for b in builds:
        if isinstance(b.get('created_at'), str):
            b['created_at'] = datetime.fromisoformat(b['created_at'])
        project = await db.projects.find_one({"id": b['project_id']}, {"_id": 0, "name": 1})
        user = await db.users.find_one({"id": b['user_id']}, {"_id": 0, "name": 1, "email": 1})
        b['project_name'] = project['name'] if project else 'Unknown'
        b['user_name'] = user['name'] if user else 'Unknown'
        b['user_email'] = user['email'] if user else 'Unknown'
    
    return {
        "builds": builds,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@api_router.get("/admin/logs")
async def admin_get_logs(admin_id: str, page: int = 1, limit: int = 50, level: Optional[str] = None, category: Optional[str] = None):
    # Verify admin
    admin = await db.users.find_one({"id": admin_id, "role": "admin"}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = {}
    if level:
        query["level"] = level
    if category:
        query["category"] = category
    
    skip = (page - 1) * limit
    logs = await db.system_logs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.system_logs.count_documents(query)
    
    for log in logs:
        if isinstance(log.get('created_at'), str):
            log['created_at'] = datetime.fromisoformat(log['created_at'])
    
    return {
        "logs": logs,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@api_router.get("/admin/analytics")
async def admin_get_analytics(admin_id: str):
    # Verify admin
    admin = await db.users.find_one({"id": admin_id, "role": "admin"}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get counts
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"status": "active"})
    total_projects = await db.projects.count_documents({})
    total_builds = await db.builds.count_documents({})
    successful_builds = await db.builds.count_documents({"status": "completed"})
    failed_builds = await db.builds.count_documents({"status": "failed"})
    processing_builds = await db.builds.count_documents({"status": "processing"})
    
    # Get recent activity (last 7 days)
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    new_users_week = await db.users.count_documents({"created_at": {"$gte": week_ago}})
    new_projects_week = await db.projects.count_documents({"created_at": {"$gte": week_ago}})
    new_builds_week = await db.builds.count_documents({"created_at": {"$gte": week_ago}})
    
    # Platform distribution
    android_builds = await db.builds.count_documents({"platform": "android"})
    ios_builds = await db.builds.count_documents({"platform": "ios"})
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "new_this_week": new_users_week
        },
        "projects": {
            "total": total_projects,
            "new_this_week": new_projects_week
        },
        "builds": {
            "total": total_builds,
            "successful": successful_builds,
            "failed": failed_builds,
            "processing": processing_builds,
            "new_this_week": new_builds_week,
            "success_rate": round(successful_builds / total_builds * 100, 1) if total_builds > 0 else 0
        },
        "platforms": {
            "android": android_builds,
            "ios": ios_builds
        }
    }

@api_router.get("/admin/config")
async def admin_get_config(admin_id: str):
    # Verify admin
    admin = await db.users.find_one({"id": admin_id, "role": "admin"}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    config = await db.platform_config.find_one({"id": "platform_config"}, {"_id": 0})
    if not config:
        config = PlatformConfig().model_dump()
        config['updated_at'] = config['updated_at'].isoformat()
        await db.platform_config.insert_one(config)
    
    return config

@api_router.put("/admin/config")
async def admin_update_config(admin_id: str, config_data: dict):
    # Verify admin
    admin = await db.users.find_one({"id": admin_id, "role": "admin"}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    config_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.platform_config.update_one(
        {"id": "platform_config"},
        {"$set": config_data},
        upsert=True
    )
    
    await log_system_event("warning", "admin", "Platform configuration updated", user_id=admin_id)
    
    return {"message": "Configuration updated"}

# ==================== MAKE USER ADMIN (one-time setup) ====================

@api_router.post("/admin/setup")
async def setup_admin(email: str, secret: str):
    # Simple secret check (in production, use proper auth)
    if secret != "nativiweb_admin_setup_2024":
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    result = await db.users.update_one(
        {"email": email},
        {"$set": {"role": "admin"}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    await log_system_event("warning", "admin", f"Admin role granted to {email}")
    
    return {"message": f"Admin role granted to {email}"}

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "NativiWeb Studio API v2.0.0", "status": "operational"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include the router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
