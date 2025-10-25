package pl.remoh.wowarenanotify.fcm

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.widget.Toast
import androidx.core.app.NotificationCompat
import com.google.firebase.database.*
import com.google.firebase.messaging.FirebaseMessaging

class RealtimeListenerService : Service() {

    private lateinit var dbRef: DatabaseReference
    private var listener: ChildEventListener? = null

    override fun onCreate() {
        super.onCreate()
        TimeSync.start()  // 🔹 uruchamia monitorowanie offsetu

        // --- ForegroundService protection (cichy kanał) ---
        val channelId = "arena_listener_channel"
        val nm = getSystemService(NOTIFICATION_SERVICE) as NotificationManager

        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
            if (nm.getNotificationChannel(channelId) == null) {
                val ch = NotificationChannel(
                    channelId,
                    "Arena Listener",
                    NotificationManager.IMPORTANCE_NONE
                ).apply {
                    description = "Keeps the realtime listener active silently"
                    setShowBadge(false)
                    lockscreenVisibility = Notification.VISIBILITY_SECRET
                }
                nm.createNotificationChannel(ch)
            }
        }

        val notif = NotificationCompat.Builder(this, channelId)
            .setContentTitle("")
            .setContentText("")
            .setSmallIcon(pl.remoh.wowarenanotify.R.drawable.ic_launcher_foreground)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_MIN)
            .build()

        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.Q) {
            startForeground(
                7777,
                notif,
                android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
            )
        } else {
            startForeground(7777, notif)
        }

        Log.i("RTDB", "👂 Starting RealtimeListenerService...")

        // ✅ Poczekaj, aż Firebase zwróci token
        FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
            if (!task.isSuccessful) {
                Log.e("RTDB", "❌ Failed to get FCM token: ${task.exception?.message}")
                return@addOnCompleteListener
            }

            val token = task.result ?: return@addOnCompleteListener
            Log.i("RTDB", "✅ FCM token resolved: $token")

            val safeToken = token.replace(":", "_")
            dbRef = FirebaseDatabase.getInstance(
                "https://wow-arena-notify-default-rtdb.europe-west1.firebasedatabase.app/"
            ).getReference("arena_events").child(safeToken).child("current")

            listener = object : ChildEventListener {
                override fun onChildAdded(snapshot: DataSnapshot, previousChildName: String?) {
                    val data = snapshot.value as? Map<*, *> ?: return
                    val type = data["type"] as? String ?: return
                    Log.i("RTDB", "📡 New event: $type → $data")

                    when (type) {
                        "arena_pop" -> {
                            val endsAt = (data["endsAt"] as? Number)?.toLong() ?: return

                            // 🔹 Poczekaj aż TimeSync zaktualizuje offset
                            Thread {
                                var tries = 0
                                while (TimeSync.firebaseOffsetMs == 0L && tries < 50) {
                                    Thread.sleep(100)
                                    tries++
                                }
                                val offset = TimeSync.firebaseOffsetMs
                                Log.i("RTDB", "🕒 Using Firebase offset before countdown: $offset ms (waited ${tries * 100} ms)")

                                val intent = Intent(this@RealtimeListenerService, CountdownService::class.java)
                                intent.putExtra("endsAt", endsAt)
                                startService(intent)
                            }.start()
                        }

                        "arena_stop" -> {
                            stopService(Intent(this@RealtimeListenerService, CountdownService::class.java))
                            val intent = Intent("ARENA_STOP_UI_RESET")
                            sendBroadcast(intent)
                        }

                        "test_connection" -> {
                            Handler(Looper.getMainLooper()).post {
                                Toast.makeText(
                                    this@RealtimeListenerService,
                                    "✅ Connection test OK",
                                    Toast.LENGTH_SHORT
                                ).show()
                            }
                        }
                    }
                }

                override fun onChildChanged(snapshot: DataSnapshot, previousChildName: String?) {}
                override fun onChildRemoved(snapshot: DataSnapshot) {}
                override fun onChildMoved(snapshot: DataSnapshot, previousChildName: String?) {}
                override fun onCancelled(error: DatabaseError) {
                    Log.w("RTDB", "⚠ Listener error: ${error.message}")
                    Handler(Looper.getMainLooper()).postDelayed({
                        dbRef.removeEventListener(listener!!)
                        dbRef.addChildEventListener(listener!!)
                        Log.i("RTDB", "🔄 Listener reattached after error.")
                    }, 5000)
                }
            }

            dbRef.addChildEventListener(listener!!)
        }
    }


    override fun onDestroy() {
        listener?.let { dbRef.removeEventListener(it) }
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
