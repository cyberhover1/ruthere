/// Server address configuration for the RuThere backend.
///
/// Default: 110.42.251.26:8000
/// Set via the settings UI or programmatically.
class ServerConfig {
  static final ServerConfig _instance = ServerConfig._();
  static ServerConfig get instance => _instance;
  ServerConfig._();

  String host = '110.42.251.26';
  int port = 8000;

  String get baseUrl => 'http://$host:$port';

  void set(String h, int p) {
    host = h;
    port = p;
  }
}