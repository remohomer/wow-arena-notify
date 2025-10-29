package pl.remoh.wowarenanotify

// Android / System
import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import com.google.firebase.messaging.FirebaseMessaging
import pl.remoh.wowarenanotify.ui.screens.ArenaApp
import pl.remoh.wowarenanotify.ui.theme.WoWArenaNotifyTheme
import java.util.concurrent.TimeUnit

import androidx.core.splashscreen.SplashScreen
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import pl.remoh.wowarenanotify.core.SettingsManager
import pl.remoh.wowarenanotify.ui.theme.ThemeController

class MainActivity : ComponentActivity() {

    // 🔹 Launcher do uprawnień powiadomień (Android 13+)
    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) Log.i("FCM", "✅ Notifications permission granted")
        else Log.w("FCM", "⚠ Notifications permission denied")
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        requestedOrientation = android.content.pm.ActivityInfo.SCREEN_ORIENTATION_PORTRAIT

        // 💾 Wczytaj preferencje motywu (ciemny domyślny)
        ThemeController.loadTheme(this)

        // (pozostała część kodu bez zmian...)

        setContent {
            WoWArenaNotifyTheme(
                darkTheme = ThemeController.isDarkTheme
            ) {
                ArenaApp()
            }
        }

        // ✅ Poproś o uprawnienia do powiadomień (Android 13+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(
                    this,
                    Manifest.permission.POST_NOTIFICATIONS
                ) != PackageManager.PERMISSION_GRANTED
            ) {
                requestPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }

        // ✅ Uruchom cyklicznego Workera (utrzymanie alive)
        val constraints = Constraints.Builder()
            .setRequiresDeviceIdle(false)
            .setRequiresCharging(false)
            .build()

        val workRequest = PeriodicWorkRequestBuilder<HeartbeatWorker>(15, TimeUnit.MINUTES)
            .setConstraints(constraints)
            .build()

        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            "ArenaHeartbeat",
            ExistingPeriodicWorkPolicy.KEEP,
            workRequest
        )

        Log.i("WorkManager", "🕒 HeartbeatWorker registered every 15 min")

        // ✅ Zainicjalizuj token FCM (jednorazowo)
        FirebaseMessaging.getInstance().token.addOnCompleteListener {
            if (it.isSuccessful) {
                Log.i("FCM", "📱 Device token: ${it.result}")
            } else {
                Log.e("FCM", "❌ Failed to get FCM token: ${it.exception?.message}")
            }
        }

        // ✅ Uruchom serwis nasłuchu Firebase Realtime Database
        if (SettingsManager.isBackgroundEnabled(this)) {
            val intent = Intent(this, pl.remoh.wowarenanotify.fcm.RealtimeListenerService::class.java)
            ContextCompat.startForegroundService(this, intent)
            Log.i("RTDB", "🚀 Realtime listener started from MainActivity")
        } else {
            Log.i("RTDB", "⚙️ Background operation disabled by user")
        }

        // ✅ Start aplikacji (Compose)
        setContent {
            WoWArenaNotifyTheme {
                ArenaApp()
            }
        }
    }
}
