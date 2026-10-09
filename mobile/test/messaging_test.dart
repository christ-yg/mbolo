import 'package:flutter_test/flutter_test.dart';
import 'package:mbolo_mobile/demo_api.dart';

void main() {
  test('la démo liste, lit et envoie des messages', () async {
    final api = DemoApi();

    final conversations = await api.getConversations();
    expect(conversations, hasLength(1));
    expect(conversations.single.otherProfile.displayName, 'Grâce');
    expect(conversations.single.unreadCount, 1);
    expect(await api.getMessageUnreadCount(), 1);

    final initial = await api.getMessages(conversations.single.id);
    expect(initial, hasLength(1));
    expect(initial.single.mine, isFalse);

    await api.markConversationRead(conversations.single.id);
    final readConversations = await api.getConversations();
    expect(readConversations.single.unreadCount, 0);
    expect(await api.getMessageUnreadCount(), 0);

    final sent = await api.sendMessage(
      conversations.single.id,
      '  Ravi de faire ta connaissance !  ',
    );
    expect(sent.body, 'Ravi de faire ta connaissance !');
    expect(sent.mine, isTrue);

    final history = await api.getMessages(conversations.single.id);
    expect(history, hasLength(2));

    final reacted = await api.reactToMessage(
      conversations.single.id,
      sent.id,
      '❤️',
    );
    expect(reacted.myReaction, '❤️');
    expect(reacted.reactions.single.count, 1);

    final cleared = await api.reactToMessage(
      conversations.single.id,
      sent.id,
      '',
    );
    expect(cleared.myReaction, isNull);
    expect(cleared.reactions, isEmpty);

    final reply = await api.sendMessage(
      conversations.single.id,
      'Réponse ciblée',
      replyToId: initial.single.id,
    );
    expect(reply.replyPreview, isNotNull);
    expect(reply.replyPreview!.body, initial.single.body);

    final deleted = await api.deleteMessage(conversations.single.id, sent.id);
    expect(deleted.deleted, isTrue);
    expect(deleted.body, isEmpty);

    await expectLater(
      api.deleteMessage(conversations.single.id, initial.single.id),
      throwsA(isA<FormatException>()),
    );

    expect(await api.getTypingStatus(conversations.single.id), isFalse);
    await api.setTypingStatus(conversations.single.id, true);
  });

  test('la démo refuse un message vide', () async {
    final api = DemoApi();

    await expectLater(
      api.sendMessage('demo-conversation-1', '   '),
      throwsA(isA<FormatException>()),
    );
  });

  test('la démo liste les matchs et permet de répondre aux likes', () async {
    final api = DemoApi();

    final matches = await api.getMatches();
    expect(matches, hasLength(1));
    expect(matches.single.otherProfile.displayName, 'Grâce');

    final likes = await api.getReceivedLikes();
    expect(likes, hasLength(2));
    expect(likes.first.identityRevealed, isFalse);
    expect(likes.first.superLike, isTrue);

    final result = await api.respondToReceivedLike(
      interactionId: likes.first.interactionId,
      decision: 'like',
    );
    expect(result.matched, isTrue);
    expect(result.revealedProfile, isNotNull);
    expect(await api.getReceivedLikes(), hasLength(1));
  });

  test('la démo applique le quota Super Like et restaure un pass', () async {
    final api = DemoApi();
    final initial = await api.getSuperLikeState();
    expect(initial.remainingToday, 3);

    await api.decideProfile(
      profileId: '11111111-1111-1111-1111-111111111111',
      decision: 'like',
      superLike: true,
    );
    expect((await api.getSuperLikeState()).remainingToday, 2);

    await api.decideProfile(
      profileId: '33333333-3333-3333-3333-333333333333',
      decision: 'pass',
    );
    expect((await api.getRewindState()).available, isTrue);
    final restored = await api.rewindLastPass();
    expect(restored.displayName, 'Mélissa');
    expect((await api.getRewindState()).available, isFalse);
  });

  test('la démo protège la 2FA et les appareils par mot de passe', () async {
    final api = DemoApi();
    await api.confirm('demo-challenge', '123456');
    expect(await api.getConnectedSessions(), hasLength(2));

    await api.revokeConnectedSession(
      sessionId: 'demo-other-session',
      currentPassword: 'MboloDemo!',
    );
    expect(await api.getConnectedSessions(), hasLength(1));

    expect(
      await api.setEmailTwoFactor(
        enabled: false,
        currentPassword: 'MboloDemo!',
      ),
      isFalse,
    );
    expect((await api.me()).emailTwoFactorEnabled, isFalse);
  });

  test('la démo exporte les données puis supprime le compte', () async {
    final api = DemoApi();
    await api.confirm('demo-challenge', '123456');

    final export = await api.exportPersonalData();
    expect(export['export'], isA<Map<String, dynamic>>());

    await api.deleteAccount('MboloDemo!');
    await expectLater(api.me(), throwsA(isA<FormatException>()));
    expect(await api.getConnectedSessions(), isEmpty);
  });
}
