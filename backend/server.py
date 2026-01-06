from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks
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
from datetime import datetime, timezone
import json
import io
import zipfile
import hashlib
import secrets

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
    version="1.0.0"
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

class BuildCreate(BaseModel):
    project_id: str
    platform: str
    build_type: str = "debug"

class Build(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    user_id: str
    platform: str
    build_type: str
    status: str = "pending"
    progress: int = 0
    logs: List[str] = []
    download_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

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

# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

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
    
    permissions = []
    for f in enabled_features:
        if f['id'] in feature_permissions:
            permissions.append(feature_permissions[f['id']])
    
    manifest_permissions = "\n".join([f'    <uses-permission android:name="android.permission.{p}" />' for p in permissions])
    
    return f'''// NativiWeb Android Template
// Project: {project['name']}
// Generated: {datetime.now(timezone.utc).isoformat()}

// === AndroidManifest.xml ===
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.nativiweb.{project['name'].lower().replace(' ', '_')}">
    
{manifest_permissions}
    
    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="{project['name']}"
        android:theme="@style/AppTheme">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>

// === build.gradle (app) ===
plugins {{
    id 'com.android.application'
    id 'kotlin-android'
}}

android {{
    compileSdk 34
    defaultConfig {{
        applicationId "com.nativiweb.{project['name'].lower().replace(' ', '_')}"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0"
    }}
    buildTypes {{
        release {{
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }}
    }}
}}

dependencies {{
    implementation 'androidx.core:core-ktx:1.12.0'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.11.0'
    implementation 'androidx.webkit:webkit:1.9.0'
}}

// === MainActivity.kt ===
package com.nativiweb.{project['name'].lower().replace(' ', '_')}

import android.os.Bundle
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {{
    private lateinit var webView: WebView
    
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        webView = findViewById(R.id.webView)
        webView.webViewClient = WebViewClient()
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        
        // Load the web app
        webView.loadUrl("{project['web_url']}")
        
        // Initialize NativiWeb SDK bridge
        initNativeWebBridge()
    }}
    
    private fun initNativeWebBridge() {{
        webView.addJavascriptInterface(NativiWebBridge(this), "NativiWebNative")
    }}
}}

// === NativiWebBridge.kt ===
package com.nativiweb.{project['name'].lower().replace(' ', '_')}

import android.content.Context
import android.webkit.JavascriptInterface

class NativiWebBridge(private val context: Context) {{
    
    @JavascriptInterface
    fun getDeviceInfo(): String {{
        return "{{\\\"platform\\\": \\\"android\\\", \\\"version\\\": \\\"${{android.os.Build.VERSION.RELEASE}}\\\"}}"
    }}
    
    @JavascriptInterface
    fun vibrate(duration: Long) {{
        // Haptic feedback implementation
    }}
    
    @JavascriptInterface
    fun showNotification(title: String, body: String) {{
        // Push notification implementation
    }}
}}
'''

def generate_ios_template(project: dict, features: list) -> str:
    """Generate iOS project structure as string"""
    enabled_features = [f for f in features if f.get('enabled', False)]
    
    privacy_keys = []
    for f in enabled_features:
        if f['id'] == 'camera':
            privacy_keys.append('<key>NSCameraUsageDescription</key>\n<string>This app needs camera access</string>')
        if f['id'] == 'geolocation':
            privacy_keys.append('<key>NSLocationWhenInUseUsageDescription</key>\n<string>This app needs location access</string>')
        if f['id'] == 'contacts':
            privacy_keys.append('<key>NSContactsUsageDescription</key>\n<string>This app needs contacts access</string>')
    
    privacy_section = "\n".join(privacy_keys)
    
    return f'''// NativiWeb iOS Template
// Project: {project['name']}
// Generated: {datetime.now(timezone.utc).isoformat()}

// === Info.plist ===
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>{project['name']}</string>
    <key>CFBundleIdentifier</key>
    <string>com.nativiweb.{project['name'].lower().replace(' ', '_')}</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    {privacy_section}
</dict>
</plist>

// === ContentView.swift ===
import SwiftUI
import WebKit

struct ContentView: View {{
    var body: some View {{
        WebView(url: URL(string: "{project['web_url']}")!)
            .edgesIgnoringSafeArea(.all)
    }}
}}

struct WebView: UIViewRepresentable {{
    let url: URL
    
    func makeUIView(context: Context) -> WKWebView {{
        let config = WKWebViewConfiguration()
        config.userContentController.add(context.coordinator, name: "NativiWebNative")
        
        let webView = WKWebView(frame: .zero, configuration: config)
        webView.load(URLRequest(url: url))
        return webView
    }}
    
    func updateUIView(_ webView: WKWebView, context: Context) {{}}
    
    func makeCoordinator() -> Coordinator {{
        Coordinator()
    }}
    
    class Coordinator: NSObject, WKScriptMessageHandler {{
        func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {{
            // Handle messages from JavaScript
            print("Received message: \\(message.body)")
        }}
    }}
}}

// === NativiWebApp.swift ===
import SwiftUI

@main
struct NativiWebApp: App {{
    var body: some Scene {{
        WindowGroup {{
            ContentView()
        }}
    }}
}}

// === project.pbxproj (simplified) ===
// Xcode project configuration would go here
// This is a template - actual .xcodeproj needs Xcode to generate
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
 */

(function(global) {{
  'use strict';

  const ENABLED_FEATURES = {json.dumps(feature_ids)};
  
  class NativiWeb {{
    constructor() {{
      this.platform = this._detectPlatform();
      this.isNative = this._checkNativeEnvironment();
      this.version = '1.0.0';
      this._eventHandlers = {{}};
      
      if (this.isNative) {{
        this._initBridge();
      }}
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
      window.addEventListener('NativiWebEvent', (e) => {{
        const {{ type, data }} = e.detail;
        if (this._eventHandlers[type]) {{
          this._eventHandlers[type].forEach(handler => handler(data));
        }}
      }});
    }}
    
    _callNative(method, params = {{}}) {{
      return new Promise((resolve, reject) => {{
        if (!this.isNative) {{
          reject(new Error('Not running in native environment'));
          return;
        }}
        
        try {{
          if (this.platform === 'android' && window.NativiWebNative) {{
            const result = window.NativiWebNative[method](JSON.stringify(params));
            resolve(JSON.parse(result || '{{}}'));
          }} else if (this.platform === 'ios' && window.webkit?.messageHandlers?.NativiWebNative) {{
            window.webkit.messageHandlers.NativiWebNative.postMessage({{
              method,
              params,
              callbackId: Date.now()
            }});
            resolve({{}});
          }}
        }} catch (error) {{
          reject(error);
        }}
      }});
    }}
    
    on(event, handler) {{
      if (!this._eventHandlers[event]) {{
        this._eventHandlers[event] = [];
      }}
      this._eventHandlers[event].push(handler);
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
        online: navigator.onLine
      }};
    }}
    
    // ==================== PUSH NOTIFICATIONS ====================
    {'async requestNotificationPermission() {' if 'push_notifications' in feature_ids else '// Push notifications not enabled'}
    {'  if (this.isNative) {' if 'push_notifications' in feature_ids else ''}
    {'    return this._callNative("requestNotificationPermission");' if 'push_notifications' in feature_ids else ''}
    {'  }' if 'push_notifications' in feature_ids else ''}
    {'  return Notification.requestPermission();' if 'push_notifications' in feature_ids else ''}
    {'}' if 'push_notifications' in feature_ids else ''}
    
    {'async showNotification(title, options = {}) {' if 'push_notifications' in feature_ids else ''}
    {'  if (this.isNative) {' if 'push_notifications' in feature_ids else ''}
    {'    return this._callNative("showNotification", { title, ...options });' if 'push_notifications' in feature_ids else ''}
    {'  }' if 'push_notifications' in feature_ids else ''}
    {'  return new Notification(title, options);' if 'push_notifications' in feature_ids else ''}
    {'}' if 'push_notifications' in feature_ids else ''}
    
    // ==================== CAMERA ====================
    {'async openCamera(options = {}) {' if 'camera' in feature_ids else '// Camera not enabled'}
    {'  if (this.isNative) {' if 'camera' in feature_ids else ''}
    {'    return this._callNative("openCamera", options);' if 'camera' in feature_ids else ''}
    {'  }' if 'camera' in feature_ids else ''}
    {'  // Fallback to HTML5 camera' if 'camera' in feature_ids else ''}
    {'  return navigator.mediaDevices.getUserMedia({ video: true });' if 'camera' in feature_ids else ''}
    {'}' if 'camera' in feature_ids else ''}
    
    {'async takePhoto() {' if 'camera' in feature_ids else ''}
    {'  return this._callNative("takePhoto");' if 'camera' in feature_ids else ''}
    {'}' if 'camera' in feature_ids else ''}
    
    // ==================== GEOLOCATION ====================
    {'async getCurrentPosition(options = {}) {' if 'geolocation' in feature_ids else '// Geolocation not enabled'}
    {'  if (this.isNative) {' if 'geolocation' in feature_ids else ''}
    {'    return this._callNative("getCurrentPosition", options);' if 'geolocation' in feature_ids else ''}
    {'  }' if 'geolocation' in feature_ids else ''}
    {'  return new Promise((resolve, reject) => {' if 'geolocation' in feature_ids else ''}
    {'    navigator.geolocation.getCurrentPosition(resolve, reject, options);' if 'geolocation' in feature_ids else ''}
    {'  });' if 'geolocation' in feature_ids else ''}
    {'}' if 'geolocation' in feature_ids else ''}
    
    {'watchPosition(callback, options = {}) {' if 'geolocation' in feature_ids else ''}
    {'  return navigator.geolocation.watchPosition(callback, console.error, options);' if 'geolocation' in feature_ids else ''}
    {'}' if 'geolocation' in feature_ids else ''}
    
    // ==================== LOCAL STORAGE ====================
    {'async setItem(key, value) {' if 'local_storage' in feature_ids else '// Local storage not enabled'}
    {'  if (this.isNative) {' if 'local_storage' in feature_ids else ''}
    {'    return this._callNative("setStorageItem", { key, value: JSON.stringify(value) });' if 'local_storage' in feature_ids else ''}
    {'  }' if 'local_storage' in feature_ids else ''}
    {'  localStorage.setItem(key, JSON.stringify(value));' if 'local_storage' in feature_ids else ''}
    {'}' if 'local_storage' in feature_ids else ''}
    
    {'async getItem(key) {' if 'local_storage' in feature_ids else ''}
    {'  if (this.isNative) {' if 'local_storage' in feature_ids else ''}
    {'    const result = await this._callNative("getStorageItem", { key });' if 'local_storage' in feature_ids else ''}
    {'    return result.value ? JSON.parse(result.value) : null;' if 'local_storage' in feature_ids else ''}
    {'  }' if 'local_storage' in feature_ids else ''}
    {'  const item = localStorage.getItem(key);' if 'local_storage' in feature_ids else ''}
    {'  return item ? JSON.parse(item) : null;' if 'local_storage' in feature_ids else ''}
    {'}' if 'local_storage' in feature_ids else ''}
    
    // ==================== HAPTICS ====================
    {'async vibrate(pattern = 100) {' if 'haptics' in feature_ids else '// Haptics not enabled'}
    {'  if (this.isNative) {' if 'haptics' in feature_ids else ''}
    {'    return this._callNative("vibrate", { pattern });' if 'haptics' in feature_ids else ''}
    {'  }' if 'haptics' in feature_ids else ''}
    {'  navigator.vibrate?.(pattern);' if 'haptics' in feature_ids else ''}
    {'}' if 'haptics' in feature_ids else ''}
    
    // ==================== SHARE ====================
    {'async share(data) {' if 'share' in feature_ids else '// Share not enabled'}
    {'  if (this.isNative) {' if 'share' in feature_ids else ''}
    {'    return this._callNative("share", data);' if 'share' in feature_ids else ''}
    {'  }' if 'share' in feature_ids else ''}
    {'  return navigator.share?.(data);' if 'share' in feature_ids else ''}
    {'}' if 'share' in feature_ids else ''}
    
    // ==================== BIOMETRICS ====================
    {'async authenticateWithBiometrics(reason = "Authenticate") {' if 'biometrics' in feature_ids else '// Biometrics not enabled'}
    {'  if (!this.isNative) {' if 'biometrics' in feature_ids else ''}
    {'    throw new Error("Biometrics only available in native app");' if 'biometrics' in feature_ids else ''}
    {'  }' if 'biometrics' in feature_ids else ''}
    {'  return this._callNative("authenticateBiometric", { reason });' if 'biometrics' in feature_ids else ''}
    {'}' if 'biometrics' in feature_ids else ''}
    
    // ==================== CLIPBOARD ====================
    {'async copyToClipboard(text) {' if 'clipboard' in feature_ids else '// Clipboard not enabled'}
    {'  if (this.isNative) {' if 'clipboard' in feature_ids else ''}
    {'    return this._callNative("copyToClipboard", { text });' if 'clipboard' in feature_ids else ''}
    {'  }' if 'clipboard' in feature_ids else ''}
    {'  return navigator.clipboard.writeText(text);' if 'clipboard' in feature_ids else ''}
    {'}' if 'clipboard' in feature_ids else ''}
    
    {'async readFromClipboard() {' if 'clipboard' in feature_ids else ''}
    {'  if (this.isNative) {' if 'clipboard' in feature_ids else ''}
    {'    return this._callNative("readFromClipboard");' if 'clipboard' in feature_ids else ''}
    {'  }' if 'clipboard' in feature_ids else ''}
    {'  return navigator.clipboard.readText();' if 'clipboard' in feature_ids else ''}
    {'}' if 'clipboard' in feature_ids else ''}
  }}
  
  // Export
  global.NativiWeb = new NativiWeb();
  
  if (typeof module !== 'undefined' && module.exports) {{
    module.exports = global.NativiWeb;
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
        name=user_data.name
    )
    user_dict = user.model_dump()
    user_dict['password_hash'] = hash_password(user_data.password)
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    return user

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if user.get('password_hash') != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate simple token (in production, use JWT)
    token = secrets.token_hex(32)
    await db.sessions.insert_one({
        "token": token,
        "user_id": user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "token": token,
        "user": {
            "id": user['id'],
            "email": user['email'],
            "name": user['name']
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
    return {"message": "Project deleted"}

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
        status="processing",
        logs=["Build started..."]
    )
    
    build_dict = build.model_dump()
    build_dict['created_at'] = build_dict['created_at'].isoformat()
    
    await db.builds.insert_one(build_dict)
    
    # Simulate build process
    background_tasks.add_task(process_build, build.id, project)
    
    return build

async def process_build(build_id: str, project: dict):
    """Simulate build processing"""
    import asyncio
    
    logs = [
        "Initializing build environment...",
        "Fetching web app content...",
        "Generating native project structure...",
        "Configuring native features...",
        "Compiling resources...",
        "Packaging application...",
        "Build completed successfully!"
    ]
    
    for i, log in enumerate(logs):
        await asyncio.sleep(1)
        progress = int((i + 1) / len(logs) * 100)
        await db.builds.update_one(
            {"id": build_id},
            {"$push": {"logs": log}, "$set": {"progress": progress}}
        )
    
    await db.builds.update_one(
        {"id": build_id},
        {"$set": {
            "status": "completed",
            "progress": 100,
            "completed_at": datetime.now(timezone.utc).isoformat(),
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
        
        if build['platform'] == 'android':
            zip_file.writestr('android/README.md', f"# {project['name']} - Android\n\nGenerated by NativiWeb Studio")
            zip_file.writestr('android/template.txt', generate_android_template(project, features))
        else:
            zip_file.writestr('ios/README.md', f"# {project['name']} - iOS\n\nGenerated by NativiWeb Studio")
            zip_file.writestr('ios/template.txt', generate_ios_template(project, features))
        
        zip_file.writestr('sdk/nativiweb-sdk.js', generate_sdk_js(project, features))
        zip_file.writestr('config/app-config.json', json.dumps({
            "project": project['name'],
            "web_url": project['web_url'],
            "platform": build['platform'],
            "features": [f['id'] for f in features if f.get('enabled')]
        }, indent=2))
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={project['name']}_{build['platform']}.zip"}
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

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "NativiWeb Studio API v1.0.0", "status": "operational"}

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
