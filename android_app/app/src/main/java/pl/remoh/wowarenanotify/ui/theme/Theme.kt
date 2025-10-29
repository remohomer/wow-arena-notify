package pl.remoh.wowarenanotify.ui.theme

import android.app.Activity
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

// 🌑 Dark theme — kontrastowy, ciepły
private val DarkColorScheme = darkColorScheme(
    primary = PortalOrange,
    onPrimary = Color.White,              // ✅ biały tekst na pomarańczowych przyciskach
    secondary = PortalAmber,
    background = BackgroundDark,
    surface = SurfaceDark,
    onSurface = TextPrimaryDark
)

// ☀️ Light theme — chłodny kamień + ciepłe akcenty
private val LightColorScheme = lightColorScheme(
    primary = PortalDeep,
    onPrimary = Color.White,              // ✅ biały tekst na przyciskach
    secondary = PortalAmber,
    background = BackgroundLight,
    surface = SurfaceLight,
    onSurface = TextPrimaryLight
)

@Composable
fun WoWArenaNotifyTheme(
    darkTheme: Boolean = ThemeController.isDarkTheme,
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme
    val navBarColor = if (darkTheme) NavBarDark else NavBarLight

    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.background.toArgb()
            window.navigationBarColor = navBarColor.toArgb()
            WindowCompat.getInsetsController(window, view)
                .isAppearanceLightStatusBars = !darkTheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
