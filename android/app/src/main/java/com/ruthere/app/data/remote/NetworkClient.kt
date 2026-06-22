package com.ruthere.app.data.remote

import com.ruthere.app.data.local.ServerAddress
import com.ruthere.app.data.local.ServerConfigStore
import com.ruthere.app.data.prefs.TokenStore
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import java.util.concurrent.TimeUnit

/**
 * Builds and rebuilds the Retrofit [ApiService] from the current server config.
 *
 * The base URL is dynamic: when the user changes the server address in Settings,
 * call [rebuild] to construct a fresh Retrofit instance pointing at the new host.
 */
class NetworkClient(
    private val serverConfigStore: ServerConfigStore,
    private val tokenStore: TokenStore,
) {
    private val moshi: Moshi = Moshi.Builder().add(KotlinJsonAdapterFactory()).build()

    private val authInterceptor = Interceptor { chain ->
        val token = runBlocking { tokenStore.current() }
        val req = chain.request().newBuilder().apply {
            if (!token.isNullOrBlank()) header("Authorization", "Bearer $token")
        }.build()
        chain.proceed(req)
    }

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val httpClient: OkHttpClient = OkHttpClient.Builder()
        .addInterceptor(authInterceptor)
        .addInterceptor(loggingInterceptor)
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .writeTimeout(20, TimeUnit.SECONDS)
        .build()

    @Volatile
    private var currentAddress: ServerAddress? = null

    @Volatile
    private var currentApi: ApiService? = null

    /** The live [ApiService]; (re)builds on demand when the address changes. */
    val api: ApiService
        get() {
            val addr = runBlocking { serverConfigStore.current() }
            val cached = currentApi
            if (cached != null && currentAddress == addr) return cached
            return build(addr).also {
                currentAddress = addr
                currentApi = it
            }
        }

    /** Force a rebuild after the server config is saved (next [api] call uses new address). */
    fun rebuild() {
        currentApi = null
        currentAddress = null
    }

    private fun build(addr: ServerAddress): ApiService {
        val retrofit = Retrofit.Builder()
            .baseUrl(addr.toBaseUrl())
            .client(httpClient)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()
        return retrofit.create(ApiService::class.java)
    }
}
