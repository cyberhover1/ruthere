package com.ruthere.app.data.remote

import com.ruthere.app.data.remote.dto.AddByQrCodeRequest
import com.ruthere.app.data.remote.dto.ActivityReportRequest
import com.ruthere.app.data.remote.dto.ActivityReportResponse
import com.ruthere.app.data.remote.dto.CheckInCreate
import com.ruthere.app.data.remote.dto.CheckInOut
import com.ruthere.app.data.remote.dto.DataSourcesOut
import com.ruthere.app.data.remote.dto.DataSourcesUpdate
import com.ruthere.app.data.remote.dto.FriendOut
import com.ruthere.app.data.remote.dto.FriendRequestCreate
import com.ruthere.app.data.remote.dto.FriendRequestOut
import com.ruthere.app.data.remote.dto.HealthResponse
import com.ruthere.app.data.remote.dto.FriendsListResponse
import com.ruthere.app.data.remote.dto.PokeStatsResponse
import com.ruthere.app.data.remote.dto.LoginRequest
import com.ruthere.app.data.remote.dto.MessageResponse
import com.ruthere.app.data.remote.dto.NicknameUpdate
import com.ruthere.app.data.remote.dto.NicknameUpdateRequest
import com.ruthere.app.data.remote.dto.NotificationOut
import com.ruthere.app.data.remote.dto.PokeOut
import com.ruthere.app.data.remote.dto.QrCodeResponse
import com.ruthere.app.data.remote.dto.RegisterRequest
import com.ruthere.app.data.remote.dto.ResendCodeRequest
import com.ruthere.app.data.remote.dto.SearchUserOut
import com.ruthere.app.data.remote.dto.TokenResponse
import com.ruthere.app.data.remote.dto.UserOut
import com.ruthere.app.data.remote.dto.VerifyRequest
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query

/** Retrofit API surface. Auth (M1) + Friends (M2). */
interface ApiService {

    // --- auth ---

    @POST("auth/register")
    suspend fun register(@Body body: RegisterRequest): MessageResponse

    @POST("auth/resend-code")
    suspend fun resendCode(@Body body: ResendCodeRequest): MessageResponse

    @POST("auth/verify")
    suspend fun verify(@Body body: VerifyRequest): MessageResponse

    @POST("auth/login")
    suspend fun login(@Body body: LoginRequest): TokenResponse

    @POST("auth/logout")
    suspend fun logout(): MessageResponse

    @GET("auth/me")
    suspend fun me(): UserOut

    @PATCH("auth/me/nickname")
    suspend fun updateMyNickname(@Body body: NicknameUpdateRequest): MessageResponse

    // --- friends (M2) ---

    @POST("friends/qrcode")
    suspend fun createQrCode(): QrCodeResponse

    @POST("friends/add-by-qrcode")
    suspend fun addByQrCode(@Body body: AddByQrCodeRequest): MessageResponse

    @GET("friends/search")
    suspend fun searchByEmail(@Query("email") email: String): List<SearchUserOut>

    @POST("friends/request")
    suspend fun createRequest(@Body body: FriendRequestCreate): MessageResponse

    @GET("friends/requests")
    suspend fun listRequests(): List<FriendRequestOut>

    @POST("friends/requests/{req_id}/accept")
    suspend fun acceptRequest(@Path("req_id") reqId: Int): MessageResponse

    @POST("friends/requests/{req_id}/reject")
    suspend fun rejectRequest(@Path("req_id") reqId: Int): MessageResponse

    @GET("friends")
    suspend fun listFriends(): FriendsListResponse

    @PATCH("friends/{friendship_id}/nickname")
    suspend fun updateNickname(
        @Path("friendship_id") friendshipId: Int,
        @Body body: NicknameUpdate,
    ): MessageResponse

    @DELETE("friends/{friendship_id}")
    suspend fun deleteFriend(@Path("friendship_id") friendshipId: Int): MessageResponse

    @GET("friends/{friendship_id}/data-sources")
    suspend fun getDataSources(@Path("friendship_id") friendshipId: Int): DataSourcesOut

    @PUT("friends/{friendship_id}/data-sources")
    suspend fun setDataSources(
        @Path("friendship_id") friendshipId: Int,
        @Body body: DataSourcesUpdate,
    ): DataSourcesOut

    @GET("friends/{friendship_id}/poke-stats")
    suspend fun getPokeStats(@Path("friendship_id") friendshipId: Int): PokeStatsResponse

    @GET("friends/notifications")
    suspend fun listNotifications(): List<NotificationOut>

    // --- activity (M3/M9) ---

    @POST("activity/report")
    suspend fun reportActivity(@Body body: ActivityReportRequest): ActivityReportResponse

    // --- interactions (M4/M11) ---

    @POST("checkins")
    suspend fun createCheckin(@Body body: CheckInCreate): CheckInOut

    @GET("checkins")
    suspend fun listCheckins(
        @Query("limit") limit: Int = 50,
        @Query("offset") offset: Int = 0,
    ): List<CheckInOut>

    @POST("pokes/{friendship_id}")
    suspend fun pokeFriend(@Path("friendship_id") friendshipId: Int): PokeOut

    // --- health ---

    @GET("health")
    suspend fun health(): HealthResponse
}
