package com.ruthere.app.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.ruthere.app.data.remote.dto.FriendActivityOut
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.friendsActivityDataStore: DataStore<Preferences> by preferencesDataStore("friends_activity")

/**
 * Stores the latest desensitized activity delivered for each friend (from
 * /activity/report responses). Consumed by M10 to render the friends list.
 *
 * Each friend's value/time/offline is stored under keyed preferences; the set
 * of currently-known friend ids is kept in a comma-separated index so stale
 * entries (e.g. after deleting a friend) can be pruned.
 */
class FriendsActivityStore(private val context: Context) {

    private val indexKey = stringPreferencesKey("friend_ids")
    private fun valueKey(id: Int) = intPreferencesKey("value_$id")
    private fun timeKey(id: Int) = stringPreferencesKey("time_$id")
    private fun offlineKey(id: Int) = booleanPreferencesKey("offline_$id")

    /** Flow of the latest activity for all known friends. */
    val activities: Flow<Map<Int, FriendActivityOut>> =
        context.friendsActivityDataStore.data.map { prefs ->
            val ids = prefs[indexKey]?.split(",")?.filter { it.isNotBlank() } ?: emptyList()
            ids.mapNotNull { idStr ->
                val id = idStr.toIntOrNull() ?: return@mapNotNull null
                FriendActivityOut(
                    friend_id = id,
                    value = prefs[valueKey(id)] ?: 0,
                    last_reported_at = prefs[timeKey(id)] ?: "",
                    is_offline = prefs[offlineKey(id)] ?: false,
                )
            }.associateBy { it.friend_id }
        }

    suspend fun current(): Map<Int, FriendActivityOut> = activities.first()

    /** Overwrite the store with the latest delivered batch (replaces all). */
    suspend fun replaceAll(items: List<FriendActivityOut>) {
        context.friendsActivityDataStore.edit { prefs ->
            // Clear previous friend keys.
            val oldIds = prefs[indexKey]?.split(",")?.filter { it.isNotBlank() } ?: emptyList()
            oldIds.forEach { idStr ->
                idStr.toIntOrNull()?.let { id ->
                    prefs.remove(valueKey(id))
                    prefs.remove(timeKey(id))
                    prefs.remove(offlineKey(id))
                }
            }
            // Write new.
            val newIds = items.map { it.friend_id }
            prefs[indexKey] = newIds.joinToString(",")
            items.forEach { a ->
                prefs[valueKey(a.friend_id)] = a.value
                prefs[timeKey(a.friend_id)] = a.last_reported_at
                prefs[offlineKey(a.friend_id)] = a.is_offline
            }
        }
    }
}
