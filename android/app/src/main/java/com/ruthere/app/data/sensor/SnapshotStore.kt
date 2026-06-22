package com.ruthere.app.data.sensor

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.floatPreferencesKey
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.ruthere.app.core.DataSources
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.sensorSnapshotDataStore: DataStore<Preferences> by preferencesDataStore("sensor_snapshot")

/**
 * Persisted snapshot of the last sensor collection: raw cumulative counters (for
 * delta computation next cycle) + normalized 0..1 values (for M9 to upload).
 *
 * Stored per-source so deltas (steps, unlocks, motion) can subtract the previous
 * baseline; instantaneous sources (charging, headset, light) just overwrite.
 */
class SnapshotStore(private val context: Context) {

    private val lastCollectedAt = longPreferencesKey("last_collected_at")

    /** Raw counters from the last cycle (steps total, unlock count, motion count, ...). */
    private val rawKeys: Map<String, Preferences.Key<Float>> = DataSources.IDS.associateWith {
        floatPreferencesKey("raw_${it}")
    }

    /** Normalized 0..1 values from the last cycle (consumed by M9 upload). */
    private val normKeys: Map<String, Preferences.Key<Float>> = DataSources.IDS.associateWith {
        floatPreferencesKey("norm_${it}")
    }

    /** The last normalized snapshot (7 values), or zeros if never collected. */
    val normalized: Flow<Map<String, Float>> = context.sensorSnapshotDataStore.data.map { prefs ->
        DataSources.IDS.associateWith { id -> normKeys[id]?.let { prefs[it] } ?: 0f }
    }

    suspend fun currentNormalized(): Map<String, Float> = normalized.first()

    /** Previous raw counters (baseline for delta sources), or empty if first run. */
    suspend fun previousRaw(): Map<String, Float> {
        val prefs = context.sensorSnapshotDataStore.data.first()
        return DataSources.IDS.associateWith { id -> rawKeys[id]?.let { prefs[it] } ?: 0f }
    }

    /** Persist the new raw counters + normalized values + timestamp. */
    suspend fun save(raw: Map<String, Float>, normalized: Map<String, Float>) {
        context.sensorSnapshotDataStore.edit { prefs ->
            prefs[lastCollectedAt] = System.currentTimeMillis()
            DataSources.IDS.forEach { id ->
                prefs[rawKeys[id]!!] = raw[id] ?: 0f
                prefs[normKeys[id]!!] = normalized[id] ?: 0f
            }
        }
    }
}
