import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'auth_contract.dart';
import 'home.dart';

TextTheme _mboloTextTheme(Brightness brightness) {
  final typography = Typography.material2021();
  final base = brightness == Brightness.dark
      ? typography.white
      : typography.black;
  return base.copyWith(
    displayLarge: base.displayLarge?.copyWith(
      fontWeight: FontWeight.w800,
      height: 1.02,
      letterSpacing: -1.8,
    ),
    displayMedium: base.displayMedium?.copyWith(
      fontWeight: FontWeight.w800,
      height: 1.04,
      letterSpacing: -1.45,
    ),
    displaySmall: base.displaySmall?.copyWith(
      fontWeight: FontWeight.w800,
      height: 1.06,
      letterSpacing: -1.15,
    ),
    headlineLarge: base.headlineLarge?.copyWith(
      fontWeight: FontWeight.w800,
      height: 1.08,
      letterSpacing: -1.05,
    ),
    headlineMedium: base.headlineMedium?.copyWith(
      fontWeight: FontWeight.w800,
      height: 1.1,
      letterSpacing: -.85,
    ),
    headlineSmall: base.headlineSmall?.copyWith(
      fontWeight: FontWeight.w800,
      height: 1.13,
      letterSpacing: -.55,
    ),
    titleLarge: base.titleLarge?.copyWith(
      fontWeight: FontWeight.w800,
      height: 1.18,
      letterSpacing: -.35,
    ),
    titleMedium: base.titleMedium?.copyWith(
      fontWeight: FontWeight.w700,
      letterSpacing: -.18,
    ),
    titleSmall: base.titleSmall?.copyWith(
      fontWeight: FontWeight.w700,
      letterSpacing: -.08,
    ),
    bodyLarge: base.bodyLarge?.copyWith(height: 1.5, letterSpacing: -.12),
    bodyMedium: base.bodyMedium?.copyWith(height: 1.48, letterSpacing: -.08),
    bodySmall: base.bodySmall?.copyWith(height: 1.42),
    labelLarge: base.labelLarge?.copyWith(
      fontWeight: FontWeight.w800,
      letterSpacing: -.08,
    ),
    labelMedium: base.labelMedium?.copyWith(fontWeight: FontWeight.w700),
    labelSmall: base.labelSmall?.copyWith(fontWeight: FontWeight.w600),
  );
}

class MboloApp extends StatefulWidget {
  const MboloApp({super.key, this.api, this.demo = false});
  final bool demo;
  final AuthApi? api;

  @override
  State<MboloApp> createState() => _MboloAppState();
}

class _MboloAppState extends State<MboloApp> {
  static const _storage = FlutterSecureStorage();
  ThemeMode _themeMode = ThemeMode.system;

  @override
  void initState() {
    super.initState();
    _restoreTheme();
  }

  Future<void> _restoreTheme() async {
    final saved = await _storage.read(key: 'mbolo_theme_mode');
    if (!mounted) return;
    setState(() => _themeMode = switch (saved) {
      'light' => ThemeMode.light,
      'dark' => ThemeMode.dark,
      _ => ThemeMode.system,
    });
  }

  Future<void> _setTheme(ThemeMode mode) async {
    setState(() => _themeMode = mode);
    await _storage.write(key: 'mbolo_theme_mode', value: mode.name);
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MBOLO',
      themeMode: _themeMode,
      builder: (context, child) => widget.demo
          ? Banner(
              message: 'DÉMO',
              location: BannerLocation.topEnd,
              child: child!,
            )
          : child!,
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        textTheme: _mboloTextTheme(Brightness.light),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF9C2455),
          primary: const Color(0xFF9C2455),
          secondary: const Color(0xFFC88A3D),
          surface: const Color(0xFFFFFCFD),
        ),
        scaffoldBackgroundColor: const Color(0xFFFFF8FA),
        pageTransitionsTheme: const PageTransitionsTheme(
          builders: {
            TargetPlatform.android: _MboloPageTransitionsBuilder(),
            TargetPlatform.iOS: _MboloPageTransitionsBuilder(),
          },
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFFFFF7F9),
          surfaceTintColor: Colors.transparent,
          elevation: 0,
          centerTitle: false,
        ),
        cardTheme: const CardThemeData(
          color: Colors.white,
          elevation: 0,
          margin: EdgeInsets.zero,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(28)),
            side: BorderSide(color: Color(0x0FB51F50)),
          ),
        ),
        navigationBarTheme: const NavigationBarThemeData(
          backgroundColor: Colors.white,
          indicatorColor: Color(0xFFFFD8E3),
          height: 76,
          elevation: 0,
          labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            minimumSize: const Size(0, 54),
            textStyle: const TextStyle(
              fontWeight: FontWeight.w800,
              letterSpacing: -.15,
            ),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(18),
            ),
          ),
        ),
        chipTheme: const ChipThemeData(
          backgroundColor: Color(0xFFFFEDF2),
          side: BorderSide.none,
          shape: StadiumBorder(),
        ),
        inputDecorationTheme: const InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.all(Radius.circular(18)),
            borderSide: BorderSide.none,
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.all(Radius.circular(18)),
            borderSide: BorderSide(color: Color(0x1FB51F50)),
          ),
        ),
      ),
      darkTheme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        textTheme: _mboloTextTheme(Brightness.dark),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFFF76A8),
          brightness: Brightness.dark,
          primary: const Color(0xFFFF76A8),
          secondary: const Color(0xFFF3C17C),
          surface: const Color(0xFF1C1219),
        ),
        scaffoldBackgroundColor: const Color(0xFF0D080C),
        pageTransitionsTheme: const PageTransitionsTheme(
          builders: {
            TargetPlatform.android: _MboloPageTransitionsBuilder(),
            TargetPlatform.iOS: _MboloPageTransitionsBuilder(),
          },
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0D080C),
          surfaceTintColor: Colors.transparent,
          elevation: 0,
        ),
        cardTheme: const CardThemeData(
          color: Color(0xFF1C1219),
          elevation: 0,
          margin: EdgeInsets.zero,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(28)),
            side: BorderSide(color: Color(0x2EFFA4C4)),
          ),
        ),
        navigationBarTheme: const NavigationBarThemeData(
          backgroundColor: Color(0xFF171016),
          indicatorColor: Color(0xFF51263B),
          height: 76,
          elevation: 0,
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            minimumSize: const Size(0, 54),
            textStyle: const TextStyle(
              fontWeight: FontWeight.w800,
              letterSpacing: -.15,
            ),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(18),
            ),
          ),
        ),
        chipTheme: const ChipThemeData(
          backgroundColor: Color(0xFF34202C),
          side: BorderSide(color: Color(0x22FFA4C4)),
          shape: StadiumBorder(),
        ),
        inputDecorationTheme: const InputDecorationTheme(
          filled: true,
          fillColor: Color(0xFF21151D),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.all(Radius.circular(18)),
            borderSide: BorderSide.none,
          ),
        ),
      ),
      home: widget.api == null
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
          : SessionScreen(
              api: widget.api!,
              restoreSession: !widget.demo,
              themeMode: _themeMode,
              onThemeChanged: _setTheme,
            ),
    );
  }
}

class _MboloPageTransitionsBuilder extends PageTransitionsBuilder {
  const _MboloPageTransitionsBuilder();

  @override
  Widget buildTransitions<T>(
    PageRoute<T> route,
    BuildContext context,
    Animation<double> animation,
    Animation<double> secondaryAnimation,
    Widget child,
  ) {
    if (MediaQuery.maybeOf(context)?.disableAnimations ?? false) return child;
    final curved = CurvedAnimation(
      parent: animation,
      curve: Curves.easeOutCubic,
      reverseCurve: Curves.easeInCubic,
    );
    return FadeTransition(
      opacity: curved,
      child: SlideTransition(
        position: Tween<Offset>(
          begin: const Offset(0.035, 0.018),
          end: Offset.zero,
        ).animate(curved),
        child: ScaleTransition(
          scale: Tween<double>(begin: 0.992, end: 1).animate(curved),
          child: child,
        ),
      ),
    );
  }
}

enum _AuthMode { login, register, reset, resetConfirm }

int _passwordStrength(String password) {
  var score = 0;
  if (password.length >= 12) score++;
  if (RegExp(r'[a-z]').hasMatch(password) &&
      RegExp(r'[A-Z]').hasMatch(password)) {
    score++;
  }
  if (RegExp(r'\d').hasMatch(password)) score++;
  if (RegExp(r'[^a-zA-Z0-9]').hasMatch(password)) score++;
  return score;
}

class SessionScreen extends StatefulWidget {
  const SessionScreen({
    super.key,
    required this.api,
    this.restoreSession = true,
    required this.themeMode,
    required this.onThemeChanged,
  });
  final AuthApi api;
  final bool restoreSession;
  final ThemeMode themeMode;
  final ValueChanged<ThemeMode> onThemeChanged;

  @override
  State<SessionScreen> createState() => _SessionScreenState();
}

class _SessionScreenState extends State<SessionScreen> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _passwordConfirmation = TextEditingController();
  final _resetLink = TextEditingController();
  final _code = TextEditingController();
  Account? _account;
  LoginResult? _challenge;
  _AuthMode _mode = _AuthMode.login;
  bool _busy = false;
  late bool _restoring;
  bool _hidePassword = true;
  bool _acceptTerms = false;
  bool _confirmAdult = false;
  String? _error;
  String? _notice;

  @override
  void initState() {
    super.initState();
    _restoring = widget.restoreSession;
    if (_restoring) _restoreSession();
  }

  Future<void> _restoreSession() async {
    try {
      final account = await widget.api.restoreSession();
      if (mounted) setState(() => _account = account);
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _restoring = false);
    }
  }

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _passwordConfirmation.dispose();
    _resetLink.dispose();
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
      _resetLink.clear();
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
      } else if (_mode == _AuthMode.resetConfirm) {
        final link = Uri.tryParse(_resetLink.text.trim());
        final uid = link?.queryParameters['uid'] ?? '';
        final token = link?.queryParameters['token'] ?? '';
        if (link == null || !link.hasScheme || uid.isEmpty || token.isEmpty) {
          throw const FormatException('Lien de réinitialisation incomplet.');
        }
        await widget.api.confirmPasswordReset(
          uid: uid,
          token: token,
          password: _password.text,
          passwordConfirmation: _passwordConfirmation.text,
        );
        if (!mounted) return;
        _password.clear();
        _passwordConfirmation.clear();
        _resetLink.clear();
        setState(() {
          _mode = _AuthMode.login;
          _notice = 'Mot de passe modifié. Tu peux maintenant te connecter.';
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

  Future<void> _accountClosed() async {
    if (!mounted) return;
    setState(() {
      _account = null;
      _challenge = null;
      _password.clear();
    });
  }

  String get _title {
    if (_challenge != null) return 'Confirme ta connexion';
    switch (_mode) {
      case _AuthMode.register:
        return 'Crée ton compte MBOLO';
      case _AuthMode.reset:
        return 'Retrouve ton compte';
      case _AuthMode.resetConfirm:
        return 'Choisis un nouveau mot de passe';
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
      case _AuthMode.resetConfirm:
        return 'Modifier mon mot de passe';
      case _AuthMode.login:
        return 'Se connecter';
    }
  }

  String get _subtitle {
    if (_challenge != null) {
      return 'Une dernière vérification protège ton compte et tes rencontres.';
    }
    return switch (_mode) {
      _AuthMode.register =>
        'Crée un profil authentique et découvre des rencontres sincères.',
      _AuthMode.reset =>
        'Récupère ton accès grâce à un lien sécurisé et temporaire.',
      _AuthMode.resetConfirm =>
        'Choisis un mot de passe fort pour protéger ton expérience.',
      _AuthMode.login =>
        'Des connexions vraies, une expérience sûre, pensée pour toi.',
    };
  }

  @override
  Widget build(BuildContext context) {
    if (_restoring) {
      return Scaffold(
        body: SafeArea(
          child: Center(
            child: Semantics(
              label: 'Restauration de la session sécurisée',
              child: const CircularProgressIndicator(),
            ),
          ),
        ),
      );
    }
    if (_account != null) {
      return MboloHome(
        account: _account!,
        api: widget.api,
        onLogout: _logout,
        onAccountClosed: _accountClosed,
        themeMode: widget.themeMode,
        onThemeChanged: widget.onThemeChanged,
      );
    }

    final showPassword = _challenge == null &&
        _mode != _AuthMode.reset &&
        _mode != _AuthMode.resetConfirm;
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
                    AnimatedSwitcher(
                      duration: const Duration(milliseconds: 420),
                      switchInCurve: Curves.easeOutCubic,
                      transitionBuilder: (child, animation) => FadeTransition(
                        opacity: animation,
                        child: SlideTransition(
                          position: Tween<Offset>(
                            begin: const Offset(0.04, 0),
                            end: Offset.zero,
                          ).animate(animation),
                          child: child,
                        ),
                      ),
                      child: _AuthHero(
                        key: ValueKey<String>('${_mode.name}-${_challenge != null}'),
                        title: _title,
                        subtitle: _subtitle,
                        icon: _challenge != null
                            ? Icons.verified_user_rounded
                            : _mode == _AuthMode.register
                                ? Icons.favorite_rounded
                                : _mode == _AuthMode.login
                                    ? Icons.auto_awesome_rounded
                                    : Icons.lock_reset_rounded,
                      ),
                    ),
                    const SizedBox(height: 24),
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
                      if (_mode == _AuthMode.resetConfirm) ...[
                        TextFormField(
                          controller: _resetLink,
                          enabled: !_busy,
                          keyboardType: TextInputType.url,
                          autocorrect: false,
                          decoration: const InputDecoration(
                            labelText: 'Lien de réinitialisation',
                          ),
                          validator: (value) {
                            final uri = Uri.tryParse((value ?? '').trim());
                            return uri != null &&
                                    uri.hasScheme &&
                                    (uri.queryParameters['uid'] ?? '').isNotEmpty &&
                                    (uri.queryParameters['token'] ?? '').isNotEmpty
                                ? null
                                : 'Colle le lien complet reçu par e-mail.';
                          },
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _password,
                          enabled: !_busy,
                          obscureText: _hidePassword,
                          autocorrect: false,
                          enableSuggestions: false,
                          autofillHints: const [AutofillHints.newPassword],
                          decoration: const InputDecoration(
                            labelText: 'Nouveau mot de passe',
                          ),
                          onChanged: (_) => setState(() {}),
                          validator: (value) => (value ?? '').length >= 12
                              ? null
                              : 'Utilise au moins 12 caractères.',
                        ),
                        const SizedBox(height: 10),
                        _PasswordStrengthMeter(password: _password.text),
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _passwordConfirmation,
                          enabled: !_busy,
                          obscureText: _hidePassword,
                          autocorrect: false,
                          enableSuggestions: false,
                          autofillHints: const [AutofillHints.newPassword],
                          decoration: const InputDecoration(
                            labelText: 'Confirmer le nouveau mot de passe',
                          ),
                          validator: (value) => value == _password.text
                              ? null
                              : 'Les mots de passe ne correspondent pas.',
                        ),
                      ] else TextFormField(
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
                          onChanged: _mode == _AuthMode.register
                              ? (_) => setState(() {})
                              : null,
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
                        const SizedBox(height: 10),
                        _PasswordStrengthMeter(password: _password.text),
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
                      TextButton(
                        onPressed: _busy
                            ? null
                            : () => _selectMode(_AuthMode.resetConfirm),
                        child: const Text('J’ai reçu mon lien'),
                      ),
                    ] else if (_mode == _AuthMode.reset) ...[
                      TextButton(
                        onPressed: _busy
                            ? null
                            : () => _selectMode(_AuthMode.resetConfirm),
                        child: const Text('J’ai reçu mon lien'),
                      ),
                      TextButton(
                        onPressed: _busy
                            ? null
                            : () => _selectMode(_AuthMode.login),
                        child: const Text('J’ai déjà un compte'),
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

class _AuthHero extends StatelessWidget {
  const _AuthHero({
    super.key,
    required this.title,
    required this.subtitle,
    required this.icon,
  });

  final String title;
  final String subtitle;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final compact = MediaQuery.sizeOf(context).height < 720;
    final reduceMotion = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    return TweenAnimationBuilder<double>(
      tween: Tween<double>(begin: 0.96, end: 1),
      duration: reduceMotion
          ? Duration.zero
          : const Duration(milliseconds: 620),
      curve: Curves.easeOutBack,
      builder: (context, value, child) => Transform.scale(
        scale: value,
        child: child,
      ),
      child: Container(
        padding: EdgeInsets.all(compact ? 16 : 24),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF351020), Color(0xFF851843), Color(0xFFD95675)],
          ),
          borderRadius: BorderRadius.circular(32),
          boxShadow: const [
            BoxShadow(
              color: Color(0x428B1744),
              blurRadius: 36,
              offset: Offset(0, 16),
            ),
          ],
        ),
        child: compact
            ? Row(
                children: [
                  _AuthHeroIcon(icon: icon, size: 46),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          title,
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                color: Colors.white,
                                fontWeight: FontWeight.w900,
                              ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          subtitle,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: Color(0xFFFFEAF0),
                            height: 1.3,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              )
            : Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      _AuthHeroIcon(icon: icon, size: 52),
                      const Spacer(),
                      const Text(
                        'MBOLO',
                        style: TextStyle(
                          color: Color(0xFFFFD9E4),
                          fontWeight: FontWeight.w900,
                          letterSpacing: 2.4,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  Text(
                    title,
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.w900,
                          letterSpacing: -0.8,
                        ),
                  ),
                  const SizedBox(height: 9),
                  Text(
                    subtitle,
                    style: const TextStyle(
                      color: Color(0xFFFFEAF0),
                      height: 1.45,
                      fontSize: 15,
                    ),
                  ),
                ],
              ),
      ),
    );
  }
}

class _PasswordStrengthMeter extends StatelessWidget {
  const _PasswordStrengthMeter({required this.password});

  final String password;

  @override
  Widget build(BuildContext context) {
    final score = _passwordStrength(password);
    final scheme = Theme.of(context).colorScheme;
    final reduceMotion = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    final label = switch (score) {
      4 => 'Très robuste',
      3 => 'Robuste',
      2 => 'À renforcer',
      1 => 'Faible',
      _ => 'Commence par 12 caractères',
    };
    final color = switch (score) {
      4 => const Color(0xFF247A58),
      3 => const Color(0xFF3B8060),
      2 => const Color(0xFFB27316),
      _ => scheme.error,
    };

    return Semantics(
      liveRegion: true,
      label: 'Robustesse du mot de passe : $label, $score critères sur 4.',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: List<Widget>.generate(
              4,
              (index) => Expanded(
                child: AnimatedContainer(
                  duration: reduceMotion
                      ? Duration.zero
                      : const Duration(milliseconds: 220),
                  height: 5,
                  margin: EdgeInsets.only(right: index == 3 ? 0 : 6),
                  decoration: BoxDecoration(
                    color: index < score ? color : scheme.outlineVariant,
                    borderRadius: BorderRadius.circular(999),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 7),
          Text(
            '$label · majuscule, minuscule, chiffre et symbole',
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: score == 0 ? scheme.onSurfaceVariant : color,
                  fontWeight: FontWeight.w700,
                ),
          ),
        ],
      ),
    );
  }
}

class _AuthHeroIcon extends StatelessWidget {
  const _AuthHeroIcon({required this.icon, required this.size});

  final IconData icon;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.14),
        shape: BoxShape.circle,
        border: Border.all(color: Colors.white.withValues(alpha: 0.24)),
      ),
      child: Icon(icon, color: Colors.white, size: size * 0.54),
    );
  }
}
