package com.ruthere.app.data.remote.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = false)
data class QrCodeResponse(val token: String, val expire_at: String)

@JsonClass(generateAdapter = false)
data class AddByQrCodeRequest(val token: String)

@JsonClass(generateAdapter = false)
data class SearchUserOut(val id: Int, val email: String)

@JsonClass(generateAdapter = false)
data class FriendRequestCreate(val to_user_id: Int)

@JsonClass(generateAdapter = false)
data class FriendRequestOut(
    val id: Int,
    val from_user_id: Int,
    val to_user_id: Int,
    val status: String,
    val created_at: String,
    val from_email: String = "",
    val from_nickname: String? = null,
)

@JsonClass(generateAdapter = false)
data class FriendOut(
    val friendship_id: Int,
    val friend_id: Int,
    val email: String,
    val nickname: String?,
    val friend_nickname: String?,
    val created_at: String,
)

@JsonClass(generateAdapter = false)
data class NicknameUpdate(val nickname: String?)

@JsonClass(generateAdapter = false)
data class DataSourcesOut(val friend_id: Int, val allowed_sources: List<String>)

@JsonClass(generateAdapter = false)
data class DataSourcesUpdate(val allowed_sources: List<String>)

@JsonClass(generateAdapter = false)
data class NotificationOut(
    val id: Int,
    val type: String,
    val payload: Map<String, Any?>,
    val created_at: String,
)

@JsonClass(generateAdapter = false)
data class FriendsListResponse(
    val friends: List<FriendOut>,
    val notifications: List<NotificationOut> = emptyList(),
    val friends_activity: List<FriendActivityOut> = emptyList(),
)

@JsonClass(generateAdapter = false)
data class PokeStatsResponse(
    val total_pokes: Int,
    val recent_pokes: List<String>,
)
