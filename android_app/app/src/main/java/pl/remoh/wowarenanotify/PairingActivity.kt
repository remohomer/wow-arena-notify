package pl.remoh.wowarenanotify

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.widget.Toast
import com.google.firebase.database.FirebaseDatabase
import com.google.firebase.messaging.FirebaseMessaging
import com.google.zxing.integration.android.IntentIntegrator
import androidx.activity.ComponentActivity

class PairingActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 🔹 Uruchom skaner QR od razu po wejściu
        val integrator = IntentIntegrator(this)
        integrator.setDesiredBarcodeFormats(IntentIntegrator.QR_CODE)
        integrator.setPrompt("Scan the QR code shown on your desktop app")
        integrator.setBeepEnabled(true)
        integrator.setOrientationLocked(false)
        integrator.initiateScan()
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
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
            // 🔹 Odczytaj dane z JSON-a
            val json = org.json.JSONObject(content)
            val pairingId = json.getString("pid")
            val rtdbUrl = json.getString("rtdb")

            // 🔹 Pobierz token FCM
            FirebaseMessaging.getInstance().token.addOnSuccessListener { token ->
                Log.i("Pairing", "✅ Token retrieved: $token")

                val db = FirebaseDatabase.getInstance(rtdbUrl)
                val ref = db.getReference("pairing").child(pairingId)
                val deviceId = android.provider.Settings.Secure.getString(
                    contentResolver, android.provider.Settings.Secure.ANDROID_ID
                )

                // ⬇️ DOPISZ: przekaż także deviceId do węzła parowania
                ref.updateChildren(mapOf("token" to token, "deviceId" to deviceId))
                // 🔹 Zapisz token do RTDB
                ref.child("token").setValue(token)
                    .addOnSuccessListener {
                        Toast.makeText(this, "✅ Device paired successfully!", Toast.LENGTH_LONG).show()
                        Log.i("Pairing", "Token written to RTDB")
                        finish()
                    }
                    .addOnFailureListener { e ->
                        Toast.makeText(this, "❌ Failed to upload token", Toast.LENGTH_SHORT).show()
                        Log.e("Pairing", "Error writing token", e)
                        finish()
                    }

            }.addOnFailureListener {
                Toast.makeText(this, "❌ Could not retrieve FCM token", Toast.LENGTH_SHORT).show()
                finish()
            }

        } catch (e: Exception) {
            Log.e("Pairing", "❌ Invalid QR format", e)
            Toast.makeText(this, "Invalid QR code", Toast.LENGTH_SHORT).show()
            finish()
        }
    }
}
