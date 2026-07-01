package com.ruthere.app.data.repo

import com.ruthere.app.data.remote.NetworkClient
import com.ruthere.app.data.remote.dto.AddByQrCodeRequest
import com.ruthere.app.data.remote.dto.DataSourcesOut
import com.ruthere.app.data.remote.dto.FriendOut
import com.ruthere.app.data.remote.dto.FriendRequestCreate
import com.ruthere.app.data.remote.dto.FriendRequestOut
import com.ruthere.app.data.remote.dto.FriendsListResponse
import com.ruthere.app.data.remote.dto.PokeStatsResponse
import com.ruthere.app.data.remote.dto.MessageResponse
import com.ruthere.app.data.remote.dto.NotificationOut
import com.ruthere.app.data.remote.dto.QrCodeResponse
import com.ruthere.app.data.remote.dto.SearchUserOut

/** Wraps the M2 friend API calls. Auth header is injected by NetworkClient. */
class FriendRepository(private val networkClient: NetworkClient) {
    private val api get() = networkClient.api

    suspend fun createQrCode(): QrCodeResponse = api.createQrCode()

    suspend fun addByQrCode(token: String): MessageResponse =
        api.addByQrCode(AddByQrCodeRequest(token))

    suspend fun searchByEmail(email: String): List<SearchUserOut> = api.searchByEmail(email)

    suspend fun createRequest(toUserId: Int): MessageResponse =
        api.createRequest(FriendRequestCreate(toUserId))

    suspend fun listRequests(): List<FriendRequestOut> = api.listRequests()

    suspend fun acceptRequest(reqId: Int): MessageResponse = api.acceptRequest(reqId)
    suspend fun rejectRequest(reqId: Int): MessageResponse = api.rejectRequest(reqId)

    suspend fun listFriends(): FriendsListResponse = api.listFriends()

    suspend fun updateNickname(friendshipId: Int, nickname: String?): MessageResponse =
        api.updateNickname(friendshipId, com.ruthere.app.data.remote.dto.NicknameUpdate(nickname))

    suspend fun deleteFriend(friendshipId: Int): MessageResponse = api.deleteFriend(friendshipId)

    suspend fun getDataSources(friendshipId: Int): DataSourcesOut = api.getDataSources(friendshipId)

    suspend fun setDataSources(friendshipId: Int, sources: List<String>): DataSourcesOut =
        api.setDataSources(friendshipId, com.ruthere.app.data.remote.dto.DataSourcesUpdate(sources))

    suspend fun getPokeStats(friendshipId: Int): PokeStatsResponse = api.getPokeStats(friendshipId)

    suspend fun listNotifications(): List<NotificationOut> = api.listNotifications()
}
