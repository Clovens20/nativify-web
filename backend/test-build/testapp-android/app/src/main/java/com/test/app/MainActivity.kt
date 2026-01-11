package com.test.app

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.WebView
import android.webkit.WebViewClient
import android.webkit.WebChromeClient
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    private lateinit var bridge: NativiWebBridge

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webView)
        
        // Configuration WebView
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.databaseEnabled = true
        webView.settings.setSupportZoom(true)
        webView.settings.builtInZoomControls = false
        webView.settings.displayZoomControls = false
        webView.settings.useWideViewPort = true
        webView.settings.loadWithOverviewMode = true
        webView.settings.mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_ALWAYS_ALLOW

        // Bridge pour communication native <-> JavaScript
        bridge = NativiWebBridge(this, webView)
        webView.addJavascriptInterface(bridge, "NativiWebNative")

        // WebViewClient pour intercepter les chargements
        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                // Injecter le SDK JavaScript
                val sdkScript = assets.open("nativiweb-sdk.js").bufferedReader().use { it.readText() }
                view?.evaluateJavascript(sdkScript, null)
            }
        }

        webView.webChromeClient = WebChromeClient()

        // Charger l'URL web
        webView.loadUrl("https://example.com")
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
