package com.ruthere.app.ui.screens.friends

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ruthere.app.core.ServiceLocator
import com.ruthere.app.data.local.FriendsActivityStore
import com.ruthere.app.data.remote.dto.FriendActivityOut
import com.ruthere.app.data.remote.dto.FriendOut
import com.ruthere.app.data.remote.dto.NotificationOut
import com.ruthere.app.data.remote.dto.PokeStatsResponse
import com.ruthere.app.data.repo.FriendRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

enum class FriendsSortMode(val label: String) {
    ACTIVITY("活跃度"),
    TIME("更新时间"),
    NICKNAME("昵称");
}

sealed interface FriendsListUiState {
    data object Loading : FriendsListUiState
    data class Loaded(
        val friends: List<FriendOut>,
        val notifications: List<NotificationOut>,
        val activity: Map<Int, FriendActivityOut>,
        val sortMode: FriendsSortMode,
    ) : FriendsListUiState
    data class Error(val message: String) : FriendsListUiState
}

class FriendsListViewModel(
    private val repo: FriendRepository = ServiceLocator.friendRepository,
    private val activityStore: FriendsActivityStore = ServiceLocator.friendsActivityStore,
) : ViewModel() {

    private val _state = MutableStateFlow<FriendsListUiState>(FriendsListUiState.Loading)
    val state: StateFlow<FriendsListUiState> = _state.asStateFlow()

    private var sortMode: FriendsSortMode = FriendsSortMode.ACTIVITY
    private var lastFriends: List<FriendOut> = emptyList()
    private var lastNotifications: List<NotificationOut> = emptyList()
    private var lastActivity: Map<Int, FriendActivityOut> = emptyMap()
    private var lastPokedAtMap: Map<Int, String> = emptyMap()

    init {
        refresh()
        // Reactively update when delivered activity changes (after a sensor-worker upload).
        viewModelScope.launch {
            activityStore.activities.collect { activityMap ->
                // Merge store data with our poke timestamps (which come from /friends, not /activity/report).
                lastActivity = mergePokedAt(activityMap)
                emitLoaded()
            }
        }
    }

    fun refresh() {
        _state.value = FriendsListUiState.Loading
        viewModelScope.launch {
            runCatching { repo.listFriends() }
                .fold(
                    onSuccess = { resp ->
                        lastFriends = resp.friends
                        lastNotifications = resp.notifications
                        // Use activity from the list response immediately, so we
                        // never show stale zeros while waiting for the sensor worker.
                        lastActivity = resp.friends_activity.associateBy { it.friend_id }
                        // Keep poke timestamps separate so they survive store updates.
                        lastPokedAtMap = resp.friends_activity
                            .filter { it.last_poked_at != null }
                            .associate { it.friend_id to it.last_poked_at!! }
                        // Merge in any locally-cached activity as an override.
                        lastActivity = mergePokedAt(activityStore.current() + lastActivity)
                        emitLoaded()
                    },
                    onFailure = { _state.value = FriendsListUiState.Error(it.message ?: "加载好友列表失败") },
                )
        }
    }

    fun setSortMode(mode: FriendsSortMode) {
        sortMode = mode
        emitLoaded()
    }

    /** Fetch poke stats for a friendship (called on double-click). */
    fun pokeStats(friendshipId: Int, onResult: (PokeStatsResponse) -> Unit) {
        viewModelScope.launch {
            runCatching { repo.getPokeStats(friendshipId) }
                .onSuccess { onResult(it) }
        }
    }

    /** Re-apply our poke timestamps to any activity map that lacks them. */
    private fun mergePokedAt(activityMap: Map<Int, FriendActivityOut>): Map<Int, FriendActivityOut> =
        activityMap.mapValues { (id, act) ->
            val pokeTime = lastPokedAtMap[id]
            if (pokeTime != null && act.last_poked_at == null) {
                act.copy(last_poked_at = pokeTime)
            } else act
        }

    private fun emitLoaded() {
        val sorted = sortFriends(lastFriends, lastActivity, sortMode)
        _state.value = FriendsListUiState.Loaded(sorted, lastNotifications, lastActivity, sortMode)
    }

    private fun sortFriends(
        friends: List<FriendOut>,
        activity: Map<Int, FriendActivityOut>,
        mode: FriendsSortMode,
    ): List<FriendOut> = when (mode) {
        FriendsSortMode.ACTIVITY -> friends.sortedByDescending { activity[it.friend_id]?.value ?: 0 }
        FriendsSortMode.TIME -> friends.sortedByDescending { activity[it.friend_id]?.last_reported_at ?: "" }
        FriendsSortMode.NICKNAME -> friends.sortedBy { (it.nickname ?: it.email).lowercase() }
    }
}
