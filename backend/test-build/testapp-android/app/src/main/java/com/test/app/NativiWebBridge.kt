package com.test.app

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationManager
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.webkit.JavascriptInterface
import android.webkit.WebView
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import org.json.JSONObject
import android.app.Activity

class NativiWebBridge(private val context: Context, private val webView: WebView) {
    private val vibrator = context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator

    @JavascriptInterface
    fun getPlatform(): String {
        return "android"
    }

    @JavascriptInterface
    fun isNative(): Boolean {
        return true
    }

    @JavascriptInterface
    fun getDeviceInfo(): String {
        val info = JSONObject().apply {
            put("platform", "android")
            put("platformVersion", Build.VERSION.RELEASE)
            put("deviceModel", Build.MODEL)
            put("manufacturer", Build.MANUFACTURER)
            put("appVersion", "1.0.0")
            put("sdkVersion", "1.0.0")
        }
        return info.toString()
    }

    @JavascriptInterface
    fun vibrate(duration: Int) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator?.vibrate(VibrationEffect.createOneShot(duration.toLong(), VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            vibrator?.vibrate(duration.toLong())
        }
    }

    @JavascriptInterface
    fun copyToClipboard(text: String) {
        val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as android.content.ClipboardManager
        val clip = android.content.ClipData.newPlainText("text", text)
        clipboard.setPrimaryClip(clip)
    }
}
