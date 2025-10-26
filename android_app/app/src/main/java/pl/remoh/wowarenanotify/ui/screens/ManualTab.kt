package pl.remoh.wowarenanotify.ui.screens.tabs

import android.content.Context
import android.content.Intent
import android.util.Log
import android.widget.Toast
import androidx.compose.animation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import org.json.JSONObject
import pl.remoh.wowarenanotify.core.ConfigHelper
import pl.remoh.wowarenanotify.core.network.HttpHelper
import java.util.*

@OptIn(ExperimentalAnimationApi::class)
@Composable
fun ManualTab(context: Context, dpW: Dp, dpH: Dp) {
    var manualCode by remember { mutableStateOf("") }
    var statusText by remember { mutableStateOf<String?>(null) }
    var isLoading by remember { mutableStateOf(false) }
    val focusManager = LocalFocusManager.current
    val scope = rememberCoroutineScope()
    val TAG = "PAIR"

    Column(horizontalAlignment = Alignment.CenterHorizontally) {

        OutlinedTextField(
            value = manualCode,
            onValueChange = { manualCode = it.trim() },
            label = { Text("Enter pairing code (UUID)") },
            singleLine = true,
            modifier = Modifier
                .fillMaxWidth(0.85f)
                .padding(top = dpH * 4)
        )

        Spacer(Modifier.height(dpH * 3))

        Button(
            onClick = {
                focusManager.clearFocus()
                if (!manualCode.matches(Regex("^[0-9a-fA-F-]{8,}$"))) {
                    statusText = "⚠️ Invalid code format — should look like a UUID."
                    return@Button
                }

                isLoading = true
                statusText = "⏳ Connecting to server..."
                scope.launch(Dispatchers.IO) {
                    try {
                        val deviceId = android.provider.Settings.Secure.getString(
                            context.contentResolver,
                            android.provider.Settings.Secure.ANDROID_ID
                        ) ?: UUID.randomUUID().toString()

                        val payload = JSONObject().apply {
                            put("pid", manualCode)
                            put("deviceId", deviceId)
                            put("fcmToken", "manual_mode")
                        }

                        val url = "https://us-central1-wow-arena-notify.cloudfunctions.net/pairDevice"
                        val (status, body) = HttpHelper.postJson(url, payload.toString())

                        Log.i(TAG, "🌍 Manual pair → $status: $body")

                        if (status == 200) {
                            ConfigHelper.savePairingId(context, manualCode, deviceId)
                            Log.i(TAG, "✅ Manual pairing OK → $manualCode")

                            // Start listener
                            val intent = Intent().apply {
                                setClassName(
                                    context,
                                    "pl.remoh.wowarenanotify.fcm.RealtimeListenerService"
                                )
                            }
                            context.startService(intent)

                            isLoading = false
                            statusText = "✅ Device paired successfully!"

                        } else {
                            isLoading = false
                            statusText = "❌ Pairing failed (status $status)"
                        }
                    } catch (e: Exception) {
                        Log.e(TAG, "❌ Manual pairing error", e)
                        isLoading = false
                        statusText = "❌ Error: ${e.message}"
                    }
                }
            },
            modifier = Modifier
                .fillMaxWidth(0.85f)
                .height(dpH * 7),
            shape = MaterialTheme.shapes.large,
            enabled = !isLoading
        ) {
            if (isLoading) {
                CircularProgressIndicator(
                    color = Color.White,
                    strokeWidth = 2.dp,
                    modifier = Modifier.size(24.dp)
                )
                Spacer(Modifier.width(12.dp))
                Text("Connecting…", style = MaterialTheme.typography.titleMedium)
            } else {
                Text("Pair Device", style = MaterialTheme.typography.titleMedium)
            }
        }

        AnimatedVisibility(visible = statusText != null) {
            Text(
                text = statusText ?: "",
                color = when {
                    statusText?.startsWith("✅") == true -> MaterialTheme.colorScheme.primary
                    statusText?.startsWith("⚠️") == true -> Color(0xFFFFB300)
                    else -> MaterialTheme.colorScheme.error
                },
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(top = dpH * 4)
            )
        }
    }
}
