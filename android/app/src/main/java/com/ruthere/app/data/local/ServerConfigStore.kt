package com.ruthere.app.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.ruthere.app.BuildConfig
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

/** Default backend address (from BuildConfig, user-overridable). */
val DEFAULT_SERVER_IP: String = BuildConfig.DEFAULT_SERVER_IP
const val DEFAULT_SERVER_PORT: Int = BuildConfig.DEFAULT_SERVER_PORT

private val Context.serverConfigDataStore: DataStore<Preferences> by preferencesDataStore("server_config")

/** Persists the user-configurable backend server IP and port (DataStore Preferences). */
class ServerConfigStore(private val context: Context) {

    private val ipKey = stringPreferencesKey("server_ip")
    private val portKey = intPreferencesKey("server_port")

    /** Flow of the current server address (falls back to defaults when unset). */
    val config: Flow<ServerAddress> = context.serverConfigDataStore.data.map { prefs ->
        ServerAddress(
            ip = prefs[ipKey] ?: DEFAULT_SERVER_IP,
            port = prefs[portKey] ?: DEFAULT_SERVER_PORT,
        )
    }

    /** Snapshot of the current config (defaults if unset). */
    suspend fun current(): ServerAddress = config.first()

    /** Persist the given address; empty/blank IP resets to default. */
    suspend fun save(ip: String, port: Int) {
        context.serverConfigDataStore.edit { prefs ->
            prefs[ipKey] = ip.trim()
            prefs[portKey] = port
        }
    }

    /** Reset to the BuildConfig defaults. */
    suspend fun resetToDefault() {
        context.serverConfigDataStore.edit { prefs ->
            prefs[ipKey] = DEFAULT_SERVER_IP
            prefs[portKey] = DEFAULT_SERVER_PORT
        }
    }
}

data class ServerAddress(val ip: String, val port: Int) {
    /** `http://ip:port/` — the Retrofit base URL. */
    fun toBaseUrl(): String = "http://$ip:$port/"
}
