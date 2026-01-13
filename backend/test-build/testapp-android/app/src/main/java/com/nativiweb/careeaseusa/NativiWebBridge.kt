package com.nativiweb.careeaseusa

import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.content.Context
import android.widget.Toast
import android.util.Log
import org.json.JSONObject

class NativiWebBridge(
    private val context: Context,
    private val webView: WebView
) {
    private val TAG = "NativiWebBridge"

    /**
     * Affiche un toast natif
     */
    @JavascriptInterface
    fun showToast(message: String) {
        try {
            context.mainExecutor.execute {
                Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
            }
            Log.d(TAG, "Toast displayed: $message")
        } catch (e: Exception) {
            Log.e(TAG, "Error showing toast", e)
        }
    }

    /**
     * Affiche un toast long
     */
    @JavascriptInterface
    fun showLongToast(message: String) {
        try {
            context.mainExecutor.execute {
                Toast.makeText(context, message, Toast.LENGTH_LONG).show()
            }
            Log.d(TAG, "Long toast displayed: $message")
        } catch (e: Exception) {
            Log.e(TAG, "Error showing long toast", e)
        }
    }

    /**
     * Log un message dans le logcat Android
     */
    @JavascriptInterface
    fun log(message: String) {
        Log.d(TAG, "JS Log: $message")
    }

    /**
     * Log une erreur dans le logcat Android
     */
    @JavascriptInterface
    fun logError(message: String) {
        Log.e(TAG, "JS Error: $message")
    }

    /**
     * Retourne des informations sur l'appareil
     */
    @JavascriptInterface
    fun getDeviceInfo(): String {
        return try {
            val deviceInfo = JSONObject().apply {
                put("model", android.os.Build.MODEL)
                put("manufacturer", android.os.Build.MANUFACTURER)
                put("androidVersion", android.os.Build.VERSION.RELEASE)
                put("sdkVersion", android.os.Build.VERSION.SDK_INT)
                put("brand", android.os.Build.BRAND)
            }
            deviceInfo.toString()
        } catch (e: Exception) {
            Log.e(TAG, "Error getting device info", e)
            JSONObject().apply {
                put("error", e.message ?: "Unknown error")
            }.toString()
        }
    }

    /**
     * Vérifie si l'application est en mode debug
     */
    @JavascriptInterface
    fun isDebugMode(): Boolean {
        return android.os.Build.TYPE == "userdebug" || android.os.Build.TYPE == "eng"
    }

    /**
     * Exécute du JavaScript dans le WebView
     */
    fun executeJavaScript(script: String) {
        try {
            webView.post {
                webView.evaluateJavascript(script, null)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error executing JavaScript", e)
        }
    }

    /**
     * Envoie un événement au JavaScript
     */
    fun sendEventToJS(eventName: String, data: JSONObject) {
        try {
            val script = """
                (function() {
                    if (window.NativiWeb && window.NativiWeb.handleNativeEvent) {
                        window.NativiWeb.handleNativeEvent('$eventName', $data);
                    }
                })();
            """.trimIndent()
            executeJavaScript(script)
        } catch (e: Exception) {
            Log.e(TAG, "Error sending event to JS", e)
        }
    }

    /**
     * Callback pour les requêtes asynchrones
     */
    @JavascriptInterface
    fun callback(callbackId: String, result: String) {
        try {
            val script = """
                (function() {
                    if (window.NativiWeb && window.NativiWeb.handleCallback) {
                        window.NativiWeb.handleCallback('$callbackId', $result);
                    }
                })();
            """.trimIndent()
            executeJavaScript(script)
        } catch (e: Exception) {
            Log.e(TAG, "Error executing callback", e)
        }
    }

    /**
     * Retourne la version de l'application
     */
    @JavascriptInterface
    fun getAppVersion(): String {
        return try {
            val packageInfo = context.packageManager.getPackageInfo(context.packageName, 0)
            JSONObject().apply {
                put("versionName", packageInfo.versionName)
                put("versionCode", packageInfo.longVersionCode)
            }.toString()
        } catch (e: Exception) {
            Log.e(TAG, "Error getting app version", e)
            JSONObject().apply {
                put("error", e.message ?: "Unknown error")
            }.toString()
        }
    }

    /**
     * Vérifie si une permission est accordée
     */
    @JavascriptInterface
    fun hasPermission(permission: String): Boolean {
        return try {
            context.checkSelfPermission(permission) == android.content.pm.PackageManager.PERMISSION_GRANTED
        } catch (e: Exception) {
            Log.e(TAG, "Error checking permission: $permission", e)
            false
        }
    }

    /**
     * Ouvre les paramètres de l'application
     */
    @JavascriptInterface
    fun openAppSettings() {
        try {
            val intent = android.content.Intent(
                android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                android.net.Uri.fromParts("package", context.packageName, null)
            )
            intent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(intent)
        } catch (e: Exception) {
            Log.e(TAG, "Error opening app settings", e)
        }
    }

    /**
     * Copie du texte dans le presse-papier
     */
    @JavascriptInterface
    fun copyToClipboard(text: String) {
        try {
            val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as android.content.ClipboardManager
            val clip = android.content.ClipData.newPlainText("NativiWeb", text)
            clipboard.setPrimaryClip(clip)
            showToast("Copié dans le presse-papier")
        } catch (e: Exception) {
            Log.e(TAG, "Error copying to clipboard", e)
        }
    }

    /**
     * Vibre l'appareil
     */
    @JavascriptInterface
    fun vibrate(duration: Int) {
        try {
            val vibrator = context.getSystemService(Context.VIBRATOR_SERVICE) as android.os.Vibrator
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                vibrator.vibrate(
                    android.os.VibrationEffect.createOneShot(
                        duration.toLong(),
                        android.os.VibrationEffect.DEFAULT_AMPLITUDE
                    )
                )
            } else {
                @Suppress("DEPRECATION")
                vibrator.vibrate(duration.toLong())
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error vibrating device", e)
        }
    }
}

