package com.ruthere.app.data.sensor

import android.content.Context
import android.util.Log
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.ruthere.app.core.ServiceLocator

/**
 * Periodic sensor-collection + activity-report worker.
 *
 * Each run:
 * 1. Takes a snapshot of all 7 data sources, normalizes to 0..1, persists the
 *    raw baseline + normalized values (M8).
 * 2. Uploads the normalized values to /activity/report (M9). The backend
 *    computes per-friend visible values and delivers friends' desensitized
 *    activity + pending notifications.
 * 3. Stores the delivered friends' activity locally for M10 to render.
 *
 * Upload failure (e.g. no token, network error) does NOT fail the worker —
 * collection is local and succeeds regardless; upload retries next cycle.
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

            // Upload (M9). Skip silently if not logged in or upload fails.
            runCatching {
                val token = ServiceLocator.tokenStore.current()
                if (!token.isNullOrBlank()) {
                    val resp = ServiceLocator.activityRepository.report(normalized)
                    ServiceLocator.friendsActivityStore.replaceAll(resp.friends_activity)
                    Log.d(TAG, "reported; ${resp.friends_activity.size} friends activity delivered")
                }
            }.onFailure { Log.w(TAG, "upload skipped/failed: ${it.message}") }

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
