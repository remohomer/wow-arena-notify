package pl.remoh.wowarenanotify.ui.screens.tabs

import android.content.Context
import android.content.Intent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import pl.remoh.wowarenanotify.PairingActivity

@Composable
fun QRTab(context: Context, dpW: Dp, dpH: Dp) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Button(
            onClick = {
                val intent = Intent(context, PairingActivity::class.java)
                context.startActivity(intent)
            },
            modifier = Modifier
                .fillMaxWidth(0.85f)
                .height(dpH * 8),
            shape = MaterialTheme.shapes.large
        ) {
            Text("📷 Open QR Scanner", style = MaterialTheme.typography.titleMedium)
        }

        Spacer(Modifier.height(dpH * 2))
        Text(
            text = "Scan the QR code from your desktop app to connect devices.",
            textAlign = TextAlign.Center,
            color = Color.Gray,
            modifier = Modifier.padding(horizontal = dpW * 4)
        )
    }
}
