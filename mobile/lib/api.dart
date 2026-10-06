import 'dart:typed_data';

import 'package:cookie_jar/cookie_jar.dart';
import 'package:dio/dio.dart';
import 'package:dio_cookie_manager/dio_cookie_manager.dart';

import 'auth_contract.dart';
import 'session_store.dart';
export 'auth_contract.dart';

/// Native Android/iOS only. The Django session identifier is encrypted at rest.
/// Passwords, CSRF values and authentication challenges are never persisted.
class MboloApi implements AuthApi {
  MboloApi(String origin, {Dio? client, SessionStore? sessionStore})
    : origin = validateOrigin(origin),
      client = client ?? Dio(),
      sessionStore = sessionStore ?? MemorySessionStore() {
    this.client.options = BaseOptions(
      baseUrl: '${this.origin.origin}/api/v1/',
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 20),
      sendTimeout: const Duration(seconds: 20),
      followRedirects: false,
      headers: {'Accept': 'application/json', 'Origin': this.origin.origin},
    );
    this.client.interceptors.add(CookieManager(cookies));
    this.client.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          final sessionId = _sessionId;
          final existing = options.headers['Cookie']?.toString() ?? '';
          if (sessionId != null &&
              sessionId.isNotEmpty &&
              !existing.contains('sessionid=')) {
            options.headers['Cookie'] = existing.isEmpty
                ? 'sessionid=$sessionId'
                : '$existing; sessionid=$sessionId';
          }
          handler.next(options);
        },
        onResponse: (response, handler) async {
          await _captureSessionCookie(response);
          handler.next(response);
        },
      ),
    );
  }

  final Uri origin;
  final Dio client;
  final SessionStore sessionStore;
  final CookieJar cookies = CookieJar();
  String? _sessionId;

  Future<void> _captureSessionCookie(Response<dynamic> response) async {
    final values = response.headers.map['set-cookie'] ?? const <String>[];
    for (final value in values) {
      final match = RegExp(r'(?:^|;\s*)sessionid=([^;]*)').firstMatch(value);
      if (match == null) continue;
      final sessionId = match.group(1)?.trim() ?? '';
      if (sessionId.isEmpty) {
        _sessionId = null;
        await sessionStore.clear();
      } else {
        _sessionId = sessionId;
        await sessionStore.write(sessionId);
      }
      break;
    }
  }

  Future<dynamic> _post(String path, Map<String, dynamic> body) async {
    // Fetch for every mutation: Django rotates CSRF on authentication changes.
    final csrf = await client.get<dynamic>('csrf/');
    final token = objectData(csrf.data)['csrfToken'];
    if (token is! String || token.isEmpty) {
      throw const FormatException('Protection CSRF indisponible.');
    }
    final response = await client.post<dynamic>(
      path,
      data: body,
      options: Options(headers: {'X-CSRFToken': token}),
    );
    return response.data;
  }

  Future<Map<String, dynamic>> _postObject(
    String path,
    Map<String, dynamic> body,
  ) async {
    return objectData(await _post(path, body));
  }


  Future<Map<String, dynamic>> _patchObject(
    String path,
    Map<String, dynamic> body,
  ) async {
    final csrf = await client.get<dynamic>('csrf/');
    final token = objectData(csrf.data)['csrfToken'];
    if (token is! String || token.isEmpty) {
      throw const FormatException('Protection CSRF indisponible.');
    }
    final response = await client.patch<dynamic>(
      path,
      data: body,
      options: Options(headers: {'X-CSRFToken': token}),
    );
    return objectData(response.data);
  }

  @override
  Future<Account> register({
    required String email,
    required String password,
    required String passwordConfirmation,
    required bool acceptTerms,
    required bool confirmAdult,
  }) async {
    return Account.fromJson(
      await _postObject('auth/register/', {
        'email': email.trim(),
        'password': password,
        'password_confirmation': passwordConfirmation,
        'accept_terms': acceptTerms,
        'confirm_adult': confirmAdult,
      }),
    );
  }

  @override
  Future<void> requestPasswordReset(String email) async {
    await _post('auth/password-reset/request/', {'email': email.trim()});
  }

  @override
  Future<void> confirmPasswordReset({
    required String uid,
    required String token,
    required String password,
    required String passwordConfirmation,
  }) async {
    await _post('auth/password-reset/confirm/', {
      'uid': uid.trim(),
      'token': token.trim(),
      'password': password,
      'password_confirmation': passwordConfirmation,
    });
  }

  @override
  Future<LoginResult> login(String email, String password) async {
    return LoginResult.fromJson(
      await _postObject('auth/login/', {
        'email': email.trim(),
        'password': password,
      }),
    );
  }

  @override
  Future<Account> confirm(String challenge, String code) async {
    return Account.fromJson(
      await _postObject('auth/login/2fa/confirm/', {
        'challenge_token': challenge,
        'code': code.trim(),
      }),
    );
  }

  @override
  Future<Account> me() async {
    final response = await client.get<dynamic>('auth/me/');
    return Account.fromJson(objectData(response.data));
  }


  @override
  Future<Account?> restoreSession() async {
    _sessionId = await sessionStore.read();
    if (_sessionId == null || _sessionId!.isEmpty) return null;
    try {
      return await me();
    } on DioException catch (error) {
      if (error.response?.statusCode == 401 ||
          error.response?.statusCode == 403) {
        _sessionId = null;
        await sessionStore.clear();
        await cookies.deleteAll();
        return null;
      }
      rethrow;
    }
  }

  @override
  Future<MemberProfile> getProfile() async {
    final response = await client.get<dynamic>('profiles/me/');
    return MemberProfile.fromJson(objectData(response.data));
  }

  @override
  Future<MemberProfile> updateProfile({
    required String displayName,
    required String birthDate,
    required String gender,
    required String city,
    required String biography,
    required String datingIntent,
    required List<String> interests,
  }) async {
    return MemberProfile.fromJson(
      await _patchObject('profiles/me/', {
        'display_name': displayName.trim(),
        'birth_date': birthDate,
        'gender': gender,
        'city': city,
        'biography': biography.trim(),
        'dating_intent': datingIntent,
        'interests': interests,
      }),
    );
  }

  @override
  Future<List<DiscoveryProfile>> getDiscovery() async {
    final response = await client.get<dynamic>(
      'profiles/discovery/',
      queryParameters: const {'page_size': 20},
    );
    final raw = response.data;
    if (raw is! Map<String, dynamic> || raw['results'] is! List) {
      throw const FormatException('Découverte indisponible.');
    }
    return (raw['results'] as List)
        .map((item) {
          if (item is! Map<String, dynamic>) {
            throw const FormatException('Profil de découverte incorrect.');
          }
          return DiscoveryProfile.fromJson(item);
        })
        .toList(growable: false);
  }

  @override
  Future<InteractionResult> decideProfile({
    required String profileId,
    required String decision,
  }) async {
    if (decision != 'like' && decision != 'pass') {
      throw const FormatException('Décision de rencontre incorrecte.');
    }
    return InteractionResult.fromJson(
      await _postObject('interactions/', {
        'target_profile_id': profileId,
        'decision': decision,
      }),
    );
  }

  @override
  Future<List<ProfilePhoto>> getPhotos() async {
    final response = await client.get<dynamic>('profiles/photos/');
    final raw = response.data;
    if (raw is! Map<String, dynamic> || raw['results'] is! List) {
      throw const FormatException('Galerie de photos incorrecte.');
    }
    return (raw['results'] as List)
        .map((item) {
          if (item is! Map<String, dynamic>) {
            throw const FormatException('Photo de profil incorrecte.');
          }
          return ProfilePhoto.fromJson(item);
        })
        .toList(growable: false);
  }

  @override
  Future<ProfilePhoto> uploadPhoto({
    required Uint8List bytes,
    required String filename,
    required int position,
    required bool primary,
  }) async {
    final csrf = await client.get<dynamic>('csrf/');
    final token = objectData(csrf.data)['csrfToken'];
    if (token is! String || token.isEmpty) {
      throw const FormatException('Protection CSRF indisponible.');
    }
    final response = await client.post<dynamic>(
      'profiles/photos/',
      data: FormData.fromMap({
        'image': MultipartFile.fromBytes(bytes, filename: filename),
        'position': position,
        'is_primary': primary,
      }),
      options: Options(headers: {'X-CSRFToken': token}),
    );
    return ProfilePhoto.fromJson(objectData(response.data));
  }

  @override
  Future<ProfilePhoto> updatePhoto({
    required String id,
    int? position,
    bool? primary,
  }) async {
    final body = <String, dynamic>{};
    if (position != null) body['position'] = position;
    if (primary != null) body['is_primary'] = primary;
    return ProfilePhoto.fromJson(
      await _patchObject('profiles/photos/$id/', body),
    );
  }

  @override
  Future<void> deletePhoto(String id) async {
    final csrf = await client.get<dynamic>('csrf/');
    final token = objectData(csrf.data)['csrfToken'];
    if (token is! String || token.isEmpty) {
      throw const FormatException('Protection CSRF indisponible.');
    }
    await client.delete<dynamic>(
      'profiles/photos/$id/',
      options: Options(headers: {'X-CSRFToken': token}),
    );
  }

  @override
  Future<DiscoveryPreferences> getPreferences() async {
    final response = await client.get<dynamic>('profiles/preferences/me/');
    return DiscoveryPreferences.fromJson(objectData(response.data));
  }

  @override
  Future<DiscoveryPreferences> updatePreferences({
    required int minimumAge,
    required int maximumAge,
    required List<String> preferredGenders,
  }) async {
    return DiscoveryPreferences.fromJson(
      await _patchObject('profiles/preferences/me/', {
        'minimum_age': minimumAge,
        'maximum_age': maximumAge,
        'preferred_genders': preferredGenders,
      }),
    );
  }

  @override
  Future<SafetyActionResult> blockProfile(String profileId) async {
    return SafetyActionResult.fromJson(
      await _postObject(
        'safety/profiles/$profileId/block/',
        const {'confirm': true},
      ),
    );
  }

  @override
  Future<SafetyActionResult> reportProfile({
    required String profileId,
    required String reason,
    required String description,
  }) async {
    return SafetyActionResult.fromJson(
      await _postObject(
        'safety/profiles/$profileId/report/',
        {'reason': reason, 'description': description.trim()},
      ),
    );
  }

  @override
  Future<void> unmatch(String matchId) async {
    final csrf = await client.get<dynamic>('csrf/');
    final token = objectData(csrf.data)['csrfToken'];
    if (token is! String || token.isEmpty) {
      throw const FormatException('Protection CSRF indisponible.');
    }
    await client.delete<dynamic>(
      'matches/$matchId/',
      options: Options(headers: {'X-CSRFToken': token}),
    );
  }

  @override
  Future<List<MatchSummary>> getMatches() async {
    final response = await client.get<dynamic>(
      'matches/',
      queryParameters: const {'page_size': 50},
    );
    return _paginatedResults(
      response.data,
      MatchSummary.fromJson,
      'Liste des matchs incorrecte.',
    );
  }

  @override
  Future<List<ReceivedLike>> getReceivedLikes() async {
    final response = await client.get<dynamic>(
      'likes-received/',
      queryParameters: const {'page_size': 50},
    );
    return _paginatedResults(
      response.data,
      ReceivedLike.fromJson,
      'Liste des likes reçus incorrecte.',
    );
  }

  @override
  Future<ReceivedLikeResult> respondToReceivedLike({
    required String interactionId,
    required String decision,
  }) async {
    if (decision != 'like' && decision != 'pass') {
      throw const FormatException('Réponse au like incorrecte.');
    }
    return ReceivedLikeResult.fromJson(
      await _postObject(
        'likes-received/$interactionId/respond/',
        {'decision': decision},
      ),
    );
  }

  List<T> _paginatedResults<T>(
    dynamic raw,
    T Function(Map<String, dynamic>) decoder,
    String errorMessage,
  ) {
    if (raw is! Map<String, dynamic> || raw['results'] is! List) {
      throw FormatException(errorMessage);
    }
    return (raw['results'] as List).map((item) {
      if (item is! Map<String, dynamic>) throw FormatException(errorMessage);
      return decoder(item);
    }).toList(growable: false);
  }

  @override
  Future<List<ConversationSummary>> getConversations() async {
    final response = await client.get<dynamic>(
      'conversations/',
      queryParameters: const {'page_size': 50},
    );
    return _paginatedResults(
      response.data,
      ConversationSummary.fromJson,
      'Liste des conversations incorrecte.',
    );
  }

  @override
  Future<List<ChatMessage>> getMessages(String conversationId) async {
    final response = await client.get<dynamic>(
      'conversations/$conversationId/messages/',
      queryParameters: const {'page_size': 100},
    );
    return _paginatedResults(
      response.data,
      ChatMessage.fromJson,
      'Historique des messages incorrect.',
    );
  }

  @override
  Future<ChatMessage> sendMessage(String conversationId, String body) async {
    final trimmed = body.trim();
    if (trimmed.isEmpty || trimmed.length > 2000) {
      throw const FormatException('Le message doit contenir entre 1 et 2000 caractères.');
    }
    return ChatMessage.fromJson(
      await _postObject(
        'conversations/$conversationId/messages/',
        {'body': trimmed},
      ),
    );
  }

  @override
  Future<void> markConversationRead(String conversationId) async {
    await _post('conversations/$conversationId/read/', {});
  }

  @override
  Future<List<AppNotification>> getNotifications() async {
    final response = await client.get<dynamic>('notifications/');
    return _paginatedResults(
      response.data,
      AppNotification.fromJson,
      'Notifications indisponibles.',
    );
  }

  @override
  Future<int> getNotificationUnreadCount() async {
    final response = await client.get<dynamic>('notifications/unread-count/');
    final data = objectData(response.data);
    final count = data['unread_count'];
    if (count is! int || count < 0) {
      throw const FormatException('Compteur de notifications incorrect.');
    }
    return count;
  }

  @override
  Future<AppNotification> markNotificationRead(String notificationId) async {
    return AppNotification.fromJson(
      await _postObject('notifications/$notificationId/read/', {}),
    );
  }

  @override
  Future<void> markAllNotificationsRead() async {
    await _post('notifications/read-all/', {});
  }

  @override
  Future<void> deleteNotification(String notificationId) async {
    final csrf = await client.get<dynamic>('csrf/');
    final token = objectData(csrf.data)['csrfToken'];
    if (token is! String || token.isEmpty) {
      throw const FormatException('Protection CSRF indisponible.');
    }
    await client.delete<dynamic>(
      'notifications/$notificationId/',
      options: Options(headers: {'X-CSRFToken': token}),
    );
  }

  @override
  Future<void> logout() async {
    // Keep the session when the server cannot confirm revocation; allow retry.
    await _post('auth/logout/', {});
    await cookies.deleteAll();
    _sessionId = null;
    await sessionStore.clear();
  }

  @override
  void close() {
    client.close(force: true);
  }
}
