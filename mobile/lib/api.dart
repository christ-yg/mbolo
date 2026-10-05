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
