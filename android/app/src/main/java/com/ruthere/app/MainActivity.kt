package com.ruthere.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.ruthere.app.ui.RutThereApp
import com.ruthere.app.ui.theme.RutThereTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            RutThereTheme {
                RutThereApp()
            }
        }
    }
}
