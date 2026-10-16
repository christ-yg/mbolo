import 'package:flutter_test/flutter_test.dart';
import 'package:mbolo_mobile/demo_api.dart';

void main() {
  test('bloquer un profil ferme le match de démonstration', () async {
    final api = DemoApi();
    final conversations = await api.getConversations();
    expect(conversations, hasLength(1));

    final result = await api.blockProfile(
      conversations.single.otherProfile.id,
    );

    expect(result.created, isTrue);
    expect(result.deactivatedMatches, 1);
    expect(await api.getConversations(), isEmpty);
  });

  test('signaler un profil valide le motif et la description', () async {
    final api = DemoApi();
    final profile = (await api.getDiscovery()).first;

    final result = await api.reportProfile(
      profileId: profile.id,
      reason: 'harassment',
      description: 'Messages insistants et irrespectueux.',
    );

    expect(result.created, isTrue);
    expect(result.message, contains('modération'));

    await expectLater(
      api.reportProfile(
        profileId: profile.id,
        reason: 'other',
        description: '   ',
      ),
      throwsA(isA<FormatException>()),
    );
  });

  test('supprimer le match ferme la conversation', () async {
    final api = DemoApi();

    await api.unmatch('demo-match-1');

    expect(await api.getConversations(), isEmpty);
  });
}
