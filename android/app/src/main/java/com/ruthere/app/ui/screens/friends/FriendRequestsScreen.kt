package com.ruthere.app.ui.screens.friends

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.ruthere.app.data.remote.dto.FriendRequestOut

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FriendRequestsScreen(
    myUserId: Int,
    onBack: () -> Unit,
    vm: FriendRequestsViewModel = viewModel(),
) {
    vm.setMyUserId(myUserId)
    val state by vm.state.collectAsState()

    Scaffold(topBar = { TopAppBar(title = { Text("好友申请") }) }) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when (val s = state) {
                is FriendRequestsUiState.Loading -> CircularProgressIndicator(Modifier.align(Alignment.Center))
                is FriendRequestsUiState.Error -> Text(
                    s.message, color = MaterialTheme.colorScheme.error, modifier = Modifier.align(Alignment.Center)
                )
                is FriendRequestsUiState.Loaded -> {
                    if (s.requests.isEmpty()) {
                        Text("暂无申请", modifier = Modifier.align(Alignment.Center))
                    } else {
                        LazyColumn {
                            items(s.requests) { r -> RequestRow(r, vm.isIncoming(r), vm::accept, vm::reject) }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun RequestRow(
    r: FriendRequestOut,
    isIncoming: Boolean,
    onAccept: (Int) -> Unit,
    onReject: (Int) -> Unit,
) {
    Column(Modifier.fillMaxWidth().padding(16.dp)) {
        val other = if (isIncoming) r.from_user_id else r.to_user_id
        val direction = if (isIncoming) "收到来自" else "已发送给"
        Text("$direction 用户 $other", style = MaterialTheme.typography.bodyLarge)
        Text("状态：${statusLabel(r.status)}", style = MaterialTheme.typography.bodySmall)
        if (isIncoming && r.status == "pending") {
            Row(Modifier.padding(top = 8.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = { onAccept(r.id) }) { Text("同意") }
                OutlinedButton(onClick = { onReject(r.id) }) { Text("拒绝") }
            }
        }
    }
    HorizontalDivider()
}

private fun statusLabel(s: String) = when (s) {
    "pending" -> "待处理"
    "accepted" -> "已接受"
    "rejected" -> "已拒绝"
    else -> s
}
