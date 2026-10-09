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
import android.view.Gravity;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.style.ForegroundColorSpan;
import android.graphics.Typeface;
import android.widget.Toast;

import org.mozilla.geckoview.AllowOrDeny;
import org.mozilla.geckoview.GeckoResult;
import org.mozilla.geckoview.GeckoRuntime;
import org.mozilla.geckoview.GeckoRuntimeSettings;
import org.mozilla.geckoview.GeckoSession;
import org.mozilla.geckoview.GeckoSessionSettings;
import org.mozilla.geckoview.GeckoView;

/**
 * LeviTV for Android TV: shows levitv.com full screen.
 *
 * Uses GeckoView (Mozilla's Firefox engine) instead of Android's WebView:
 * YouTube refuses to play embedded live streams inside an Android WebView
 * (error 150), but plays them in a regular browser engine.
 *
 * Remote: OK / Menu = settings, Left / Right = previous / next camera,
 * Back twice = exit.
 */
public class MainActivity extends Activity {

    static final String SITE = "https://levitv.com/";
    static final String PREFS = "levitv";
    static final String[] LOC_KEYS = {"levi", "yllas", "helsinki"};
    static final String[] LOC_NAMES = {"Levi", "Ylläs", "Helsinki"};
    static final String[] VIEW_NAMES = {"Full screen (camera + sidebar)", "Info TV (large camera)"};

    private static final long RELOAD_EVERY_MS = 6L * 60 * 60 * 1000;   // fresh page every 6 h
    private static final long RETRY_MS = 30_000;                       // after a network error

    private static GeckoRuntime sRuntime;                               // one per process

    private GeckoView view;
    private GeckoSession session;
    private SharedPreferences prefs;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private long lastBack = 0;
    private String pageUrl = "";
    private int skipCounter = 0;
    private View splash;
    private final Runnable hideSplash = this::hideSplash;

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

        if (sRuntime == null) {
            sRuntime = GeckoRuntime.create(getApplicationContext(),
                    new GeckoRuntimeSettings.Builder()
                            .consoleOutput(false)
                            .build());
        }

        session = new GeckoSession(new GeckoSessionSettings.Builder()
                .usePrivateMode(false)
                .build());

        // Muted camera streams must autoplay
        session.setPermissionDelegate(new GeckoSession.PermissionDelegate() {
            @Override
            public GeckoResult<Integer> onContentPermissionRequest(GeckoSession s, ContentPermission perm) {
                if (perm.permission == PERMISSION_AUTOPLAY_INAUDIBLE
                        || perm.permission == PERMISSION_AUTOPLAY_AUDIBLE) {
                    return GeckoResult.fromValue(ContentPermission.VALUE_ALLOW);
                }
                return GeckoResult.fromValue(ContentPermission.VALUE_DENY);
            }
        });

        // Stay on LeviTV: ad links can't be opened on a TV
        session.setNavigationDelegate(new GeckoSession.NavigationDelegate() {
            @Override
            public GeckoResult<AllowOrDeny> onLoadRequest(GeckoSession s, LoadRequest request) {
                return GeckoResult.fromValue(isAllowed(request.uri) ? AllowOrDeny.ALLOW : AllowOrDeny.DENY);
            }
        });

        // Network error → offline screen and retry
        session.setProgressDelegate(new GeckoSession.ProgressDelegate() {
            @Override
            public void onPageStop(GeckoSession s, boolean success) {
                if (!success && pageUrl.startsWith(SITE)) showOffline();
                else handler.postDelayed(hideSplash, 2500);     // fallback if no paint event
            }
        });

        // Page painted → fade the splash away
        session.setContentDelegate(new GeckoSession.ContentDelegate() {
            @Override
            public void onFirstContentfulPaint(GeckoSession s) {
                handler.postDelayed(hideSplash, 600);
            }
        });

        session.open(sRuntime);

        view = new GeckoView(this);
        view.setBackgroundColor(Color.rgb(5, 8, 15));
        view.coverUntilFirstPaint(Color.rgb(5, 8, 15));       // no white surface before the page
        view.setFocusable(true);
        view.setSession(session);
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(5, 8, 15));
        root.addView(view, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        splash = makeSplash();
        root.addView(splash, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(root);
        view.requestFocus();
        hideSystemUi();

        load();
        handler.postDelayed(periodicReload, RELOAD_EVERY_MS);

        if (!prefs.getBoolean("seenHint", false)) {
            Toast.makeText(this, "Press OK or Menu for settings", Toast.LENGTH_LONG).show();
            prefs.edit().putBoolean("seenHint", true).apply();
        }
    }

    private boolean isAllowed(String url) {
        if (url == null) return false;
        if (url.startsWith("data:") || url.startsWith("about:")) return true;
        String host = Uri.parse(url).getHost();
        if (host == null) return false;
        return host.equals("levitv.com") || host.endsWith(".levitv.com")
                || host.endsWith("youtube.com") || host.endsWith("youtube-nocookie.com");
    }

    /** The page itself (no redirect), so a #cam= fragment can steer it without reloading. */
    private String url() {
        String loc = prefs.getString("loc", "levi");
        boolean full = prefs.getInt("view", 0) == 0;
        String screen = prefs.getString("screen", null);
        if (screen == null) {
            String id = Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID);
            screen = "atv-" + (id == null ? "tv" : id.substring(0, Math.min(6, id.length())));
            prefs.edit().putString("screen", screen).apply();
        }
        return SITE + "levi-infotv.html?loc=" + loc + "&view=" + (full ? "full" : "tv")
                + "&screen=" + Uri.encode(screen) + "&app=androidtv&engine=gecko"
                + (prefs.getBoolean("debug", false) ? "&debug=1" : "");
    }

    /** Start-up screen: LEVITV.com wordmark, tagline and a spinner. */
    private View makeSplash() {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER);
        box.setBackgroundColor(Color.rgb(5, 8, 15));
        box.setClickable(false);
        box.setFocusable(false);

        SpannableString word = new SpannableString("LEVITV.com");
        word.setSpan(new ForegroundColorSpan(Color.rgb(95, 180, 255)), 4, 6, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        word.setSpan(new ForegroundColorSpan(Color.rgb(120, 140, 165)), 6, 10, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        TextView t = new TextView(this);
        t.setText(word);
        t.setTextColor(Color.WHITE);
        t.setTextSize(56);
        t.setTypeface(Typeface.create("sans-serif-condensed", Typeface.BOLD));
        t.setLetterSpacing(0.08f);
        t.setGravity(Gravity.CENTER);
        box.addView(t);

        TextView sub = new TextView(this);
        int li = indexOf(LOC_KEYS, prefs.getString("loc", "levi"));
        sub.setText("your real-time view of " + LOC_NAMES[li < 0 ? 0 : li]);
        sub.setTextColor(Color.rgb(160, 178, 198));
        sub.setTextSize(20);
        sub.setGravity(Gravity.CENTER);
        sub.setPadding(0, 8, 0, 48);
        box.addView(sub);

        ProgressBar p = new ProgressBar(this);
        p.setIndeterminate(true);
        box.addView(p, new LinearLayout.LayoutParams(72, 72));
        return box;
    }

    private void showSplash() {
        if (splash == null) return;
        splash.animate().cancel();
        splash.setAlpha(1f);
        splash.setVisibility(View.VISIBLE);
        handler.removeCallbacks(hideSplash);
        handler.postDelayed(hideSplash, 20_000);              // never stay forever
    }

    private void hideSplash() {
        if (splash == null || splash.getVisibility() != View.VISIBLE) return;
        handler.removeCallbacks(hideSplash);
        splash.animate().alpha(0f).setDuration(600)
                .withEndAction(() -> splash.setVisibility(View.GONE)).start();
    }

    private void load() {
        showSplash();
        handler.removeCallbacks(retry);
        pageUrl = url();
        session.loadUri(pageUrl);
    }

    private void showOffline() {
        String html = "<html><body style='margin:0;background:#05080f;color:#c9d6e3;font-family:sans-serif;"
                + "display:flex;align-items:center;justify-content:center;height:100vh;text-align:center'>"
                + "<div><div style='font-size:48px;font-weight:800;letter-spacing:6px;color:#fff'>LEVI<span style='color:#5fb4ff'>TV</span></div>"
                + "<p style='font-size:22px'>No connection — retrying in 30 seconds…</p></div></body></html>";
        pageUrl = "data:";
        session.loadUri("data:text/html;charset=utf-8," + Uri.encode(html));
        handler.removeCallbacks(retry);
        handler.postDelayed(retry, RETRY_MS);
    }

    // ── Remote control ───────────────────────────────────────────────
    // Handled before the browser view, otherwise it swallows OK / Back.
    @Override
    public boolean dispatchKeyEvent(KeyEvent event) {
        int code = event.getKeyCode();
        boolean up = event.getAction() == KeyEvent.ACTION_UP;
        switch (code) {
            case KeyEvent.KEYCODE_MENU:
            case KeyEvent.KEYCODE_SETTINGS:
            case KeyEvent.KEYCODE_DPAD_CENTER:
            case KeyEvent.KEYCODE_ENTER:
            case KeyEvent.KEYCODE_NUMPAD_ENTER:
            case KeyEvent.KEYCODE_BUTTON_A:
                if (up) showMenu();
                return true;
            case KeyEvent.KEYCODE_DPAD_RIGHT:
            case KeyEvent.KEYCODE_MEDIA_NEXT:
            case KeyEvent.KEYCODE_CHANNEL_UP:
                if (up) skipCamera(1);
                return true;
            case KeyEvent.KEYCODE_DPAD_LEFT:
            case KeyEvent.KEYCODE_MEDIA_PREVIOUS:
            case KeyEvent.KEYCODE_CHANNEL_DOWN:
                if (up) skipCamera(-1);
                return true;
            case KeyEvent.KEYCODE_DPAD_UP:
            case KeyEvent.KEYCODE_DPAD_DOWN:
                return true;                      // nothing to scroll on the TV layout
            case KeyEvent.KEYCODE_BACK:
                if (up) {
                    long now = System.currentTimeMillis();
                    if (now - lastBack < 2500) { finish(); return true; }
                    lastBack = now;
                    Toast.makeText(this, "Press Back again to exit · OK for menu", Toast.LENGTH_SHORT).show();
                }
                return true;
            default:
                return super.dispatchKeyEvent(event);
        }
    }

    /** Next / previous camera: a #cam= fragment the page listens for (no reload). */
    private void skipCamera(int dir) {
        if (!pageUrl.startsWith(SITE)) return;
        skipCounter++;
        String base = pageUrl.contains("#") ? pageUrl.substring(0, pageUrl.indexOf('#')) : pageUrl;
        session.loadUri(base + "#cam=" + dir + "_" + skipCounter);
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
                "Diagnostics: " + (prefs.getBoolean("debug", false) ? "On" : "Off"),
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
                        case 5: prefs.edit().putBoolean("debug", !prefs.getBoolean("debug", false)).apply();
                                load(); break;
                        case 6: finish(); break;
                    }
                })
                .setOnDismissListener(d -> { hideSystemUi(); view.requestFocus(); })
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
                .setOnDismissListener(d -> { hideSystemUi(); view.requestFocus(); })
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
                .setOnDismissListener(d -> { hideSystemUi(); view.requestFocus(); })
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
        if (session != null) session.setActive(true);
    }

    @Override
    protected void onPause() {
        if (session != null) session.setActive(false);
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        if (session != null) session.close();
        super.onDestroy();
    }
}
