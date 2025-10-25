package pl.remoh.wowarenanotify.ui.screens

import android.content.Context
import androidx.compose.animation.*
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import pl.remoh.wowarenanotify.ui.screens.tabs.QRTab
import pl.remoh.wowarenanotify.ui.screens.tabs.ManualTab

@OptIn(ExperimentalAnimationApi::class)
@Composable
fun PairingScreen() {
    val context = LocalContext.current
    var selectedTab by remember { mutableStateOf(0) }

    val tabs = listOf("QR Code", "Manual Code")
    val icons = listOf("📷", "🔢")

    val screenHeight = LocalConfiguration.current.screenHeightDp
    val screenWidth = LocalConfiguration.current.screenWidthDp
    val dpH = (screenHeight / 100f).dp
    val dpW = (screenWidth / 100f).dp
    val dynamicTopPadding = dpH * 5

    Column(
        modifier = Modifier
            .fillMaxSize()
            .imePadding()
            .padding(horizontal = dpW * 6)
            .padding(top = dynamicTopPadding)
            .wrapContentHeight(align = Alignment.Top),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = "🔗 Pair Your Device",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.padding(vertical = dpH * 2)
        )

        TabRow(
            selectedTabIndex = selectedTab,
            containerColor = Color.Transparent,
            contentColor = MaterialTheme.colorScheme.primary
        ) {
            tabs.forEachIndexed { index, title ->
                Tab(
                    selected = selectedTab == index,
                    onClick = { selectedTab = index },
                    text = {
                        Text(
                            text = "${icons[index]} $title",
                            style = MaterialTheme.typography.bodyMedium
                        )
                    }
                )
            }
        }

        Spacer(Modifier.height(dpH * 5))

        AnimatedContent(
            targetState = selectedTab,
            transitionSpec = {
                (slideInHorizontally(
                    animationSpec = tween(350),
                    initialOffsetX = { if (targetState > initialState) it else -it }
                ) + fadeIn(animationSpec = tween(350)))
                    .with(
                        slideOutHorizontally(
                            animationSpec = tween(350),
                            targetOffsetX = { if (targetState > initialState) -it else it }
                        ) + fadeOut(animationSpec = tween(350))
                    )
            },
            label = "pairing_tab_transition"
        ) { tab ->
            when (tab) {
                0 -> QRTab(context, dpW, dpH)
                1 -> ManualTab(context, dpW, dpH)
            }
        }
    }
}
