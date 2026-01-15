# NativiWeb Studio - Production Build Architecture

## 🏗 Overview

This document describes the architecture required to implement a real native build system for NativiWeb Studio, similar to Expo EAS or Codemagic.

## 📊 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NativiWeb Studio                              │
│                      (Frontend + Backend)                            │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Build Queue                                  │
│                    (Redis / RabbitMQ)                               │
└─────────────────────────────────────────────────────────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            ▼                                       ▼
┌───────────────────────┐               ┌───────────────────────┐
│   Android Build Farm   │               │    iOS Build Farm     │
│   (Linux Servers)      │               │    (macOS Servers)    │
│                        │               │                       │
│  • Docker containers   │               │  • Mac Minis/Studios  │
│  • Android SDK         │               │  • Xcode              │
│  • Gradle              │               │  • CocoaPods          │
│  • Signing keys        │               │  • Code signing       │
└───────────────────────┘               └───────────────────────┘
            │                                       │
            └───────────────────┬───────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Artifact Storage                              │
│                    (S3 / Google Cloud Storage)                       │
│                                                                      │
│  • APK files        • IPA files        • Build logs                 │
│  • AAB files        • dSYM files       • Code signing certs         │
└─────────────────────────────────────────────────────────────────────┘
```

## 🖥 Infrastructure Requirements

### Android Build Servers

```yaml
# Recommended specs per build server
CPU: 8+ cores (AMD/Intel)
RAM: 32GB minimum
Storage: 500GB SSD
OS: Ubuntu 22.04 LTS

# Required software
- Docker
- Android SDK (API 24-34)
- Gradle 8.x
- JDK 17
- Node.js 18+
```

### iOS Build Servers

```yaml
# Recommended specs
Hardware: Mac Mini M2 / Mac Studio M2
RAM: 16GB minimum
Storage: 512GB SSD
OS: macOS Sonoma 14.x

# Required software
- Xcode 15+
- CocoaPods
- Ruby 3.x
- Node.js 18+
- Fastlane
```

### Cost Estimation

| Component | Monthly Cost |
|-----------|-------------|
| 3x Linux build servers (AWS c5.2xlarge) | ~$750 |
| 2x Mac Mini M2 (MacStadium/AWS EC2 Mac) | ~$800 |
| Redis Queue (AWS ElastiCache) | ~$50 |
| S3 Storage (500GB) | ~$25 |
| CloudFront CDN | ~$50 |
| **Total** | **~$1,675/month** |

## 🔧 Build Pipeline

### 1. Build Request Flow

```
User Request → API Server → Validation → Queue → Build Worker → Artifact → Notification
```

### 2. Android Build Steps

```bash
#!/bin/bash
# android-build.sh

# 1. Setup environment
export ANDROID_HOME=/opt/android-sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

# 2. Clone/generate project
mkdir -p /builds/$BUILD_ID
cd /builds/$BUILD_ID
# Generate native project from NativiWeb template

# 3. Install dependencies
./gradlew dependencies

# 4. Build APK (debug)
./gradlew assembleDebug

# 5. Build AAB (release)
./gradlew bundleRelease

# 6. Sign the release build
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 \
    -keystore $KEYSTORE_PATH \
    -storepass $KEYSTORE_PASSWORD \
    app/build/outputs/bundle/release/app-release.aab \
    $KEY_ALIAS

# 7. Upload artifacts
aws s3 cp app/build/outputs/ s3://nativiweb-builds/$BUILD_ID/ --recursive
```

### 3. iOS Build Steps

```bash
#!/bin/bash
# ios-build.sh

# 1. Setup environment
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer

# 2. Install certificates
security create-keychain -p "" build.keychain
security import $P12_PATH -k build.keychain -P "$P12_PASSWORD" -T /usr/bin/codesign
security set-keychain-settings build.keychain
security unlock-keychain -p "" build.keychain

# 3. Install provisioning profile
mkdir -p ~/Library/MobileDevice/Provisioning\ Profiles
cp $PROVISIONING_PROFILE ~/Library/MobileDevice/Provisioning\ Profiles/

# 4. Install CocoaPods
cd /builds/$BUILD_ID
pod install

# 5. Build archive
xcodebuild -workspace App.xcworkspace \
    -scheme App \
    -configuration Release \
    -archivePath build/App.xcarchive \
    archive

# 6. Export IPA
xcodebuild -exportArchive \
    -archivePath build/App.xcarchive \
    -exportPath build/ \
    -exportOptionsPlist ExportOptions.plist

# 7. Upload artifacts
aws s3 cp build/ s3://nativiweb-builds/$BUILD_ID/ --recursive
```

## 🔐 Code Signing

### Android Signing

```kotlin
// build.gradle.kts
android {
    signingConfigs {
        create("release") {
            storeFile = file(System.getenv("KEYSTORE_PATH"))
            storePassword = System.getenv("KEYSTORE_PASSWORD")
            keyAlias = System.getenv("KEY_ALIAS")
            keyPassword = System.getenv("KEY_PASSWORD")
        }
    }
    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
        }
    }
}
```

### iOS Signing with Fastlane

```ruby
# Fastfile
default_platform(:ios)

platform :ios do
  desc "Build and sign IPA"
  lane :build do
    setup_ci if is_ci
    
    match(
      type: "appstore",
      app_identifier: ENV["BUNDLE_ID"],
      readonly: true
    )
    
    build_app(
      workspace: "App.xcworkspace",
      scheme: "App",
      export_method: "app-store",
      output_directory: "./build",
      output_name: "App.ipa"
    )
  end
end
```

## 📁 Project Structure for CI/CD

```
/nativiweb-build-system
├── /workers
│   ├── android-worker/
│   │   ├── Dockerfile
│   │   ├── build.sh
│   │   └── config.yaml
│   └── ios-worker/
│       ├── build.sh
│       ├── Fastfile
│       └── Matchfile
├── /queue
│   ├── redis.conf
│   └── worker-manager.py
├── /api
│   ├── build-api.py
│   └── webhook-handler.py
├── /storage
│   ├── s3-config.yaml
│   └── artifact-manager.py
└── /monitoring
    ├── prometheus.yml
    └── grafana-dashboards/
```

## 🐳 Docker Configuration

### Android Build Docker

```dockerfile
# Dockerfile.android
FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    wget \
    unzip \
    git \
    curl

# Install Android SDK
ENV ANDROID_HOME=/opt/android-sdk
RUN mkdir -p ${ANDROID_HOME}/cmdline-tools && \
    wget https://dl.google.com/android/repository/commandlinetools-linux-latest.zip && \
    unzip commandlinetools-linux-latest.zip -d ${ANDROID_HOME}/cmdline-tools && \
    mv ${ANDROID_HOME}/cmdline-tools/cmdline-tools ${ANDROID_HOME}/cmdline-tools/latest

# Accept licenses and install SDK components
RUN yes | ${ANDROID_HOME}/cmdline-tools/latest/bin/sdkmanager --licenses && \
    ${ANDROID_HOME}/cmdline-tools/latest/bin/sdkmanager \
    "platform-tools" \
    "platforms;android-34" \
    "build-tools;34.0.0"

# Install Gradle
RUN wget https://services.gradle.org/distributions/gradle-8.5-bin.zip && \
    unzip gradle-8.5-bin.zip -d /opt && \
    ln -s /opt/gradle-8.5/bin/gradle /usr/local/bin/gradle

WORKDIR /build
COPY build.sh /build/
ENTRYPOINT ["/build/build.sh"]
```

## 🔄 Queue System

### Redis Queue Configuration

```python
# worker-manager.py
import redis
import json
from rq import Queue, Worker

redis_conn = redis.Redis(host='redis', port=6379, db=0)

# Create queues for each platform
android_queue = Queue('android_builds', connection=redis_conn)
ios_queue = Queue('ios_builds', connection=redis_conn)

def enqueue_build(build_request):
    """Add build to appropriate queue"""
    platform = build_request['platform']
    
    if platform == 'android':
        job = android_queue.enqueue(
            'workers.android.build',
            build_request,
            job_timeout='30m',
            result_ttl=86400
        )
    elif platform == 'ios':
        job = ios_queue.enqueue(
            'workers.ios.build',
            build_request,
            job_timeout='45m',
            result_ttl=86400
        )
    
    return job.id

def get_build_status(job_id):
    """Get status of a build job"""
    job = Job.fetch(job_id, connection=redis_conn)
    return {
        'status': job.get_status(),
        'progress': job.meta.get('progress', 0),
        'logs': job.meta.get('logs', [])
    }
```

## 📱 Store Submission

### Google Play Store API

```python
# play_store_api.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_to_play_store(aab_path, package_name, track='internal'):
    """Upload AAB to Google Play Store"""
    credentials = service_account.Credentials.from_service_account_file(
        'play-store-credentials.json',
        scopes=['https://www.googleapis.com/auth/androidpublisher']
    )
    
    service = build('androidpublisher', 'v3', credentials=credentials)
    
    # Create new edit
    edit = service.edits().insert(
        packageName=package_name,
        body={}
    ).execute()
    
    # Upload AAB
    media = MediaFileUpload(aab_path, mimetype='application/octet-stream')
    bundle = service.edits().bundles().upload(
        packageName=package_name,
        editId=edit['id'],
        media_body=media
    ).execute()
    
    # Assign to track
    service.edits().tracks().update(
        packageName=package_name,
        editId=edit['id'],
        track=track,
        body={'releases': [{'versionCodes': [bundle['versionCode']], 'status': 'completed'}]}
    ).execute()
    
    # Commit edit
    service.edits().commit(
        packageName=package_name,
        editId=edit['id']
    ).execute()
    
    return bundle['versionCode']
```

### App Store Connect API

```python
# app_store_api.py
import jwt
import time
import requests

class AppStoreConnectAPI:
    def __init__(self, key_id, issuer_id, private_key_path):
        self.key_id = key_id
        self.issuer_id = issuer_id
        with open(private_key_path, 'r') as f:
            self.private_key = f.read()
    
    def _generate_token(self):
        """Generate JWT for App Store Connect API"""
        header = {
            'alg': 'ES256',
            'kid': self.key_id,
            'typ': 'JWT'
        }
        payload = {
            'iss': self.issuer_id,
            'iat': int(time.time()),
            'exp': int(time.time()) + 1200,
            'aud': 'appstoreconnect-v1'
        }
        return jwt.encode(payload, self.private_key, algorithm='ES256', headers=header)
    
    def upload_ipa(self, ipa_path, app_id):
        """Upload IPA using Transporter or altool"""
        # Use xcrun altool or Transporter CLI
        import subprocess
        
        result = subprocess.run([
            'xcrun', 'altool', '--upload-app',
            '-f', ipa_path,
            '-t', 'ios',
            '-u', os.environ['APPLE_ID'],
            '-p', os.environ['APP_SPECIFIC_PASSWORD']
        ], capture_output=True, text=True)
        
        return result.returncode == 0
```

## 🔒 Security Considerations

1. **Certificate Storage**: Use encrypted storage (AWS KMS, HashiCorp Vault)
2. **Build Isolation**: Each build runs in isolated container/VM
3. **Network Security**: Build servers in private subnet with NAT gateway
4. **Access Control**: Role-based access for certificate management
5. **Audit Logging**: Track all certificate usage and build activities

## 📈 Monitoring & Alerts

### Prometheus Metrics

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'build-workers'
    static_configs:
      - targets: ['android-worker-1:9090', 'android-worker-2:9090']
      
  - job_name: 'queue'
    static_configs:
      - targets: ['redis:9121']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - 'alerts/*.yml'
```

### Key Metrics to Monitor

- Build queue length
- Build success/failure rate
- Average build duration
- Worker availability
- Storage usage
- Certificate expiration dates

## 🚀 Getting Started

1. Set up infrastructure (AWS/GCP/Azure)
2. Deploy Redis queue
3. Configure Android build workers
4. Set up macOS build machines
5. Configure S3/GCS for artifact storage
6. Set up monitoring
7. Integrate with NativiWeb Studio API

## 📚 References

- [Expo EAS Build Architecture](https://docs.expo.dev/build/introduction/)
- [Codemagic Documentation](https://docs.codemagic.io/)
- [Fastlane Documentation](https://docs.fastlane.tools/)
- [Google Play Developer API](https://developers.google.com/android-publisher)
- [App Store Connect API](https://developer.apple.com/documentation/appstoreconnectapi)
