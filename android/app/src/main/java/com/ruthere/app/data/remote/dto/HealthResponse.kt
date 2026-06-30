package com.ruthere.app.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = false)
data class HealthResponse(
    @Json(name = "status") val status: String,
    @Json(name = "app_version") val appVersion: String?,
    @Json(name = "build_timestamp") val buildTimestamp: String?,
)