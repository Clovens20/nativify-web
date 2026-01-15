// NativiWeb SDK v1.0.0
// Généré automatiquement pour android

(function() {
    'use strict';
    
    const NativiWeb = {
        platform: 'android',
        version: '1.0.0',
        features: [],
        
        isNative: function() {
            return typeof window.NativiWebNative !== 'undefined';
        },
        
        callNative: function(action, data) {
            if (!this.isNative()) {
                console.warn('NativiWeb: Not running in native app');
                return Promise.reject(new Error('Not native'));
            }
            
            return new Promise((resolve, reject) => {
                const callbackId = 'callback_' + Date.now() + '_' + Math.random();
                window[callbackId] = { resolve, reject };
                
                if (window.NativiWebNative && window.NativiWebNative.postMessage) {
                    window.NativiWebNative.postMessage(JSON.stringify({
                        action: action,
                        data: data || {},
                        callbackId: callbackId
                    }));
                } else {
                    reject(new Error('Native bridge not available'));
                }
                
                setTimeout(() => {
                    if (window[callbackId]) {
                        delete window[callbackId];
                        reject(new Error('Timeout'));
                    }
                }, 10000);
            });
        },
        
        vibrate: function(duration) {
            if (this.isNative()) {
                return this.callNative('vibrate', { duration: duration || 100 });
            }
        },
        
        copyToClipboard: function(text) {
            if (this.isNative()) {
                return this.callNative('copyToClipboard', { text: text });
            } else {
                return navigator.clipboard.writeText(text);
            }
        },
        
        getDeviceInfo: function() {
            if (this.isNative()) {
                return this.callNative('getDeviceInfo');
            } else {
                return Promise.resolve({
                    platform: 'web',
                    userAgent: navigator.userAgent
                });
            }
        }
    };
    
    // Exposer globalement
    window.NativiWeb = NativiWeb;
    
    // Auto-initialisation
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('NativiWeb SDK initialized on', NativiWeb.platform);
        });
    } else {
        console.log('NativiWeb SDK initialized on', NativiWeb.platform);
    }
})();
