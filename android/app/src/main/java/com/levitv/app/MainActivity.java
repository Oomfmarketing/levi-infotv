package com.levitv.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

/**
 * LeviTV for Android TV: shows levitv.com full screen in a WebView.
 * OK / Menu on the remote opens settings (location, layout, start on boot).
 */
public class MainActivity extends Activity {

    static final String SITE = "https://levitv.com/";
    static final String PREFS = "levitv";
    static final String[] LOC_KEYS = {"levi", "yllas", "helsinki"};
    static final String[] LOC_NAMES = {"Levi", "Ylläs", "Helsinki"};
    static final String[] VIEW_NAMES = {"Full screen (camera + sidebar)", "Info TV (large camera)"};

    private static final long RELOAD_EVERY_MS = 6L * 60 * 60 * 1000;   // fresh page every 6 h
    private static final long RETRY_MS = 30_000;                       // after a network error

    private WebView web;
    private SharedPreferences prefs;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private long lastBack = 0;

    private final Runnable periodicReload = new Runnable() {
        @Override public void run() {
            load();
            handler.postDelayed(this, RELOAD_EVERY_MS);
        }
    };
    private final Runnable retry = this::load;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);

        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
                | WindowManager.LayoutParams.FLAG_FULLSCREEN);

        web = new WebView(this);
        web.setBackgroundColor(Color.rgb(5, 8, 15));
        web.setFocusable(true);
        setContentView(web);
        hideSystemUi();

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);   // muted camera streams autoplay
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setUserAgentString(s.getUserAgentString() + " LeviTV-AndroidTV/" + appVersion());

        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return !isAllowed(request.getUrl());   // stay on LeviTV; ad links can't open on a TV
            }

            @Override
            @SuppressWarnings("deprecation")
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return !isAllowed(Uri.parse(url));
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) showOffline();
            }

            @Override
            @SuppressWarnings("deprecation")
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                if (failingUrl != null && failingUrl.startsWith(SITE)) showOffline();
            }
        });

        load();
        handler.postDelayed(periodicReload, RELOAD_EVERY_MS);

        if (!prefs.getBoolean("seenHint", false)) {
            Toast.makeText(this, "Press OK or Menu for settings", Toast.LENGTH_LONG).show();
            prefs.edit().putBoolean("seenHint", true).apply();
        }
    }

    private boolean isAllowed(Uri u) {
        String host = u.getHost() == null ? "" : u.getHost();
        return host.equals("levitv.com") || host.endsWith(".levitv.com")
                || host.endsWith("youtube.com") || host.endsWith("youtube-nocookie.com");
    }

    /** levitv.com/<loc>/full/?screen=atv-xxxxxx  or  levitv.com/<loc>/?view=tv&screen=… */
    private String url() {
        String loc = prefs.getString("loc", "levi");
        boolean full = prefs.getInt("view", 0) == 0;
        String screen = prefs.getString("screen", null);
        if (screen == null) {
            String id = Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID);
            screen = "atv-" + (id == null ? "tv" : id.substring(0, Math.min(6, id.length())));
            prefs.edit().putString("screen", screen).apply();
        }
        return SITE + loc + "/" + (full ? "full/?" : "?view=tv&") + "screen=" + Uri.encode(screen) + "&app=androidtv";
    }

    private void load() {
        handler.removeCallbacks(retry);
        web.loadUrl(url());
    }

    private void showOffline() {
        String html = "<html><body style='margin:0;background:#05080f;color:#c9d6e3;font-family:sans-serif;"
                + "display:flex;align-items:center;justify-content:center;height:100vh;text-align:center'>"
                + "<div><div style='font-size:48px;font-weight:800;letter-spacing:6px;color:#fff'>LEVI<span style='color:#5fb4ff'>TV</span></div>"
                + "<p style='font-size:22px'>No connection — retrying in 30 seconds…</p></div></body></html>";
        web.loadDataWithBaseURL(null, html, "text/html", "utf-8", null);
        handler.removeCallbacks(retry);
        handler.postDelayed(retry, RETRY_MS);
    }

    // ── Remote control ───────────────────────────────────────────────
    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        switch (keyCode) {
            case KeyEvent.KEYCODE_MENU:
            case KeyEvent.KEYCODE_DPAD_CENTER:
            case KeyEvent.KEYCODE_ENTER:
            case KeyEvent.KEYCODE_SETTINGS:
                showMenu();
                return true;
            case KeyEvent.KEYCODE_BACK:
                long now = System.currentTimeMillis();
                if (now - lastBack < 2500) { finish(); return true; }
                lastBack = now;
                Toast.makeText(this, "Press Back again to exit", Toast.LENGTH_SHORT).show();
                return true;
            default:
                return super.onKeyDown(keyCode, event);
        }
    }

    private void showMenu() {
        int locIdx = indexOf(LOC_KEYS, prefs.getString("loc", "levi"));
        boolean boot = prefs.getBoolean("autostart", true);
        String[] items = {
                "Location: " + LOC_NAMES[locIdx],
                "Layout: " + VIEW_NAMES[prefs.getInt("view", 0)],
                "Start on boot: " + (boot ? "On" : "Off"),
                "Reload",
                "Screen name: " + prefs.getString("screen", "-"),
                "Exit LeviTV"
        };
        new AlertDialog.Builder(this)
                .setTitle("LeviTV  ·  v" + appVersion())
                .setItems(items, (d, which) -> {
                    switch (which) {
                        case 0: chooseLocation(); break;
                        case 1: chooseView(); break;
                        case 2: prefs.edit().putBoolean("autostart", !boot).apply();
                                Toast.makeText(this, "Start on boot: " + (!boot ? "On" : "Off"), Toast.LENGTH_SHORT).show();
                                break;
                        case 3: load(); break;
                        case 4: Toast.makeText(this, "This screen appears in analytics as \""
                                + prefs.getString("screen", "-") + "\"", Toast.LENGTH_LONG).show(); break;
                        case 5: finish(); break;
                    }
                })
                .setOnDismissListener(d -> hideSystemUi())
                .show();
    }

    private void chooseLocation() {
        int cur = indexOf(LOC_KEYS, prefs.getString("loc", "levi"));
        new AlertDialog.Builder(this)
                .setTitle("Location")
                .setSingleChoiceItems(LOC_NAMES, cur, (d, which) -> {
                    prefs.edit().putString("loc", LOC_KEYS[which]).apply();
                    d.dismiss();
                    load();
                })
                .setOnDismissListener(d -> hideSystemUi())
                .show();
    }

    private void chooseView() {
        new AlertDialog.Builder(this)
                .setTitle("Layout")
                .setSingleChoiceItems(VIEW_NAMES, prefs.getInt("view", 0), (d, which) -> {
                    prefs.edit().putInt("view", which).apply();
                    d.dismiss();
                    load();
                })
                .setOnDismissListener(d -> hideSystemUi())
                .show();
    }

    private String appVersion() {
        try { return getPackageManager().getPackageInfo(getPackageName(), 0).versionName; }
        catch (Exception e) { return "?"; }
    }

    private static int indexOf(String[] arr, String v) {
        for (int i = 0; i < arr.length; i++) if (arr[i].equals(v)) return i;
        return 0;
    }

    // ── Lifecycle ────────────────────────────────────────────────────
    @SuppressWarnings("deprecation")
    private void hideSystemUi() {
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) hideSystemUi();
    }

    @Override
    protected void onResume() {
        super.onResume();
        web.onResume();
        web.resumeTimers();
    }

    @Override
    protected void onPause() {
        web.onPause();
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        web.destroy();
        super.onDestroy();
    }
}
