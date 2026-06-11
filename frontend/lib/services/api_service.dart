import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'config.dart';
import '../pages/login_page.dart';

/// HTTP client wrapping all backend API calls with automatic token refresh.
class ApiService {
  static final ApiService _instance = ApiService._();
  static ApiService get instance => _instance;
  ApiService._();

  String get baseUrl => ServerConfig.instance.baseUrl;

  String? _accessToken;
  String? _refreshToken;
  int? _userId;
  String? _nickname;
  String? _phone;

  bool get isAuthenticated => _accessToken != null;
  String? get token => _accessToken;
  String? get refreshToken => _refreshToken;
  int? get userId => _userId;
  String? get nickname => _nickname;
  String? get phone => _phone;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
      };

  // ── Session persistence (shared prefs / in-memory for now) ──────────────

  void clearSession() {
    _accessToken = null;
    _refreshToken = null;
    _userId = null;
    _nickname = null;
    _phone = null;
  }

  void _saveTokens(Map<String, dynamic> body) {
    _accessToken = body['access_token'] as String?;
    _refreshToken = body['refresh_token'] as String?;
    _userId = body['user_id'] as int?;
    _nickname = body['nickname'] as String?;
    _phone = body['phone'] as String?;
  }

  // ── Token refresh ───────────────────────────────────────────────────────

  /// Try to refresh the access token using the stored refresh token.
  /// Returns true on success.
  Future<bool> _doRefresh() async {
    if (_refreshToken == null) return false;
    try {
      final resp = await http.post(
        Uri.parse('$baseUrl/api/refresh'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh_token': _refreshToken}),
      );
      if (resp.statusCode != 200) {
        clearSession();
        return false;
      }
      final body = jsonDecode(resp.body) as Map<String, dynamic>;
      _accessToken = body['access_token'] as String?;
      _refreshToken = body['refresh_token'] as String?;
      return true;
    } catch (_) {
      return false;
    }
  }

  /// Execute an HTTP request with automatic 401 → refresh → retry.
  Future<http.Response> _request(
    Future<http.Response> Function() request,
  ) async {
    final resp = await request();
    if (resp.statusCode == 401 && _refreshToken != null) {
      final refreshed = await _doRefresh();
      if (refreshed) {
        // Retry the original request with the new token
        return await request();
      }
    }
    return resp;
  }

  // ── Auth ─────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> login(String phone, String password) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/api/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'phone': phone, 'password': password}),
    );
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    if (resp.statusCode != 200) {
      throw Exception(body['detail'] ?? '登录失败');
    }
    _saveTokens(body);
    return body;
  }

  Future<Map<String, dynamic>> register(
      String phone, String nickname, String password) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/api/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'phone': phone,
        'nickname': nickname,
        'password': password,
      }),
    );
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    if (resp.statusCode != 200) {
      throw Exception(body['detail'] ?? '注册失败');
    }
    _saveTokens(body);
    return body;
  }

  // ── Auth Actions ──────────────────────────────────────────────────────────

  /// Logout: mark offline on server then clear local session.
  Future<void> logout() async {
    try {
      await _request(() => http.post(
            Uri.parse('$baseUrl/api/logout'),
            headers: _headers,
          ));
    } catch (_) {
      // Best-effort — always clear local state
    }
    clearSession();
  }

  // ── User data ────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getMe() async {
    final resp = await _request(() => http.get(
          Uri.parse('$baseUrl/api/me'),
          headers: _headers,
        ));
    if (resp.statusCode != 200) {
      throw Exception('获取用户信息失败');
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> reportActivity(int increment) async {
    final resp = await _request(() => http.post(
          Uri.parse('$baseUrl/api/activity'),
          headers: _headers,
          body: jsonEncode({'increment': increment}),
        ));
    if (resp.statusCode != 200) {
      throw Exception('上报活跃度失败');
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> heartbeat() async {
    final resp = await _request(() => http.post(
          Uri.parse('$baseUrl/api/heartbeat'),
          headers: _headers,
        ));
    if (resp.statusCode != 200) {
      throw Exception('心跳失败');
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  // ── Friends Activity ──────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getFriendsActivity() async {
    final resp = await _request(() => http.get(
          Uri.parse('$baseUrl/api/friends/activity'),
          headers: _headers,
        ));
    if (resp.statusCode != 200) {
      throw Exception('获取好友动态失败');
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  // ── Friend Request System ────────────────────────────────────────────────

  Future<Map<String, dynamic>> searchUserByPhone(String phone) async {
    final resp = await _request(() => http.post(
          Uri.parse('$baseUrl/api/friends/search-by-phone'),
          headers: _headers,
          body: jsonEncode({'phone': phone}),
        ));
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    if (resp.statusCode != 200) {
      throw Exception(body['detail'] ?? '搜索失败');
    }
    return body;
  }

  Future<Map<String, dynamic>> sendFriendRequest(String receiverPhone) async {
    final resp = await _request(() => http.post(
          Uri.parse('$baseUrl/api/friends/request'),
          headers: _headers,
          body: jsonEncode({'receiver_phone': receiverPhone}),
        ));
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    if (resp.statusCode != 200) {
      throw Exception(body['detail'] ?? '发送好友请求失败');
    }
    return body;
  }

  Future<Map<String, dynamic>> getFriendRequests() async {
    final resp = await _request(() => http.get(
          Uri.parse('$baseUrl/api/friends/requests'),
          headers: _headers,
        ));
    if (resp.statusCode != 200) {
      throw Exception('获取好友请求失败');
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> acceptFriendRequest(int requestId) async {
    final resp = await _request(() => http.post(
          Uri.parse('$baseUrl/api/friends/requests/$requestId/accept'),
          headers: _headers,
        ));
    if (resp.statusCode != 200) {
      final body = jsonDecode(resp.body) as Map<String, dynamic>;
      throw Exception(body['detail'] ?? '接受好友请求失败');
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> rejectFriendRequest(int requestId) async {
    final resp = await _request(() => http.post(
          Uri.parse('$baseUrl/api/friends/requests/$requestId/reject'),
          headers: _headers,
        ));
    if (resp.statusCode != 200) {
      final body = jsonDecode(resp.body) as Map<String, dynamic>;
      throw Exception(body['detail'] ?? '拒绝好友请求失败');
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  // ── Friend Management ─────────────────────────────────────────────────────

  Future<Map<String, dynamic>> addFriend(String phone) async {
    final resp = await _request(() => http.post(
          Uri.parse('$baseUrl/api/friends/add'),
          headers: _headers,
          body: jsonEncode({'phone': phone}),
        ));
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    if (resp.statusCode != 200) {
      throw Exception(body['detail'] ?? '添加好友失败');
    }
    return body;
  }

  Future<Map<String, dynamic>> removeFriend(String phone) async {
    final resp = await _request(() => http.post(
          Uri.parse('$baseUrl/api/friends/remove'),
          headers: _headers,
          body: jsonEncode({'phone': phone}),
        ));
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    if (resp.statusCode != 200) {
      throw Exception(body['detail'] ?? '删除好友失败');
    }
    return body;
  }

  // ── User discovery ───────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getUsers() async {
    final resp = await _request(() => http.get(
          Uri.parse('$baseUrl/api/users'),
          headers: _headers,
        ));
    if (resp.statusCode != 200) {
      throw Exception('获取用户列表失败');
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }
}