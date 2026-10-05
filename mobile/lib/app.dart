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

enum _AuthMode { login, register, reset }

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
  final _passwordConfirmation = TextEditingController();
  final _code = TextEditingController();
  Account? _account;
  LoginResult? _challenge;
  _AuthMode _mode = _AuthMode.login;
  bool _busy = false;
  bool _hidePassword = true;
  bool _acceptTerms = false;
  bool _confirmAdult = false;
  String? _error;
  String? _notice;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _passwordConfirmation.dispose();
    _code.dispose();
    widget.api.close();
    super.dispose();
  }

  void _selectMode(_AuthMode mode) {
    setState(() {
      _mode = mode;
      _challenge = null;
      _error = null;
      _notice = null;
      _password.clear();
      _passwordConfirmation.clear();
      _code.clear();
    });
  }

  Future<void> _submit() async {
    if (_busy || !(_form.currentState?.validate() ?? false)) return;
    if (_mode == _AuthMode.register && (!_acceptTerms || !_confirmAdult)) {
      setState(() {
        _error = 'Confirme ton âge et accepte les conditions pour continuer.';
      });
      return;
    }

    setState(() {
      _busy = true;
      _error = null;
      _notice = null;
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
      } else if (_mode == _AuthMode.register) {
        await widget.api.register(
          email: _email.text,
          password: _password.text,
          passwordConfirmation: _passwordConfirmation.text,
          acceptTerms: _acceptTerms,
          confirmAdult: _confirmAdult,
        );
        if (!mounted) return;
        _password.clear();
        _passwordConfirmation.clear();
        setState(() {
          _mode = _AuthMode.login;
          _acceptTerms = false;
          _confirmAdult = false;
          _notice =
              'Compte créé. Consulte ton e-mail pour vérifier ton adresse, puis connecte-toi.';
        });
      } else if (_mode == _AuthMode.reset) {
        await widget.api.requestPasswordReset(_email.text);
        if (!mounted) return;
        setState(() {
          _mode = _AuthMode.login;
          _notice =
              'Si cette adresse existe, les instructions de réinitialisation ont été envoyées.';
        });
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

  String get _title {
    if (_challenge != null) return 'Confirme ta connexion';
    switch (_mode) {
      case _AuthMode.register:
        return 'Crée ton compte MBOLO';
      case _AuthMode.reset:
        return 'Retrouve ton compte';
      case _AuthMode.login:
        return 'Une rencontre commence ici.';
    }
  }

  String get _primaryLabel {
    if (_challenge != null) return 'Confirmer';
    switch (_mode) {
      case _AuthMode.register:
        return 'Créer mon compte';
      case _AuthMode.reset:
        return 'Envoyer les instructions';
      case _AuthMode.login:
        return 'Se connecter';
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_account != null) {
      return MboloHome(
        account: _account!,
        api: widget.api,
        onLogout: _logout,
      );
    }

    final showPassword =
        _challenge == null && _mode != _AuthMode.reset;
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
                      _title,
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
                        validator: (value) => (value ?? '').trim().isEmpty
                            ? 'Entre ton code.'
                            : null,
                      ),
                    ] else ...[
                      Text(
                        _mode == _AuthMode.login
                            ? 'Retrouve ton compte MBOLO, comme sur le site.'
                            : _mode == _AuthMode.register
                                ? 'Rejoins une communauté pensée pour des rencontres sincères.'
                                : 'Nous t’enverrons un lien sécurisé si le compte existe.',
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
                        validator: (value) =>
                            (value ?? '').trim().contains('@')
                                ? null
                                : 'Entre ton adresse e-mail.',
                      ),
                      if (showPassword) ...[
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
                          validator: (value) {
                            if ((value ?? '').isEmpty) {
                              return 'Entre ton mot de passe.';
                            }
                            if (_mode == _AuthMode.register &&
                                value!.length < 12) {
                              return 'Utilise au moins 12 caractères.';
                            }
                            return null;
                          },
                        ),
                      ],
                      if (_mode == _AuthMode.register) ...[
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _passwordConfirmation,
                          enabled: !_busy,
                          obscureText: _hidePassword,
                          autocorrect: false,
                          enableSuggestions: false,
                          autofillHints: const [AutofillHints.newPassword],
                          decoration: const InputDecoration(
                            labelText: 'Confirmer le mot de passe',
                          ),
                          validator: (value) => value == _password.text
                              ? null
                              : 'Les mots de passe ne correspondent pas.',
                        ),
                        CheckboxListTile(
                          contentPadding: EdgeInsets.zero,
                          value: _confirmAdult,
                          onChanged: _busy
                              ? null
                              : (value) => setState(() {
                                  _confirmAdult = value ?? false;
                                }),
                          title: const Text(
                            'Je confirme avoir au moins 18 ans.',
                          ),
                          controlAffinity: ListTileControlAffinity.leading,
                        ),
                        CheckboxListTile(
                          contentPadding: EdgeInsets.zero,
                          value: _acceptTerms,
                          onChanged: _busy
                              ? null
                              : (value) => setState(() {
                                  _acceptTerms = value ?? false;
                                }),
                          title: const Text(
                            'J’accepte les conditions d’utilisation.',
                          ),
                          controlAffinity: ListTileControlAffinity.leading,
                        ),
                      ],
                    ],
                    const SizedBox(height: 24),
                    FilledButton(
                      onPressed: _busy ? null : _submit,
                      child: Text(_primaryLabel),
                    ),
                    if (_challenge != null)
                      TextButton(
                        onPressed: _busy
                            ? null
                            : () => _selectMode(_AuthMode.login),
                        child: const Text('Revenir à la connexion'),
                      )
                    else if (_mode == _AuthMode.login) ...[
                      TextButton(
                        onPressed: _busy
                            ? null
                            : () => _selectMode(_AuthMode.register),
                        child: const Text('Créer un compte'),
                      ),
                      TextButton(
                        onPressed: _busy
                            ? null
                            : () => _selectMode(_AuthMode.reset),
                        child: const Text('Mot de passe oublié ?'),
                      ),
                    ] else
                      TextButton(
                        onPressed: _busy
                            ? null
                            : () => _selectMode(_AuthMode.login),
                        child: const Text('J’ai déjà un compte'),
                      ),
                    if (_busy)
                      const Padding(
                        padding: EdgeInsets.all(16),
                        child: Center(child: CircularProgressIndicator()),
                      ),
                    if (_notice != null)
                      Semantics(
                        liveRegion: true,
                        child: Padding(
                          padding: const EdgeInsets.only(top: 16),
                          child: Text(
                            _notice!,
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.primary,
                            ),
                          ),
                        ),
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
