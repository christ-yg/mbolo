import 'auth_contract.dart';

/// Local-only demonstration: no HTTP client and no persistent storage.
class DemoApi implements AuthApi {
  static const account = Account('demo', 'demo@mbolo.test', true);
  bool _authenticated = false;

  @override
  Future<LoginResult> login(String email, String password) async {
    if (email.trim() != account.email || password != 'MboloDemo!') {
      throw const FormatException('Identifiants de démonstration incorrects.');
    }
    return const LoginResult(
      challenge: 'demo-challenge',
      maskedEmail: 'demo@mbolo.test',
    );
  }

  @override
  Future<Account> confirm(String challenge, String code) async {
    if (challenge != 'demo-challenge' || code.trim() != '123456') {
      throw const FormatException('Code de démonstration incorrect.');
    }
    _authenticated = true;
    return account;
  }

  @override
  Future<Account> me() async {
    if (!_authenticated) throw const FormatException('Session absente.');
    return account;
  }

  @override
  Future<void> logout() async {
    _authenticated = false;
  }

  @override
  void close() {
    _authenticated = false;
  }
}
