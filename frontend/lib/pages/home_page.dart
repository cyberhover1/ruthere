import 'dart:async';
import 'dart:math';

import 'package:flutter/material.dart';

import '../services/api_service.dart';
import 'friends_page.dart';
import 'settings_page.dart';
import 'login_page.dart';

// ── Data model ──────────────────────────────────────────────────────────────

class FriendData {
  final String nickname;
  final int vitality;
  final bool isOnline;

  const FriendData({
    required this.nickname,
    required this.vitality,
    required this.isOnline,
  });
}

// ── Home Page ───────────────────────────────────────────────────────────────

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _api = ApiService.instance;
  final _random = Random();

  int _myVitality = 50;
  List<FriendData> _friends = [];
  bool _loading = true;
  Timer? _vitalityTimer;
  Timer? _pollTimer;
  Timer? _heartbeatTimer;

  @override
  void initState() {
    super.initState();
    _loadInitialData();

    // Generate + upload vitality every 5 s
    _vitalityTimer =
        Timer.periodic(const Duration(seconds: 5), (_) => _tickVitality());

    // Poll friends activity every 10 s
    _pollTimer =
        Timer.periodic(const Duration(seconds: 10), (_) => _fetchFriends());

    // Heartbeat every 30 s
    _heartbeatTimer =
        Timer.periodic(const Duration(seconds: 30), (_) => _sendHeartbeat());
  }

  @override
  void dispose() {
    _vitalityTimer?.cancel();
    _pollTimer?.cancel();
    _heartbeatTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadInitialData() async {
    try {
      await _fetchFriends();
      await _tickVitality(); // first upload
    } catch (_) {}
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _fetchFriends() async {
    try {
      final data = await _api.getFriendsActivity();
      final list = (data['friends'] as List).map((e) {
        final m = e as Map<String, dynamic>;
        return FriendData(
          nickname: m['nickname'] as String? ?? '',
          vitality: m['activity_score'] as int? ?? 0,
          isOnline: m['is_online'] as bool? ?? false,
        );
      }).toList();
      if (mounted) setState(() => _friends = list);
    } catch (_) {}
  }

  Future<void> _tickVitality() async {
    // Upload a random vitality increment (1-100).
    // Backend formula: new_score = max(100, current_score + increment)
    final inc = 1 + _random.nextInt(100);   // 1..100
    try {
      final data = await _api.reportActivity(inc);
      if (mounted) {
        setState(() => _myVitality = data['activity_score'] as int? ?? 0);
      }
    } catch (_) {}
  }

  Future<void> _sendHeartbeat() async {
    try {
      await _api.heartbeat();
    } catch (_) {}
  }

  Color _color(int v) =>
      v >= 70 ? Colors.green : v >= 40 ? Colors.orange : Colors.red;

  void _openSettings() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const SettingsPage()),
    );
  }

  Future<void> _logout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('退出登录'),
        content: const Text('确定要退出登录吗？'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('取消')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('退出', style: TextStyle(color: Colors.red))),
        ],
      ),
    );
    if (confirmed != true) return;

    await _api.logout();
    if (!mounted) return;
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (_) => const LoginPage()),
      (route) => false,
    );
  }

  void _openFriends() async {
    final result = await Navigator.push<bool>(
      context,
      MaterialPageRoute(builder: (_) => const FriendsPage()),
    );
    // Refresh friends list after returning (e.g. after adding/removing)
    if (result == true) {
      _fetchFriends();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('安心圈'),
        centerTitle: true,
        backgroundColor: theme.colorScheme.inversePrimary,
        actions: [
          IconButton(
            icon: const Icon(Icons.people),
            tooltip: '好友管理',
            onPressed: _openFriends,
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            tooltip: '服务器设置',
            onPressed: _openSettings,
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: '退出登录',
            onPressed: _logout,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                _buildMyCard(),
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 8, 8, 0),
                  child: Row(
                    children: [
                      const Text('好友动态',
                          style: TextStyle(
                              fontSize: 14, fontWeight: FontWeight.w600)),
                      const Spacer(),
                      IconButton(
                        icon: const Icon(Icons.refresh, size: 20),
                        onPressed: _fetchFriends,
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: _friends.isEmpty
                      ? const Center(child: Text('暂无好友'))
                      : ListView.separated(
                          itemCount: _friends.length,
                          separatorBuilder: (_, __) =>
                              const Divider(height: 1),
                          itemBuilder: (_, i) => _buildFriendTile(_friends[i]),
                        ),
                ),
              ],
            ),
    );
  }

  Widget _buildMyCard() {
    final c = _color(_myVitality);
    final name = _api.nickname ?? '';
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: c.withAlpha(25),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: c.withAlpha(40),
            child: Text(
              name.isNotEmpty ? name[0].toUpperCase() : '?',
              style:
                  TextStyle(color: c, fontWeight: FontWeight.bold, fontSize: 18),
            ),
          ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(name.isNotEmpty ? name : '我',
                  style: const TextStyle(
                      fontWeight: FontWeight.bold, fontSize: 16)),
              const Text('我的活力',
                  style: TextStyle(fontSize: 12, color: Colors.grey)),
            ],
          ),
          const Spacer(),
          Text(
            '$_myVitality',
            style:
                TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: c),
          ),
        ],
      ),
    );
  }

  Widget _buildFriendTile(FriendData f) {
    final c = _color(f.vitality);
    return ListTile(
      leading: CircleAvatar(
        backgroundColor: c.withAlpha(40),
        child: Text(
          f.nickname.isNotEmpty ? f.nickname[0].toUpperCase() : '?',
          style: TextStyle(color: c, fontWeight: FontWeight.bold),
        ),
      ),
      title: Row(
        children: [
          Text(f.nickname),
          if (!f.isOnline) ...[
            const SizedBox(width: 8),
            const Text('(离线)', style: TextStyle(fontSize: 12, color: Colors.grey)),
          ],
        ],
      ),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: f.isOnline ? c : Colors.grey,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 8),
          SizedBox(
            width: 36,
            child: Text(
              '${f.vitality}',
              textAlign: TextAlign.right,
              style: TextStyle(
                  fontWeight: FontWeight.w600,
                  color: f.isOnline ? c : Colors.grey),
            ),
          ),
        ],
      ),
    );
  }
}