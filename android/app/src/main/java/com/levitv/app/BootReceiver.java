package com.levitv.app;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Opens LeviTV when the TV starts (if "Start on boot" is on). Best effort:
 *  some Android TV versions block activities from starting at boot. */
public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (!Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) return;
        boolean on = context.getSharedPreferences(MainActivity.PREFS, Context.MODE_PRIVATE)
                .getBoolean("autostart", true);
        if (!on) return;
        Intent i = new Intent(context, MainActivity.class);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try { context.startActivity(i); } catch (Exception ignored) { }
    }
}
