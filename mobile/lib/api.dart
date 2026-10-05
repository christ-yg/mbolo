import 'dart:typed_data';

import 'package:cookie_jar/cookie_jar.dart';
import 'package:dio/dio.dart';
import 'package:dio_cookie_manager/dio_cookie_manager.dart';

import 'auth_contract.dart';
export 'auth_contract.dart';

/// Native Android/iOS only. Cookies deliberately stay in memory in this version.
/// No password, cookie or challenge is logged or written to disk.
class MboloApi implements AuthApi {
  MboloApi(String origin, {Dio? client})
    : origin = validateOrigin(origin),
      client = client ?? Dio() {
    this.client.options = BaseOptions(
      baseUrl: '${this.origin.origin}/api/v1/',
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 20),
      sendTimeout: const Duration(seconds: 20),
      followRedirects: false,
      headers: {'Accept': 'application/json', 'Origin': this.origin.origin},
    );
    this.client.interceptors.add(CookieManager(cookies));
  }

  final Uri origin;
  final Dio client;
  final CookieJar cookies = CookieJar();

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
  Future<void> logout() async {
    // Keep the session when the server cannot confirm revocation; allow retry.
    await _post('auth/logout/', {});
    await cookies.deleteAll();
  }

  @override
  void close() {
    client.close(force: true);
  }
}
