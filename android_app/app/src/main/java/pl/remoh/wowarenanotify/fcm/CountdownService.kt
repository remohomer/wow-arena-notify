package pl.remoh.wowarenanotify.fcm

import android.app.*
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.graphics.Color
import android.os.*
import android.util.Log
import androidx.core.app.NotificationCompat
import pl.remoh.wowarenanotify.MainActivity
import pl.remoh.wowarenanotify.R
import kotlin.math.abs
import kotlin.math.max

class CountdownService : Service() {

    private var handler: Handler? = null
    private var tickRunnable: Runnable? = null
    private var wakeLock: PowerManager.WakeLock? = null
    private val channelId = "arena_countdown_channel"
    private val notificationId = 42

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val endsAt = intent?.getLongExtra("endsAt", 0L) ?: 0L
        if (endsAt == 0L) {
            stopSelf()
            return START_NOT_STICKY
        }

        val eventReceivedAt = System.currentTimeMillis()
        isRunning = true

        // 🔧 Oblicz czas pozostały z uwzględnieniem offsetu Firebase i ewentualnego opóźnienia FCM
        val now = System.currentTimeMillis()
        val serverNow = now + TimeSync.firebaseOffsetMs
        val rawRemaining = endsAt - serverNow
        val delayCompensation = (now - eventReceivedAt)
        var remaining = rawRemaining - delayCompensation

        // 🧮 Pobierz desktopOffset (jeśli przyszedł z FCM)
        val desktopOffset = intent?.getLongExtra("desktopOffset", Long.MIN_VALUE) ?: Long.MIN_VALUE
        if (desktopOffset != Long.MIN_VALUE) {
            val localOffset = TimeSync.firebaseOffsetMs
            val offsetDiff = desktopOffset - localOffset
            val adjustedRemaining = remaining + offsetDiff

            Log.i(
                "CountdownService",
                "🧭 Offset sync check → localOffset=$localOffset | desktopOffset=$desktopOffset | " +
                        "offsetDiff=$offsetDiff | rawRemaining=$remaining | adjustedRemaining=$adjustedRemaining"
            )

            // Jeśli różnica jest mała (<3s), zastosuj korektę czasu
            if (abs(offsetDiff) < 3000) {
                remaining = adjustedRemaining
                Log.i("CountdownService", "✅ Adjusted remaining using offsetDiff ($offsetDiff ms)")
            } else {
                Log.w("CountdownService", "⚠️ OffsetDiff too large (${offsetDiff}ms) → ignoring correction.")
            }
        } else {
            Log.i("CountdownService", "ℹ️ No desktopOffset in intent → using standard Firebase offset only.")
        }

        Log.i(
            "CountdownService",
            "🕒 endsAt=$endsAt | localNow=$now | offset=${TimeSync.firebaseOffsetMs} | " +
                    "serverNow=$serverNow | delayComp=$delayCompensation | remaining=$remaining ms"
        )

        // WakeLock – żeby system nie ubił w tle
        val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "WoWArenaNotify::CountdownLock")
        wakeLock?.acquire(remaining + 2000)

        // Uruchom notyfikację
        createNotificationChannel()
        val notification = buildNotification(remaining)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(notificationId, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        } else {
            startForeground(notificationId, notification)
        }

        playAlert()

        handler = Handler(Looper.getMainLooper())
        tickRunnable = object : Runnable {
            override fun run() {
                val currentNow = System.currentTimeMillis()
                val currentServerNow = currentNow + TimeSync.firebaseOffsetMs
                val rem = endsAt - currentServerNow
                val secondsLeft = (rem / 1000).toInt()

                val updateIntent = Intent("ARENA_COUNTDOWN_UPDATE").apply {
                    setPackage(packageName)
                    putExtra("state", if (rem > 0) "COUNTDOWN" else "WAITING")
                    putExtra("remaining", secondsLeft)
                }
                sendBroadcast(updateIntent)

                if (rem <= 0) {
                    Log.i("CountdownService", "🏁 Countdown complete → stopSelf()")
                    stopSelf()
                    return
                }

                if (secondsLeft == 10) playAlert(true)
                else if (secondsLeft in 1..9) playAlert(false)

                (getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager)
                    .notify(notificationId, buildNotification(rem))
                handler?.postDelayed(this, 1000)
            }
        }
        handler?.post(tickRunnable!!)
        return START_STICKY
    }

    private fun buildNotification(remainingMs: Long): Notification {
        val seconds = (remainingMs / 1000).coerceAtLeast(0)
        val formatted = String.format("%02d:%02d", seconds / 60, seconds % 60)
        val color = when {
            seconds > 20 -> Color.parseColor("#4CAF50")
            seconds > 10 -> Color.parseColor("#FF9800")
            else -> Color.parseColor("#F44336")
        }

        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        return NotificationCompat.Builder(this, channelId)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle("Arena begins in $formatted")
            .setContentText("Prepare for battle!")
            .setColor(color)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setShowWhen(false)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(pendingIntent)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "Arena Countdown",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Arena queue countdown notifications"
                lockscreenVisibility = Notification.VISIBILITY_PUBLIC
                enableVibration(true)
                setSound(null, null)
            }
            val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            nm.createNotificationChannel(channel)
        }
    }

    private fun playAlert(final: Boolean = false) {
        try {
            val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
            val pattern = if (final) longArrayOf(0, 200, 80, 200) else longArrayOf(0, 100, 60, 100)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator.vibrate(VibrationEffect.createWaveform(pattern, -1))
            } else vibrator.vibrate(pattern, -1)
        } catch (_: Exception) {}
    }

    override fun onDestroy() {
        Log.i("CountdownService", "🛑 CountdownService destroyed – cleaning up.")

        // Usuń ticki
        handler?.removeCallbacks(tickRunnable ?: return)
        tickRunnable = null

        // 🔹 Wyślij ostatni broadcast do UI — zawsze!
        val intent = Intent("ARENA_COUNTDOWN_UPDATE").apply {
            setPackage(packageName)
            putExtra("state", "WAITING")
            putExtra("remaining", 0)
        }
        sendBroadcast(intent)
        Log.i("CountdownService", "📡 Broadcasted final WAITING state before stop")

        // Usuń notyfikację
        (getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager).cancel(notificationId)

        // Zwolnij zasoby
        try { wakeLock?.release() } catch (_: Exception) {}
        wakeLock = null
        isRunning = false

        super.onDestroy()
    }

    companion object {
        @Volatile
        var isRunning = false
    }
}
