package com.ruthere.app.data.remote.dto

import com.squareup.moshi.JsonClass

/** Fixed check-in types (PRD §5.1). */
val CHECKIN_TYPES: List<String> = listOf("起床", "休息", "运动", "吃饭")

@JsonClass(generateAdapter = false)
data class CheckInCreate(val type: String, val note: String? = null)

@JsonClass(generateAdapter = false)
data class CheckInOut(
    val id: Int,
    val type: String,
    val note: String?,
    val created_at: String,
)

@JsonClass(generateAdapter = false)
data class PokeOut(val to_user_id: Int, val created_at: String)
