package com.ruthere.app.ui.screens.friends

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ruthere.app.core.ServiceLocator
import com.ruthere.app.data.remote.dto.FriendRequestOut
import com.ruthere.app.data.repo.FriendRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

sealed interface FriendRequestsUiState {
    data object Loading : FriendRequestsUiState
    data class Loaded(val requests: List<FriendRequestOut>) : FriendRequestsUiState
    data class Error(val message: String) : FriendRequestsUiState
}

class FriendRequestsViewModel(
    private val repo: FriendRepository = ServiceLocator.friendRepository,
) : ViewModel() {

    private val _state = MutableStateFlow<FriendRequestsUiState>(FriendRequestsUiState.Loading)
    val state: StateFlow<FriendRequestsUiState> = _state.asStateFlow()

    init { refresh() }

    fun refresh() {
        _state.value = FriendRequestsUiState.Loading
        viewModelScope.launch {
            _state.update {
                runCatching { repo.listRequests() }
                    .fold(
                        onSuccess = { FriendRequestsUiState.Loaded(it) },
                        onFailure = { FriendRequestsUiState.Error(it.message ?: "加载申请列表失败") },
                    )
            }
        }
    }

    fun accept(reqId: Int) = act(reqId, true)
    fun reject(reqId: Int) = act(reqId, false)

    private fun act(reqId: Int, accept: Boolean) {
        viewModelScope.launch {
            runCatching {
                if (accept) repo.acceptRequest(reqId) else repo.rejectRequest(reqId)
            }.fold(
                onSuccess = { refresh() },
                onFailure = { _state.value = FriendRequestsUiState.Error(it.message ?: "操作失败") },
            )
        }
    }
}