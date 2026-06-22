package com.ruthere.app.data.prefs

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.tokenDataStore: DataStore<Preferences> by preferencesDataStore("auth_tokens")

/** Stores the JWT access token (DataStore Preferences). */
class TokenStore(private val context: Context) {

    private val tokenKey = stringPreferencesKey("access_token")

    val token: Flow<String?> = context.tokenDataStore.data.map { it[tokenKey] }

    suspend fun current(): String? = token.first()

    suspend fun save(token: String) {
        context.tokenDataStore.edit { it[tokenKey] = token }
    }

    suspend fun clear() {
        context.tokenDataStore.edit { it.remove(tokenKey) }
    }
}
