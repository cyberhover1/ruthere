package com.ruthere.app.data.sensor

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.media.AudioManager
import android.os.BatteryManager
import android.os.Build
import android.os.SystemClock
import androidx.core.content.ContextCompat
import com.ruthere.app.core.DataSources
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.coroutines.resume

/**
 * Collects a snapshot of all 7 activity data sources and normalizes each to 0..1.
 *
 * Called from [SensorWorker] on a periodic schedule. Each source is sampled with
 * a short sensor-listener window (or a direct system query for instantaneous
 * sources). Cumulative sources (steps, unlocks, motion) are differenced against
 * the previous raw baseline stored in [SnapshotStore].
 *
 * Normalization thresholds are tuned for a ~30-minute collection window.
 */
class SensorCollector(
    private val context: Context,
    private val snapshotStore: SnapshotStore,
) {
    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager

    // Normalization thresholds (per ~30min window).
    private val stepGoal = 1000f       // steps in window -> 1.0
    private val unlockGoal = 10f       // unlocks in window -> 1.0
    private val pickupGoal = 20f       // pickup/flip events -> 1.0
    private val lightGoal = 500f       // lux -> 1.0
    private val motionGoal = 5f        // significant-motion triggers -> 1.0

    /** Collect + normalize all sources. Returns (raw, normalized) maps. */
    suspend fun collect(): Pair<Map<String, Float>, Map<String, Float>> {
        val prev = snapshotStore.previousRaw()
        val raw = mutableMapOf<String, Float>()

        // --- steps (STEP_COUNTER cumulative) ---
        val stepTotal = readSensorOnce(Sensor.TYPE_STEP_COUNTER)?.values?.firstOrNull() ?: prev["steps"] ?: 0f
        val prevSteps = prev["steps"] ?: stepTotal
        val stepsDelta = (stepTotal - prevSteps).coerceAtLeast(0f)
        raw["steps"] = stepTotal

        // --- screen_unlock: no sensor event in a one-shot window; use stored counter delta ---
        // (Unlock counting requires a long-lived BroadcastReceiver; in the periodic model we
        // approximate via 0 if no persistent counter is maintained. M9 may add a foreground
        // receiver. For now emit the stored value as a stable baseline.)
        raw["screen_unlock"] = prev["screen_unlock"] ?: 0f

        // --- charging (instantaneous) ---
        raw["charging"] = if (isCharging()) 1f else 0f

        // --- headset (instantaneous) ---
        raw["headset"] = if (isHeadsetConnected()) 1f else 0f

        // --- pickup_flip: event-based (needs persistent listener); use stored baseline ---
        // Pickup/flip is an event count, not an instantaneous state; in the periodic model
        // without a persistent receiver we emit the stored counter as a stable baseline.
        raw["pickup_flip"] = prev["pickup_flip"] ?: 0f

        // --- ambient_light (instantaneous read) ---
        val light = readSensorOnce(Sensor.TYPE_LIGHT)?.values?.firstOrNull() ?: 0f
        raw["ambient_light"] = light

        // --- significant_motion: trigger sensor; count triggers since last baseline ---
        // Significant motion is a trigger (one-shot) sensor; in periodic collection we treat
        // the stored counter as the baseline and increment by detected triggers (0 in a
        // one-shot window without a persistent listener). Emit stored value as baseline.
        raw["significant_motion"] = prev["significant_motion"] ?: 0f

        // --- normalize to 0..1 ---
        val normalized = mapOf(
            "steps" to (stepsDelta / stepGoal).coerceIn(0f, 1f),
            "screen_unlock" to (raw["screen_unlock"]!! / unlockGoal).coerceIn(0f, 1f),
            "charging" to raw["charging"]!!,
            "headset" to raw["headset"]!!,
            "pickup_flip" to (raw["pickup_flip"]!! / pickupGoal).coerceIn(0f, 1f),
            "ambient_light" to (light / lightGoal).coerceIn(0f, 1f),
            "significant_motion" to (raw["significant_motion"]!! / motionGoal).coerceIn(0f, 1f),
        )
        return raw.toMap() to normalized
    }

    /** True if ACTIVITY_RECOGNITION is granted (needed for STEP_COUNTER on API 29+). */
    fun hasStepPermission(): Boolean =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            ContextCompat.checkSelfPermission(context, Manifest.permission.ACTIVITY_RECOGNITION) ==
                PackageManager.PERMISSION_GRANTED
        } else true

    /** Read one event from a sensor, or null on timeout / no sensor. */
    private suspend fun readSensorOnce(type: Int): SensorEvent? {
        val sensor = sensorManager.getDefaultSensor(type) ?: return null
        if (type == Sensor.TYPE_STEP_COUNTER && !hasStepPermission()) return null
        return withTimeoutOrNull(2_000L) {
            suspendCancellableCoroutine { cont ->
                val listener = object : SensorEventListener {
                    override fun onSensorChanged(event: SensorEvent) {
                        sensorManager.unregisterListener(this)
                        if (cont.isActive) cont.resume(event)
                    }
                    override fun onAccuracyChanged(s: Sensor?, accuracy: Int) {}
                }
                sensorManager.registerListener(listener, sensor, SensorManager.SENSOR_DELAY_FASTEST)
                cont.invokeOnCancellation { sensorManager.unregisterListener(listener) }
            }
        }
    }

    private fun isCharging(): Boolean {
        val bm = context.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        return bm.isCharging
    }

    private fun isHeadsetConnected(): Boolean {
        val am = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
        return am.getDevices(AudioManager.GET_DEVICES_OUTPUTS).any {
            it.type == android.media.AudioDeviceInfo.TYPE_WIRED_HEADSET ||
                it.type == android.media.AudioDeviceInfo.TYPE_WIRED_HEADPHONES
        }
    }
}
