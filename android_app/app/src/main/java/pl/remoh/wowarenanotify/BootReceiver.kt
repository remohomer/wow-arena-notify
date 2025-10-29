package pl.remoh.wowarenanotify

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import androidx.core.content.ContextCompat
import pl.remoh.wowarenanotify.core.SettingsManager
import pl.remoh.wowarenanotify.fcm.RealtimeListenerService

/**
 * 🚀 BootReceiver (v2.0, 2025-10-26)
 * -----------------------------------
 * ✅ Uruchamia RealtimeListenerService po:
 *    - restarcie telefonu (BOOT_COMPLETED / LOCKED_BOOT_COMPLETED)
 *    - aktualizacji aplikacji (MY_PACKAGE_REPLACED)
 * 🔧 Działa tylko, jeśli użytkownik włączył "Allow Background Operation"
 */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        val action = intent?.action ?: "UNKNOWN"
        Log.i("BootReceiver", "📡 onReceive: $action")

        if (SettingsManager.isBackgroundEnabled(context)) {
            try {
                val svc = Intent(context, RealtimeListenerService::class.java)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    ContextCompat.startForegroundService(context, svc)
                } else {
                    context.startService(svc)
                }
                Log.i("BootReceiver", "✅ RealtimeListenerService started (background allowed)")
            } catch (e: Exception) {
                Log.e("BootReceiver", "❌ Failed to start service: ${e.message}")
            }
        } else {
            Log.i("BootReceiver", "⚙️ Background operation disabled — skipping service start")
        }
    }
}
