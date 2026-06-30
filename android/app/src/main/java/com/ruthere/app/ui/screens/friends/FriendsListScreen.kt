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
import androidx.compose.material.icons.filled.FeaturedPlayList
import androidx.compose.material.icons.filled.PersonAdd
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.ruthere.app.core.TimeFormat
import com.ruthere.app.data.remote.dto.FriendActivityOut
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
                    IconButton(onClick = onOpenRequests) { Icon(Icons.Filled.FeaturedPlayList, "申请") }
                    IconButton(onClick = onAddFriend) { Icon(Icons.Filled.PersonAdd, "添加") }
                },
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            when (val s = state) {
                is FriendsListUiState.Loading -> Box(Modifier.fillMaxSize()) {
                    CircularProgressIndicator(Modifier.align(Alignment.Center))
                }
                is FriendsListUiState.Error -> Box(Modifier.fillMaxSize()) {
                    Text(s.message, color = MaterialTheme.colorScheme.error, modifier = Modifier.align(Alignment.Center))
                }
                is FriendsListUiState.Loaded -> {
                    if (s.friends.isEmpty()) {
                        Box(Modifier.fillMaxSize()) {
                            Text("还没有好友，点右上角添加", modifier = Modifier.align(Alignment.Center))
                        }
                    } else {
                        // Sort selector (PRD §7).
                        SortBar(s.sortMode, vm::setSortMode)
                        LazyColumn(Modifier.fillMaxSize()) {
                            items(s.friends) { f ->
                                FriendRow(
                                    friend = f,
                                    activity = s.activity[f.friend_id],
                                    onClick = { onOpenFriend(f.friendship_id, f.nickname, f.email) },
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SortBar(selected: FriendsSortMode, onSelect: (FriendsSortMode) -> Unit) {
    SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp)) {
        FriendsSortMode.entries.forEachIndexed { index, mode ->
            SegmentedButton(
                selected = mode == selected,
                onClick = { onSelect(mode) },
                shape = SegmentedButtonDefaults.itemShape(index, FriendsSortMode.entries.size),
            ) { Text(mode.label, style = MaterialTheme.typography.labelSmall) }
        }
    }
}

@Composable
private fun FriendRow(friend: FriendOut, activity: FriendActivityOut?, onClick: () -> Unit) {
    val value = activity?.value ?: 0
    val isOffline = activity?.is_offline ?: false
    val timeText = TimeFormat.fuzzy(activity?.last_reported_at, value, isOffline)
    val barColor = if (isOffline) MaterialTheme.colorScheme.outline else MaterialTheme.colorScheme.primary

    Column(Modifier.fillMaxWidth().clickable { onClick() }.padding(16.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(friend.nickname ?: friend.email, style = MaterialTheme.typography.bodyLarge)
                if (friend.nickname != null) Text(friend.email, style = MaterialTheme.typography.bodySmall)
            }
            Column(horizontalAlignment = Alignment.End) {
                Text("$value", style = MaterialTheme.typography.labelLarge, color = barColor)
                Text(timeText, style = MaterialTheme.typography.labelSmall, color = if (isOffline) MaterialTheme.colorScheme.outline else MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
        LinearProgressIndicator(
            progress = { value / 100f },
            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
            color = barColor,
            trackColor = MaterialTheme.colorScheme.surfaceVariant,
        )
    }
    HorizontalDivider()
}
