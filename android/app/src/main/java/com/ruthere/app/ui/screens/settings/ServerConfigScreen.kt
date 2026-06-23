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
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel

/** Settings → Server: edit backend IP/port, restore defaults, save & apply. */
@Composable
fun ServerConfigScreen(
    vm: ServerConfigViewModel = viewModel(),
    onGoAbout: () -> Unit = {},
) {
    val state by vm.state.collectAsState()

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
    }
}
