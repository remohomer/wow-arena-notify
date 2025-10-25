package pl.remoh.wowarenanotify.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.QrCode
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import androidx.navigation.compose.currentBackStackEntryAsState

@Composable
fun BottomNavigationBar(navController: NavHostController) {
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = backStackEntry?.destination?.route

    val scheme = MaterialTheme.colorScheme
    val activeColor = scheme.primary
    val inactiveColor = scheme.onSurface.copy(alpha = 0.6f)
    val background = scheme.surface

    NavigationBar(
        containerColor = background,
        tonalElevation = 6.dp
    ) {
        listOf(
            Triple("home", Icons.Default.Home, "Home"),
            Triple("pairing", Icons.Default.QrCode, "Pair devices"),
            Triple("settings", Icons.Default.Settings, "Settings")
        ).forEach { (route, icon, label) ->
            val selected = currentRoute == route

            NavigationBarItem(
                selected = false, // ❗ wyłączamy natywne zaznaczenie
                onClick = { navController.navigate(route) },
                icon = {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center,
                        modifier = Modifier
                            .clickable { navController.navigate(route) }
                            .padding(vertical = 4.dp, horizontal = 12.dp)
                            .background(
                                color = if (selected) activeColor.copy(alpha = 0.15f)
                                else Color.Transparent,
                                shape = CircleShape
                            )
                            .padding(8.dp)
                    ) {
                        Icon(
                            imageVector = icon,
                            contentDescription = label,
                            tint = if (selected) activeColor else inactiveColor,
                            modifier = Modifier.size(22.dp)
                        )
                        Text(
                            text = label,
                            color = if (selected) activeColor else inactiveColor,
                            style = MaterialTheme.typography.labelSmall
                        )
                    }
                },
                label = null,
                colors = NavigationBarItemDefaults.colors(
                    indicatorColor = Color.Transparent,
                    selectedIconColor = Color.Transparent,
                    unselectedIconColor = Color.Transparent
                )
            )
        }
    }
}
