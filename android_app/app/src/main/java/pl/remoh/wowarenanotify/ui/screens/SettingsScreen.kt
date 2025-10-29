package pl.remoh.wowarenanotify.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import pl.remoh.wowarenanotify.ui.theme.ThemeController
import pl.remoh.wowarenanotify.core.SettingsManager

@Composable
fun SettingsScreen() {
    val context = LocalContext.current
    var darkMode by remember { mutableStateOf(ThemeController.isDarkTheme) }

    var notificationsEnabled by remember { mutableStateOf(SettingsManager.isNotificationsEnabled(context)) }
    var feedbackVibration by remember { mutableStateOf(SettingsManager.isVibrationEnabled(context)) }
    var feedbackSound by remember { mutableStateOf(SettingsManager.isSoundsEnabled(context)) }
    var feedbackSeconds by remember { mutableStateOf(SettingsManager.getFinalSeconds(context).toFloat()) }
    var backgroundEnabled by remember { mutableStateOf(SettingsManager.isBackgroundEnabled(context)) }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        contentAlignment = Alignment.TopCenter
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {

            Text(
                text = "⚙️ Settings",
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(28.dp))

            // 🌙 Display & Theme
            Text(
                text = "🌙 Display & Theme",
                style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.SemiBold)
            )
            Spacer(modifier = Modifier.height(12.dp))
            SettingToggleRow(
                label = "Dark Mode",
                checked = darkMode,
                onCheckedChange = {
                    darkMode = it
                    ThemeController.setDarkTheme(context, it)
                }
            )

            Spacer(modifier = Modifier.height(32.dp))

            // 🔔 Notifications & Feedback
            Text(
                text = "🔔 Notifications & Feedback",
                style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.SemiBold)
            )
            Spacer(modifier = Modifier.height(12.dp))
            SettingToggleRow(
                label = "Enable Notifications",
                checked = notificationsEnabled,
                onCheckedChange = {
                    notificationsEnabled = it
                    SettingsManager.setNotificationsEnabled(context, it)
                }
            )
            SettingToggleRow(
                label = "Vibration Feedback",
                checked = feedbackVibration,
                onCheckedChange = {
                    feedbackVibration = it
                    SettingsManager.setVibrationEnabled(context, it)
                }
            )
            SettingToggleRow(
                label = "Sound Feedback",
                checked = feedbackSound,
                onCheckedChange = {
                    feedbackSound = it
                    SettingsManager.setSoundsEnabled(context, it)
                }
            )

            if (feedbackVibration || feedbackSound) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Final seconds range: ${feedbackSeconds.toInt()} s",
                    style = MaterialTheme.typography.bodyLarge
                )
                Slider(
                    value = feedbackSeconds,
                    onValueChange = {
                        feedbackSeconds = it
                        SettingsManager.setFinalSeconds(context, it.toInt())
                    },
                    valueRange = 3f..15f,
                    steps = 11
                )
            }

            Spacer(modifier = Modifier.height(32.dp))

            // ⚙️ Advanced
            Text(
                text = "⚙️ Advanced Settings",
                style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.SemiBold)
            )
            Spacer(modifier = Modifier.height(12.dp))
            SettingToggleRow(
                label = "Run quietly in background",
                checked = backgroundEnabled,
                onCheckedChange = {
                    backgroundEnabled = it
                    SettingsManager.setBackgroundEnabled(context, it)
                }
            )
        }
    }
}


@Composable
private fun SettingToggleRow(
    label: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 6.dp)
    ) {
        Text(label, style = MaterialTheme.typography.bodyLarge)
        Switch(checked = checked, onCheckedChange = onCheckedChange)
    }
}
