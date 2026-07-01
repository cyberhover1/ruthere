package com.ruthere.app.ui.screens.friends

import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
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
import androidx.compose.material.icons.outlined.TouchApp
import androidx.compose.material3.AlertDialog
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
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.viewmodel.compose.viewModel
import com.ruthere.app.core.TimeFormat
import com.ruthere.app.data.remote.dto.FriendActivityOut
import com.ruthere.app.data.remote.dto.FriendOut
import com.ruthere.app.data.remote.dto.PokeStatsResponse
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

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

    // Refresh friend list every time the screen becomes visible (fixes blank
    // list after returning from the add-friend screen).
    val lifecycleOwner = LocalLifecycleOwner.current
    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) vm.refresh()
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }

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

    // Dialog state for double-click poke stats.
    var pokeStatsDialog by remember { mutableStateOf<PokeStatsDialogState?>(null) }

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
                                    onDoubleClickNickname = {
                                        // Fetch poke stats and show dialog.
                                        vm.pokeStats(f.friendship_id) { stats ->
                                            pokeStatsDialog = PokeStatsDialogState(
                                                friend = f,
                                                stats = stats,
                                            )
                                        }
                                    },
                                )
                            }
                        }
                    }
                }
            }
        }
    }

    // Poke stats dialog.
    pokeStatsDialog?.let { d ->
        PokeStatsDialog(
            friend = d.friend,
            stats = d.stats,
            onDismiss = { pokeStatsDialog = null },
        )
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
private fun FriendRow(friend: FriendOut, activity: FriendActivityOut?, onClick: () -> Unit, onDoubleClickNickname: () -> Unit) {
    val value = activity?.value ?: 0
    val isOffline = activity?.is_offline ?: false
    val timeText = TimeFormat.fuzzy(activity?.last_reported_at, value, isOffline)
    val pokeTime = activity?.last_poked_at
    val pokeText = TimeFormat.fuzzyPoked(pokeTime)
    val barColor = if (isOffline) MaterialTheme.colorScheme.outline else MaterialTheme.colorScheme.primary

    // Display the friend's own nickname, falling back to per-friendship nickname, then email.
    val displayName = friend.friend_nickname ?: friend.nickname ?: friend.email

    Column(Modifier.fillMaxWidth().clickable { onClick() }.padding(16.dp)) {
        // Poke indicator: only shown when this friend has poked the current user.
        if (pokeText != null) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Outlined.TouchApp,
                    contentDescription = "戳了戳",
                    modifier = Modifier.padding(end = 4.dp),
                    tint = MaterialTheme.colorScheme.tertiary,
                )
                Text(
                    text = pokeText,
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.tertiary,
                )
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                // Nickname — double-tap opens poke-stats dialog
                Text(
                    text = displayName,
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier.pointerInput(Unit) {
                        detectTapGestures(
                            onDoubleTap = { onDoubleClickNickname() },
                        )
                    },
                )
                // Show email as subtitle when display name differs from email
                if (displayName != friend.email) {
                    Text(friend.email, style = MaterialTheme.typography.bodySmall)
                }
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

// --- Double-click poke stats dialog ---

private data class PokeStatsDialogState(
    val friend: FriendOut,
    val stats: PokeStatsResponse,
)

private val BEIJING_ZONE = ZoneId.of("Asia/Shanghai")
private val POKE_FORMATTER = DateTimeFormatter.ofPattern("MM-dd HH:mm")

@Composable
private fun PokeStatsDialog(
    friend: FriendOut,
    stats: PokeStatsResponse,
    onDismiss: () -> Unit,
) {
    val displayName = friend.friend_nickname ?: friend.nickname ?: friend.email

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(displayName) },
        text = {
            Column {
                Text("邮箱：${friend.email}", style = MaterialTheme.typography.bodyMedium)
                Text("")
                Text("对方戳了你 ${stats.total_pokes} 次", style = MaterialTheme.typography.bodyMedium)
                if (stats.recent_pokes.isNotEmpty()) {
                    Text("", style = MaterialTheme.typography.bodySmall)
                    Text("最近两次：", style = MaterialTheme.typography.bodySmall)
                    stats.recent_pokes.forEach { iso ->
                        val formatted = runCatching {
                            Instant.parse(iso).atZone(BEIJING_ZONE).format(POKE_FORMATTER)
                        }.getOrElse { iso.take(16).replace("T", " ") }
                        Text("  · $formatted", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) { Text("关闭") }
        },
    )
}
