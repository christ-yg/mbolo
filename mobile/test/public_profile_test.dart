import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mbolo_mobile/auth_contract.dart';
import 'package:mbolo_mobile/demo_api.dart';
import 'package:mbolo_mobile/public_profile.dart';

const profileId = '11111111-1111-1111-1111-111111111111';

class PublicApi extends DemoApi {
  bool unavailable = false;
  bool photo = false;
  @override
  Future<DiscoveryProfile> getPublicProfile(String id) async {
    if (unavailable) {
      final options = RequestOptions(path: 'profiles/public/$id/');
      throw DioException(requestOptions: options,
        response: Response<dynamic>(requestOptions: options, statusCode: 404));
    }
    return DiscoveryProfile.fromJson({
      'id': id, 'display_name': 'Profil test', 'age': 29, 'city': 'Libreville',
      'biography': '', 'dating_intent': 'Amitié', 'is_verified': false,
      'email': 'private@example.test', 'birth_date': '1997-01-01',
      'photos': photo ? [{'id': 'photo-1', 'image_url': '', 'position': 0,
        'is_primary': true, 'moderation_status': 'approved'}] : [],
    });
  }
}

Future<void> openPage(WidgetTester tester, DemoApi api) async {
  await tester.pumpWidget(MaterialApp(home: Builder(builder: (context) => Scaffold(
    body: TextButton(onPressed: () => Navigator.of(context).push<bool>(
      MaterialPageRoute<bool>(builder: (_) => PublicProfilePage(api: api, profileId: profileId))),
      child: const Text('Ouvrir')),
  ))));
  await tester.tap(find.text('Ouvrir'));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('Public display has empty states and excludes private fields', (tester) async {
    await openPage(tester, PublicApi());
    expect(find.text('Profil test, 29'), findsOneWidget);
    expect(find.text('Aucune photo publique'), findsOneWidget);
    expect(find.text('Identité non vérifiée'), findsOneWidget);
    expect(find.textContaining('private@example.test'), findsNothing);
    expect(find.textContaining('1997-01-01'), findsNothing);
    await tester.scrollUntilVisible(find.text('Ce membre n’a pas encore ajouté de présentation.'),
      150, scrollable: find.byType(Scrollable).last);
    expect(find.text('Ce membre n’a pas encore ajouté de présentation.'), findsOneWidget);
  });

  testWidgets('Refresh removes stale data when access is lost', (tester) async {
    final api = PublicApi();
    await openPage(tester, api);
    api.unavailable = true;
    await tester.tap(find.byTooltip('Actualiser le profil'));
    await tester.pumpAndSettle();
    expect(find.text('Ce profil n’est pas disponible.'), findsOneWidget);
    expect(find.text('Profil test, 29'), findsNothing);
    api.unavailable = false;
    await tester.tap(find.text('Réessayer'));
    await tester.pumpAndSettle();
    expect(find.text('Profil test, 29'), findsOneWidget);
  });

  testWidgets('Photo opens full screen zoom and closes', (tester) async {
    await openPage(tester, PublicApi()..photo = true);
    await tester.tap(find.text('Photo 1/1'));
    await tester.pumpAndSettle();
    expect(find.byType(InteractiveViewer), findsOneWidget);
    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(find.text('Profil public'), findsOneWidget);
  });

  testWidgets('Safety offers report and block with confirmation', (tester) async {
    final api = DemoApi();
    await openPage(tester, api);
    await tester.tap(find.byTooltip('Signaler ou bloquer'));
    await tester.pumpAndSettle();
    expect(find.text('Signaler ce profil'), findsOneWidget);
    await tester.tap(find.text('Bloquer ce profil'));
    await tester.pumpAndSettle();
    expect(find.text('Bloquer Arielle ?'), findsOneWidget);
    await tester.tap(find.text('Annuler'));
    await tester.pumpAndSettle();
    expect((await api.getPublicProfile(profileId)).displayName, 'Arielle');
  });

  test('Blocked demo profile cannot be reopened', () async {
    final api = DemoApi();
    await api.blockProfile(profileId);
    await expectLater(api.getPublicProfile(profileId), throwsFormatException);
  });
}
