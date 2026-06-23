package com.ruthere.app.data.repo

import com.ruthere.app.data.remote.NetworkClient
import com.ruthere.app.data.remote.dto.ActivityReportRequest
import com.ruthere.app.data.remote.dto.ActivityReportResponse

/** Wraps the M3 /activity/report endpoint. Auth header injected by NetworkClient. */
class ActivityRepository(private val networkClient: NetworkClient) {
    private val api get() = networkClient.api

    /** Upload raw component values; backend computes per-friend visible values + delivers. */
    suspend fun report(components: Map<String, Float>): ActivityReportResponse =
        api.reportActivity(ActivityReportRequest(components))
}
