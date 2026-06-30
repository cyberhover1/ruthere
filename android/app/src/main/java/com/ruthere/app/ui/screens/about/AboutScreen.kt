package com.ruthere.app.ui.screens.about

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.ruthere.app.BuildConfig
import com.ruthere.app.core.ServiceLocator
import kotlinx.coroutines.launch

/** About screen: app info, version, check for updates. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AboutScreen(onBack: () -> Unit) {
    val scope = rememberCoroutineScope()
    var checking by remember { mutableStateOf(false) }
    var dialogInfo by remember { mutableStateOf<VersionDialog?>(null) }

    Scaffold(
        topBar = {
            androidx.compose.material3.TopAppBar(
                title = { Text("关于") },
                navigationIcon = {
                    IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "返回") }
                },
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier.fillMaxSize().padding(padding).padding(24.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text("安心圈", style = MaterialTheme.typography.headlineMedium)
            Spacer(Modifier.height(8.dp))
            Text("RutThere", style = MaterialTheme.typography.bodyMedium)

            Spacer(Modifier.height(16.dp))
            Text(
                "v${BuildConfig.VERSION_NAME}",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.primary,
            )

            Spacer(Modifier.height(32.dp))
            Button(
                onClick = {
                    scope.launch {
                        checking = true
                        dialogInfo = checkVersion()
                        checking = false
                    }
                },
                enabled = !checking,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (checking) {
                    CircularProgressIndicator(
                        modifier = Modifier.height(20.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onPrimary,
                    )
                } else {
                    Text("检查新版本")
                }
            }

            Spacer(Modifier.height(32.dp))
            Text(
                "武汉三合鼎盛科技股份有限公司",
                style = MaterialTheme.typography.bodyLarge,
            )
            Spacer(Modifier.height(4.dp))
            Text(
                "Copyright © 2026 武汉三合鼎盛科技股份有限公司",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center,
            )
            Text(
                "All Rights Reserved.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center,
            )
        }
    }

    // Result dialog
    dialogInfo?.let { info ->
        AlertDialog(
            onDismissRequest = { dialogInfo = null },
            title = { Text(info.title) },
            text = { Text(info.message) },
            confirmButton = {
                TextButton(onClick = { dialogInfo = null }) {
                    Text("确定")
                }
            },
        )
    }
}

private data class VersionDialog(val title: String, val message: String)

private suspend fun checkVersion(): VersionDialog {
    val localVersion = BuildConfig.VERSION_NAME
    return try {
        val health = ServiceLocator.networkClient.api.health()
        val remoteVersion = health.appVersion

        if (remoteVersion == null) {
            VersionDialog("检查失败", "无法获取远程版本信息")
        } else if (remoteVersion == localVersion) {
            VersionDialog("已是最新版本", "当前版本 v$localVersion 已是最新")
        } else {
            VersionDialog("发现新版本", "当前版本 v$localVersion\n后端版本 v$remoteVersion\n请更新应用")
        }
    } catch (e: Exception) {
        VersionDialog("检查失败", "无法连接服务器，请检查网络设置")
    }
}