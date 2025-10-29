package pl.remoh.wowarenanotify.ui.theme

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

// 🌗 Globalny kontroler motywu z pamięcią w SharedPreferences
object ThemeController {
    private const val PREFS_NAME = "wow_arena_prefs"
    private const val KEY_DARK_MODE = "dark_mode_enabled"

    // Domyślnie ciemny motyw
    var isDarkTheme by mutableStateOf(true)
        private set

    // 🔹 Wczytaj motyw z pamięci (wywoływane w MainActivity)
    fun loadTheme(context: Context) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        isDarkTheme = prefs.getBoolean(KEY_DARK_MODE, true)
    }

    // 🔹 Zapisz zmianę motywu
    fun setDarkTheme(context: Context, value: Boolean) {
        isDarkTheme = value
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putBoolean(KEY_DARK_MODE, value).apply()
    }
}
