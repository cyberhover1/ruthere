package com.ruthere.app.data.remote

import com.ruthere.app.data.remote.dto.LoginRequest
import com.ruthere.app.data.remote.dto.MessageResponse
import com.ruthere.app.data.remote.dto.RegisterRequest
import com.ruthere.app.data.remote.dto.ResendCodeRequest
import com.ruthere.app.data.remote.dto.TokenResponse
import com.ruthere.app.data.remote.dto.UserOut
import com.ruthere.app.data.remote.dto.VerifyRequest
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

/** Retrofit API surface. M5 covers the M1 auth endpoints; friends/activity arrive later. */
interface ApiService {

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
}
