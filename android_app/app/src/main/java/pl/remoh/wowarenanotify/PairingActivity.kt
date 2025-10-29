package pl.remoh.wowarenanotify

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.core.content.ContextCompat
import com.google.firebase.database.FirebaseDatabase
import com.google.firebase.messaging.FirebaseMessaging
import com.google.zxing.integration.android.IntentIntegrator
import org.json.JSONObject
import pl.remoh.wowarenanotify.core.network.HttpHelper
import pl.remoh.wowarenanotify.fcm.RealtimeListenerService
import java.util.UUID

/**
 * 🔐 PairingActivity (v4, 2025-10-26)
 * ------------------------------------
 * ✅ Scans QR → calls Cloud Function /pairDevice
 * ✅ Secure REST pairing (no RTDB writes)
 * ✅ Saves pairing_id, device_id, and desktop_id locally
 * ✅ Fully compatible with new desktop pairing.py v8
 */
class PairingActivity : ComponentActivity() {

    private val TAG = "PairingActivity"
    private val PAIR_DEVICE_URL =
        "https://us-central1-wow-arena-notify.cloudfunctions.net/pairDevice"
    private val RTDB_URL =
        "https://wow-arena-notify-default-rtdb.europe-west1.firebasedatabase.app/"
    private val PREFS_NAME = "wow_arena_prefs"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 🔹 Start QR scanner immediately
        val integrator = IntentIntegrator(this)
        integrator.setDesiredBarcodeFormats(IntentIntegrator.QR_CODE)
        integrator.setPrompt("Scan the QR code from your desktop app")
        integrator.setBeepEnabled(true)
        integrator.setOrientationLocked(false)
        integrator.initiateScan()
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: android.content.Intent?) {
        val result = IntentIntegrator.parseActivityResult(requestCode, resultCode, data)
        if (result != null) {
            if (resultCode == Activity.RESULT_OK && result.contents != null) {
                handleQrResult(result.contents)
            } else {
                Toast.makeText(this, "Cancelled", Toast.LENGTH_SHORT).show()
                finish()
            }
        } else {
            super.onActivityResult(requestCode, resultCode, data)
        }
    }

    private fun handleQrResult(content: String) {
        try {
            val json = JSONObject(content)
            val pairingId = json.optString("pid", "").trim()

            if (pairingId.isEmpty()) {
                Toast.makeText(this, "Invalid QR code (missing pid)", Toast.LENGTH_SHORT).show()
                finish()
                return
            }

            Log.i(TAG, "📡 Starting pairing for pid=$pairingId")

            // 🔹 Generate local device ID
            val deviceId = android.provider.Settings.Secure.getString(
                contentResolver, android.provider.Settings.Secure.ANDROID_ID
            ) ?: UUID.randomUUID().toString()

            // 🔹 Retrieve FCM token
            FirebaseMessaging.getInstance().token
                .addOnSuccessListener { token ->
                    Log.i(TAG, "✅ FCM token: $token")
                    sendPairingRequest(pairingId, deviceId, token)
                }
                .addOnFailureListener { e ->
                    Log.e(TAG, "❌ Could not retrieve FCM token", e)
                    Toast.makeText(this, "❌ FCM token unavailable", Toast.LENGTH_SHORT).show()
                    finish()
                }

        } catch (e: Exception) {
            Log.e(TAG, "❌ Invalid QR content", e)
            Toast.makeText(this, "Invalid QR code format", Toast.LENGTH_SHORT).show()
            finish()
        }
    }

    private fun sendPairingRequest(pairingId: String, deviceId: String, fcmToken: String) {
        val payload = JSONObject().apply {
            put("pid", pairingId)
            put("deviceId", deviceId)
            put("fcmToken", fcmToken)
        }

        Thread {
            val (status, body) = HttpHelper.postJson(PAIR_DEVICE_URL, payload.toString())

            Log.i(TAG, "🌍 Server response → $status: $body")

            when (status) {
                200 -> {
                    // 🔹 Save pairing info locally
                    savePairingLocally(pairingId, deviceId)

                    // 🆕 Fetch desktop_id from RTDB (sent by desktop app)
                    fetchAndSaveDesktopId(pairingId)

                    runOnUiThread {
                        Toast.makeText(
                            this,
                            "✅ Device paired successfully!\nID: $deviceId",
                            Toast.LENGTH_LONG
                        ).show()
                        // 🔄 Restart RealtimeListenerService to apply new pairing_id
                        try {
                            val ctx = applicationContext
                            val intent = Intent(ctx, RealtimeListenerService::class.java)
                            ctx.stopService(intent) // in case old listener was running
                            ContextCompat.startForegroundService(ctx, intent)
                            Log.i("PAIR", "🔄 RealtimeListenerService restarted after pairing.")
                        } catch (e: Exception) {
                            Log.e("PAIR", "⚠️ Failed to restart listener: ${e.message}")
                        }
                        finish()
                    }
                }

                in 400..499 -> {
                    runOnUiThread {
                        Toast.makeText(
                            this,
                            "⚠️ Pairing failed (client error $status)\n$body",
                            Toast.LENGTH_LONG
                        ).show()
                        finish()
                    }
                }

                in 500..599 -> {
                    runOnUiThread {
                        Toast.makeText(
                            this,
                            "❌ Server error ($status)\nTry again later.",
                            Toast.LENGTH_LONG
                        ).show()
                        finish()
                    }
                }

                else -> {
                    runOnUiThread {
                        Toast.makeText(
                            this,
                            "❌ Unexpected response ($status)",
                            Toast.LENGTH_SHORT
                        ).show()
                        finish()
                    }
                }
            }
        }.start()
    }

    private fun fetchAndSaveDesktopId(pairingId: String) {
        try {
            val dbRef = FirebaseDatabase.getInstance(RTDB_URL)
                .getReference("devices")
                .child(pairingId)
                .child("desktop_id")

            dbRef.get().addOnSuccessListener { snapshot ->
                val desktopId = snapshot.getValue(String::class.java)
                if (!desktopId.isNullOrEmpty()) {
                    val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                    prefs.edit().putString("desktop_id", desktopId).apply()
                    Log.i(TAG, "🖥 Saved desktop_id=$desktopId locally")
                } else {
                    Log.w(TAG, "⚠ No desktop_id found for pairing $pairingId")
                }
            }.addOnFailureListener {
                Log.w(TAG, "⚠ Failed to fetch desktop_id: ${it.message}")
            }
        } catch (e: Exception) {
            Log.e(TAG, "❌ Error fetching desktop_id", e)
        }
    }

    private fun savePairingLocally(pairingId: String, deviceId: String) {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit()
            .putString("pairing_id", pairingId)
            .putString("device_id", deviceId)
            .apply()
        Log.i(TAG, "💾 Saved pairing_id=$pairingId, device_id=$deviceId locally")
    }
}
