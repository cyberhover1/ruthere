package com.ruthere.app.ui.screens.friends

import android.graphics.Bitmap
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.journeyapps.barcodescanner.ScanContract
import com.journeyapps.barcodescanner.ScanIntentResult
import com.journeyapps.barcodescanner.ScanOptions

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FriendAddScreen(
    onBack: () -> Unit,
    vm: FriendAddViewModel = viewModel(),
) {
    val state by vm.state.collectAsState()
    var tab by remember { mutableStateOf(0) }

    // ZXing intent scan launcher
    val scanLauncher = rememberLauncherForActivityResult(ScanContract()) { result: ScanIntentResult ->
        val token = result.contents
        if (!token.isNullOrBlank()) vm.addByQrToken(token)
    }

    Scaffold(topBar = { TopAppBar(title = { Text("添加好友") }) }) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            TabRow(selectedTabIndex = tab) {
                Tab(selected = tab == 0, onClick = { tab = 0; vm.reset() }, text = { Text("我的二维码") })
                Tab(selected = tab == 1, onClick = { tab = 1; vm.reset() }, text = { Text("扫码") })
                Tab(selected = tab == 2, onClick = { tab = 2; vm.reset() }, text = { Text("邮箱搜索") })
            }

            when (tab) {
                0 -> MyQrTab(state, vm)
                1 -> ScanTab(state, scanLauncher) { vm.reset() }
                2 -> SearchTab(state, vm)
            }
        }
    }
}

@Composable
private fun MyQrTab(state: FriendAddUiState, vm: FriendAddViewModel) {
    Column(
        Modifier.fillMaxSize().padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Button(onClick = vm::generateQr, enabled = state !is FriendAddUiState.Loading) { Text("生成二维码") }
        when (state) {
            is FriendAddUiState.Loading -> CircularProgressIndicator()
            is FriendAddUiState.QrReady -> {
                val bmp = remember(state.token) { generateQrBitmap(state.token) }
                Image(bitmap = bmp.asImageBitmap(), contentDescription = "好友二维码", modifier = Modifier.size(300.dp))
                Text("让好友扫描此二维码加你为好友", style = MaterialTheme.typography.bodySmall)
            }
            is FriendAddUiState.Error -> Text(state.message, color = MaterialTheme.colorScheme.error)
            else -> {}
        }
    }
}

@Composable
private fun ScanTab(
    state: FriendAddUiState,
    scanLauncher: androidx.activity.compose.ManagedActivityResultLauncher<ScanOptions, ScanIntentResult>,
    onReset: () -> Unit,
) {
    Column(
        Modifier.fillMaxSize().padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Button(onClick = {
            scanLauncher.launch(ScanOptions().apply {
                setDesiredBarcodeFormats(ScanOptions.QR_CODE)
                setPrompt("扫描好友的二维码")
                setBeepEnabled(true)
            })
        }) { Text("开始扫码") }
        when (state) {
            is FriendAddUiState.Loading -> CircularProgressIndicator()
            is FriendAddUiState.Success -> {
                Text(state.message, color = MaterialTheme.colorScheme.primary)
                OutlinedButton(onClick = onReset) { Text("继续扫描") }
            }
            is FriendAddUiState.Error -> Text(state.message, color = MaterialTheme.colorScheme.error)
            else -> {}
        }
    }
}

@Composable
private fun SearchTab(state: FriendAddUiState, vm: FriendAddViewModel) {
    var email by remember { mutableStateOf("") }
    Column(
        Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        OutlinedTextField(
            value = email, onValueChange = { email = it },
            label = { Text("邮箱") }, singleLine = true, modifier = Modifier.fillMaxWidth(),
        )
        Button(
            onClick = { vm.search(email) },
            enabled = email.isNotBlank() && state !is FriendAddUiState.Loading,
            modifier = Modifier.fillMaxWidth(),
        ) { Text("搜索") }

        when (state) {
            is FriendAddUiState.Loading -> CircularProgressIndicator(Modifier.align(Alignment.CenterHorizontally))
            is FriendAddUiState.SearchResults -> {
                if (state.users.isEmpty()) Text("未找到用户")
                else state.users.forEach { u ->
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(u.email)
                        OutlinedButton(onClick = { vm.sendRequest(u.id) }) { Text("加好友") }
                    }
                }
            }
            is FriendAddUiState.Success -> Text(state.message, color = MaterialTheme.colorScheme.primary)
            is FriendAddUiState.Error -> Text(state.message, color = MaterialTheme.colorScheme.error)
            else -> {}
        }
    }
}
