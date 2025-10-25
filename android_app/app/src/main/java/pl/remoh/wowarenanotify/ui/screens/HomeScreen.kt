package pl.remoh.wowarenanotify.ui.screens

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.Crossfade
import androidx.compose.animation.ExperimentalAnimationApi
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.scaleIn
import androidx.compose.animation.scaleOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import pl.remoh.wowarenanotify.R

enum class ArenaState {
    WAITING, COUNTDOWN
}

@Composable
fun HomeScreen() {
    val context = LocalContext.current
    var arenaState by remember { mutableStateOf(ArenaState.WAITING) }
    var remaining by remember { mutableStateOf(0) }

    // 📡 Nasłuchuj broadcastów z CountdownService i RealtimeListenerService
    DisposableEffect(Unit) {
        val mainReceiver = object : BroadcastReceiver() {
            override fun onReceive(ctx: Context?, intent: Intent?) {
                when (intent?.action) {
                    "ARENA_COUNTDOWN_UPDATE" -> {
                        when (intent.getStringExtra("state")) {
                            "COUNTDOWN" -> {
                                arenaState = ArenaState.COUNTDOWN
                                remaining = intent.getIntExtra("remaining", 0)
                            }

                            "WAITING" -> {
                                arenaState = ArenaState.WAITING
                                remaining = 0
                            }
                        }
                    }

                    // 🔹 Dodatkowy broadcast z RealtimeListenerService przy arena_stop
                    "ARENA_STOP_UI_RESET" -> {
                        arenaState = ArenaState.WAITING
                        remaining = 0
                    }
                }
            }
        }

        val filter = IntentFilter().apply {
            addAction("ARENA_COUNTDOWN_UPDATE")
            addAction("ARENA_STOP_UI_RESET")
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            context.registerReceiver(mainReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            context.registerReceiver(mainReceiver, filter)
        }

        onDispose { context.unregisterReceiver(mainReceiver) }
    }

    // 🧭 Główny layout
    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 32.dp),
        contentAlignment = Alignment.Center
    ) {
        Crossfade(
            targetState = arenaState,
            animationSpec = tween(500, easing = FastOutSlowInEasing),
            label = "arena_state_crossfade"
        ) { state ->
            when (state) {
                ArenaState.WAITING -> WaitingView()
                ArenaState.COUNTDOWN -> CountdownView(remaining)
            }
        }
    }
}

@Composable
fun WaitingView() {
    // 🔹 Subtelna animacja pulsowania portalu
    val scaleAnim = remember { Animatable(1f) }
    val alphaAnim = remember { Animatable(1f) }

    LaunchedEffect(Unit) {
        while (true) {
            scaleAnim.animateTo(
                1.08f,
                animationSpec = tween(1800, easing = FastOutSlowInEasing)
            )
            alphaAnim.animateTo(0.8f, animationSpec = tween(1800))
            scaleAnim.animateTo(1f, animationSpec = tween(1800))
            alphaAnim.animateTo(1f, animationSpec = tween(1800))
        }
    }

    // 🔹 Subtelna animacja błysku na tekście
    val textAlpha = remember { Animatable(1f) }
    LaunchedEffect(Unit) {
        while (true) {
            textAlpha.animateTo(0.4f, tween(1200))
            textAlpha.animateTo(1f, tween(1200))
        }
    }

    // 🔹 Layout
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 24.dp)
    ) {
        // 🌀 Portal
        Image(
            painter = painterResource(id = R.drawable.portal_icon),
            contentDescription = "Arena Portal",
            modifier = Modifier
                .size(220.dp)
                .scale(scaleAnim.value)
                .alpha(alphaAnim.value)
        )

        Spacer(Modifier.height(32.dp))

        // 🕓 Tekst
        Text(
            text = "Waiting for worthy opponents...",
            style = MaterialTheme.typography.titleMedium,
            color = Color.Gray.copy(alpha = textAlpha.value),
            textAlign = TextAlign.Center,
            fontWeight = FontWeight.Medium
        )
    }
}

@OptIn(ExperimentalAnimationApi::class)
@Composable
fun CountdownView(remaining: Int) {
    // 🔹 Emoji i kolor zależnie od zakresu sekund
    val (emoji, color) = when {
        remaining <= 0 -> "💀 FIGHT!" to Color(0xFFB71C1C)
        remaining <= 5 -> "💀" to Color(0xFFD32F2F)
        remaining <= 10 -> "🔥" to Color(0xFFF44336)
        remaining <= 20 -> "⚡" to Color(0xFFFFA000)
        else -> "🕒" to MaterialTheme.colorScheme.primary
    }

    // 🔹 Animacja pulsowania
    val scale = remember { Animatable(1f) }
    LaunchedEffect(remaining) {
        scale.snapTo(1.3f)
        scale.animateTo(
            1f,
            animationSpec = tween(400, easing = FastOutSlowInEasing)
        )
    }

    AnimatedContent(
        targetState = remaining,
        transitionSpec = {
            (fadeIn(animationSpec = tween(250)) + scaleIn(initialScale = 1.5f)) togetherWith
                    (fadeOut(animationSpec = tween(250)) + scaleOut(targetScale = 0.7f))
        },
        label = "arena_countdown_dynamic"
    ) { value ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = emoji,
                fontSize = 64.sp,
                modifier = Modifier.scale(scale.value),
                color = color
            )
            if (value > 0) {
                Text(
                    text = "$value",
                    fontSize = 64.sp,
                    fontWeight = FontWeight.Bold,
                    color = color,
                    modifier = Modifier.scale(scale.value)
                )
            }
        }
    }
}
