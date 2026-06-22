package com.ruthere.app.core

import android.content.Context
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import com.ruthere.app.data.sensor.SensorWorker
import java.util.concurrent.TimeUnit

/** Schedules the periodic sensor-collection work (every 30 minutes). */
object SensorScheduler {

    private const val INTERVAL_MINUTES = 30L

    /** Enqueue the periodic sensor worker (keeps existing, updates interval). */
    fun start(context: Context) {
        val constraints = Constraints.Builder()
            // Local collection only — no network/battery constraints.
            .build()
        val request = PeriodicWorkRequestBuilder<SensorWorker>(INTERVAL_MINUTES, TimeUnit.MINUTES)
            .setConstraints(constraints)
            .build()
        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            SensorWorker.WORK_NAME,
            ExistingPeriodicWorkPolicy.UPDATE,
            request,
        )
    }

    /** Cancel the periodic sensor worker (e.g. on logout). */
    fun stop(context: Context) {
        WorkManager.getInstance(context).cancelUniqueWork(SensorWorker.WORK_NAME)
    }
}
