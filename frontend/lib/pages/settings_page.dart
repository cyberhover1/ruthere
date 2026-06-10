import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../services/config.dart';
import '../services/api_service.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  final _hostCtrl = TextEditingController();
  final _portCtrl = TextEditingController();
  bool _testing = false;
  String? _testResult;

  @override
  void initState() {
    super.initState();
    final cfg = ServerConfig.instance;
    _hostCtrl.text = cfg.host;
    _portCtrl.text = cfg.port.toString();
  }

  @override
  void dispose() {
    _hostCtrl.dispose();
    _portCtrl.dispose();
    super.dispose();
  }

  void _save() {
    final host = _hostCtrl.text.trim();
    final port = int.tryParse(_portCtrl.text.trim()) ?? 8000;
    if (host.isEmpty) {
      _show('请输入服务器地址');
      return;
    }
    ServerConfig.instance.set(host, port);
    ApiService.instance.clearSession();
    _show('已保存并清除登录状态');
  }

  Future<void> _testConnection() async {
    final host = _hostCtrl.text.trim();
    final port = int.tryParse(_portCtrl.text.trim()) ?? 8000;
    if (host.isEmpty) return;

    ServerConfig.instance.set(host, port);
    final url = '${ServerConfig.instance.baseUrl}/health';

    setState(() {
      _testing = true;
      _testResult = null;
    });

    try {
      final resp = await http.get(Uri.parse(url));
      if (resp.statusCode == 200) {
        _testResult = '✅ 连接成功';
      } else {
        _testResult = '❌ 服务器返回状态码 ${resp.statusCode}';
      }
    } catch (e) {
      _testResult = '❌ 连接失败: ${e.toString().replaceFirst('Exception: ', '')}';
    } finally {
      if (mounted) setState(() => _testing = false);
    }
  }

  void _show(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(msg)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('服务器设置'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _hostCtrl,
              decoration: const InputDecoration(
                labelText: '服务器地址',
                hintText: '例如 127.0.0.1',
                prefixIcon: Icon(Icons.dns),
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.url,
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _portCtrl,
              decoration: const InputDecoration(
                labelText: '端口',
                hintText: '8000',
                prefixIcon: Icon(Icons.numbers),
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.number,
              textInputAction: TextInputAction.done,
            ),
            const SizedBox(height: 32),
            FilledButton.icon(
              onPressed: _testing ? null : _testConnection,
              icon: _testing
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white),
                    )
                  : const Icon(Icons.wifi_find),
              label: Text(_testing ? '测试中...' : '测试连接'),
            ),
            if (_testResult != null) ...[
              const SizedBox(height: 8),
              Text(
                _testResult!,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 14,
                  color: _testResult!.startsWith('✅')
                      ? Colors.green
                      : Colors.red,
                ),
              ),
            ],
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: _save,
              icon: const Icon(Icons.save),
              label: const Text('保存'),
            ),
          ],
        ),
      ),
    );
  }
}