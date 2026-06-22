package com.ruthere.app.ui

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.People
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.ruthere.app.ui.nav.Routes
import com.ruthere.app.ui.screens.PlaceholderScreen
import com.ruthere.app.ui.screens.login.LoginScreen
import com.ruthere.app.ui.screens.login.RegisterScreen
import com.ruthere.app.ui.screens.login.VerifyScreen
import com.ruthere.app.ui.screens.settings.ServerConfigScreen

private data class Tab(val route: String, val label: String, val icon: @Composable () -> Unit)

/** Root composable: hosts the nav graph (auth flow + main placeholder). */
@Composable
fun RutThereRoot(
    startRoute: String,
    onLogout: () -> Unit,
) {
    val navController = rememberNavController()

    val tabs = remember {
        listOf(
            Tab(Routes.MAIN, "好友", { Icon(Icons.Filled.People, null) }),
            Tab("profile", "我的", { Icon(Icons.Filled.Person, null) }),
            Tab(Routes.SERVER_CONFIG, "设置", { Icon(Icons.Filled.Settings, null) }),
        )
    }

    val backStack by navController.currentBackStackEntryAsState()
    val currentRoute = backStack?.destination?.route

    Scaffold(
        bottomBar = {
            // Show the bottom bar only inside the main graph.
            val showBar = currentRoute in setOf(Routes.MAIN, "profile", Routes.SERVER_CONFIG)
            if (showBar) {
                NavigationBar {
                    tabs.forEach { tab ->
                        val selected = currentRoute == tab.route ||
                            navController.currentDestination?.hierarchy?.any { it.route == tab.route } == true
                        NavigationBarItem(
                            selected = selected,
                            onClick = {
                                navController.navigate(tab.route) {
                                    popUpTo(navController.graph.findStartDestination().id) { saveState = true }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            icon = tab.icon,
                            label = { Text(tab.label) },
                        )
                    }
                }
            }
        },
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = startRoute,
            modifier = Modifier.fillMaxSize().padding(padding),
        ) {
            composable(Routes.LOGIN) {
                LoginScreen(
                    onLoggedIn = { navController.navigate(Routes.MAIN) { popUpTo(Routes.LOGIN) { inclusive = true } } },
                    onGoRegister = { navController.navigate(Routes.REGISTER) },
                )
            }
            composable(Routes.REGISTER) {
                RegisterScreen(
                    onRegistered = { email -> navController.navigate("${Routes.VERIFY}/$email") },
                    onBack = { navController.popBackStack() },
                )
            }
            composable("${Routes.VERIFY}/{email}") { entry ->
                val email = entry.arguments?.getString("email").orEmpty()
                VerifyScreen(
                    email = email,
                    onVerified = { navController.navigate(Routes.LOGIN) { popUpTo(Routes.REGISTER) { inclusive = true } } },
                    onBack = { navController.popBackStack() },
                )
            }
            composable(Routes.MAIN) { PlaceholderScreen("好友列表") }
            composable("profile") { PlaceholderScreen("我的") }
            composable(Routes.SERVER_CONFIG) { ServerConfigScreen() }
        }
    }

    // Drive external logout by popping back to login.
    androidx.compose.runtime.LaunchedEffect(Unit) {
        // placeholder for future logout events
    }
}
