import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mbolo_mobile/api.dart';
import 'package:mbolo_mobile/session_store.dart';

import 'api_test.dart' show FakeServer;

class ForbiddenSessionStore implements SessionStore {
  @override
  Future<String?> read() async => throw StateError('Browser read sessionid');
  @override
  Future<void> write(String value) async => throw StateError('Browser wrote sessionid');
  @override
  Future<void> clear() async => throw StateError('Browser accessed native storage');
}

void main() {
  test('Browser restores via server without reading or copying session cookies', () async {
    final server = FakeServer();
    final api = MboloApi(
      'https://example.com',
      browserSession: true,
      client: Dio()..httpClientAdapter = server,
      sessionStore: ForbiddenSessionStore(),
    );
    addTearDown(api.close);
    expect((await api.restoreSession())?.email, 'test@example.com');
    await api.login('test@example.com', 'password');
    await api.me();
    await api.logout();
    for (final request in server.requests) {
      final names = request.headers.keys.map((name) => name.toLowerCase());
      expect(names, isNot(contains('cookie')));
      expect(names, isNot(contains('origin')));
      if (request.method == 'POST') {
        expect(request.headers['X-CSRFToken'], 'csrf-test');
      }
    }
  });

  test('Browser logout surfaces revocation failures', () async {
    final server = FakeServer()..rejectLogout = true;
    final api = MboloApi(
      'https://example.com',
      browserSession: true,
      client: Dio()..httpClientAdapter = server,
      sessionStore: ForbiddenSessionStore(),
    );
    addTearDown(api.close);
    await expectLater(api.logout(), throwsA(isA<DioException>()));
  });
}
