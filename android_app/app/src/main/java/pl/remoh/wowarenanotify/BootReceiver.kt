package pl.remoh.wowarenanotify

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import pl.remoh.wowarenanotify.fcm.RealtimeListenerService

/**
 * 🚀 BootReceiver
 * Startuje RealtimeListenerService po:
 *  - restarcie telefonu (BOOT_COMPLETED / LOCKED_BOOT_COMPLETED),
 *  - aktualizacji aplikacji (MY_PACKAGE_REPLACED).
 */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        val action = intent?.action ?: "UNKNOWN"
        Log.i("BootReceiver", "📡 onReceive: $action")

        // Możesz dodać tu warunki (np. tylko jeśli user włączył autostart w ustawieniach appki).
        startRealtimeListener(context)
    }

    private fun startRealtimeListener(context: Context) {
        try {
            val svc = Intent(context, RealtimeListenerService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(svc)
            } else {
                context.startService(svc)
            }
            Log.i("BootReceiver", "✅ RealtimeListenerService start requested")
        } catch (e: Exception) {
            Log.e("BootReceiver", "❌ Failed to start RealtimeListenerService: ${e.message}")
        }
    }
}
