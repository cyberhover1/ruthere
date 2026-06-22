package com.ruthere.app.core

import android.content.Context
import com.ruthere.app.data.local.ServerConfigStore
import com.ruthere.app.data.prefs.TokenStore
import com.ruthere.app.data.remote.NetworkClient
import com.ruthere.app.data.repo.AuthRepository

/**
 * Lightweight singleton service container (no DI framework).
 *
 * Initialized once from [RutThereApp.onCreate]; the rest of the app reads
 * dependencies from here. Keeps configuration-cache happy by being a plain
 * object with late-init state.
 */
object ServiceLocator {

    private lateinit var appContext: Context

    val serverConfigStore: ServerConfigStore by lazy { ServerConfigStore(appContext) }
    val tokenStore: TokenStore by lazy { TokenStore(appContext) }
    val networkClient: NetworkClient by lazy { NetworkClient(serverConfigStore, tokenStore) }

    val authRepository: AuthRepository by lazy { AuthRepository(networkClient, tokenStore) }

    fun init(context: Context) {
        appContext = context.applicationContext
    }
}
