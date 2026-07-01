package com.ruthere.app.ui.screens.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
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

/** Settings → Server: edit backend IP/port, nickname, restore defaults, save & apply. */
@Composable
fun ServerConfigScreen(
    vm: ServerConfigViewModel = viewModel(),
    onGoAbout: () -> Unit = {},
    onLogout: () -> Unit = {},
) {
    val state by vm.state.collectAsState()
    var showLogoutDialog by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp).verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("设置", style = MaterialTheme.typography.headlineSmall)

        // --- Nickname card ---
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("个人资料", style = MaterialTheme.typography.titleSmall)
                Text("邮箱：${state.userEmail}", style = MaterialTheme.typography.bodyMedium)
                OutlinedTextField(
                    value = state.nicknameInput,
                    onValueChange = vm::onNicknameChange,
                    label = { Text("昵称（留空则使用邮箱名）") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                Button(
                    onClick = vm::saveNickname,
                    enabled = !state.savingNickname,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    if (state.savingNickname) {
                        CircularProgressIndicator(
                            modifier = Modifier.padding(end = 4.dp).size(16.dp),
                            strokeWidth = 2.dp,
                        )
                    }
                    Text("保存昵称")
                }
            }
        }

        // --- Server config card ---
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("服务器配置", style = MaterialTheme.typography.titleSmall)
                Text(
                    "当前生效地址：${state.ip}:${state.port}",
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
                Spacer(Modifier.width(8.dp))
                Text("保存中…")
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

        Spacer(Modifier.height(16.dp))
        Text(
            "v${BuildConfig.VERSION_NAME}",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.fillMaxWidth(),
            textAlign = TextAlign.Center,
        )
    }

    // Logout confirmation dialog (outside Column, at top level of @Composable)
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