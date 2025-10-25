package pl.remoh.wowarenanotify.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import pl.remoh.wowarenanotify.ui.theme.ThemeController

@Composable
fun SettingsScreen() {
    var darkMode by remember { mutableStateOf(ThemeController.isDarkTheme) }

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

            Spacer(modifier = Modifier.height(32.dp))

            // 🔘 Dark Mode toggle
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    "Dark Mode",
                    style = MaterialTheme.typography.bodyLarge
                )

                Switch(
                    checked = darkMode,
                    onCheckedChange = {
                        darkMode = it
                        ThemeController.isDarkTheme = it
                    }
                )
            }

            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = if (darkMode) "🌙 Dark mode enabled" else "☀️ Light mode enabled",
                color = if (darkMode)
                    MaterialTheme.colorScheme.primary
                else
                    MaterialTheme.colorScheme.secondary
            )
        }
    }
}
