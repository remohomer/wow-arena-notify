package pl.remoh.wowarenanotify.ui.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

// 🌙 Dark mode color scheme
private val DarkColorScheme = darkColorScheme(
    primary = PrimaryBlueLight,
    onPrimary = Color.Black,
    background = BackgroundDark,
    surface = BackgroundDark,
    onSurface = Color.White,
    secondary = PrimaryBlueDark
)

// ☀️ Light mode color scheme
private val LightColorScheme = lightColorScheme(
    primary = PrimaryBlue,
    onPrimary = Color.White,
    background = BackgroundLight,
    surface = BackgroundLight,
    onSurface = Color.Black,
    secondary = PrimaryBlueLight
)

@Composable
fun WoWArenaNotifyTheme(
    darkTheme: Boolean = ThemeController.isDarkTheme, // 👈 zmienione
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        // 🎨 Dynamic colors (Android 12+)
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }

        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    // 🪟 Status bar kolor i kontrast
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.primary.toArgb()
            WindowCompat.getInsetsController(window, view)
                .isAppearanceLightStatusBars = !darkTheme
        }
    }

    // 💅 Globalny motyw aplikacji
    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
