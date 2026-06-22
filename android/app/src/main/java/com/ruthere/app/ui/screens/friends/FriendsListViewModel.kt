package com.ruthere.app.ui.screens.friends

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ruthere.app.core.ServiceLocator
import com.ruthere.app.data.remote.dto.FriendOut
import com.ruthere.app.data.remote.dto.NotificationOut
import com.ruthere.app.data.repo.FriendRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

sealed interface FriendsListUiState {
    data object Loading : FriendsListUiState
    data class Loaded(
        val friends: List<FriendOut>,
        val notifications: List<NotificationOut>,
    ) : FriendsListUiState
    data class Error(val message: String) : FriendsListUiState
}

class FriendsListViewModel(
    private val repo: FriendRepository = ServiceLocator.friendRepository,
) : ViewModel() {

    private val _state = MutableStateFlow<FriendsListUiState>(FriendsListUiState.Loading)
    val state: StateFlow<FriendsListUiState> = _state.asStateFlow()

    init { refresh() }

    fun refresh() {
        _state.value = FriendsListUiState.Loading
        viewModelScope.launch {
            _state.update {
                runCatching { repo.listFriends() }
                    .fold(
                        onSuccess = { FriendsListUiState.Loaded(it.friends, it.notifications) },
                        onFailure = { FriendsListUiState.Error(it.message ?: "加载好友列表失败") },
                    )
            }
        }
    }
}
