import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mbolo_mobile/auth_contract.dart';
import 'package:mbolo_mobile/demo_api.dart';
import 'package:mbolo_mobile/security_activity.dart';

class ActivityApi extends DemoApi {
  bool fail = false;
  bool empty = false;
  int updates = 0;
  @override
  Future<List<LoginActivity>> getLoginActivity() async {
    if (fail) throw const FormatException('Network failure');
    return empty ? <LoginActivity>[] : await super.getLoginActivity();
  }
  @override
  Future<List<AccountSecurityEvent>> getSecurityEvents() async => empty ? [] : [
    ...await super.getSecurityEvents(),
    AccountSecurityEvent(id: 'accepted', event: 'auth.login', outcome: 'accepted',
      reason: 'generic_response', createdAt: DateTime(2026, 10, 13)),
    AccountSecurityEvent(id: 'unknown', event: 'auth.login', outcome: 'unknown',
      reason: 'unknown', createdAt: DateTime(2026, 10, 13)),
  ];
  @override
  Future<LoginAlertPreference> updateLoginAlertPreference({required bool enabled, required String currentPassword}) {
    updates += 1;
    return super.updateLoginAlertPreference(enabled: enabled, currentPassword: currentPassword);
  }
}

Future<void> open(WidgetTester tester, ActivityApi api) async {
  await tester.pumpWidget(MaterialApp(home: SecurityActivityPage(api: api)));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('Search filters devices and clear restores history', (tester) async {
    await open(tester, ActivityApi());
    await tester.enterText(find.byType(TextField), 'Chrome');
    await tester.pumpAndSettle();
    expect(find.text('Chrome · Windows'), findsOneWidget);
    expect(find.text('MBOLO · Android'), findsNothing);
    await tester.tap(find.byTooltip('Effacer la recherche'));
    await tester.pumpAndSettle();
    expect(find.text('MBOLO · Android'), findsOneWidget);
  });

  testWidgets('Journal filters outcomes without classifying unknown as failure', (tester) async {
    await open(tester, ActivityApi());
    await tester.tap(find.text('Journal'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Réussites'));
    await tester.pumpAndSettle();
    expect(find.text('Réussi'), findsOneWidget);
    expect(find.text('Refusé'), findsNothing);
    await tester.ensureVisible(find.text('Autres'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Autres'));
    await tester.pumpAndSettle();
    expect(find.text('Non précisé'), findsOneWidget);
    expect(find.text('Refusé'), findsNothing);
  });

  testWidgets('Initial error disables mutations and can retry', (tester) async {
    final api = ActivityApi()..fail = true;
    await open(tester, api);
    expect(tester.widget<SwitchListTile>(find.byType(SwitchListTile)).onChanged, isNull);
    api.fail = false;
    await tester.tap(find.text('Réessayer'));
    await tester.pumpAndSettle();
    expect(find.text('MBOLO · Android'), findsOneWidget);
    expect(tester.widget<SwitchListTile>(find.byType(SwitchListTile)).onChanged, isNotNull);
  });

  testWidgets('Empty histories are explicit and refreshable', (tester) async {
    final api = ActivityApi()..empty = true;
    await open(tester, api);
    expect(find.text('Aucune connexion enregistrée.'), findsOneWidget);
    await tester.tap(find.text('Journal'));
    await tester.pumpAndSettle();
    expect(find.text('Aucun événement de sécurité.'), findsOneWidget);
    api.empty = false;
    await tester.tap(find.byTooltip('Actualiser l’activité'));
    await tester.pumpAndSettle();
    expect(find.text('Aucun événement de sécurité.'), findsNothing);
  });

  testWidgets('Cancelling confirmation never changes the email preference', (tester) async {
    final api = ActivityApi();
    await open(tester, api);
    await tester.tap(find.byType(Switch));
    await tester.pumpAndSettle();
    expect(tester.widget<FilledButton>(find.widgetWithText(FilledButton, 'Confirmer')).onPressed, isNull);
    await tester.tap(find.text('Annuler'));
    await tester.pumpAndSettle();
    expect(api.updates, 0);
    expect(tester.widget<SwitchListTile>(find.byType(SwitchListTile)).value, isTrue);
  });

  testWidgets('Password confirmation updates preference without controller lifecycle errors', (tester) async {
    final api = ActivityApi();
    await open(tester, api);
    await tester.tap(find.byType(Switch));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).last, 'MboloDemo!');
    await tester.pump();
    await tester.tap(find.text('Confirmer'));
    await tester.pumpAndSettle();
    expect(api.updates, 1);
    expect(tester.widget<SwitchListTile>(find.byType(SwitchListTile)).value, isFalse);
    expect((await api.getLoginAlertPreference()).internalEnabled, isTrue);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Wrong password preserves the previous preference', (tester) async {
    final api = ActivityApi();
    await open(tester, api);
    await tester.tap(find.byType(Switch));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).last, 'wrong');
    await tester.pump();
    await tester.tap(find.text('Confirmer'));
    await tester.pumpAndSettle();
    expect(tester.widget<SwitchListTile>(find.byType(SwitchListTile)).value, isTrue);
    expect(find.textContaining('réponse du serveur'), findsOneWidget);
  });
}
