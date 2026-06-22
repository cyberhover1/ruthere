package com.ruthere.app.data.remote.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = false)
data class RegisterRequest(val email: String, val password: String)

@JsonClass(generateAdapter = false)
data class ResendCodeRequest(val email: String)

@JsonClass(generateAdapter = false)
data class VerifyRequest(val email: String, val code: String)

@JsonClass(generateAdapter = false)
data class LoginRequest(val email: String, val password: String, val device_identifier: String)

@JsonClass(generateAdapter = false)
data class TokenResponse(val access_token: String, val token_type: String = "bearer", val user_id: Int)

@JsonClass(generateAdapter = false)
data class UserOut(val id: Int, val email: String, val is_verified: Boolean)

@JsonClass(generateAdapter = false)
data class MessageResponse(val message: String)
