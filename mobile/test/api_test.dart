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
    } else if (path.endsWith('/premium/overview/')) {
      data = {
        'data': {
          'subscription': {'plan': 'free', 'plan_name': 'Gratuit', 'status': 'inactive', 'is_premium': false, 'ends_at': null},
          'plans': [
            {'code': 'plus', 'name': 'MBOLO Plus', 'description': 'Plus de liberté', 'features': ['Likes illimités'], 'price_label': '4 900 FCFA / mois', 'amount_xaf': 4900, 'payment_available': true},
          ],
          'payment_methods': [
            {'code': 'airtel_money', 'name': 'Airtel Money', 'description': 'Paiement sécurisé', 'available': true},
          ],
          'payment_notice': 'Confirmation serveur obligatoire.',
          'privacy': {'incognito_enabled': false, 'incognito_available': false, 'effective_incognito': false},
          'boost': {'entitled': false, 'active': false, 'active_until': null, 'duration_minutes': 30, 'allowance_per_7_days': 0, 'remaining': 0, 'next_available_at': null},
        },
      };
    } else if (path.endsWith('/premium/payments/history/')) {
      data = {'data': {'transactions': <Map<String, dynamic>>[]}};
    } else if (path.endsWith('/premium/payments/checkout/')) {
      data = {'data': {'id': '99999999-9999-9999-9999-999999999999', 'plan_name': 'MBOLO Plus', 'method_name': 'Airtel Money', 'status': 'created', 'amount_xaf': 4900, 'currency': 'XAF', 'can_confirm_in_test_mode': false}};
    } else if (path.endsWith('/premium/privacy/')) {
      data = {'data': {'incognito_enabled': true, 'incognito_available': true, 'effective_incognito': true}};
    } else if (path.endsWith('/premium/boost/')) {
      data = {'data': {'entitled': true, 'active': true, 'active_until': '2026-10-06T18:30:00Z', 'duration_minutes': 30, 'allowance_per_7_days': 1, 'remaining': 0, 'next_available_at': null}};
    } else if (path.endsWith('/premium/payments/confirm-test/')) {
      data = {'data': {'transaction': {'id': '99999999-9999-9999-9999-999999999999', 'plan_name': 'MBOLO Plus', 'method_name': 'Airtel Money', 'status': 'succeeded', 'amount_xaf': 4900, 'currency': 'XAF', 'can_confirm_in_test_mode': false}, 'subscription': {'plan': 'plus'}}};
    } else if (path.endsWith('/premium/payments/cancel/')) {
      data = {'data': {'id': '99999999-9999-9999-9999-999999999999', 'plan_name': 'MBOLO Plus', 'method_name': 'Airtel Money', 'status': 'canceled', 'amount_xaf': 4900, 'currency': 'XAF', 'can_confirm_in_test_mode': false}};
    } else if (path.endsWith('/super-like/')) {
      data = {
        'entitled': true,
        'daily_limit': 3,
        'remaining_today': 2,
      };
    } else if (path.endsWith('/interactions/rewind/')) {
      if (options.method == 'GET') {
        data = {
          'entitled': true,
          'available': true,
          'reason': 'available',
        };
      } else {
        data = {
          'rewound': true,
          'profile': {
            'id': '22222222-2222-2222-2222-222222222222',
            'display_name': 'Grâce',
            'age': 29,
            'city': 'libreville',
            'biography': 'Profil restauré.',
            'dating_intent': 'serious_relationship',
            'is_verified': true,
            'photos': <Map<String, dynamic>>[],
          },
        };
      }
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
    } else if (path.endsWith('/matches/')) {
      data = {
        'results': [
          {
            'id': '44444444-4444-4444-4444-444444444444',
            'other_profile': {
              'id': '22222222-2222-2222-2222-222222222222',
              'display_name': 'Grâce',
              'age': 29,
              'city': 'libreville',
              'biography': 'Profil de test.',
              'dating_intent': 'serious_relationship',
              'is_verified': true,
              'photos': <Map<String, dynamic>>[],
            },
            'created_at': '2026-10-06T10:00:00Z',
          },
        ],
      };
    } else if (path.endsWith('/likes-received/')) {
      data = {
        'results': [
          {
            'interaction_id': '55555555-5555-5555-5555-555555555555',
            'city': 'Libreville',
            'age_range': '25–29 ans',
            'dating_intent': 'Relation sérieuse',
            'has_photo': true,
            'profile_id': null,
            'display_name': null,
            'image_url': null,
            'received_at': '2026-10-06T11:00:00Z',
            'is_identity_revealed': false,
            'is_super_like': true,
          },
        ],
      };
    } else if (path.endsWith(
      '/likes-received/55555555-5555-5555-5555-555555555555/respond/',
    )) {
      data = {
        'decision': options.data['decision'],
        'matched': true,
        'match_created': true,
        'match_id': '44444444-4444-4444-4444-444444444444',
        'revealed_profile': {
          'id': '22222222-2222-2222-2222-222222222222',
          'display_name': 'Grâce',
          'age': 29,
          'city': 'libreville',
          'biography': 'Profil de test.',
          'dating_intent': 'serious_relationship',
          'is_verified': true,
          'photos': <Map<String, dynamic>>[],
        },
      };
    } else if (path.endsWith('/notifications/')) {
      if (options.method == 'DELETE') {
        status = 204;
        data = <String, dynamic>{};
      } else {
        data = {
          'results': [
            {
              'id': '99999999-9999-9999-9999-999999999999',
              'kind': 'match',
              'title': 'Nouveau match',
              'body': 'Une belle rencontre commence.',
              'target_path': '/messages',
              'is_read': false,
              'read_at': null,
              'created_at': '2026-10-06T10:30:00Z',
            },
          ],
          'count': 1,
          'next': null,
          'previous': null,
        };
      }
    } else if (path.endsWith('/notifications/unread-count/')) {
      data = {'unread_count': 1};
    } else if (path.endsWith('/notifications/read-all/')) {
      data = {'marked_count': 1, 'read_at': '2026-10-06T11:00:00Z'};
    } else if (path.endsWith('/notifications/99999999-9999-9999-9999-999999999999/read/')) {
      data = {
        'id': '99999999-9999-9999-9999-999999999999',
        'kind': 'match',
        'title': 'Nouveau match',
        'body': 'Une belle rencontre commence.',
        'target_path': '/messages',
        'is_read': true,
        'read_at': '2026-10-06T11:00:00Z',
        'created_at': '2026-10-06T10:30:00Z',
      };
    } else if (path.endsWith('/notifications/99999999-9999-9999-9999-999999999999/')) {
      status = 204;
      data = <String, dynamic>{};
    } else if (path.endsWith('/auth/security/sessions/')) {
      data = {
        'data': [
          {
            'id': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
            'device': 'MBOLO · Android',
            'ipFingerprint': 'c8f2a4d9',
            'createdAt': '2026-10-06T08:00:00Z',
            'lastSeenAt': '2026-10-06T15:00:00Z',
            'isCurrent': true,
          },
          {
            'id': 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
            'device': 'Chrome · Windows',
            'ipFingerprint': 'a19e20bf',
            'createdAt': '2026-10-05T18:00:00Z',
            'lastSeenAt': '2026-10-06T11:00:00Z',
            'isCurrent': false,
          },
        ],
      };
    } else if (path.endsWith(
      '/auth/security/sessions/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb/revoke/',
    )) {
      data = {'message': 'Appareil déconnecté.'};
    } else if (path.endsWith('/auth/security/revoke-sessions/')) {
      data = {
        'message': 'Autres sessions déconnectées.',
        'data': {'revokedSessions': 1},
      };
    } else if (path.endsWith('/auth/security/email-2fa/')) {
      data = {
        'message': 'Double authentification activée.',
        'data': {'emailTwoFactorEnabled': options.data['enabled']},
      };
    } else if (path.endsWith('/auth/security/change-password/')) {
      data = {
        'message': 'Mot de passe modifié.',
        'data': {'revokedSessions': 1},
      };
    } else if (path.endsWith('/auth/privacy/export/')) {
      data = {
        'export': {
          'generated_at': '2026-10-06T15:00:00Z',
          'account': {'email': 'test@example.com'},
        },
      };
    } else if (path.endsWith('/auth/security/deactivate/')) {
      data = {'message': 'Compte désactivé.'};
      headers['set-cookie'] = ['sessionid=; Path=/; Secure; HttpOnly'];
    } else if (path.endsWith('/auth/privacy/delete/')) {
      data = {'message': 'Compte supprimé.'};
      headers['set-cookie'] = ['sessionid=; Path=/; Secure; HttpOnly'];
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

  test('Matches and received likes follow the private API contract', () async {
    final server = FakeServer();
    final api = MboloApi(
      'https://example.com',
      client: Dio()..httpClientAdapter = server,
    );
    addTearDown(api.close);

    final matches = await api.getMatches();
    expect(matches.single.otherProfile.displayName, 'Grâce');

    final likes = await api.getReceivedLikes();
    expect(likes.single.identityRevealed, isFalse);
    expect(likes.single.displayName, isNull);
    expect(likes.single.superLike, isTrue);

    final result = await api.respondToReceivedLike(
      interactionId: likes.single.interactionId,
      decision: 'like',
    );
    expect(result.matched, isTrue);
    expect(result.revealedProfile?.displayName, 'Grâce');
    expect(server.requests.last.data['decision'], 'like');
  });

  test('Super Like and Rewind use server-side entitlement state', () async {
    final server = FakeServer();
    final api = MboloApi(
      'https://example.com',
      client: Dio()..httpClientAdapter = server,
    );
    addTearDown(api.close);

    final superLike = await api.getSuperLikeState();
    expect(superLike.entitled, isTrue);
    expect(superLike.remainingToday, 2);

    final rewind = await api.getRewindState();
    expect(rewind.available, isTrue);

    await api.decideProfile(
      profileId: '22222222-2222-2222-2222-222222222222',
      decision: 'like',
      superLike: true,
    );
    expect(server.requests.last.data['is_super_like'], isTrue);

    final restored = await api.rewindLastPass();
    expect(restored.displayName, 'Grâce');
    final rewindPosts = server.requests.where(
      (request) =>
          request.uri.path.endsWith('/interactions/rewind/') &&
          request.method == 'POST',
    );
    expect(rewindPosts, hasLength(1));
  });

  test('Security centre manages 2FA, password and connected devices', () async {
    final server = FakeServer();
    final api = MboloApi(
      'https://example.com',
      client: Dio()..httpClientAdapter = server,
    );
    addTearDown(api.close);

    final sessions = await api.getConnectedSessions();
    expect(sessions, hasLength(2));
    expect(sessions.first.current, isTrue);

    await api.revokeConnectedSession(
      sessionId: sessions.last.id,
      currentPassword: 'mot-de-passe-actuel',
    );
    expect(server.requests.last.data['current_password'], 'mot-de-passe-actuel');

    expect(await api.revokeOtherSessions('mot-de-passe-actuel'), 1);
    expect(
      await api.setEmailTwoFactor(
        enabled: true,
        currentPassword: 'mot-de-passe-actuel',
      ),
      isTrue,
    );
    expect(
      await api.changePassword(
        currentPassword: 'mot-de-passe-actuel',
        newPassword: 'NouveauMotDePasse!2026',
        newPasswordConfirmation: 'NouveauMotDePasse!2026',
      ),
      1,
    );
  });

  test('Privacy export and account closure use protected contracts', () async {
    final server = FakeServer();
    final store = MemorySessionStore();
    final api = MboloApi(
      'https://example.com',
      client: Dio()..httpClientAdapter = server,
      sessionStore: store,
    );
    addTearDown(api.close);

    final export = await api.exportPersonalData();
    expect(export['export'], isA<Map<String, dynamic>>());

    await api.login('test@example.com', 'mot-de-passe-actuel');
    expect(await store.read(), 'session-test');
    await api.deactivateAccount('mot-de-passe-actuel');
    expect(await store.read(), isNull);
    final deactivation = server.requests.last;
    expect(deactivation.data['confirmation'], 'DESACTIVER');

    await api.login('test@example.com', 'mot-de-passe-actuel');
    await api.deleteAccount('mot-de-passe-actuel');
    expect(await store.read(), isNull);
    final deletion = server.requests.last;
    expect(deletion.data['confirmation'], 'SUPPRIMER DEFINITIVEMENT');
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

    await api.confirmPasswordReset(
      uid: ' uid-value ',
      token: ' token-value ',
      password: 'A-new-demo-password!',
      passwordConfirmation: 'A-new-demo-password!',
    );
    final confirmation = server.requests.last;
    expect(confirmation.uri.path, endsWith('/auth/password-reset/confirm/'));
    expect(confirmation.data, {
      'uid': 'uid-value',
      'token': 'token-value',
      'password': 'A-new-demo-password!',
      'password_confirmation': 'A-new-demo-password!',
    });
    expect(confirmation.headers['X-CSRFToken'], 'csrf-test');
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

  test('Notification centre uses protected account routes', () async {
    final server = FakeServer();
    final api = MboloApi(
      'https://example.com',
      client: Dio()..httpClientAdapter = server,
    );
    addTearDown(api.close);

    final items = await api.getNotifications();
    expect(items, hasLength(1));
    expect(items.single.title, 'Nouveau match');
    expect(await api.getNotificationUnreadCount(), 1);

    final updated = await api.markNotificationRead(items.single.id);
    expect(updated.read, isTrue);
    await api.markAllNotificationsRead();
    await api.deleteNotification(items.single.id);
    expect(server.requests.last.method, 'DELETE');
    expect(server.requests.last.headers['X-CSRFToken'], 'csrf-test');
  });

  test('Premium catalogue and checkout remain server-driven', () async {
    final server = FakeServer();
    final api = MboloApi(
      'https://example.com',
      client: Dio()..httpClientAdapter = server,
    );
    addTearDown(api.close);

    final overview = await api.getPremiumOverview();
    expect(overview.subscription.plan, 'free');
    expect(overview.plans.single.amountXaf, 4900);
    expect(overview.paymentMethods.single.name, 'Airtel Money');

    final payment = await api.createPremiumCheckout(
      plan: 'plus',
      method: 'airtel_money',
    );
    expect(payment.status, 'created');
    expect(payment.amountXaf, 4900);
    expect(server.requests.last.data['plan'], 'plus');
    expect(server.requests.last.headers['X-CSRFToken'], 'csrf-test');
    expect(await api.getPremiumPaymentHistory(), isEmpty);

    final privacy = await api.updatePremiumPrivacy(true);
    expect(privacy.effective, isTrue);
    final boost = await api.activatePremiumBoost();
    expect(boost.active, isTrue);
    final confirmed = await api.confirmPremiumPaymentTest(payment.id);
    expect(confirmed.status, 'succeeded');
    final canceled = await api.cancelPremiumPayment(payment.id);
    expect(canceled.status, 'canceled');
  });

}
