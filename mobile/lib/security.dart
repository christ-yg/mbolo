import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'auth_contract.dart';

class SecurityPage extends StatefulWidget {
  const SecurityPage({
    super.key,
    required this.api,
    required this.initialAccount,
    required this.onAccountClosed,
  });

  final AuthApi api;
  final Account initialAccount;
  final Future<void> Function() onAccountClosed;

  @override
  State<SecurityPage> createState() => _SecurityPageState();
}

class _SecurityPageState extends State<SecurityPage> {
  List<ConnectedSession> _sessions = <ConnectedSession>[];
  late bool _twoFactorEnabled;
  bool _loading = true;
  bool _working = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _twoFactorEnabled = widget.initialAccount.emailTwoFactorEnabled;
    _load();
  }

  Future<void> _load() async {
    try {
      final account = await widget.api.me();
      final sessions = await widget.api.getConnectedSessions();
      if (!mounted) return;
      setState(() {
        _twoFactorEnabled = account.emailTwoFactorEnabled;
        _sessions = sessions;
        _error = null;
      });
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<String?> _askPassword(String title) async {
    final controller = TextEditingController();
    final password = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: controller,
          obscureText: true,
          autofocus: true,
          decoration: const InputDecoration(
            labelText: 'Mot de passe actuel',
            prefixIcon: Icon(Icons.lock_outline),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () {
              final value = controller.text;
              Navigator.of(dialogContext).pop(
                value.isEmpty ? null : value,
              );
            },
            child: const Text('Confirmer'),
          ),
        ],
      ),
    );
    controller.dispose();
    return password;
  }

  void _notice(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  Future<void> _toggleTwoFactor(bool enabled) async {
    if (_working) return;
    final password = await _askPassword(
      enabled
          ? 'Activer la double authentification'
          : 'Désactiver la double authentification',
    );
    if (password == null || !mounted) return;
    setState(() => _working = true);
    try {
      final value = await widget.api.setEmailTwoFactor(
        enabled: enabled,
        currentPassword: password,
      );
      if (!mounted) return;
      setState(() => _twoFactorEnabled = value);
      _notice(
        value
            ? 'Double authentification activée.'
            : 'Double authentification désactivée.',
      );
    } catch (error) {
      if (mounted) _notice(friendlyError(error));
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Future<void> _revoke(ConnectedSession session) async {
    if (_working || session.current) return;
    final password = await _askPassword('Déconnecter cet appareil');
    if (password == null || !mounted) return;
    setState(() => _working = true);
    try {
      await widget.api.revokeConnectedSession(
        sessionId: session.id,
        currentPassword: password,
      );
      if (!mounted) return;
      setState(() => _sessions.removeWhere((item) => item.id == session.id));
      _notice('Appareil déconnecté avec succès.');
    } catch (error) {
      if (mounted) _notice(friendlyError(error));
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Future<void> _revokeOthers() async {
    if (_working || !_sessions.any((item) => !item.current)) return;
    final password = await _askPassword('Déconnecter les autres appareils');
    if (password == null || !mounted) return;
    setState(() => _working = true);
    try {
      final count = await widget.api.revokeOtherSessions(password);
      if (!mounted) return;
      setState(() => _sessions.removeWhere((item) => !item.current));
      _notice('$count autre${count > 1 ? 's' : ''} session${count > 1 ? 's' : ''} déconnectée${count > 1 ? 's' : ''}.');
    } catch (error) {
      if (mounted) _notice(friendlyError(error));
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Future<void> _changePassword() async {
    final current = TextEditingController();
    final password = TextEditingController();
    final confirmation = TextEditingController();
    final values = await showDialog<List<String>>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Changer le mot de passe'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: current,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'Mot de passe actuel'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: password,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'Nouveau mot de passe'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: confirmation,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'Confirmer le nouveau mot de passe'),
              ),
              const SizedBox(height: 8),
              const Text('Utilise au moins 12 caractères difficiles à deviner.'),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(
              <String>[current.text, password.text, confirmation.text],
            ),
            child: const Text('Modifier'),
          ),
        ],
      ),
    );
    current.dispose();
    password.dispose();
    confirmation.dispose();
    if (values == null || values.any((value) => value.isEmpty) || !mounted) {
      return;
    }
    if (values[1] != values[2] || values[1].length < 12) {
      _notice('Le nouveau mot de passe est trop court ou ne correspond pas.');
      return;
    }
    setState(() => _working = true);
    try {
      final revoked = await widget.api.changePassword(
        currentPassword: values[0],
        newPassword: values[1],
        newPasswordConfirmation: values[2],
      );
      if (!mounted) return;
      setState(() => _sessions.removeWhere((item) => !item.current));
      _notice('Mot de passe modifié. $revoked autre${revoked > 1 ? 's' : ''} session${revoked > 1 ? 's' : ''} fermée${revoked > 1 ? 's' : ''}.');
    } catch (error) {
      if (mounted) _notice(friendlyError(error));
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Future<void> _exportData() async {
    if (_working) return;
    setState(() => _working = true);
    try {
      final data = await widget.api.exportPersonalData();
      final formatted = const JsonEncoder.withIndent('  ').convert(data);
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: const Text('Mes données MBOLO'),
          content: SizedBox(
            width: 560,
            height: 420,
            child: SingleChildScrollView(
              child: SelectableText(formatted),
            ),
          ),
          actions: [
            TextButton.icon(
              onPressed: () async {
                await Clipboard.setData(ClipboardData(text: formatted));
                if (dialogContext.mounted) Navigator.of(dialogContext).pop();
                if (mounted) _notice('Export copié dans le presse-papiers.');
              },
              icon: const Icon(Icons.copy_all_outlined),
              label: const Text('Copier'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: const Text('Fermer'),
            ),
          ],
        ),
      );
    } catch (error) {
      if (mounted) _notice(friendlyError(error));
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Future<String?> _confirmDanger({
    required String title,
    required String explanation,
    required String phrase,
    required String actionLabel,
  }) async {
    final password = TextEditingController();
    final confirmation = TextEditingController();
    final result = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(title),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(explanation),
              const SizedBox(height: 16),
              TextField(
                controller: password,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'Mot de passe actuel',
                ),
              ),
              const SizedBox(height: 12),
              Text('Écris exactement : $phrase'),
              const SizedBox(height: 6),
              TextField(
                controller: confirmation,
                decoration: const InputDecoration(labelText: 'Confirmation'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Annuler'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.error,
            ),
            onPressed: () {
              if (password.text.isEmpty || confirmation.text != phrase) return;
              Navigator.of(dialogContext).pop(password.text);
            },
            child: Text(actionLabel),
          ),
        ],
      ),
    );
    password.dispose();
    confirmation.dispose();
    return result;
  }

  Future<void> _deactivateAccount() async {
    if (_working) return;
    final password = await _confirmDanger(
      title: 'Désactiver mon compte ?',
      explanation:
          'Ton profil disparaîtra de Découvrir et toutes tes sessions seront fermées.',
      phrase: 'DESACTIVER',
      actionLabel: 'Désactiver',
    );
    if (password == null || !mounted) return;
    setState(() => _working = true);
    try {
      await widget.api.deactivateAccount(password);
      if (mounted) await widget.onAccountClosed();
    } catch (error) {
      if (mounted) _notice(friendlyError(error));
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Future<void> _deleteAccount() async {
    if (_working) return;
    final password = await _confirmDanger(
      title: 'Supprimer définitivement mon compte ?',
      explanation:
          'Cette action efface définitivement tes données personnelles et ne peut pas être annulée.',
      phrase: 'SUPPRIMER DEFINITIVEMENT',
      actionLabel: 'Supprimer définitivement',
    );
    if (password == null || !mounted) return;
    setState(() => _working = true);
    try {
      await widget.api.deleteAccount(password);
      if (mounted) await widget.onAccountClosed();
    } catch (error) {
      if (mounted) _notice(friendlyError(error));
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  String _date(DateTime value) {
    final local = value.toLocal();
    return '${local.day.toString().padLeft(2, '0')}/${local.month.toString().padLeft(2, '0')} à ${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 8, 18, 96),
        children: [
          TweenAnimationBuilder<double>(
            tween: Tween<double>(begin: 0, end: 1),
            duration: const Duration(milliseconds: 650),
            curve: Curves.easeOutBack,
            builder: (context, value, child) => Transform.translate(
              offset: Offset(0, 18 * (1 - value)),
              child: Opacity(opacity: value.clamp(0, 1), child: child),
            ),
            child: Container(
            padding: const EdgeInsets.all(22),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF201018), Color(0xFF711B3B), Color(0xFFB92E5C)],
              ),
              borderRadius: BorderRadius.circular(28),
              boxShadow: const [
                BoxShadow(
                  color: Color(0x36201018),
                  blurRadius: 30,
                  offset: Offset(0, 14),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 54,
                      height: 54,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.14),
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: Colors.white.withValues(alpha: 0.24),
                        ),
                      ),
                      child: const Icon(
                        Icons.shield_rounded,
                        color: Colors.white,
                        size: 31,
                      ),
                    ),
                    const Spacer(),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 7,
                      ),
                      decoration: BoxDecoration(
                        color: _twoFactorEnabled
                            ? const Color(0xFF2F8F66)
                            : Colors.white.withValues(alpha: 0.14),
                        borderRadius: BorderRadius.circular(999),
                      ),
                      child: Text(
                        _twoFactorEnabled ? 'PROTECTION FORTE' : 'À RENFORCER',
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w900,
                          fontSize: 11,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                const Text(
                  'Centre de sécurité',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 25,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Protège ton compte, tes échanges et ton identité.',
                  style: TextStyle(color: Colors.white70),
                ),
              ],
            ),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
          ],
          const SizedBox(height: 20),
          Card(
            child: Column(
              children: [
                SwitchListTile(
                  value: _twoFactorEnabled,
                  onChanged: _working || !widget.initialAccount.verified
                      ? null
                      : _toggleTwoFactor,
                  secondary: const Icon(Icons.mark_email_read_outlined),
                  title: const Text('Double authentification e-mail'),
                  subtitle: Text(
                    widget.initialAccount.verified
                        ? 'Un code à 6 chiffres protège chaque nouvelle connexion.'
                        : 'Vérifie ton e-mail avant de l’activer.',
                  ),
                ),
                const Divider(height: 1),
                ListTile(
                  enabled: !_working,
                  leading: const Icon(Icons.password_outlined),
                  title: const Text('Changer mon mot de passe'),
                  subtitle: const Text('Les autres appareils seront déconnectés.'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: _working ? null : _changePassword,
                ),
              ],
            ),
          ),
          const SizedBox(height: 22),
          Row(
            children: [
              Expanded(
                child: Text(
                  'Appareils connectés',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
              ),
              TextButton(
                onPressed: _working ? null : _revokeOthers,
                child: const Text('Tout déconnecter'),
              ),
            ],
          ),
          const SizedBox(height: 8),
          if (_sessions.isEmpty)
            const Card(
              child: Padding(
                padding: EdgeInsets.all(20),
                child: Text('Aucun appareil enregistré pour le moment.'),
              ),
            )
          else
            ..._sessions.indexed.map(
              (entry) {
                final index = entry.$1;
                final session = entry.$2;
                return TweenAnimationBuilder<double>(
                  tween: Tween<double>(begin: 0, end: 1),
                  duration: Duration(milliseconds: 300 + index.clamp(0, 5) * 55),
                  curve: Curves.easeOutCubic,
                  builder: (context, value, child) => Opacity(
                    opacity: value,
                    child: Transform.translate(
                      offset: Offset(16 * (1 - value), 0),
                      child: child,
                    ),
                  ),
                  child: Card(
                    child: ListTile(
                  contentPadding: const EdgeInsets.all(14),
                  leading: Icon(
                    session.current ? Icons.phone_android : Icons.devices,
                    color: session.current ? const Color(0xFFB51F50) : null,
                  ),
                  title: Text(
                    session.device,
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  subtitle: Text(
                    '${session.current ? 'Cet appareil · ' : ''}Vu le ${_date(session.lastSeenAt)}\nEmpreinte réseau ${session.ipFingerprint}',
                  ),
                  isThreeLine: true,
                  trailing: session.current
                      ? const Chip(label: Text('Actuel'))
                      : IconButton(
                          tooltip: 'Déconnecter cet appareil',
                          onPressed: _working ? null : () => _revoke(session),
                          icon: const Icon(Icons.logout),
                        ),
                    ),
                  ),
                );
              },
            ),
          const SizedBox(height: 24),
          Text(
            'Confidentialité et compte',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
          ),
          const SizedBox(height: 10),
          Card(
            child: Column(
              children: [
                ListTile(
                  enabled: !_working,
                  leading: const Icon(Icons.download_outlined),
                  title: const Text('Exporter mes données'),
                  subtitle: const Text('Consulter et copier une archive JSON portable.'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: _working ? null : _exportData,
                ),
                const Divider(height: 1),
                ListTile(
                  enabled: !_working,
                  leading: const Icon(Icons.pause_circle_outline),
                  title: const Text('Désactiver mon compte'),
                  subtitle: const Text('Masquer le profil et fermer les sessions.'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: _working ? null : _deactivateAccount,
                ),
                const Divider(height: 1),
                ListTile(
                  enabled: !_working,
                  textColor: Theme.of(context).colorScheme.error,
                  iconColor: Theme.of(context).colorScheme.error,
                  leading: const Icon(Icons.delete_forever_outlined),
                  title: const Text('Supprimer définitivement'),
                  subtitle: const Text('Effacer le compte et ses données personnelles.'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: _working ? null : _deleteAccount,
                ),
              ],
            ),
          ),
          if (_working) ...[
            const SizedBox(height: 12),
            const LinearProgressIndicator(),
          ],
        ],
      ),
    );
  }
}
