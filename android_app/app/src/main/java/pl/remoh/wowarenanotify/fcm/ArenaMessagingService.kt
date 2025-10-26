package pl.remoh.wowarenanotify.fcm

import android.util.Log
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

/**
 * 📡 ArenaMessagingService (v2, 2025-10-26)
 * -----------------------------------------
 * ✅ Handles optional FCM messages from backend
 * ✅ Currently acts as fallback / diagnostic service
 * ✅ Logs message types and tokens
 */
class ArenaMessagingService : FirebaseMessagingService() {

    override fun onMessageReceived(message: RemoteMessage) {
        val data = message.data
        val type = data["type"] ?: "unknown"
        Log.i("FCM", "📦 FCM message received → type=$type | data=$data")

        when (type) {
            "test_connection" -> {
                // Optional toast/log if you ever send broadcast FCMs
                Log.i("FCM", "✅ Test connection message received.")
            }

            else -> {
                Log.w("FCM", "⚠ Unhandled FCM type: $type")
            }
        }
    }

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        Log.i("FCM", "🔄 Refreshed FCM token: $token")
        // Możesz tu dodać automatyczną aktualizację tokena do RTDB, jeśli chcesz
    }
}
