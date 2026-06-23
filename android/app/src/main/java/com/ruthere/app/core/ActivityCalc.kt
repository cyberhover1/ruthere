package com.ruthere.app.core

/**
 * Default activity contribution weights (PRD §4.3), mirroring the backend's
 * DEFAULT_WEIGHTS. The backend performs the actual per-friend computation
 * (M3 decision); these constants are exposed on the frontend for the future
 * weight-settings UI and for display.
 */
object ActivityCalc {
    val DEFAULT_WEIGHTS: Map<String, Float> = mapOf(
        "steps" to 0.40f,
        "screen_unlock" to 0.20f,
        "significant_motion" to 0.15f,
        "charging" to 0.05f,
        "headset" to 0.05f,
        "pickup_flip" to 0.10f,
        "ambient_light" to 0.05f,
    )
}
