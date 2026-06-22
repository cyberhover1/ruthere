package com.ruthere.app.core

/** The 7 activity data-source ids (PRD §4.1) with Chinese display labels. */
object DataSources {
    data class Source(val id: String, val label: String)

    val ALL: List<Source> = listOf(
        Source("steps", "步数"),
        Source("screen_unlock", "解锁次数"),
        Source("charging", "充电"),
        Source("headset", "耳机"),
        Source("pickup_flip", "拿起翻转"),
        Source("ambient_light", "环境光"),
        Source("significant_motion", "显著运动"),
    )

    val IDS: List<String> = ALL.map { it.id }

    fun labelOf(id: String): String = ALL.firstOrNull { it.id == id }?.label ?: id
}
