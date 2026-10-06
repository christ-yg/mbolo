import 'dart:convert';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mbolo_mobile/api.dart';
import 'package:mbolo_mobile/session_store.dart';

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
    } else if (path.endsWith('/profiles/discovery/')) {
      data = {
        'results': [
          {
            'id': '22222222-2222-2222-2222-222222222222',
            'display_name': 'Grâce',
            'age': 29,
            'gender': 'woman',
            'city': 'libreville',
            'biography': 'Profil de découverte sécurisé.',
            'dating_intent': 'serious_relationship',
            'is_verified': true,
            'photos': <Map<String, dynamic>>[],
            'interest_labels': ['Musique', 'Voyages'],
            'common_interest_labels': ['Musique'],
            'compatibility_score': 50,
            'distance_label': 'À moins de 10 km',
          },
        ],
        'count': 1,
        'next': null,
        'previous': null,
      };
    } else if (path.endsWith('/interactions/')) {
      data = {
        'interaction_id': '33333333-3333-3333-3333-333333333333',
        'decision': options.data['decision'],
        'is_super_like': false,
        'interaction_created': true,
        'matched': options.data['decision'] == 'like',
        'match_created': options.data['decision'] == 'like',
        'match_id': options.data['decision'] == 'like'
            ? '44444444-4444-4444-4444-444444444444'
            : null,
      };
    } else if (path.endsWith('/profiles/photos/')) {
      final photo = {
        'id': '11111111-1111-1111-1111-111111111111',
        'image_url': 'https://example.com/media/photo.webp',
        'position': 0,
        'is_primary': true,
        'moderation_status': 'pending',
        'moderation_status_label': 'En attente',
      };
      data = options.method == 'GET'
          ? {
              'results': [photo],
              'count': 1,
            }
          : {'data': photo, 'message': 'Photo ajoutée avec succès.'};
    } else if (path.contains('/profiles/photos/')) {
      if (options.method == 'DELETE') {
        status = 204;
        data = <String, dynamic>{};
      } else {
        data = {
          'data': {
            'id': '11111111-1111-1111-1111-111111111111',
            'image_url': 'https://example.com/media/photo.webp',
            'position': 0,
            'is_primary': true,
            'moderation_status': 'pending',
            'moderation_status_label': 'En attente',
          },
        };
      }
    } else if (path.endsWith('/profiles/preferences/me/')) {
      data = {
        'data': {
          'minimum_age': 21,
          'maximum_age': 39,
          'preferred_genders': ['woman'],
          'advanced_filters_available': false,
        },
      };
    } else if (path.endsWith('/profiles/me/')) {
      data = {
        'data': {
          'display_name': 'Christ YG',
          'birth_date': '1994-06-15',
          'gender': 'man',
          'city': 'libreville',
          'biography': 'Une présentation de test suffisamment complète.',
          'dating_intent': 'serious_relationship',
          'interests': ['technology', 'travel', 'music'],
          'is_complete': true,
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

    expect(profile.birthDate, '1994-06-15');
    expect(profile.gender, 'man');
    expect(profile.datingIntent, 'serious_relationship');
    expect(profile.interests, ['technology', 'travel', 'music']);

    await api.updateProfile(
      displayName: ' Christ YG ',
      birthDate: '1994-06-15',
      gender: 'man',
      city: 'libreville',
      biography: ' Présentation mobile sécurisée. ',
      datingIntent: 'serious_relationship',
      interests: const ['technology', 'travel', 'music'],
    );
    final profilePatch = server.requests.last;
    expect(profilePatch.method, 'PATCH');
    expect(profilePatch.uri.path, endsWith('/profiles/me/'));
    expect(profilePatch.data['display_name'], 'Christ YG');
    expect(profilePatch.data['birth_date'], '1994-06-15');
    expect(profilePatch.data['gender'], 'man');
    expect(profilePatch.data['biography'], 'Présentation mobile sécurisée.');
    expect(profilePatch.data['dating_intent'], 'serious_relationship');
    expect(profilePatch.data['interests'], ['technology', 'travel', 'music']);
    expect(profilePatch.headers['X-CSRFToken'], 'csrf-test');

    final preferences = await api.getPreferences();
    expect(preferences.minimumAge, 21);
    expect(preferences.preferredGenders, ['woman']);

    await api.updatePreferences(
      minimumAge: 22,
      maximumAge: 40,
      preferredGenders: const ['woman'],
    );
    final preferencesPatch = server.requests.last;
    expect(preferencesPatch.method, 'PATCH');
    expect(
      preferencesPatch.uri.path,
      endsWith('/profiles/preferences/me/'),
    );
    expect(preferencesPatch.data['minimum_age'], 22);
    expect(preferencesPatch.data['maximum_age'], 40);
    expect(preferencesPatch.data['preferred_genders'], ['woman']);
    expect(preferencesPatch.headers['X-CSRFToken'], 'csrf-test');
  });


  test('Photo gallery uses multipart upload and protected mutations', () async {
    final server = FakeServer();
    final api = MboloApi(
      'https://example.com',
      client: Dio()..httpClientAdapter = server,
    );
    addTearDown(api.close);

    final photos = await api.getPhotos();
    expect(photos, hasLength(1));
    expect(photos.single.primary, isTrue);
    expect(photos.single.moderationStatus, 'pending');

    await api.uploadPhoto(
      bytes: Uint8List.fromList([1, 2, 3, 4]),
      filename: 'portrait.jpg',
      position: 0,
      primary: true,
    );
    final upload = server.requests.last;
    expect(upload.method, 'POST');
    expect(upload.uri.path, endsWith('/profiles/photos/'));
    expect(upload.headers['X-CSRFToken'], 'csrf-test');
    expect(upload.data, isA<FormData>());
    final form = upload.data as FormData;
    expect(Map<String, String>.fromEntries(form.fields)['position'], '0');
    expect(Map<String, String>.fromEntries(form.fields)['is_primary'], 'true');
    expect(form.files.single.value.filename, 'portrait.jpg');

    await api.updatePhoto(
      id: photos.single.id,
      primary: true,
    );
    final update = server.requests.last;
    expect(update.method, 'PATCH');
    expect(update.data['is_primary'], isTrue);
    expect(update.headers['X-CSRFToken'], 'csrf-test');

    await api.deletePhoto(photos.single.id);
    final deletion = server.requests.last;
    expect(deletion.method, 'DELETE');
    expect(deletion.headers['X-CSRFToken'], 'csrf-test');
  });


  test('Discovery and likes use the protected Django routes', () async {
    final server = FakeServer();
    final api = MboloApi(
      'https://example.com',
      client: Dio()..httpClientAdapter = server,
    );
    addTearDown(api.close);

    final profiles = await api.getDiscovery();
    expect(profiles, hasLength(1));
    expect(profiles.single.displayName, 'Grâce');
    expect(profiles.single.compatibilityScore, 50);
    expect(profiles.single.commonInterestLabels, ['Musique']);
    expect(server.requests.last.uri.queryParameters['page_size'], '20');

    final result = await api.decideProfile(
      profileId: profiles.single.id,
      decision: 'like',
    );
    expect(result.matched, isTrue);
    expect(result.matchCreated, isTrue);

    final interaction = server.requests.last;
    expect(interaction.method, 'POST');
    expect(interaction.uri.path, endsWith('/interactions/'));
    expect(
      interaction.data['target_profile_id'],
      '22222222-2222-2222-2222-222222222222',
    );
    expect(interaction.data['decision'], 'like');
    expect(interaction.headers['X-CSRFToken'], 'csrf-test');
  });
  test('Session is encrypted, restored and cleared without the password', () async {
    final store = MemorySessionStore();
    final firstServer = FakeServer();
    final firstApi = MboloApi(
      'https://example.com',
      client: Dio()..httpClientAdapter = firstServer,
      sessionStore: store,
    );
    addTearDown(firstApi.close);

    await firstApi.login('test@example.com', 'password');
    expect(await store.read(), 'session-test');

    final restoredServer = FakeServer();
    final restoredApi = MboloApi(
      'https://example.com',
      client: Dio()..httpClientAdapter = restoredServer,
      sessionStore: store,
    );
    addTearDown(restoredApi.close);

    final account = await restoredApi.restoreSession();
    expect(account?.email, 'test@example.com');
    expect(
      restoredServer.requests.last.headers.values.join(';'),
      contains('sessionid=session-test'),
    );

    await restoredApi.logout();
    expect(await store.read(), isNull);
  });


}
