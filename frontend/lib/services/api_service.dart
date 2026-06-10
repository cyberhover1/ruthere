import 'dart:convert';
import 'package:http/http.dart' as http;
import 'config.dart';

/// HTTP client wrapping all backend API calls.
///
/// Uses a singleton pattern: call [ApiService.instance] to access.
///
/// Base URL is derived from [ServerConfig] (default 127.0.0.1:8000).
/// Update it via the settings UI or [ServerConfig.instance.set()].
class ApiService {
  static final ApiService _instance = ApiService._();
  static ApiService get instance => _instance;
  ApiService._();

  /// Base URL from ServerConfig.
  String get baseUrl => ServerConfig.instance.baseUrl;

  String? _token;
  int? _userId;
  String? _username;

  bool get isAuthenticated => _token != null;
  String? get token => _token;
  int? get userId => _userId;
  String? get username => _username;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  /// Clear session state (e.g. on logout or when server URL changes).
  void clearSession() {
    _token = null;
    _userId = null;
    _username = null;
  }

  // ── Auth ─────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> login(String username, String password) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/api/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'password': password}),
    );
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    if (resp.statusCode != 200) {
      throw Exception(body['detail'] ?? 'Login failed');
    }
    _token = body['token'] as String;
    _userId = body['user_id'] as int;
    _username = body['username'] as String;
    return body;
  }

  Future<Map<String, dynamic>> register(
      String username, String password) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/api/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'password': password}),
    );
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    if (resp.statusCode != 200) {
      throw Exception(body['detail'] ?? 'Registration failed');
    }
    _token = body['token'] as String;
    _userId = body['user_id'] as int;
    _username = body['username'] as String;
    return body;
  }

  // ── User data ────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getMe() async {
    final resp = await http.get(
      Uri.parse('$baseUrl/api/me'),
      headers: _headers,
    );
    if (resp.statusCode != 200) {
      throw Exception('Failed to fetch user info');
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> reportActivity(int score) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/api/activity'),
      headers: _headers,
      body: jsonEncode({'score': score}),
    );
    if (resp.statusCode != 200) {
      throw Exception('Failed to report activity');
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> heartbeat() async {
    final resp = await http.post(
      Uri.parse('$baseUrl/api/heartbeat'),
      headers: _headers,
    );
    if (resp.statusCode != 200) {
      throw Exception('Heartbeat failed');
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  // ── Friends ──────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getFriendsActivity() async {
    final resp = await http.get(
      Uri.parse('$baseUrl/api/friends/activity'),
      headers: _headers,
    );
    if (resp.statusCode != 200) {
      throw Exception('Failed to fetch friends activity');
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> addFriend(String username) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/api/friends/add'),
      headers: _headers,
      body: jsonEncode({'username': username}),
    );
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    if (resp.statusCode != 200) {
      throw Exception(body['detail'] ?? 'Failed to add friend');
    }
    return body;
  }

  Future<Map<String, dynamic>> removeFriend(String username) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/api/friends/remove'),
      headers: _headers,
      body: jsonEncode({'username': username}),
    );
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    if (resp.statusCode != 200) {
      throw Exception(body['detail'] ?? 'Failed to remove friend');
    }
    return body;
  }

  // ── User discovery ───────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getUsers() async {
    final resp = await http.get(
      Uri.parse('$baseUrl/api/users'),
      headers: _headers,
    );
    if (resp.statusCode != 200) {
      throw Exception('Failed to fetch users');
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }
}