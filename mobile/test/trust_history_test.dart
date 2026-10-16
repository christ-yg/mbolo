import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mbolo_mobile/auth_contract.dart';
import 'package:mbolo_mobile/demo_api.dart';
import 'package:mbolo_mobile/trust_center.dart';

class HistoryApi extends DemoApi {
  bool failMore = false;
  bool empty = false;
  bool failUnblock = false;
  final pages = <int>[];
  final reportPages = <int>[];
  BlockedUserItem item(String id) => BlockedUserItem(id: id, displayName: 'Profil $id',
    city: 'Libreville', createdAt: DateTime(2026, 10, 13));
  @override
  Future<SafetyHistoryPage<BlockedUserItem>> getBlockedUsersPage({int page = 1}) async {
    pages.add(page);
    if (failMore && page == 2) throw const FormatException('Network failure');
    return SafetyHistoryPage(items: empty ? [] : page == 1 ? [item('A')] : [item('A'), item('B')],
      totalCount: empty ? 0 : 2, hasNext: !empty && page == 1);
  }
  @override
  Future<SafetyHistoryPage<UserReportItem>> getMyReportsPage({int page = 1}) async {
    reportPages.add(page);
    return SafetyHistoryPage(items: [UserReportItem(id: 'report-$page', displayName: 'Signalement $page',
      reason: 'scam', description: '', status: 'pending', createdAt: DateTime(2026, 10, 13))],
      totalCount: 2, hasNext: page == 1);
  }
  @override
  Future<void> unblockUser(String id) async {
    if (failUnblock) throw const FormatException('Denied');
    empty = true;
  }
}

Future<void> open(WidgetTester tester, HistoryApi api) async {
  await tester.pumpWidget(MaterialApp(home: TrustCenterPage(api: api)));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('Blocked history loads next page and removes duplicates', (tester) async {
    final api = HistoryApi();
    await open(tester, api);
    await tester.tap(find.text('Charger la suite').hitTestable());
    await tester.pumpAndSettle();
    expect(api.pages, [1, 2]);
    expect(find.text('Profil A'), findsOneWidget);
    expect(find.text('Profil B'), findsOneWidget);
    expect(find.text('2 sur 2 blocages'), findsOneWidget);
    expect(find.text('Charger la suite'), findsNothing);
  });

  testWidgets('Failed page preserves rows and retries the same page', (tester) async {
    final api = HistoryApi()..failMore = true;
    await open(tester, api);
    await tester.tap(find.text('Charger la suite').hitTestable());
    await tester.pumpAndSettle();
    expect(find.text('Profil A'), findsOneWidget);
    expect(find.textContaining('réponse du serveur'), findsOneWidget);
    api.failMore = false;
    await tester.tap(find.text('Charger la suite').hitTestable());
    await tester.pumpAndSettle();
    expect(api.pages, [1, 2, 2]);
    expect(find.text('Profil B'), findsOneWidget);
  });

  testWidgets('Empty history can refresh from toolbar', (tester) async {
    final api = HistoryApi()..empty = true;
    await open(tester, api);
    expect(find.text('Aucun profil bloqué'), findsOneWidget);
    api.empty = false;
    await tester.tap(find.byTooltip('Actualiser le centre de confiance'));
    await tester.pumpAndSettle();
    expect(find.text('Profil A'), findsOneWidget);
  });

  testWidgets('Unblock failure is visible and preserves the blocked member', (tester) async {
    final api = HistoryApi()..failUnblock = true;
    await open(tester, api);
    await tester.tap(find.text('Débloquer'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, 'Débloquer'));
    await tester.pumpAndSettle();
    expect(find.text('Profil A'), findsOneWidget);
    expect(find.textContaining('réponse du serveur'), findsOneWidget);
  });

  testWidgets('Reports paginate independently from blocked history', (tester) async {
    final api = HistoryApi();
    await open(tester, api);
    await tester.tap(find.text('Signalements'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Charger la suite').hitTestable());
    await tester.pumpAndSettle();
    expect(api.reportPages, [1, 2]);
    expect(api.pages, [1]);
    expect(find.text('Signalement 2'), findsOneWidget);
  });
}
