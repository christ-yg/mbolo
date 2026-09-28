import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mbolo_mobile/app.dart';
import 'package:mbolo_mobile/demo_api.dart';

void main() {
  testWidgets('Preview completes 2FA and logout using the shared screens', (
    tester,
  ) async {
    await tester.pumpWidget(MboloApp(api: DemoApi(), demo: true));
    await tester.enterText(find.byType(TextFormField).at(0), 'demo@mbolo.test');
    await tester.enterText(find.byType(TextFormField).at(1), 'MboloDemo!');
    await tester.tap(find.text('Se connecter'));
    await tester.pumpAndSettle();
    expect(find.text('Code de confirmation'), findsOneWidget);
    await tester.enterText(find.byType(TextFormField), '123456');
    await tester.tap(find.text('Confirmer'));
    await tester.pumpAndSettle();
    expect(find.text('Bienvenue sur MBOLO'), findsOneWidget);
    await tester.tap(find.text('Se déconnecter'));
    await tester.pumpAndSettle();
    expect(find.text('Se connecter'), findsOneWidget);
  });
}
