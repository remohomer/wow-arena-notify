// #ArenaCountdown.kt

package pl.remoh.wowarenanotify.ui.screens

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay

@OptIn(ExperimentalAnimationApi::class)
@Composable
fun EpicArenaCountdown(remaining: Int) {
    var showFight by remember { mutableStateOf(false) }
    var showMissed by remember { mutableStateOf(false) }

    // Sterowanie fazami po osiągnięciu 0
    LaunchedEffect(remaining) {
        if (remaining > 0) {
            // reset stanów kiedy wracamy do dodatnich sekund
            showFight = false
            showMissed = false
        } else if (remaining == 0) {
            // 2s FIGHT, potem (jeśli nadal jesteśmy na tym ekranie) 2.5s missed
            showFight = true
            showMissed = false
            delay(2000)
            if (showFight) { // jeśli w międzyczasie nie przyszło arena_stop
                showFight = false
                showMissed = true
                delay(2500)
                showMissed = false
            }
        }
    }

    when {
        showFight -> FightScreen()
        showMissed -> MissedArenaScreen()
        remaining in 1..3 -> CountdownNumber(remaining)
        // dla pozostałych sekund nie renderujemy nic (ekran rodzica pokazuje „Waiting”)
        else -> Spacer(Modifier.size(0.dp))
    }
}

@Composable
private fun CountdownNumber(remaining: Int) {
    val scale = remember { Animatable(1f) }
    val color = when (remaining) {
        3 -> Color(0xFF4CAF50) // zielony
        2 -> Color(0xFFFFC107) // żółty
        1 -> Color(0xFFF44336) // czerwony
        else -> MaterialTheme.colorScheme.primary
    }

    LaunchedEffect(remaining) {
        scale.snapTo(1.5f)
        scale.animateTo(1f, animationSpec = tween(400, easing = FastOutSlowInEasing))
    }

    AnimatedContent(
        targetState = remaining,
        transitionSpec = {
            (fadeIn(animationSpec = tween(250)) + scaleIn(initialScale = 2f)) togetherWith
                    (fadeOut(animationSpec = tween(250)) + scaleOut(targetScale = 0.3f))
        },
        label = "arena_countdown_anim"
    ) { value ->
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = value.toString(),
                fontSize = 96.sp,
                fontWeight = FontWeight.Bold,
                color = color,
                modifier = Modifier.scale(scale.value),
                textAlign = TextAlign.Center
            )
        }
    }
}

@Composable
private fun FightScreen() {
    val scale = remember { Animatable(0.9f) }
    val color = Color(0xFFE53935)

    LaunchedEffect(Unit) {
        scale.animateTo(1.3f, tween(450, easing = FastOutSlowInEasing))
        scale.animateTo(1f, tween(450))
    }

    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = "⚔️ The battle has begun.",
            fontSize = 40.sp,
            fontWeight = FontWeight.ExtraBold,
            color = color,
            modifier = Modifier.scale(scale.value),
            textAlign = TextAlign.Center
        )
    }
}

@Composable
private fun MissedArenaScreen() {
    val fade = remember { Animatable(0f) }
    LaunchedEffect(Unit) { fade.animateTo(1f, tween(800)) }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .alpha(fade.value),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = "💀 The gates opened... without you.",
            fontSize = 22.sp,
            fontWeight = FontWeight.Medium,
            color = Color.Gray.copy(alpha = 0.85f),
            textAlign = TextAlign.Center
        )
    }
}
