import 'package:flutter/material.dart';

import '../services/api_service.dart';

// ── Data model ──────────────────────────────────────────────────────────────

class _UserEntry {
  final int userId;
  final String username;
  final bool isOnline;
  bool isFriend;

  _UserEntry({
    required this.userId,
    required this.username,
    required this.isOnline,
    this.isFriend = false,
  });
}

// ── Friends Page ────────────────────────────────────────────────────────────

class FriendsPage extends StatefulWidget {
  const FriendsPage({super.key});

  @override
  State<FriendsPage> createState() => _FriendsPageState();
}

class _FriendsPageState extends State<FriendsPage> {
  final _api = ApiService.instance;
  List<_UserEntry> _users = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      // Fetch all users and current friends
      final usersResp = await _api.getUsers();
      final friendsResp = await _api.getFriendsActivity();

      final allUsers = (usersResp['users'] as List).map((e) {
        final m = e as Map<String, dynamic>;
        return _UserEntry(
          userId: m['user_id'] as int,
          username: m['username'] as String? ?? '',
          isOnline: m['is_online'] as bool? ?? false,
        );
      }).toList();

      // Build a set of friend usernames for quick lookup
      final friendNames = (friendsResp['friends'] as List)
          .map((e) => (e as Map<String, dynamic>)['username'] as String? ?? '')
          .toSet();

      for (final u in allUsers) {
        u.isFriend = friendNames.contains(u.username);
      }

      if (mounted) setState(() {
        _users = allUsers;
        _loading = false;
      });
    } catch (e) {
      if (mounted) setState(() => _loading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('加载失败: ${e.toString().replaceFirst('Exception: ', '')}')),
        );
      }
    }
  }

  Future<void> _toggleFriend(_UserEntry user) async {
    try {
      if (user.isFriend) {
        await _api.removeFriend(user.username);
      } else {
        await _api.addFriend(user.username);
      }
      if (mounted) {
        setState(() => user.isFriend = !user.isFriend);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('操作失败: ${e.toString().replaceFirst('Exception: ', '')}')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('好友管理'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _load,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _users.isEmpty
              ? const Center(child: Text('没有其他用户'))
              : ListView.separated(
                  itemCount: _users.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (_, i) => _buildUserTile(_users[i]),
                ),
    );
  }

  Widget _buildUserTile(_UserEntry user) {
    return ListTile(
      leading: CircleAvatar(
        backgroundColor:
            user.isOnline ? Colors.green.withAlpha(40) : Colors.grey.withAlpha(40),
        child: Icon(
          Icons.person,
          color: user.isOnline ? Colors.green : Colors.grey,
        ),
      ),
      title: Text(user.username),
      subtitle: Text(user.isOnline ? '在线' : '离线'),
      trailing: ElevatedButton(
        onPressed: () => _toggleFriend(user),
        style: ElevatedButton.styleFrom(
          backgroundColor: user.isFriend ? Colors.red.withAlpha(30) : Colors.green.withAlpha(30),
          foregroundColor: user.isFriend ? Colors.red : Colors.green,
          padding: const EdgeInsets.symmetric(horizontal: 16),
        ),
        child: Text(user.isFriend ? '删除' : '添加'),
      ),
    );
  }
}