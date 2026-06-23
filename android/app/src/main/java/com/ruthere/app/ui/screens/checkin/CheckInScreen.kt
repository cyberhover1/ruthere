package com.ruthere.app.ui.screens.checkin

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
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
import com.ruthere.app.data.remote.dto.CHECKIN_TYPES
import com.ruthere.app.data.remote.dto.CheckInOut

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CheckInScreen(vm: CheckInViewModel = viewModel()) {
    val state by vm.state.collectAsState()

    Scaffold(topBar = { TopAppBar(title = { Text("打卡") }) }) { padding ->
        Column(Modifier.fillMaxSize().padding(padding).padding(16.dp)) {
            // Type selector
            Text("选择状态", style = MaterialTheme.typography.labelLarge)
            Row(Modifier.fillMaxWidth().padding(vertical = 8.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                CHECKIN_TYPES.forEach { type ->
                    FilterChip(
                        selected = type == state.selectedType,
                        onClick = { vm.onSelectType(type) },
                        label = { Text(type) },
                    )
                }
            }

            OutlinedTextField(
                value = state.note,
                onValueChange = vm::onNoteChange,
                label = { Text("备注（可选）") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            Spacer(Modifier.height(12.dp))

            Button(
                onClick = vm::create,
                enabled = !state.loading,
                modifier = Modifier.fillMaxWidth(),
            ) { Text("打卡") }

            state.message?.let {
                Spacer(Modifier.height(8.dp))
                Text(it, color = MaterialTheme.colorScheme.primary)
            }

            Spacer(Modifier.height(16.dp))
            Text("历史记录", style = MaterialTheme.typography.titleSmall)
            Spacer(Modifier.height(8.dp))

            if (state.loading && state.checkins.isEmpty()) {
                CircularProgressIndicator(Modifier.align(Alignment.CenterHorizontally))
            } else if (state.checkins.isEmpty()) {
                Text("暂无打卡记录", style = MaterialTheme.typography.bodySmall)
            } else {
                LazyColumn(Modifier.fillMaxSize()) {
                    items(state.checkins) { c -> CheckInRow(c) }
                }
            }
        }
    }
}

@Composable
private fun CheckInRow(c: CheckInOut) {
    Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
        Column(Modifier.padding(12.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(c.type, style = MaterialTheme.typography.bodyLarge)
                Text(c.created_at.take(16).replace("T", " "), style = MaterialTheme.typography.labelSmall)
            }
            c.note?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
        }
    }
}
