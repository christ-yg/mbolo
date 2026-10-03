import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mbolo_mobile/api.dart';
import 'package:mbolo_mobile/demo_api.dart';
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

  testWidgets('Demo authentication opens discovery navigation', (tester) async {
    await tester.pumpWidget(MboloApp(api: DemoApi(), demo: true));
    await tester.enterText(
      find.byType(TextFormField).at(0),
      'demo@mbolo.test',
    );
    await tester.enterText(
      find.byType(TextFormField).at(1),
      'MboloDemo!',
    );
    await tester.tap(find.text('Se connecter'));
    await tester.pump();
    await tester.enterText(
      find.byType(TextFormField),
      '123456',
    );
    await tester.tap(find.text('Confirmer'));
    await tester.pumpAndSettle();

    expect(find.text('Découvrir'), findsWidgets);
    expect(find.textContaining('Arielle'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Ça me plaît'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Ça me plaît'), findsOneWidget);
    expect(find.text('Profil'), findsOneWidget);
  });

  testWidgets('A like is listed in activity and logout returns to login', (
    tester,
  ) async {
    await tester.pumpWidget(MboloApp(api: DemoApi(), demo: true));
    await tester.enterText(find.byType(TextFormField).at(0), 'demo@mbolo.test');
    await tester.enterText(find.byType(TextFormField).at(1), 'MboloDemo!');
    await tester.tap(find.text('Se connecter'));
    await tester.pump();
    await tester.enterText(find.byType(TextFormField), '123456');
    await tester.tap(find.text('Confirmer'));
    await tester.pumpAndSettle();

    await tester.scrollUntilVisible(
      find.text('Ça me plaît'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text('Ça me plaît'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Activité'));
    await tester.pumpAndSettle();
    expect(find.text('1 intérêt envoyé'), findsOneWidget);
    expect(find.text('Arielle'), findsOneWidget);

    await tester.tap(find.text('Profil'));
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(
      find.text('Se déconnecter'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text('Se déconnecter'));
    await tester.pumpAndSettle();
    expect(find.text('Se connecter'), findsOneWidget);
  });
}
