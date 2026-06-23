package com.ruthere.app.ui.screens.checkin

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ruthere.app.core.ServiceLocator
import com.ruthere.app.data.remote.dto.CheckInOut
import com.ruthere.app.data.remote.dto.CHECKIN_TYPES
import com.ruthere.app.data.repo.InteractionRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class CheckInUiState(
    val checkins: List<CheckInOut> = emptyList(),
    val selectedType: String = CHECKIN_TYPES.first(),
    val note: String = "",
    val loading: Boolean = false,
    val message: String? = null,
)

class CheckInViewModel(
    private val repo: InteractionRepository = ServiceLocator.interactionRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(CheckInUiState(loading = true))
    val state: StateFlow<CheckInUiState> = _state.asStateFlow()

    init { refresh() }

    fun refresh() {
        _state.update { it.copy(loading = true, message = null) }
        viewModelScope.launch {
            runCatching { repo.listCheckins() }
                .fold(
                    onSuccess = { list -> _state.update { it.copy(checkins = list, loading = false) } },
                    onFailure = { e -> _state.update { it.copy(loading = false, message = e.message ?: "加载失败") } },
                )
        }
    }

    fun onSelectType(type: String) = _state.update { it.copy(selectedType = type) }

    fun onNoteChange(v: String) = _state.update { it.copy(note = v) }

    fun create() {
        val s = _state.value
        _state.update { it.copy(loading = true, message = null) }
        viewModelScope.launch {
            runCatching { repo.createCheckin(s.selectedType, s.note.ifBlank { null }) }
                .fold(
                    onSuccess = {
                        _state.update { it.copy(loading = false, note = "", message = "打卡成功") }
                        refresh()
                    },
                    onFailure = { e -> _state.update { it.copy(loading = false, message = e.message ?: "打卡失败") } },
                )
        }
    }
}
