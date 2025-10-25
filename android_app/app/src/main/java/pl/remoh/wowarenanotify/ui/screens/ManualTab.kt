package pl.remoh.wowarenanotify.ui.screens.tabs

import android.content.Context
import androidx.compose.animation.AnimatedVisibility
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

@Composable
fun ManualTab(context: Context, dpW: Dp, dpH: Dp) {
    var manualCode by remember { mutableStateOf("") }
    var showResult by remember { mutableStateOf<String?>(null) }
    val focusManager = LocalFocusManager.current

    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        OutlinedTextField(
            value = manualCode,
            onValueChange = { manualCode = it },
            label = { Text("Enter connection code") },
            singleLine = true,
            modifier = Modifier
                .fillMaxWidth(0.85f)
                .padding(top = dpH * 4)
        )

        Spacer(Modifier.height(dpH * 2))

        Button(
            onClick = {
                focusManager.clearFocus()
                showResult = if (manualCode.length >= 6)
                    "✅ Device paired successfully!"
                else
                    "⚠️ Invalid code — please check again."
            },
            modifier = Modifier
                .fillMaxWidth(0.85f)
                .height(dpH * 7),
            shape = MaterialTheme.shapes.large
        ) {
            Text("Pair Device", style = MaterialTheme.typography.titleMedium)
        }

        AnimatedVisibility(visible = showResult != null) {
            Text(
                text = showResult ?: "",
                color = if (showResult?.startsWith("✅") == true)
                    Color(0xFF4CAF50)
                else
                    Color(0xFFF44336),
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(top = dpH * 3)
            )
        }
    }
}
