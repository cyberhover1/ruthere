package com.ruthere.app.data.repo

import com.ruthere.app.data.remote.NetworkClient
import com.ruthere.app.data.remote.dto.CheckInCreate
import com.ruthere.app.data.remote.dto.CheckInOut
import com.ruthere.app.data.remote.dto.PokeOut

/** Wraps the M4 check-in + poke endpoints. Auth header injected by NetworkClient. */
class InteractionRepository(private val networkClient: NetworkClient) {
    private val api get() = networkClient.api

    suspend fun createCheckin(type: String, note: String?): CheckInOut =
        api.createCheckin(CheckInCreate(type, note))

    suspend fun listCheckins(limit: Int = 50, offset: Int = 0): List<CheckInOut> =
        api.listCheckins(limit, offset)

    suspend fun poke(friendshipId: Int): PokeOut = api.pokeFriend(friendshipId)
}
