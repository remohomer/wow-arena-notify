package pl.remoh.wowarenanotify.fcm

import android.app.*
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.graphics.Color
import android.media.AudioManager
import android.media.ToneGenerator
import android.os.*
import android.util.Log
import androidx.core.app.NotificationCompat
import pl.remoh.wowarenanotify.MainActivity
import pl.remoh.wowarenanotify.R
import kotlin.math.abs
import pl.remoh.wowarenanotify.core.SettingsManager

class CountdownService : Service() {

    private var handler: Handler? = null
    private var tickRunnable: Runnable? = null
    private var wakeLock: PowerManager.WakeLock? = null
    private val channelId = "arena_countdown_channel"
    private val notificationId = 42
    private var isStopped = false

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        isStopped = false

        val endsAt = intent?.getLongExtra("endsAt", 0L) ?: 0L
        if (endsAt == 0L) {
            stopSelf()
            return START_NOT_STICKY
        }

        val eventReceivedAt = System.currentTimeMillis()
        isRunning = true

        // 🔧 Oblicz czas pozostały z uwzględnieniem offsetu Firebase i opóźnienia
        val now = System.currentTimeMillis()
        val serverNow = now + TimeSync.firebaseOffsetMs
        val rawRemaining = endsAt - serverNow
        val delayCompensation = (now - eventReceivedAt)
        var remaining = rawRemaining - delayCompensation

        // 🧮 Korekta offsetu desktopowego (jeśli istnieje)
        val desktopOffset = intent?.getLongExtra("desktopOffset", Long.MIN_VALUE) ?: Long.MIN_VALUE
        if (desktopOffset != Long.MIN_VALUE) {
            val localOffset = TimeSync.firebaseOffsetMs
            val offsetDiff = desktopOffset - localOffset
            val adjustedRemaining = remaining + offsetDiff
            if (abs(offsetDiff) < 3000) {
                remaining = adjustedRemaining
                Log.i("CountdownService", "✅ Offset sync: applied $offsetDiff ms correction")
            } else {
                Log.w("CountdownService", "⚠ OffsetDiff too large ($offsetDiff ms) — ignored")
            }
        }

        Log.i("CountdownService", "🕒 Remaining time: $remaining ms")

        // 💤 WakeLock
        val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "WoWArenaNotify::CountdownLock")
        wakeLock?.acquire(remaining + 2000)

        // 🔔 Notyfikacja
        createNotificationChannel()
        val notification = buildNotification(remaining)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(notificationId, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        } else {
            startForeground(notificationId, notification)
        }

        // 🔄 Tick loop
        handler = Handler(Looper.getMainLooper())
        tickRunnable = object : Runnable {
            override fun run() {
                if (isStopped) return

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

                // 📦 Ustawienia użytkownika
                val vibrationEnabled = SettingsManager.isVibrationEnabled(this@CountdownService)
                val soundsEnabled = SettingsManager.isSoundsEnabled(this@CountdownService)
                val finalSeconds = SettingsManager.getFinalSeconds(this@CountdownService)
                val notificationsEnabled = SettingsManager.isNotificationsEnabled(this@CountdownService)

                // 🎯 Uruchamiaj wibracje / dźwięk tylko w ostatnich sekundach
                if (secondsLeft in 1..finalSeconds) {
                    if (vibrationEnabled || soundsEnabled) {
                        val isFinal = (secondsLeft == 1)
                        playAlert(isFinal, vibrationEnabled, soundsEnabled)
                    }
                }

                // 🔔 Aktualizacja notyfikacji tylko jeśli włączone
                if (notificationsEnabled) {
                    (getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager)
                        .notify(notificationId, buildNotification(rem))
                }

                if (!isStopped) handler?.postDelayed(this, 1000)
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

    /**
     * 🎵 Wibracja + dźwięk zgodne z ustawieniami użytkownika
     */
    private fun playAlert(final: Boolean, vibration: Boolean, sound: Boolean) {
        try {
            if (vibration) {
                val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
                val pattern = if (final)
                    longArrayOf(0, 250, 100, 250)
                else
                    longArrayOf(0, 120, 80, 120)

                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    vibrator.vibrate(VibrationEffect.createWaveform(pattern, -1))
                } else {
                    vibrator.vibrate(pattern, -1)
                }
            }

            if (sound) {
                val toneType = if (final) ToneGenerator.TONE_CDMA_ALERT_CALL_GUARD
                else ToneGenerator.TONE_PROP_BEEP
                val toneGen = ToneGenerator(AudioManager.STREAM_MUSIC, 100)
                toneGen.startTone(toneType, if (final) 300 else 120)
            }

        } catch (e: Exception) {
            Log.e("CountdownService", "⚠️ playAlert() failed: ${e.message}")
        }
    }

    override fun onDestroy() {
        Log.i("CountdownService", "🛑 CountdownService destroyed – cleaning up.")
        isStopped = true
        handler?.removeCallbacks(tickRunnable ?: return)
        tickRunnable = null

        // 🔹 Wyślij końcowy broadcast
        val intent = Intent("ARENA_COUNTDOWN_UPDATE").apply {
            setPackage(packageName)
            putExtra("state", "WAITING")
            putExtra("remaining", 0)
        }
        sendBroadcast(intent)

        (getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager).cancel(notificationId)
        try { wakeLock?.release() } catch (_: Exception) {}
        wakeLock = null
        isRunning = false

        super.onDestroy()
    }

    override fun onTaskRemoved(rootIntent: Intent?) {
        isStopped = true
        super.onTaskRemoved(rootIntent)
    }

    companion object {
        @Volatile
        var isRunning = false
    }
}
