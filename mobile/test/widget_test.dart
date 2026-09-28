import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mbolo_mobile/api.dart';
import 'package:mbolo_mobile/main.dart';

void main() {
  testWidgets('Missing configuration does not open a login form', (
    tester,
  ) async {
    await tester.pumpWidget(const MboloApp());
    expect(
      find.textContaining('Configuration MBOLO manquante'),
      findsOneWidget,
    );
    expect(find.byType(TextFormField), findsNothing);
  });
  testWidgets('Empty credentials are rejected locally', (tester) async {
    final api = MboloApi('https://example.com');
    await tester.pumpWidget(MboloApp(api: api));
    await tester.tap(find.text('Se connecter'));
    await tester.pump();
    expect(find.text('Entre ton adresse e-mail.'), findsOneWidget);
    expect(find.text('Entre ton mot de passe.'), findsOneWidget);
  });
}
