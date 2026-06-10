import 'package:flutter/material.dart';
import 'pages/login_page.dart';

void main() {
  runApp(const RuThereApp());
}

class RuThereApp extends StatelessWidget {
  const RuThereApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'RuThere',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
        useMaterial3: true,
      ),
      home: const LoginPage(),
    );
  }
}