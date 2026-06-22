package com.ruthere.app

import android.app.Application
import com.ruthere.app.core.SensorScheduler
import com.ruthere.app.core.ServiceLocator

/** Application entry point — initializes the ServiceLocator + sensor scheduler. */
class RutThereApp : Application() {
    override fun onCreate() {
        super.onCreate()
        ServiceLocator.init(this)
        // Start periodic sensor collection (every 30 min). Harmless if started before
        // login; collection is local-only, upload arrives in M9.
        SensorScheduler.start(this)
    }
}
