import 'dart:convert';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mbolo_mobile/api.dart';

class FakeServer implements HttpClientAdapter {
  final requests = <RequestOptions>[];
  bool rejectLogout = false;
  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    final path = options.uri.path;
    Object data = {
      'data': {
        'id': 'account-1',
        'email': 'test@example.com',
        'isEmailVerified': true,
      },
    };
    final headers = <String, List<String>>{
      Headers.contentTypeHeader: ['application/json'],
    };
    var status = 200;
    if (path.endsWith('/csrf/')) {
      data = {'csrfToken': 'csrf-test'};
      headers['set-cookie'] = ['csrftoken=csrf-test; Path=/; Secure'];
    } else if (path.endsWith('/login/')) {
      headers['set-cookie'] = [
        'sessionid=session-test; Path=/; Secure; HttpOnly',
      ];
    } else if (path.endsWith('/profiles/preferences/me/')) {
      data = {
        'data': {
          'minimum_age': 21,
          'maximum_age': 39,
          'preferred_genders': ['female'],
          'advanced_filters_available': false,
        },
      };
    } else if (path.endsWith('/profiles/me/')) {
      data = {
        'data': {
          'display_name': 'Christ YG',
          'city': 'libreville',
          'biography': 'Une présentation de test suffisamment complète.',
          'is_complete': false,
        },
      };
    } else if (path.endsWith('/logout/')) {
      status = rejectLogout ? 503 : 200;
      data = {'message': 'Déconnexion réussie.'};
    }
    return ResponseBody.fromString(jsonEncode(data), status, headers: headers);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  test('Reject insecure, credential-bearing and path-based origins', () {
    for (final origin in [
      '',
      'http://example.com',
      'https://user:pass@example.com',
      'https://example.com/api',
      'https://example.com?secret=x',
      'https://example.com#x',
    ]) {
      expect(() => validateOrigin(origin), throwsFormatException);
    }
    expect(validateOrigin('https://example.com').host, 'example.com');
  });

  test('Account parsing fails closed on malformed data', () {
    expect(() => objectData([]), throwsFormatException);
    expect(() => objectData({'data': null}), throwsFormatException);
    expect(
      () => Account.fromJson({'email': 'test@example.com'}),
      throwsFormatException,
    );
    expect(
      () => LoginResult.fromJson({'requiresTwoFactor': true}),
      throwsFormatException,
    );
    final result = LoginResult.fromJson({
      'requiresTwoFactor': true,
      'challengeToken': 'test-challenge',
      'maskedEmail': 't***@example.com',
    });
    expect(result.account, isNull);
    expect(result.challenge, 'test-challenge');
  });

  test(
    'Login sends CSRF, carries cookie to me and clears it after logout',
    () async {
      final server = FakeServer();
      final dio = Dio()..httpClientAdapter = server;
      final api = MboloApi('https://example.com', client: dio);
      addTearDown(api.close);
      final result = await api.login(' test@example.com ', ' password ');
      expect(result.account!.id, 'account-1');
      final login = server.requests.last;
      expect(login.headers['X-CSRFToken'], 'csrf-test');
      expect(login.data['email'], 'test@example.com');
      expect(login.data['password'], ' password ');
      await api.me();
      expect(
        server.requests.last.headers['cookie'].toString(),
        contains('sessionid=session-test'),
      );
      await api.logout();
      expect(
        await api.cookies.loadForRequest(Uri.parse('https://example.com')),
        isEmpty,
      );
      expect(
        server.requests.where((r) => r.uri.path.endsWith('/csrf/')).length,
        2,
      );
    },
  );


  test('Registration and password reset follow the Django contract', () async {
    final server = FakeServer();
    final api = MboloApi(
      'https://example.com',
      client: Dio()..httpClientAdapter = server,
    );
    addTearDown(api.close);

    final account = await api.register(
      email: ' new@example.com ',
      password: 'A-strong-demo-password!',
      passwordConfirmation: 'A-strong-demo-password!',
      acceptTerms: true,
      confirmAdult: true,
    );
    expect(account.id, 'account-1');
    final registration = server.requests.last;
    expect(registration.uri.path, endsWith('/auth/register/'));
    expect(registration.data['email'], 'new@example.com');
    expect(registration.data['password_confirmation'], 'A-strong-demo-password!');
    expect(registration.data['accept_terms'], isTrue);
    expect(registration.data['confirm_adult'], isTrue);
    expect(registration.headers['X-CSRFToken'], 'csrf-test');

    await api.requestPasswordReset(' new@example.com ');
    final reset = server.requests.last;
    expect(reset.uri.path, endsWith('/auth/password-reset/request/'));
    expect(reset.data, {'email': 'new@example.com'});
    expect(reset.headers['X-CSRFToken'], 'csrf-test');
  });

  test('Failed logout preserves session to retry server revocation', () async {
    final server = FakeServer()..rejectLogout = true;
    final api = MboloApi(
      'https://example.com',
      client: Dio()..httpClientAdapter = server,
    );
    addTearDown(api.close);
    await api.login('test@example.com', 'password');
    await expectLater(api.logout(), throwsA(isA<DioException>()));
    expect(
      await api.cookies.loadForRequest(Uri.parse('https://example.com')),
      isNotEmpty,
    );
  });

  test('Profile and preference updates use protected PATCH routes', () async {
    final server = FakeServer();
    final api = MboloApi(
      'https://example.com',
      client: Dio()..httpClientAdapter = server,
    );
    addTearDown(api.close);

    final profile = await api.getProfile();
    expect(profile.displayName, 'Christ YG');
    expect(server.requests.last.method, 'GET');

    await api.updateProfile(
      displayName: ' Christ YG ',
      city: 'libreville',
      biography: ' Présentation mobile sécurisée. ',
    );
    final profilePatch = server.requests.last;
    expect(profilePatch.method, 'PATCH');
    expect(profilePatch.uri.path, endsWith('/profiles/me/'));
    expect(profilePatch.data['display_name'], 'Christ YG');
    expect(profilePatch.data['biography'], 'Présentation mobile sécurisée.');
    expect(profilePatch.headers['X-CSRFToken'], 'csrf-test');

    final preferences = await api.getPreferences();
    expect(preferences.minimumAge, 21);
    expect(preferences.preferredGenders, ['female']);

    await api.updatePreferences(
      minimumAge: 22,
      maximumAge: 40,
      preferredGenders: const ['female'],
    );
    final preferencesPatch = server.requests.last;
    expect(preferencesPatch.method, 'PATCH');
    expect(
      preferencesPatch.uri.path,
      endsWith('/profiles/preferences/me/'),
    );
    expect(preferencesPatch.data['minimum_age'], 22);
    expect(preferencesPatch.data['maximum_age'], 40);
    expect(preferencesPatch.data['preferred_genders'], ['female']);
    expect(preferencesPatch.headers['X-CSRFToken'], 'csrf-test');
  });

}
