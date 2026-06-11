import 'package:flutter/material.dart';

import '../services/api_service.dart';

// ── Data models ────────────────────────────────────────────────────────────

class _FriendRequestItem {
  final int requestId;
  final int senderId;
  final String senderNickname;
  final String senderPhone;
  final String? createdAt;

  _FriendRequestItem({
    required this.requestId,
    required this.senderId,
    required this.senderNickname,
    required this.senderPhone,
    this.createdAt,
  });
}

// ── Friends Page ────────────────────────────────────────────────────────────

class FriendsPage extends StatefulWidget {
  const FriendsPage({super.key});

  @override
  State<FriendsPage> createState() => _FriendsPageState();
}

class _FriendsPageState extends State<FriendsPage>
    with SingleTickerProviderStateMixin {
  final _api = ApiService.instance;
  final _searchPhoneCtrl = TextEditingController();

  late TabController _tabCtrl;

  // Current friends list
  List<Map<String, dynamic>> _friends = [];
  bool _friendsLoading = true;

  // Pending friend requests
  List<_FriendRequestItem> _pendingRequests = [];
  bool _requestsLoading = true;

  // Search result
  Map<String, dynamic>? _searchResult;
  bool _searching = false;
  String? _searchError;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 3, vsync: this);
    _loadData();
  }

  @override
  void dispose() {
    _searchPhoneCtrl.dispose();
    _tabCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    await Future.wait([_loadFriends(), _loadRequests()]);
  }

  Future<void> _loadFriends() async {
    setState(() => _friendsLoading = true);
    try {
      final data = await _api.getFriendsActivity();
      final list = (data['friends'] as List)
          .map((e) => e as Map<String, dynamic>)
          .toList();
      if (mounted) setState(() => _friends = list);
    } catch (_) {}
    if (mounted) setState(() => _friendsLoading = false);
  }

  Future<void> _loadRequests() async {
    setState(() => _requestsLoading = true);
    try {
      final data = await _api.getFriendRequests();
      final items = (data['requests'] as List).map((e) {
        final m = e as Map<String, dynamic>;
        return _FriendRequestItem(
          requestId: m['request_id'] as int,
          senderId: m['sender_id'] as int,
          senderNickname: m['sender_nickname'] as String? ?? '',
          senderPhone: m['sender_phone'] as String? ?? '',
          createdAt: m['created_at'] as String?,
        );
      }).toList();
      if (mounted) setState(() => _pendingRequests = items);
    } catch (_) {}
    if (mounted) setState(() => _requestsLoading = false);
  }

  Future<void> _searchUser() async {
    final phone = _searchPhoneCtrl.text.trim();
    if (phone.isEmpty) return;

    setState(() {
      _searching = true;
      _searchResult = null;
      _searchError = null;
    });

    try {
      final result = await _api.searchUserByPhone(phone);
      if (mounted) setState(() => _searchResult = result);
    } catch (e) {
      if (mounted) {
        setState(() =>
            _searchError = e.toString().replaceFirst('Exception: ', ''));
      }
    } finally {
      if (mounted) setState(() => _searching = false);
    }
  }

  Future<void> _sendFriendRequest(String phone) async {
    try {
      await _api.sendFriendRequest(phone);
      if (!mounted) return;
      _showSuccess('好友请求已发送');
      setState(() => _searchResult = null);
      _searchPhoneCtrl.clear();
    } catch (e) {
      if (!mounted) return;
      _showError(e.toString().replaceFirst('Exception: ', ''));
    }
  }

  Future<void> _acceptRequest(int requestId) async {
    try {
      await _api.acceptFriendRequest(requestId);
      if (!mounted) return;
      _showSuccess('已添加好友');
      await _loadData();
    } catch (e) {
      if (!mounted) return;
      _showError(e.toString().replaceFirst('Exception: ', ''));
    }
  }

  Future<void> _rejectRequest(int requestId) async {
    try {
      await _api.rejectFriendRequest(requestId);
      if (!mounted) return;
      await _loadRequests();
    } catch (e) {
      if (!mounted) return;
      _showError(e.toString().replaceFirst('Exception: ', ''));
    }
  }

  Future<void> _removeFriend(String phone, String nickname) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('删除好友'),
        content: Text('确定要删除 $nickname 吗？'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('取消')),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('删除', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    try {
      await _api.removeFriend(phone);
      if (!mounted) return;
      _showSuccess('已删除好友');
      await _loadFriends();
    } catch (e) {
      if (!mounted) return;
      _showError(e.toString().replaceFirst('Exception: ', ''));
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(msg)));
  }

  void _showSuccess(String msg) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.green));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('好友管理'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        bottom: TabBar(
          controller: _tabCtrl,
          tabs: const [
            Tab(text: '当前好友'),
            Tab(text: '好友请求'),
            Tab(text: '添加好友'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabCtrl,
        children: [
          _buildFriendsTab(),
          _buildRequestsTab(),
          _buildAddFriendTab(),
        ],
      ),
    );
  }

  // ── Tab 1: Current friends ──────────────────────────────────────────────

  Widget _buildFriendsTab() {
    if (_friendsLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_friends.isEmpty) {
      return const Center(child: Text('暂无好友，快去添加吧'));
    }
    return RefreshIndicator(
      onRefresh: _loadFriends,
      child: ListView.separated(
        itemCount: _friends.length,
        separatorBuilder: (_, __) => const Divider(height: 1),
        itemBuilder: (_, i) {
          final f = _friends[i];
          final nickname = f['nickname'] as String? ?? '';
          final phone = f['phone'] as String? ?? '';
          final isOnline = f['is_online'] as bool? ?? false;
          final score = f['activity_score'] as int? ?? 0;

          return ListTile(
            leading: CircleAvatar(
              backgroundColor: isOnline
                  ? Colors.green.withAlpha(40)
                  : Colors.grey.withAlpha(40),
              child: Text(
                nickname.isNotEmpty ? nickname[0] : '?',
                style: TextStyle(
                  color: isOnline ? Colors.green : Colors.grey,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            title: Text(nickname),
            subtitle: Text('$phone  ·  活跃度 $score'),
            trailing: TextButton(
              onPressed: () => _removeFriend(phone, nickname),
              style: TextButton.styleFrom(foregroundColor: Colors.red),
              child: const Text('删除'),
            ),
          );
        },
      ),
    );
  }

  // ── Tab 2: Friend requests ──────────────────────────────────────────────

  Widget _buildRequestsTab() {
    if (_requestsLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_pendingRequests.isEmpty) {
      return const Center(child: Text('暂无待处理的好友请求'));
    }
    return RefreshIndicator(
      onRefresh: _loadRequests,
      child: ListView.separated(
        itemCount: _pendingRequests.length,
        separatorBuilder: (_, __) => const Divider(height: 1),
        itemBuilder: (_, i) {
          final r = _pendingRequests[i];
          return ListTile(
            leading: CircleAvatar(
              backgroundColor: Colors.blue.withAlpha(40),
              child: Text(
                r.senderNickname.isNotEmpty ? r.senderNickname[0] : '?',
                style: const TextStyle(
                  color: Colors.blue,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            title: Text(r.senderNickname),
            subtitle: Text(r.senderPhone),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  icon: const Icon(Icons.check_circle, color: Colors.green),
                  tooltip: '接受',
                  onPressed: () => _acceptRequest(r.requestId),
                ),
                IconButton(
                  icon: const Icon(Icons.cancel, color: Colors.red),
                  tooltip: '拒绝',
                  onPressed: () => _rejectRequest(r.requestId),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  // ── Tab 3: Search & add friend ──────────────────────────────────────────

  Widget _buildAddFriendTab() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _searchPhoneCtrl,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: '输入对方手机号',
                    hintText: '13800138000',
                    prefixIcon: Icon(Icons.search),
                    border: OutlineInputBorder(),
                  ),
                  onSubmitted: (_) => _searchUser(),
                ),
              ),
              const SizedBox(width: 8),
              IconButton(
                icon: _searching
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.search),
                onPressed: _searching ? null : _searchUser,
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Search result
          if (_searchError != null)
            Card(
              color: Colors.red.withAlpha(20),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    const Icon(Icons.error_outline, color: Colors.red),
                    const SizedBox(width: 8),
                    Expanded(child: Text(_searchError!)),
                  ],
                ),
              ),
            ),

          if (_searchResult != null) ..._buildSearchResult(),

          const Spacer(),

          // Hint text
          Text(
            '通过手机号搜索用户，发送好友请求后等待对方同意',
            style: TextStyle(fontSize: 13, color: Colors.grey[500]),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  List<Widget> _buildSearchResult() {
    final r = _searchResult!;
    final nickname = r['nickname'] as String? ?? '';
    final phone = r['phone'] as String? ?? '';
    final isOnline = r['is_online'] as bool? ?? false;
    final alreadyFriends = r['already_friends'] as bool? ?? false;
    final hasPending = r['has_pending_request'] as bool? ?? false;

    return [
      Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              CircleAvatar(
                radius: 28,
                backgroundColor: isOnline
                    ? Colors.green.withAlpha(40)
                    : Colors.grey.withAlpha(40),
                child: Text(
                  nickname.isNotEmpty ? nickname[0] : '?',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: isOnline ? Colors.green : Colors.grey,
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Text(nickname,
                  style:
                      const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              Text(phone,
                  style: TextStyle(fontSize: 14, color: Colors.grey[600])),
              const SizedBox(height: 4),
              Text(isOnline ? '在线' : '离线',
                  style: TextStyle(
                      fontSize: 13,
                      color: isOnline ? Colors.green : Colors.grey)),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: alreadyFriends
                      ? null
                      : hasPending
                          ? null
                          : () => _sendFriendRequest(phone),
                  icon: Icon(
                    alreadyFriends
                        ? Icons.check
                        : hasPending
                            ? Icons.hourglass_empty
                            : Icons.person_add,
                  ),
                  label: Text(
                    alreadyFriends
                        ? '已是好友'
                        : hasPending
                            ? '已发送请求'
                            : '发送好友请求',
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: alreadyFriends || hasPending
                        ? Colors.grey.withAlpha(30)
                        : Colors.indigo.withAlpha(30),
                    foregroundColor:
                        alreadyFriends || hasPending ? Colors.grey : Colors.indigo,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    ];
  }
}