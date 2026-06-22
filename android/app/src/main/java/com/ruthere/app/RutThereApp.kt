package com.ruthere.app

import android.app.Application
import com.ruthere.app.core.ServiceLocator

/** Application entry point — initializes the ServiceLocator before any UI runs. */
class RutThereApp : Application() {
    override fun onCreate() {
        super.onCreate()
        ServiceLocator.init(this)
    }
}
