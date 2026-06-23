package com.ruthere.app.core

import com.ruthere.app.data.remote.dto.MessageResponse
import com.squareup.moshi.JsonClass
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import retrofit2.HttpException

/**
 * Extracts a user-friendly error message from a Retrofit/HTTP failure.
 *
 * Backend error responses are `{"detail": "中文提示"}`. This parses the error
 * body and returns the detail; if parsing fails or the error is non-HTTP, it
 * returns a generic fallback.
 */
object ErrorMessage {

    private val moshi = Moshi.Builder().add(KotlinJsonAdapterFactory()).build()
    private val detailAdapter = moshi.adapter(DetailBody::class.java)

    fun from(throwable: Throwable, fallback: String = "操作失败，请重试"): String {
        if (throwable is HttpException) {
            val raw = throwable.response()?.errorBody()?.string()
            if (!raw.isNullOrBlank()) {
                runCatching {
                    val body = detailAdapter.fromJson(raw)
                    if (!body?.detail.isNullOrBlank()) return body!!.detail
                }
                // Some backends return {"message": "..."}.
                runCatching {
                    val msg = moshi.adapter(MessageResponse::class.java).fromJson(raw)
                    if (!msg?.message.isNullOrBlank()) return msg!!.message
                }
            }
            // Fall back to a code-based hint.
            return when (throwable.code()) {
                401 -> "邮箱或密码错误"
                403 -> "邮箱未验证，请先完成验证"
                404 -> "资源不存在"
                409 -> "该邮箱已注册"
                422 -> "输入格式不正确"
                429 -> "操作过于频繁，请稍后再试"
                502 -> "服务器邮件发送失败"
                in 500..599 -> "服务器异常，请稍后重试"
                else -> "请求失败（${throwable.code()}）"
            }
        }
        // Non-HTTP errors (network, timeout, parsing).
        return throwable.message?.takeIf { it.isNotBlank() } ?: fallback
    }
}

@JsonClass(generateAdapter = false)
private data class DetailBody(val detail: String?)
