package com.ruthere.app.ui.screens.friends

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PersonAdd
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.ruthere.app.data.remote.dto.FriendOut

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FriendsListScreen(
    onAddFriend: () -> Unit,
    onOpenRequests: () -> Unit,
    onOpenFriend: (Int, String?, String) -> Unit,
    vm: FriendsListViewModel = viewModel(),
) {
    val state by vm.state.collectAsState()
    val snackbar = remember { SnackbarHostState() }

    LaunchedEffect(state) {
        val s = state
        if (s is FriendsListUiState.Loaded && s.notifications.isNotEmpty()) {
            val text = s.notifications.joinToString("\n") { n ->
                when (n.type) {
                    "friend_removed" -> "${n.payload["removed_by_email"]} 删除了你"
                    "poked" -> "${n.payload["poked_by_email"]} 戳了你"
                    else -> n.type
                }
            }
            snackbar.showSnackbar(text)
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("好友") },
                actions = {
                    IconButton(onClick = onOpenRequests) { Icon(Icons.Filled.PersonAdd, "申请") }
                    IconButton(onClick = onAddFriend) { Icon(Icons.Filled.PersonAdd, "添加") }
                },
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when (val s = state) {
                is FriendsListUiState.Loading -> CircularProgressIndicator(Modifier.align(Alignment.Center))
                is FriendsListUiState.Error -> Text(
                    s.message, color = MaterialTheme.colorScheme.error, modifier = Modifier.align(Alignment.Center)
                )
                is FriendsListUiState.Loaded -> {
                    if (s.friends.isEmpty()) {
                        Text("还没有好友，点右上角添加", modifier = Modifier.align(Alignment.Center))
                    } else {
                        LazyColumn {
                            items(s.friends) { f -> FriendRow(f) { onOpenFriend(f.friendship_id, f.nickname, f.email) } }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun FriendRow(f: FriendOut, onClick: () -> Unit) {
    Column(Modifier.fillMaxWidth().clickable { onClick() }.padding(16.dp)) {
        Text(f.nickname ?: f.email, style = MaterialTheme.typography.bodyLarge)
        if (f.nickname != null) Text(f.email, style = MaterialTheme.typography.bodySmall)
    }
    HorizontalDivider()
}
