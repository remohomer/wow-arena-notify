package pl.remoh.wowarenanotify.fcm

import android.app.*
import android.content.Intent
import android.os.*
import android.util.Log
import android.widget.Toast
import androidx.core.app.NotificationCompat
import com.google.firebase.database.*
import pl.remoh.wowarenanotify.R
import pl.remoh.wowarenanotify.fcm.TimeSync
import pl.remoh.wowarenanotify.core.CredentialsProvider
import pl.remoh.wowarenanotify.core.ConfigHelper

/**
 * 👂 RealtimeListenerService (v3.4, 2025-10-26)
 * --------------------------------------------
 * ✅ Listens to /arena_events/{pairing_id}/current (whole object)
 * ✅ Uses ValueEventListener — ideal for REST .put() pełnego obiektu
 * ✅ arena_pop -> start licznika, arena_stop -> stop licznika
 * ✅ Solidne logi i auto-reattach
 */
class RealtimeListenerService : Service() {

    private val TAG = "RTDB"
    private var dbRef: DatabaseReference? = null
    private var listener: ValueEventListener? = null
    private var pairingId: String? = null

    override fun onCreate() {
        super.onCreate()

        Log.i(TAG, "👂 Starting RealtimeListenerService...")
        TimeSync.start()

        Log.i(TAG, "🧩 Loaded pairingId from config: $pairingId")

        // --- ForegroundService (silent channel) ---
        createSilentNotificationChannel()
        val notif = buildSilentNotification()

        if (Build.VERSION.SDK_INT >= 29) {
            try {
                val method = Service::class.java.getMethod(
                    "startForeground",
                    Int::class.javaPrimitiveType,
                    Notification::class.java,
                    Int::class.javaPrimitiveType
                )
                method.invoke(this, 7777, notif, 1 shl 1) // FOREGROUND_SERVICE_TYPE_DATA_SYNC
            } catch (e: Exception) {
                Log.w(TAG, "⚠ Reflection fallback for startForeground failed: ${e.message}")
                startForeground(7777, notif)
            }
        } else {
            startForeground(7777, notif)
        }

        // --- Load pairing ID ---
        pairingId = ConfigHelper.getPairingId(this)
        if (pairingId.isNullOrBlank()) {
            Log.e(TAG, "❌ No pairing_id found in config, stopping service.")
            Toast.makeText(this, "No pairing configured", Toast.LENGTH_SHORT).show()
            stopSelf()
            return
        }

        // --- Connect to Firebase RTDB ---
        val creds = CredentialsProvider()
        val rtdbUrl = creds.getRtdbUrl()
        val inst = FirebaseDatabase.getInstance(rtdbUrl)
        // inst.setPersistenceEnabled(false) // (opcjonalnie)
        dbRef = inst.getReference("arena_events")
            .child(pairingId!!)
            .child("current")

        Log.i(TAG, "🔗 Will listen on: $rtdbUrl/arena_events/$pairingId/current")
        attachValueListener()
    }

    private fun createSilentNotificationChannel() {
        val channelId = "arena_listener_channel"
        val nm = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            if (nm.getNotificationChannel(channelId) == null) {
                val ch = NotificationChannel(
                    channelId,
                    "Arena Listener",
                    NotificationManager.IMPORTANCE_MIN
                ).apply {
                    description = "Keeps the realtime listener active silently"
                    setShowBadge(false)
                    lockscreenVisibility = Notification.VISIBILITY_SECRET
                }
                nm.createNotificationChannel(ch)
            }
        }
    }

    private fun buildSilentNotification(): Notification {
        return NotificationCompat.Builder(this, "arena_listener_channel")
            .setContentTitle("")
            .setContentText("")
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_MIN)
            .build()
    }

    private fun attachValueListener() {
        val ref = dbRef ?: return
        listener = object : ValueEventListener {
            override fun onDataChange(snapshot: DataSnapshot) {
                if (!snapshot.exists()) {
                    Log.i(TAG, "ℹ current node is empty / doesn't exist yet")
                    return
                }
                Log.i(TAG, "📡 Data update: ${snapshot.value}")

                // Oczekujemy całej mapy, bo desktop robi REST PUT pełnego obiektu
                val map = snapshot.value
                if (map !is Map<*, *>) {
                    Log.w(TAG, "⚠ Snapshot is not a Map (type=${map?.javaClass?.name}). Ignoring.")
                    return
                }

                val type = (map["type"] as? String)?.lowercase()
                if (type.isNullOrBlank()) {
                    Log.w(TAG, "⚠ No 'type' in event: $map")
                    return
                }

                when (type) {
                    "arena_pop" -> {
                        val endsAt = (map["endsAt"] as? Number)?.toLong()
                        if (endsAt == null) {
                            Log.w(TAG, "⚠ Missing endsAt in arena_pop event: $map")
                            return
                        }

                        Thread {
                            var tries = 0
                            while (TimeSync.firebaseOffsetMs == 0L && tries < 50) {
                                Thread.sleep(100)
                                tries++
                            }
                            val offset = TimeSync.firebaseOffsetMs
                            Log.i(TAG, "🕒 Using offset: $offset ms (waited ${tries * 100} ms)")

                            val intent = Intent(this@RealtimeListenerService, CountdownService::class.java)
                            intent.putExtra("endsAt", endsAt)
                            startService(intent)
                        }.start()
                    }

                    "arena_stop" -> {
                        Log.i(TAG, "🛑 arena_stop received → stopping countdown & resetting UI")
                        stopService(Intent(this@RealtimeListenerService, CountdownService::class.java))
                        sendBroadcast(Intent("ARENA_STOP_UI_RESET"))
                    }

                    "test_connection" -> {
                        Handler(Looper.getMainLooper()).post {
                            Toast.makeText(this@RealtimeListenerService, "✅ Connection test OK", Toast.LENGTH_SHORT).show()
                        }
                    }

                    else -> Log.w(TAG, "⚠ Unknown event type: $type (raw=$map)")
                }
            }

            override fun onCancelled(error: DatabaseError) {
                Log.w(TAG, "⚠ Listener cancelled: ${error.message}")
                Handler(Looper.getMainLooper()).postDelayed({ reattachValueListener() }, 5000)
            }
        }

        ref.addValueEventListener(listener!!)
        Log.i(TAG, "🔗 Listening (ValueEventListener) on /arena_events/$pairingId/current")
    }

    private fun reattachValueListener() {
        listener?.let { dbRef?.removeEventListener(it) }
        attachValueListener()
        Log.i(TAG, "🔄 Listener reattached")
    }

    override fun onDestroy() {
        listener?.let { dbRef?.removeEventListener(it) }
        Log.i(TAG, "🛑 Listener stopped")
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
