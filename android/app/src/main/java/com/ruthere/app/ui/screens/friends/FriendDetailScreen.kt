package com.ruthere.app.ui.screens.friends

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.ruthere.app.core.DataSources

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FriendDetailScreen(
    friendshipId: Int,
    email: String,
    nickname: String?,
    onDeleted: () -> Unit,
    onBack: () -> Unit,
    vm: FriendDetailViewModel = viewModel(),
) {
    LaunchedEffect(friendshipId) { vm.init(friendshipId, nickname) }
    val state by vm.state.collectAsState()
    var showDeleteDialog by remember { mutableStateOf(false) }

    if (state.deleted) {
        LaunchedEffect(Unit) { onDeleted() }
    }

    Scaffold(topBar = { TopAppBar(title = { Text(nickname ?: email) }) }) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            LazyColumn(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            item {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("邮箱", style = MaterialTheme.typography.labelMedium)
                        Text(email, style = MaterialTheme.typography.bodyLarge)
                        Text("昵称", style = MaterialTheme.typography.labelMedium)
                        OutlinedTextField(
                            value = state.nicknameInput,
                            onValueChange = vm::onNicknameChange,
                            label = { Text("设置昵称（留空清除）") },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth(),
                        )
                        Button(onClick = vm::saveNickname, enabled = !state.loading) { Text("保存昵称") }
                    }
                }
            }

            item {
                Text("数据源权限（对好友开放的活跃度来源）", style = MaterialTheme.typography.titleSmall)
            }
            items(state.allSources) { src ->
                Row(
                    Modifier.fillMaxWidth().padding(vertical = 4.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(src.label)
                    Switch(
                        checked = src.id in state.allowedSources,
                        onCheckedChange = { vm.toggleSource(src.id) },
                    )
                }
            }

            item {
                state.message?.let { Text(it, color = MaterialTheme.colorScheme.primary) }
                Spacer(Modifier.height(8.dp))
                Button(
                    onClick = vm::poke,
                    enabled = !state.loading,
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("戳一戳") }
                Spacer(Modifier.height(8.dp))
                OutlinedButton(
                    onClick = { showDeleteDialog = true },
                    enabled = !state.loading,
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("删除好友", color = MaterialTheme.colorScheme.error) }
            }
        }

        if (state.loading) {
            CircularProgressIndicator(Modifier.align(Alignment.Center))
        }
        }
    }

    if (showDeleteDialog) {
        AlertDialog(
            onDismissRequest = { showDeleteDialog = false },
            title = { Text("删除好友") },
            text = { Text("确认删除 $email？此操作不可撤销。") },
            confirmButton = {
                TextButton(onClick = { showDeleteDialog = false; vm.delete() }) { Text("删除", color = MaterialTheme.colorScheme.error) }
            },
            dismissButton = { TextButton(onClick = { showDeleteDialog = false }) { Text("取消") } },
        )
    }
}
