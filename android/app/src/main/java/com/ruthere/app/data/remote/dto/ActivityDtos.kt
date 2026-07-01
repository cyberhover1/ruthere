package com.ruthere.app.data.remote.dto

import com.squareup.moshi.JsonClass

/** Request body for POST /activity/report: raw per-source 0..1 values (transient). */
@JsonClass(generateAdapter = false)
data class ActivityReportRequest(val components: Map<String, Float>)

/** A friend's desensitized activity as delivered to me (PRD §4.5). */
@JsonClass(generateAdapter = false)
data class FriendActivityOut(
    val friend_id: Int,
    val value: Int,            // 0..100
    val last_reported_at: String,
    val is_offline: Boolean,
    val last_poked_at: String? = null,  // ISO timestamp of latest poke from this friend to me
)

/** Response to /activity/report: friends' activity + piggybacked notifications. */
@JsonClass(generateAdapter = false)
data class ActivityReportResponse(
    val friends_activity: List<FriendActivityOut>,
    val notifications: List<NotificationOut> = emptyList(),
)
