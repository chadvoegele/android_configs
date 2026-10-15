package dev.chad.usproglayout;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/**
 * Android discovers layout XML through this receiver's manifest metadata.
 * Nothing runs while typing: the OS reads the KCM resource directly.
 */
public final class LayoutProvider extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        // Layout discovery is performed by Android's InputManager.
    }
}
