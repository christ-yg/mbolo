import 'package:flutter_test/flutter_test.dart';
import 'package:mbolo_mobile/demo_api.dart';

void main() {
  test('la démo liste, lit et envoie des messages', () async {
    final api = DemoApi();

    final conversations = await api.getConversations();
    expect(conversations, hasLength(1));
    expect(conversations.single.otherProfile.displayName, 'Grâce');
    expect(conversations.single.unreadCount, 1);

    final initial = await api.getMessages(conversations.single.id);
    expect(initial, hasLength(1));
    expect(initial.single.mine, isFalse);

    await api.markConversationRead(conversations.single.id);
    final readConversations = await api.getConversations();
    expect(readConversations.single.unreadCount, 0);

    final sent = await api.sendMessage(
      conversations.single.id,
      '  Ravi de faire ta connaissance !  ',
    );
    expect(sent.body, 'Ravi de faire ta connaissance !');
    expect(sent.mine, isTrue);

    final history = await api.getMessages(conversations.single.id);
    expect(history, hasLength(2));
  });

  test('la démo refuse un message vide', () async {
    final api = DemoApi();

    expect(
      () => api.sendMessage('demo-conversation-1', '   '),
      throwsA(isA<FormatException>()),
    );
  });
}
