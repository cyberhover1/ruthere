package com.ruthere.app.ui.screens.friends

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ruthere.app.core.DataSources
import com.ruthere.app.core.ServiceLocator
import com.ruthere.app.data.repo.FriendRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class FriendDetailUiState(
    val nicknameInput: String = "",
    val allowedSources: Set<String> = emptySet(),
    val allSources: List<DataSources.Source> = DataSources.ALL,
    val loading: Boolean = false,
    val message: String? = null,
    val deleted: Boolean = false,
)

class FriendDetailViewModel(
    private val repo: FriendRepository = ServiceLocator.friendRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(FriendDetailUiState())
    val state: StateFlow<FriendDetailUiState> = _state.asStateFlow()

    private var friendshipId: Int = -1

    fun init(friendshipId: Int, currentNickname: String?) {
        this.friendshipId = friendshipId
        _state.update { it.copy(nicknameInput = currentNickname.orEmpty()) }
        loadSources()
    }

    private fun loadSources() {
        _state.update { it.copy(loading = true, message = null) }
        viewModelScope.launch {
            runCatching { repo.getDataSources(friendshipId) }
                .fold(
                    onSuccess = { d ->
                        _state.update { it.copy(allowedSources = d.allowed_sources.toSet(), loading = false) }
                    },
                    onFailure = { _state.update { it.copy(loading = false, message = it.message ?: "加载数据源失败") } },
                )
        }
    }

    fun onNicknameChange(v: String) = _state.update { it.copy(nicknameInput = v) }

    fun saveNickname() {
        _state.update { it.copy(loading = true, message = null) }
        viewModelScope.launch {
            val n = _state.value.nicknameInput.ifBlank { null }
            runCatching { repo.updateNickname(friendshipId, n) }
                .fold(
                    onSuccess = { _state.update { it.copy(loading = false, message = "昵称已更新") } },
                    onFailure = { _state.update { it.copy(loading = false, message = it.message ?: "更新失败") } },
                )
        }
    }

    fun toggleSource(id: String) {
        val cur = _state.value.allowedSources
        val next = if (id in cur) cur - id else cur + id
        _state.update { it.copy(allowedSources = next) }
        viewModelScope.launch {
            runCatching { repo.setDataSources(friendshipId, next.toList()) }
                .fold(
                    onSuccess = { resp ->
                        _state.update { it.copy(allowedSources = resp.allowed_sources.toSet(), message = "数据源已更新") }
                    },
                    onFailure = {
                        // Revert on failure.
                        _state.update { it.copy(allowedSources = cur, message = "数据源更新失败") }
                    },
                )
        }
    }

    fun delete() {
        _state.update { it.copy(loading = true, message = null) }
        viewModelScope.launch {
            runCatching { repo.deleteFriend(friendshipId) }
                .fold(
                    onSuccess = { _state.update { it.copy(loading = false, deleted = true, message = "已删除好友") } },
                    onFailure = { _state.update { it.copy(loading = false, message = "删除失败") } },
                )
        }
    }
}
