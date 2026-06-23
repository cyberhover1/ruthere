package com.ruthere.app.ui.screens.settings

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier

/**
 * Server config screen reached from the login page (before the user is logged in).
 * Wraps [ServerConfigScreen] with a top bar + back button and shows NO bottom nav bar.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PreLoginConfigScreen(onBack: () -> Unit, onGoAbout: () -> Unit = {}) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("服务器配置") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, "返回")
                    }
                },
            )
        },
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            ServerConfigScreen(onGoAbout = onGoAbout)
        }
    }
}
