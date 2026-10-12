import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mbolo_mobile/advanced_discovery.dart';
import 'package:mbolo_mobile/auth_contract.dart';
import 'package:mbolo_mobile/demo_api.dart';

class RetryApi extends DemoApi {
  RetryApi() : super(advancedFiltersAvailable: true);
  bool fail = true;
  @override
  Future<AdvancedDiscoveryFilters> getAdvancedDiscoveryFilters() async {
    if (fail) { fail = false; throw const FormatException('Transient error'); }
    return super.getAdvancedDiscoveryFilters();
  }
}

Future<void> openPage(WidgetTester tester, DemoApi api) async {
  await tester.pumpWidget(MaterialApp(home: Builder(builder: (context) => Scaffold(
    body: TextButton(onPressed: () => Navigator.of(context).push<void>(
      MaterialPageRoute<void>(builder: (_) => AdvancedDiscoveryPage(api: api))),
      child: const Text('Ouvrir')),
  ))));
  await tester.tap(find.text('Ouvrir'));
  await tester.pumpAndSettle();
}

Future<void> reveal(WidgetTester tester, String label) async {
  await tester.scrollUntilVisible(find.text(label), 200,
    scrollable: find.byType(Scrollable).last);
  await tester.pumpAndSettle();
}

void main() {
  test('Malformed distance and lists are rejected', () {
    final data = <String, dynamic>{
      'advanced_filters_available': true, 'preferred_cities': ['libreville'],
      'preferred_dating_intents': [], 'maximum_distance_km': 50,
      'only_verified_profiles': false, 'only_profiles_with_photos': false,
    };
    expect(() => AdvancedDiscoveryFilters.fromJson({...data, 'maximum_distance_km': 501}), throwsFormatException);
    expect(() => AdvancedDiscoveryFilters.fromJson({...data, 'preferred_cities': [123]}), throwsFormatException);
    expect(AdvancedDiscoveryFilters.fromJson(data).cities, ['libreville']);
  });

  test('Demo denies advanced changes without entitlement', () async {
    final api = DemoApi();
    await expectLater(api.updateAdvancedDiscoveryFilters(
      const AdvancedDiscoveryFilters(available: true, photosOnly: true)), throwsFormatException);
    expect((await api.getAdvancedDiscoveryFilters()).photosOnly, isFalse);
  });

  testWidgets('Free account sees locked controls', (tester) async {
    await openPage(tester, DemoApi());
    expect(find.textContaining('Plus ou Prestige'), findsOneWidget);
    expect(tester.widget<FilterChip>(find.widgetWithText(FilterChip, 'Libreville')).onSelected, isNull);
    await reveal(tester, 'Enregistrer les filtres');
    expect(tester.widget<FilledButton>(find.widgetWithText(FilledButton, 'Enregistrer les filtres')).onPressed, isNull);
  });

  testWidgets('Cities intentions distance and switches persist together', (tester) async {
    final api = DemoApi(advancedFiltersAvailable: true);
    await openPage(tester, api);
    await tester.tap(find.text('Libreville'));
    await reveal(tester, 'Amitié');
    await tester.tap(find.text('Amitié'));
    await reveal(tester, 'Profils vérifiés uniquement');
    tester.widget<Slider>(find.byType(Slider)).onChanged!(150);
    await tester.tap(find.text('Profils vérifiés uniquement'));
    await reveal(tester, 'Profils avec photo uniquement');
    await tester.tap(find.text('Profils avec photo uniquement'));
    await reveal(tester, 'Enregistrer les filtres');
    await tester.tap(find.text('Enregistrer les filtres'));
    await tester.pumpAndSettle();
    final filters = await api.getAdvancedDiscoveryFilters();
    expect(filters.cities, ['libreville']);
    expect(filters.intents, ['friendship']);
    expect(filters.distanceKm, 150);
    expect(filters.verifiedOnly, isTrue);
    expect(filters.photosOnly, isTrue);
  });

  testWidgets('Reset remains local until saved and cancel preserves server values', (tester) async {
    final api = DemoApi(advancedFiltersAvailable: true);
    await api.updateAdvancedDiscoveryFilters(const AdvancedDiscoveryFilters(
      available: true, cities: ['oyem'], distanceKm: 200, photosOnly: true));
    await openPage(tester, api);
    await reveal(tester, 'Réinitialiser les filtres');
    await tester.tap(find.text('Réinitialiser les filtres'));
    await tester.pumpAndSettle();
    expect((await api.getAdvancedDiscoveryFilters()).cities, ['oyem']);
    await tester.pageBack();
    await tester.pumpAndSettle();
    expect((await api.getAdvancedDiscoveryFilters()).distanceKm, 200);
  });

  testWidgets('Failed initial load can be retried', (tester) async {
    await openPage(tester, RetryApi());
    await tester.tap(find.text('Réessayer'));
    await tester.pumpAndSettle();
    expect(find.text('Réessayer'), findsNothing);
    expect(tester.widget<FilterChip>(find.widgetWithText(FilterChip, 'Libreville')).onSelected, isNotNull);
  });
}
