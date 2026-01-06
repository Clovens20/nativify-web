# NativiWeb SDK Documentation

## Installation

Download the SDK from your project page in NativiWeb Studio and include it in your web application:

```html
<script src="nativiweb-sdk.js"></script>
```

Or include via CDN (coming soon):
```html
<script src="https://cdn.nativiweb.io/sdk/v1/nativiweb-sdk.js"></script>
```

## Quick Start

```javascript
// The SDK is automatically initialized and available as `NativiWeb`

// Check if running in native app
if (NativiWeb.isNative) {
  console.log('Running in native app!');
  console.log('Platform:', NativiWeb.platform); // 'android' or 'ios'
}
```

## Core Properties

| Property | Type | Description |
|----------|------|-------------|
| `NativiWeb.isNative` | boolean | True if running in native WebView |
| `NativiWeb.platform` | string | 'android', 'ios', or 'web' |
| `NativiWeb.version` | string | SDK version (e.g., '1.0.0') |

## Methods

### Device Information

```javascript
// Get device info
const info = await NativiWeb.getDeviceInfo();
// Returns: { platform: 'android', version: '14', userAgent: '...', ... }
```

### Push Notifications

```javascript
// Request notification permission
const permission = await NativiWeb.requestNotificationPermission();

// Show a notification
await NativiWeb.showNotification('New Message', {
  body: 'You have a new message from John',
  icon: '/icon.png',
  badge: '/badge.png'
});
```

### Geolocation

```javascript
// Get current position
const position = await NativiWeb.getCurrentPosition({
  enableHighAccuracy: true,
  timeout: 5000
});
console.log(position.coords.latitude, position.coords.longitude);

// Watch position changes
const watchId = NativiWeb.watchPosition((position) => {
  console.log('New position:', position);
});
```

### Camera

```javascript
// Open camera
const stream = await NativiWeb.openCamera({
  facingMode: 'environment' // or 'user' for front camera
});

// Take photo (returns base64 image)
const photo = await NativiWeb.takePhoto();
```

### Local Storage

```javascript
// Save data
await NativiWeb.setItem('user', { name: 'John', age: 30 });

// Read data
const user = await NativiWeb.getItem('user');
console.log(user); // { name: 'John', age: 30 }
```

### Biometric Authentication

```javascript
// Authenticate using biometrics (fingerprint, Face ID)
try {
  const result = await NativiWeb.authenticateWithBiometrics('Confirm your identity');
  if (result.success) {
    console.log('Authentication successful!');
  }
} catch (error) {
  console.error('Biometric auth failed:', error);
}
```

### Haptic Feedback

```javascript
// Simple vibration
await NativiWeb.vibrate(100); // 100ms

// Pattern vibration
await NativiWeb.vibrate([100, 50, 100]); // vibrate, pause, vibrate
```

### Native Share

```javascript
await NativiWeb.share({
  title: 'Check this out!',
  text: 'Amazing content from my app',
  url: 'https://myapp.com/content/123'
});
```

### Clipboard

```javascript
// Copy to clipboard
await NativiWeb.copyToClipboard('Text to copy');

// Read from clipboard
const text = await NativiWeb.readFromClipboard();
```

## Event Handling

```javascript
// Listen for native events
NativiWeb.on('push-received', (data) => {
  console.log('Push notification received:', data);
});

NativiWeb.on('app-resume', () => {
  console.log('App resumed from background');
});

NativiWeb.on('app-pause', () => {
  console.log('App going to background');
});

// Remove event listener
NativiWeb.off('push-received', handler);
```

## Error Handling

All SDK methods return Promises and should be wrapped in try-catch blocks:

```javascript
try {
  const position = await NativiWeb.getCurrentPosition();
  console.log('Position:', position);
} catch (error) {
  if (error.code === 'PERMISSION_DENIED') {
    console.error('Location permission denied');
  } else if (error.code === 'NOT_NATIVE') {
    console.error('This feature requires the native app');
  } else {
    console.error('Error:', error.message);
  }
}
```

## Feature Detection

```javascript
// Check if feature is available before using
if (NativiWeb.isNative && NativiWeb.platform === 'android') {
  // Android-specific code
}

// Check specific feature availability
const features = await NativiWeb.getDeviceInfo();
if (features.camera) {
  // Camera is available
}
```

## Best Practices

1. **Always check `isNative`** before calling native-only features
2. **Handle errors gracefully** with try-catch blocks
3. **Request permissions** before using sensitive features
4. **Provide fallbacks** for web browser usage
5. **Test on real devices** when possible

## Supported Platforms

| Feature | Android | iOS | Web (Fallback) |
|---------|---------|-----|----------------|
| Device Info | ✅ | ✅ | ✅ |
| Push Notifications | ✅ | ✅ | ✅ (Web Push) |
| Geolocation | ✅ | ✅ | ✅ |
| Camera | ✅ | ✅ | ✅ |
| Local Storage | ✅ | ✅ | ✅ |
| Biometrics | ✅ | ✅ | ❌ |
| Haptics | ✅ | ✅ | Limited |
| Share | ✅ | ✅ | ✅ (Web Share) |
| Clipboard | ✅ | ✅ | ✅ |

## Version History

### v1.0.0
- Initial release
- Support for all core native features
- Android and iOS support

---

For more information, visit [NativiWeb Studio Documentation](https://nativiweb.io/docs)
