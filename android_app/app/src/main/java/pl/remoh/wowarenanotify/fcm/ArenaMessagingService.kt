package pl.remoh.wowarenanotify.fcm

import android.app.Service
import android.content.Context
import android.content.Intent
import android.util.Log
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

class ArenaMessagingService : FirebaseMessagingService() {

    override fun onMessageReceived(message: RemoteMessage) {
        val data = message.data
        val type = data["type"]
        val endsAt = data["endsAt"]?.toLongOrNull() ?: 0L

        Log.i("FCM", "📦 arena_${type} received, endsAt=$endsAt")

        val now = System.currentTimeMillis()
        val offset = TimeSync.firebaseOffsetMs
        val serverNow = now + offset
        val diff = endsAt - serverNow
        Log.i("FCM", "🕒 Device now=$now | offset=$offset | serverNow=$serverNow | diff=$diff ms")

        if (type == "arena_pop") {
            if (CountdownService.isRunning) {
                Log.w("FCM", "⚠ CountdownService already running, ignoring duplicate arena_pop")
                return
            }

            val intent = Intent(this, CountdownService::class.java).apply {
                putExtra("endsAt", endsAt)
            }
            Log.i("FCM", "🚀 Starting CountdownService (remaining=$diff ms)")
            startForegroundServiceCompat(intent)
        } else if (type == "arena_stop") {
            Log.i("FCM", "🛑 arena_stop → stopping CountdownService")
            stopService(Intent(this, CountdownService::class.java))
        }
    }

    private fun Context.startForegroundServiceCompat(intent: Intent) {
        try {
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                startForegroundService(intent)
            } else {
                startService(intent)
            }
        } catch (e: Exception) {
            Log.e("FCM", "❌ Failed to start service: ${e.message}")
        }
    }

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        Log.i("FCM", "🔄 New FCM token: $token")
    }
}
