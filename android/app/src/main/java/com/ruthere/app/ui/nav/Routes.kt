package com.ruthere.app.ui.nav

/** Navigation routes for the auth + friends graph. */
object Routes {
    const val LOGIN = "login"
    const val REGISTER = "register"
    const val VERIFY = "verify"
    const val MAIN = "main"
    const val SERVER_CONFIG = "server_config"
    const val FRIEND_ADD = "friend_add"
    const val FRIEND_REQUESTS = "friend_requests"
    const val FRIEND_DETAIL = "friend_detail/{friendship_id}/{email}/{nickname}"
    const val PROFILE = "profile"
    const val ABOUT = "about"
    const val PRE_LOGIN_CONFIG = "pre_login_config"

    fun friendDetail(friendshipId: Int, email: String, nickname: String?): String =
        "friend_detail/$friendshipId/$email/${nickname ?: ""}"
}
