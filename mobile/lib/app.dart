import 'package:flutter/material.dart';
import 'auth_contract.dart';
import 'home.dart';

class MboloApp extends StatelessWidget {
  const MboloApp({super.key, this.api, this.demo = false});
  final bool demo;
  final AuthApi? api;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MBOLO',
      builder: (context, child) => demo
          ? Banner(
              message: 'DÉMO',
              location: BannerLocation.topEnd,
              child: child!,
            )
          : child!,
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF9D3451)),
        scaffoldBackgroundColor: const Color(0xFFFFF8F4),
        inputDecorationTheme: const InputDecorationTheme(
          border: OutlineInputBorder(),
        ),
      ),
      home: api == null
          ? const Scaffold(
              body: SafeArea(
                child: Center(
                  child: Padding(
                    padding: EdgeInsets.all(24),
                    child: Text(
                      'Configuration MBOLO manquante. Configure une origine API HTTPS pour démarrer.',
                    ),
                  ),
                ),
              ),
            )
          : SessionScreen(api: api!),
    );
  }
}

class SessionScreen extends StatefulWidget {
  const SessionScreen({super.key, required this.api});
  final AuthApi api;
  @override
  State<SessionScreen> createState() => _SessionScreenState();
}

class _SessionScreenState extends State<SessionScreen> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _code = TextEditingController();
  Account? _account;
  LoginResult? _challenge;
  bool _busy = false;
  bool _hidePassword = true;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _code.dispose();
    widget.api.close();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_busy || !(_form.currentState?.validate() ?? false)) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      if (_challenge != null) {
        final account = await widget.api.confirm(
          _challenge!.challenge!,
          _code.text,
        );
        if (!mounted) return;
        setState(() {
          _account = account;
          _challenge = null;
        });
        _code.clear();
      } else {
        final result = await widget.api.login(_email.text, _password.text);
        if (!mounted) return;
        _password.clear();
        setState(() {
          _account = result.account;
          _challenge = result.challenge != null ? result : null;
        });
      }
    } catch (error) {
      if (mounted) {
        setState(() {
          _error = friendlyError(error);
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
        });
      }
    }
  }

  Future<void> _logout() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await widget.api.logout();
      if (mounted) {
        setState(() {
          _account = null;
          _challenge = null;
        });
      }
    } catch (error) {
      if (mounted) {
        setState(() {
          _error = friendlyError(error);
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_account != null) {
      return MboloHome(account: _account!, onLogout: _logout);
    }
    return Scaffold(
      appBar: AppBar(title: const Text('MBOLO')),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Form(
                key: _form,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Icon(
                      Icons.favorite_outline,
                      size: 56,
                      color: Color(0xFF9D3451),
                    ),
                    const SizedBox(height: 24),
                    Text(
                      'Une rencontre commence ici.',
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
                    const SizedBox(height: 12),
                    if (_challenge != null) ...[
                      Text(
                        'Entre le code envoyé à ${_challenge!.maskedEmail}.',
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _code,
                        enabled: !_busy,
                        keyboardType: TextInputType.number,
                        autofillHints: const [AutofillHints.oneTimeCode],
                        decoration: const InputDecoration(
                          labelText: 'Code de confirmation',
                        ),
                        validator: (v) => (v ?? '').trim().isEmpty
                            ? 'Entre ton code.'
                            : null,
                      ),
                    ] else ...[
                      const Text(
                        'Retrouve ton compte MBOLO, comme sur le site.',
                      ),
                      const SizedBox(height: 24),
                      TextFormField(
                        controller: _email,
                        enabled: !_busy,
                        keyboardType: TextInputType.emailAddress,
                        autofillHints: const [AutofillHints.username],
                        autocorrect: false,
                        decoration: const InputDecoration(
                          labelText: 'Adresse e-mail',
                        ),
                        validator: (v) => (v ?? '').trim().contains('@')
                            ? null
                            : 'Entre ton adresse e-mail.',
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _password,
                        enabled: !_busy,
                        obscureText: _hidePassword,
                        autocorrect: false,
                        enableSuggestions: false,
                        autofillHints: const [AutofillHints.password],
                        decoration: InputDecoration(
                          labelText: 'Mot de passe',
                          suffixIcon: IconButton(
                            tooltip: _hidePassword
                                ? 'Afficher le mot de passe'
                                : 'Masquer le mot de passe',
                            onPressed: () => setState(() {
                              _hidePassword = !_hidePassword;
                            }),
                            icon: Icon(
                              _hidePassword
                                  ? Icons.visibility
                                  : Icons.visibility_off,
                            ),
                          ),
                        ),
                        validator: (v) => (v ?? '').isEmpty
                            ? 'Entre ton mot de passe.'
                            : null,
                      ),
                    ],
                    const SizedBox(height: 24),
                    FilledButton(
                      onPressed: _busy ? null : _submit,
                      child: Text(
                        _challenge == null ? 'Se connecter' : 'Confirmer',
                      ),
                    ),
                    if (_challenge != null)
                      TextButton(
                        onPressed: _busy
                            ? null
                            : () => setState(() {
                                _challenge = null;
                                _code.clear();
                                _error = null;
                              }),
                        child: const Text('Revenir à la connexion'),
                      ),
                    if (_busy)
                      const Padding(
                        padding: EdgeInsets.all(16),
                        child: Center(child: CircularProgressIndicator()),
                      ),
                    if (_error != null)
                      Semantics(
                        liveRegion: true,
                        child: Padding(
                          padding: const EdgeInsets.only(top: 16),
                          child: Text(
                            _error!,
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.error,
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
