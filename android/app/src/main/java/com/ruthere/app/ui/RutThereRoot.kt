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
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.ruthere.app.core.ServiceLocator
import com.ruthere.app.ui.nav.Routes
import com.ruthere.app.ui.screens.PlaceholderScreen
import com.ruthere.app.ui.screens.about.AboutScreen
import com.ruthere.app.ui.screens.checkin.CheckInScreen
import com.ruthere.app.ui.screens.friends.FriendAddScreen
import com.ruthere.app.ui.screens.friends.FriendDetailScreen
import com.ruthere.app.ui.screens.friends.FriendRequestsScreen
import com.ruthere.app.ui.screens.friends.FriendsListScreen
import com.ruthere.app.ui.screens.login.LoginScreen
import com.ruthere.app.ui.screens.login.RegisterScreen
import com.ruthere.app.ui.screens.login.VerifyScreen
import com.ruthere.app.ui.screens.settings.ServerConfigScreen
import kotlinx.coroutines.launch

private data class Tab(val route: String, val label: String, val icon: @Composable () -> Unit)

private val MAIN_TABS = setOf(Routes.MAIN, Routes.PROFILE, Routes.SERVER_CONFIG)

/** Root composable: hosts the nav graph (auth flow + friends + settings). */
@Composable
fun RutThereRoot(
    startRoute: String,
    onLogout: () -> Unit,
) {
    val navController = rememberNavController()
    val scope = androidx.compose.runtime.rememberCoroutineScope()
    var myUserId by remember { mutableStateOf(-1) }

    // Fetch the current user id once (for the requests screen to distinguish in/out).
    androidx.compose.runtime.LaunchedEffect(startRoute) {
        if (startRoute != Routes.LOGIN) {
            scope.launch {
                runCatching { ServiceLocator.networkClient.api.me() }.onSuccess { myUserId = it.id }
            }
        }
    }

    val tabs = remember {
        listOf(
            Tab(Routes.MAIN, "好友", { Icon(Icons.Filled.People, null) }),
            Tab(Routes.PROFILE, "我的", { Icon(Icons.Filled.Person, null) }),
            Tab(Routes.SERVER_CONFIG, "设置", { Icon(Icons.Filled.Settings, null) }),
        )
    }

    val backStack by navController.currentBackStackEntryAsState()
    val currentRoute = backStack?.destination?.route

    Scaffold(
        bottomBar = {
            if (currentRoute in MAIN_TABS) {
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
                    onGoSettings = { navController.navigate(Routes.SERVER_CONFIG) },
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

            // --- friends (M7) ---
            composable(Routes.MAIN) {
                FriendsListScreen(
                    onAddFriend = { navController.navigate(Routes.FRIEND_ADD) },
                    onOpenRequests = { navController.navigate(Routes.FRIEND_REQUESTS) },
                    onOpenFriend = { fsId, nick, email ->
                        navController.navigate(Routes.friendDetail(fsId, email, nick))
                    },
                )
            }
            composable(Routes.FRIEND_ADD) {
                FriendAddScreen(onBack = { navController.popBackStack() })
            }
            composable(Routes.FRIEND_REQUESTS) {
                FriendRequestsScreen(
                    myUserId = myUserId,
                    onBack = { navController.popBackStack() },
                )
            }
            composable(
                Routes.FRIEND_DETAIL,
                arguments = listOf(
                    navArgument("friendship_id") { type = NavType.IntType },
                    navArgument("email") { type = NavType.StringType },
                    navArgument("nickname") { type = NavType.StringType; nullable = true },
                ),
            ) { entry ->
                val fsId = entry.arguments?.getInt("friendship_id") ?: -1
                val email = entry.arguments?.getString("email").orEmpty()
                val nick = entry.arguments?.getString("nickname")?.ifBlank { null }
                FriendDetailScreen(
                    friendshipId = fsId,
                    email = email,
                    nickname = nick,
                    onDeleted = { navController.popBackStack() },
                    onBack = { navController.popBackStack() },
                )
            }

            composable(Routes.PROFILE) { CheckInScreen() }
            composable(Routes.SERVER_CONFIG) {
                ServerConfigScreen(onGoAbout = { navController.navigate(Routes.ABOUT) })
            }
            composable(Routes.ABOUT) {
                AboutScreen(onBack = { navController.popBackStack() })
            }
        }
    }
}
