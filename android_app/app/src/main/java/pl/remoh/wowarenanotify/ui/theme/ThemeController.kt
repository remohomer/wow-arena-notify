package pl.remoh.wowarenanotify.ui.theme

import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue

// 🌗 Globalny stan motywu aplikacji
object ThemeController {
    var isDarkTheme by mutableStateOf(false)
}
