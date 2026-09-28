import 'package:dio/dio.dart';

Uri validateOrigin(String value) {
  final uri = Uri.parse(value);
  if (uri.scheme != 'https' ||
      uri.host.isEmpty ||
      uri.userInfo.isNotEmpty ||
      uri.hasQuery ||
      uri.hasFragment ||
      (uri.path.isNotEmpty && uri.path != '/')) {
    throw const FormatException(
      'MBOLO_API_ORIGIN doit être une origine HTTPS.',
    );
  }
  return uri;
}

Map<String, dynamic> objectData(dynamic raw) {
  if (raw is! Map<String, dynamic>) {
    throw const FormatException('Réponse serveur incorrecte.');
  }
  final data = raw.containsKey('data') ? raw['data'] : raw;
  if (data is! Map<String, dynamic>) {
    throw const FormatException('Réponse serveur incomplète.');
  }
  return data;
}

class Account {
  const Account(this.id, this.email, this.verified);
  final String id;
  final String email;
  final bool verified;

  factory Account.fromJson(Map<String, dynamic> data) {
    if (data['id'] is! String ||
        (data['id'] as String).isEmpty ||
        data['email'] is! String ||
        (data['email'] as String).isEmpty) {
      throw const FormatException('Compte incomplet.');
    }
    return Account(
      data['id'] as String,
      data['email'] as String,
      data['isEmailVerified'] == true || data['is_email_verified'] == true,
    );
  }
}

class LoginResult {
  const LoginResult({this.account, this.challenge, this.maskedEmail});
  final Account? account;
  final String? challenge;
  final String? maskedEmail;

  factory LoginResult.fromJson(Map<String, dynamic> data) {
    if (data['requiresTwoFactor'] == true) {
      final token = data['challengeToken'];
      final email = data['maskedEmail'];
      if (token is! String || token.isEmpty || email is! String) {
        throw const FormatException('Confirmation de connexion incomplète.');
      }
      return LoginResult(challenge: token, maskedEmail: email);
    }
    return LoginResult(account: Account.fromJson(data));
  }
}

String friendlyError(Object error) {
  if (error is DioException) {
    final status = error.response?.statusCode;
    if (status == 429)
      return 'Trop de tentatives. Patiente avant de réessayer.';
    if (status == 400 || status == 401) {
      return 'Vérifie tes identifiants ou ton code de confirmation.';
    }
    if (status == 403) return 'Accès refusé. Vérifie ton compte et réessaie.';
    return 'Connexion au serveur impossible. Réessaie dans un instant.';
  }
  return 'La réponse du serveur est invalide. Réessaie plus tard.';
}

abstract class AuthApi {
  Future<LoginResult> login(String email, String password);
  Future<Account> confirm(String challenge, String code);
  Future<Account> me();
  Future<void> logout();
  void close();
}
