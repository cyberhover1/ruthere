package com.ruthere.app.ui.screens.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ruthere.app.core.ServiceLocator
import com.ruthere.app.data.local.DEFAULT_SERVER_IP
import com.ruthere.app.data.local.DEFAULT_SERVER_PORT
import com.ruthere.app.data.local.ServerAddress
import com.ruthere.app.data.repo.AuthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class ServerConfigUiState(
    val ip: String = DEFAULT_SERVER_IP,
    val port: Int = DEFAULT_SERVER_PORT,
    val ipInput: String = DEFAULT_SERVER_IP,
    val portInput: String = DEFAULT_SERVER_PORT.toString(),
    val saving: Boolean = false,
    val message: String? = null,
    val isValid: Boolean = true,
)

class ServerConfigViewModel(
    private val repo: AuthRepository = ServiceLocator.authRepository,
) : ViewModel() {

    private val store = ServiceLocator.serverConfigStore

    private val _state = MutableStateFlow(ServerConfigUiState())
    val state: StateFlow<ServerConfigUiState> = _state.asStateFlow()

    init {
        viewModelScope.launch {
            store.current().also { addr ->
                _state.update {
                    it.copy(
                        ip = addr.ip, port = addr.port,
                        ipInput = addr.ip, portInput = addr.port.toString(),
                    )
                }
            }
        }
    }

    fun onIpChange(value: String) {
        _state.update { it.copy(ipInput = value, message = null) }
        revalidate()
    }

    fun onPortChange(value: String) {
        _state.update { it.copy(portInput = value, message = null) }
        revalidate()
    }

    private fun revalidate() {
        val s = _state.value
        val ok = isValidIp(s.ipInput) && isValidPort(s.portInput)
        _state.update { it.copy(isValid = ok) }
    }

    /** Reset IP/port fields to the BuildConfig defaults (does not save yet). */
    fun restoreDefaults() {
        _state.update {
            it.copy(
                ipInput = DEFAULT_SERVER_IP,
                portInput = DEFAULT_SERVER_PORT.toString(),
                message = null,
            )
        }
        revalidate()
    }

    /** Persist the current inputs and rebuild the network client. */
    fun save() {
        val s = _state.value
        if (!isValidIp(s.ipInput) || !isValidPort(s.portInput)) {
            _state.update { it.copy(message = "IP 或端口不合法") }
            return
        }
        _state.update { it.copy(saving = true, message = null) }
        viewModelScope.launch {
            val port = s.portInput.toInt()
            store.save(s.ipInput, port)
            repo.rebuildClient()
            _state.update {
                it.copy(
                    saving = false,
                    ip = s.ipInput, port = port,
                    message = "已保存并生效：${s.ipInput}:$port",
                )
            }
        }
    }

    companion object {
        // Accept IPv4 dotted form or a plain hostname.
        private val ipRegex = Regex(
            """^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*)$"""
        )

        fun isValidIp(v: String): Boolean = v.isNotBlank() && ipRegex.matches(v.trim())
        fun isValidPort(v: String): Boolean = v.toIntOrNull()?.let { it in 1..65535 } ?: false
    }
}
