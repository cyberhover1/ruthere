import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ruthere/main.dart';

void main() {
  testWidgets('显示联系人列表', (WidgetTester tester) async {
    await tester.pumpWidget(const RuThereApp());

    // 验证 AppBar 标题
    expect(find.text('联系人'), findsOneWidget);

    // 验证列表中有联系人条目
    expect(find.byType(ListTile), findsWidgets);

    // 验证刷新按钮存在
    expect(find.byIcon(Icons.refresh), findsOneWidget);
  });

  testWidgets('点击刷新按钮重新生成数据', (WidgetTester tester) async {
    await tester.pumpWidget(const RuThereApp());

    // 获取初始的第一个联系人名字
    final firstTile = tester.widget<Text>(
      find.descendant(
        of: find.byType(ListTile).first,
        matching: find.byType(Text),
      ).first,
    );
    final firstName = firstTile.data!;

    // 点击刷新
    await tester.tap(find.byIcon(Icons.refresh));
    await tester.pump();

    // 验证页面仍然有联系人
    expect(find.byType(ListTile), findsWidgets);
  });
}