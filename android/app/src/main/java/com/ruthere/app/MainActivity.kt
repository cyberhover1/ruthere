package com.ruthere.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import com.ruthere.app.core.ServiceLocator
import com.ruthere.app.ui.RutThereRoot
import com.ruthere.app.ui.nav.Routes
import com.ruthere.app.ui.theme.RutThereTheme
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            RutThereTheme {
                AppEntry()
            }
        }
    }
}

/** Resolves the start route from the stored token, then renders the root graph. */
@Composable
private fun AppEntry() {
    var startRoute by remember { mutableStateOf<String?>(null) }
    val scope = androidx.compose.runtime.rememberCoroutineScope()

    LaunchedEffect(Unit) {
        scope.launch {
            startRoute = if (ServiceLocator.authRepository.isTokenPresent()) Routes.MAIN else Routes.LOGIN
        }
    }

    val route = startRoute
    if (route != null) {
        RutThereRoot(
            startRoute = route,
            onLogout = {
                // Handled within screens; placeholder for future global logout wiring.
            },
        )
    }
}
