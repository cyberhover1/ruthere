package com.ruthere.app.ui.screens.friends

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ruthere.app.core.ServiceLocator
import com.ruthere.app.data.remote.dto.QrCodeResponse
import com.ruthere.app.data.remote.dto.SearchUserOut
import com.ruthere.app.data.repo.FriendRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

sealed interface FriendAddUiState {
    data object Idle : FriendAddUiState
    data object Loading : FriendAddUiState
    data class QrReady(val token: String) : FriendAddUiState
    data class SearchResults(val users: List<SearchUserOut>) : FriendAddUiState
    data class Success(val message: String) : FriendAddUiState
    data class Error(val message: String) : FriendAddUiState
}

class FriendAddViewModel(
    private val repo: FriendRepository = ServiceLocator.friendRepository,
) : ViewModel() {

    private val _state = MutableStateFlow<FriendAddUiState>(FriendAddUiState.Idle)
    val state: StateFlow<FriendAddUiState> = _state.asStateFlow()

    fun generateQr() {
        _state.value = FriendAddUiState.Loading
        viewModelScope.launch {
            _state.update {
                runCatching { repo.createQrCode() }
                    .fold(
                        onSuccess = { FriendAddUiState.QrReady(it.token) },
                        onFailure = { FriendAddUiState.Error(it.message ?: "生成二维码失败") },
                    )
            }
        }
    }

    fun addByQrToken(token: String) {
        _state.value = FriendAddUiState.Loading
        viewModelScope.launch {
            _state.update {
                runCatching { repo.addByQrCode(token) }
                    .fold(
                        onSuccess = { FriendAddUiState.Success(it.message) },
                        onFailure = { FriendAddUiState.Error(it.message ?: "添加好友失败") },
                    )
            }
        }
    }

    fun search(email: String) {
        _state.value = FriendAddUiState.Loading
        viewModelScope.launch {
            _state.update {
                runCatching { repo.searchByEmail(email) }
                    .fold(
                        onSuccess = { FriendAddUiState.SearchResults(it) },
                        onFailure = { FriendAddUiState.Error(it.message ?: "搜索失败") },
                    )
            }
        }
    }

    fun sendRequest(toUserId: Int) {
        _state.value = FriendAddUiState.Loading
        viewModelScope.launch {
            _state.update {
                runCatching { repo.createRequest(toUserId) }
                    .fold(
                        onSuccess = { FriendAddUiState.Success(it.message) },
                        onFailure = { FriendAddUiState.Error(it.message ?: "发送申请失败") },
                    )
            }
        }
    }

    fun reset() { _state.value = FriendAddUiState.Idle }
}
