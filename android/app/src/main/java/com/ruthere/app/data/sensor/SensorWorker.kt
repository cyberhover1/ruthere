package com.ruthere.app.data.sensor

import android.content.Context
import android.util.Log
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.ruthere.app.core.ServiceLocator

/**
 * Periodic sensor-collection worker.
 *
 * Each run takes a snapshot of all 7 data sources, normalizes to 0..1, and
 * persists both the raw baseline (for next cycle's deltas) and the normalized
 * values (for M9 to upload). No network or upload here.
 */
class SensorWorker(appContext: Context, params: WorkerParameters) :
    CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result {
        return try {
            val collector = ServiceLocator.sensorCollector
            val store = ServiceLocator.snapshotStore
            val (raw, normalized) = collector.collect()
            store.save(raw, normalized)
            Log.d(TAG, "collected: $normalized")
            Result.success()
        } catch (e: Exception) {
            Log.e(TAG, "sensor collection failed", e)
            Result.retry()
        }
    }

    companion object {
        const val TAG = "SensorWorker"
        const val WORK_NAME = "ruthere_sensor_collection"
    }
}
