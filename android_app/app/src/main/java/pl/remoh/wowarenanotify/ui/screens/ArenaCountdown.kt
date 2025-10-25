package pl.remoh.wowarenanotify.ui.screens

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@OptIn(ExperimentalAnimationApi::class)
@Composable
fun EpicArenaCountdown(remaining: Int) {
    val displayValue = when {
        remaining <= 0 -> "⚔️ FIGHT!"
        remaining <= 3 -> remaining.toString()
        else -> null // pokazujemy tylko ostatnie 3 sekundy
    }

    if (displayValue != null) {
        val scale = remember { Animatable(1f) }
        val color = when (remaining) {
            3 -> Color(0xFF4CAF50) // zielony
            2 -> Color(0xFFFFC107) // żółty
            1 -> Color(0xFFF44336) // czerwony
            else -> Color(0xFF4CAF50)
        }

        // 🔥 Animacja pulsującej skali
        LaunchedEffect(remaining) {
            scale.snapTo(1.5f)
            scale.animateTo(
                1f,
                animationSpec = tween(400, easing = FastOutSlowInEasing)
            )
        }

        AnimatedContent(
            targetState = displayValue,
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
                    text = value,
                    fontSize = if (value == "⚔️ FIGHT!") 48.sp else 96.sp,
                    fontWeight = FontWeight.Bold,
                    color = color,
                    modifier = Modifier.scale(scale.value),
                    textAlign = TextAlign.Center
                )
            }
        }
    }
}
