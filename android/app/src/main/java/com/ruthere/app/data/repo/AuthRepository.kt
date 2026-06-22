package com.ruthere.app.data.repo

import com.ruthere.app.data.prefs.TokenStore
import com.ruthere.app.data.remote.NetworkClient
import com.ruthere.app.data.remote.dto.LoginRequest
import com.ruthere.app.data.remote.dto.RegisterRequest
import com.ruthere.app.data.remote.dto.ResendCodeRequest
import com.ruthere.app.data.remote.dto.VerifyRequest

/** Wraps auth API calls + token persistence. */
class AuthRepository(
    private val networkClient: NetworkClient,
    private val tokenStore: TokenStore,
) {
    private val api get() = networkClient.api

    suspend fun register(email: String, password: String) =
        api.register(RegisterRequest(email, password))

    suspend fun resendCode(email: String) = api.resendCode(ResendCodeRequest(email))

    suspend fun verify(email: String, code: String) = api.verify(VerifyRequest(email, code))

    suspend fun login(email: String, password: String, deviceIdentifier: String): String {
        val resp = api.login(LoginRequest(email, password, deviceIdentifier))
        tokenStore.save(resp.access_token)
        return resp.access_token
    }

    suspend fun logout() {
        runCatching { api.logout() }
        tokenStore.clear()
    }

    suspend fun isTokenPresent(): Boolean = tokenStore.current() != null

    /** Force the next request to use the updated server address. */
    fun rebuildClient() = networkClient.rebuild()
}
