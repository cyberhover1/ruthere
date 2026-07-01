package com.ruthere.app.core

import java.time.Instant
import java.time.LocalDateTime
import java.time.ZoneId
import java.time.temporal.ChronoUnit

/** Beijing timezone (UTC+8) — used for all time display. */
private val BEIJING_ZONE: ZoneId = ZoneId.of("Asia/Shanghai")

/**
 * Fuzzy time formatting (PRD §5.3): turns an ISO timestamp into an interval
 * expression like 刚刚 / 活跃中 / 2小时前 / 今天上午 / 今天 / 很久以前.
 *
 * The displayed time is deliberately imprecise — no exact clock time is shown.
 */
object TimeFormat {

    /** @param isoTime ISO-8601 string (e.g. "2026-06-23T08:10:17.439946")
     *  @param value the friend's activity value 0..100 (used for "活跃中") */
    fun fuzzy(isoTime: String?, value: Int = 0, isOffline: Boolean = false): String {
        if (isOffline) return "离线"
        if (isoTime.isNullOrBlank()) return "未知"
        val instant = runCatching { Instant.parse(isoTime) }.getOrNull()
            ?: runCatching { LocalDateTime.parse(isoTime).atZone(BEIJING_ZONE).toInstant() }.getOrNull()
            ?: return "未知"

        val now = Instant.now()
        val minutes = ChronoUnit.MINUTES.between(instant, now)
        val hours = ChronoUnit.HOURS.between(instant, now)
        val days = ChronoUnit.DAYS.between(instant, now)

        return when {
            minutes < 1 -> if (value > 0) "活跃中" else "刚刚"
            minutes < 60 -> "${minutes}分钟前"
            hours < 2 -> "${hours}小时前"
            days < 1 -> {
                val ldt = instant.atZone(BEIJING_ZONE)
                if (ldt.hour < 12) "今天上午" else "今天下午"
            }
            days < 7 -> "最近"
            else -> "很久以前"
        }
    }

    /**
     * Fuzzy time for when a friend poked me — shows an imprecise interval.
     * Returns null when there's no poke data.
     */
    fun fuzzyPoked(isoTime: String?): String? {
        if (isoTime.isNullOrBlank()) return null
        val instant = runCatching { Instant.parse(isoTime) }.getOrNull()
            ?: runCatching { LocalDateTime.parse(isoTime).atZone(BEIJING_ZONE).toInstant() }.getOrNull()
            ?: return null

        val now = Instant.now()
        val minutes = ChronoUnit.MINUTES.between(instant, now)
        val hours = ChronoUnit.HOURS.between(instant, now)
        val days = ChronoUnit.DAYS.between(instant, now)

        return when {
            minutes < 1 -> "刚刚"
            minutes < 60 -> "${minutes}分钟前"
            hours < 3 -> "${hours}小时前"
            days < 1 -> {
                val ldt = instant.atZone(BEIJING_ZONE)
                if (ldt.hour < 12) "今天上午" else "今天下午"
            }
            days < 2 -> "昨天"
            days < 7 -> "${days}天前"
            else -> "很久以前"
        }
    }
}
