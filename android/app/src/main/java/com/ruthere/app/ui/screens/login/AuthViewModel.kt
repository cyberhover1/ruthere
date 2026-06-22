package com.ruthere.app.ui.screens.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ruthere.app.core.ServiceLocator
import com.ruthere.app.data.repo.AuthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Shared UI state for the register → verify → login flow. */
sealed interface AuthUiState {
    data object Idle : AuthUiState
    data object Loading : AuthUiState
    data class Success(val message: String) : AuthUiState
    data class Error(val message: String) : AuthUiState
}

class AuthViewModel(
    private val repo: AuthRepository = ServiceLocator.authRepository,
) : ViewModel() {

    private val _state = MutableStateFlow<AuthUiState>(AuthUiState.Idle)
    val state: StateFlow<AuthUiState> = _state.asStateFlow()

    fun register(email: String, password: String) {
        _state.value = AuthUiState.Loading
        viewModelScope.launch {
            _state.update { runCatching { repo.register(email, password) }
                .fold(
                    onSuccess = { AuthUiState.Success(it.message) },
                    onFailure = { AuthUiState.Error(it.message ?: "注册失败") },
                ) }
        }
    }

    fun verify(email: String, code: String) {
        _state.value = AuthUiState.Loading
        viewModelScope.launch {
            _state.update {
                runCatching { repo.verify(email, code) }
                    .fold(
                        onSuccess = { AuthUiState.Success(it.message) },
                        onFailure = { AuthUiState.Error(it.message ?: "验证失败") },
                    )
            }
        }
    }

    fun login(email: String, password: String, deviceIdentifier: String) {
        _state.value = AuthUiState.Loading
        viewModelScope.launch {
            _state.update {
                runCatching { repo.login(email, password, deviceIdentifier) }
                    .fold(
                        onSuccess = { AuthUiState.Success("登录成功") },
                        onFailure = { AuthUiState.Error(it.message ?: "登录失败") },
                    )
            }
        }
    }

    fun reset() { _state.value = AuthUiState.Idle }
}
