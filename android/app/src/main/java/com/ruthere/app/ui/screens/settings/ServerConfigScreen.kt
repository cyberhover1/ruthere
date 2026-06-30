package com.ruthere.app.ui.screens.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.text.style.TextAlign
import androidx.lifecycle.viewmodel.compose.viewModel

import com.ruthere.app.BuildConfig

/** Settings → Server: edit backend IP/port, restore defaults, save & apply. */
@Composable
fun ServerConfigScreen(
    vm: ServerConfigViewModel = viewModel(),
    onGoAbout: () -> Unit = {},
    onLogout: () -> Unit = {},
) {
    val state by vm.state.collectAsState()
    var showLogoutDialog by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("服务器配置", style = MaterialTheme.typography.headlineSmall)

        Card(modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("当前生效地址", style = MaterialTheme.typography.labelLarge)
                Text(
                    "${state.ip}:${state.port}",
                    style = MaterialTheme.typography.bodyLarge,
                )
            }
        }

        OutlinedTextField(
            value = state.ipInput,
            onValueChange = vm::onIpChange,
            label = { Text("服务器 IP / 域名") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )

        OutlinedTextField(
            value = state.portInput,
            onValueChange = vm::onPortChange,
            label = { Text("端口 (1-65535)") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )

        if (!state.isValid) {
            Text("IP 或端口格式不合法", color = MaterialTheme.colorScheme.error)
        }

        state.message?.let { Text(it, color = MaterialTheme.colorScheme.primary) }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            OutlinedButton(
                onClick = vm::restoreDefaults,
                modifier = Modifier.weight(1f),
            ) { Text("恢复默认") }

            Button(
                onClick = vm::save,
                enabled = state.isValid && !state.saving,
                modifier = Modifier.weight(1f),
            ) { Text("保存并生效") }
        }

        Spacer(Modifier.height(8.dp))
        if (state.saving) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                CircularProgressIndicator()
                Spacer(Modifier.height(0.dp))
                Text("  保存中…")
            }
        }

        Spacer(Modifier.height(24.dp))
        OutlinedButton(onClick = onGoAbout, modifier = Modifier.fillMaxWidth()) {
            Text("关于")
        }

        Spacer(Modifier.height(16.dp))
        Button(
            onClick = { showLogoutDialog = true },
            colors = ButtonDefaults.buttonColors(
                containerColor = MaterialTheme.colorScheme.error,
                contentColor = MaterialTheme.colorScheme.onError,
            ),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("退出登录")
        }

        Spacer(Modifier.weight(1f))
        Text(
            "v${BuildConfig.VERSION_NAME}",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.fillMaxWidth(),
            textAlign = TextAlign.Center,
        )
    }

    // Logout confirmation dialog
    if (showLogoutDialog) {
        AlertDialog(
            onDismissRequest = { showLogoutDialog = false },
            title = { Text("退出登录") },
            text = { Text("确定退出登录吗？") },
            confirmButton = {
                Button(
                    onClick = {
                        showLogoutDialog = false
                        onLogout()
                    },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.error,
                        contentColor = MaterialTheme.colorScheme.onError,
                    ),
                ) {
                    Text("确定退出")
                }
            },
            dismissButton = {
                TextButton(onClick = { showLogoutDialog = false }) {
                    Text("取消")
                }
            },
        )
    }
}