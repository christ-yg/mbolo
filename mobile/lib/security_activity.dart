import 'package:flutter/material.dart';

import 'auth_contract.dart';

class SecurityActivityPage extends StatefulWidget {
  const SecurityActivityPage({super.key, required this.api});
  final AuthApi api;

  @override
  State<SecurityActivityPage> createState() => _SecurityActivityPageState();
}

class _SecurityActivityPageState extends State<SecurityActivityPage> {
  List<LoginActivity> _logins = const [];
  List<AccountSecurityEvent> _events = const [];
  LoginAlertPreference? _preference;
  bool _loading = true;
  bool _working = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final values = await Future.wait<Object>([
        widget.api.getLoginActivity(),
        widget.api.getSecurityEvents(),
        widget.api.getLoginAlertPreference(),
      ]);
      if (!mounted) return;
      setState(() {
        _logins = values[0] as List<LoginActivity>;
        _events = values[1] as List<AccountSecurityEvent>;
        _preference = values[2] as LoginAlertPreference;
        _error = null;
      });
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<String?> _password() async {
    final controller = TextEditingController();
    final value = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirmer cette modification'),
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
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(controller.text),
            child: const Text('Confirmer'),
          ),
        ],
      ),
    );
    controller.dispose();
    return value?.trim().isEmpty == true ? null : value;
  }

  Future<void> _toggleAlert(bool enabled) async {
    if (_working) return;
    final password = await _password();
    if (password == null || !mounted) return;
    setState(() => _working = true);
    try {
      final preference = await widget.api.updateLoginAlertPreference(
        enabled: enabled,
        currentPassword: password,
      );
      if (!mounted) return;
      setState(() => _preference = preference);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(enabled
              ? 'Alertes de connexion par e-mail activées.'
              : 'Alertes e-mail désactivées. Les alertes internes restent actives.'),
        ),
      );
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Activité de sécurité'),
          bottom: const TabBar(
            tabs: [Tab(text: 'Connexions'), Tab(text: 'Journal')],
          ),
        ),
        body: Column(
          children: [
            SwitchListTile(
              value: _preference?.emailEnabled ?? false,
              onChanged: _working ? null : _toggleAlert,
              secondary: const Icon(Icons.mark_email_read_outlined),
              title: const Text('Alertes de connexion par e-mail'),
              subtitle: const Text('Les notifications internes restent toujours actives.'),
            ),
            if (_working) const LinearProgressIndicator(),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.all(12),
                child: Text(
                  _error!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ),
            Expanded(
              child: TabBarView(
                children: [_loginList(), _eventList()],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _loginList() => ListView.separated(
        padding: const EdgeInsets.all(18),
        itemCount: _logins.length,
        separatorBuilder: (_, __) => const SizedBox(height: 10),
        itemBuilder: (context, index) {
          final item = _logins[index];
          return Card(
            child: ListTile(
              leading: Icon(item.method == 'email_2fa'
                  ? Icons.verified_user_outlined
                  : Icons.password_outlined),
              title: Text(item.device,
                  style: const TextStyle(fontWeight: FontWeight.w800)),
              subtitle: Text(
                '${item.method == 'email_2fa' ? 'Double authentification' : 'Mot de passe'} · ${_date(item.createdAt)}\nEmpreinte ${item.ipFingerprint}',
              ),
              isThreeLine: true,
            ),
          );
        },
      );

  Widget _eventList() => ListView.separated(
        padding: const EdgeInsets.all(18),
        itemCount: _events.length,
        separatorBuilder: (_, __) => const SizedBox(height: 10),
        itemBuilder: (context, index) {
          final item = _events[index];
          final success = item.outcome == 'success';
          return Card(
            child: ListTile(
              leading: CircleAvatar(
                child: Icon(success ? Icons.check_rounded : Icons.warning_amber),
              ),
              title: Text(_eventLabel(item.event),
                  style: const TextStyle(fontWeight: FontWeight.w800)),
              subtitle: Text('${_reasonLabel(item.reason)} · ${_date(item.createdAt)}'),
              trailing: Text(success ? 'Réussi' : 'Refusé'),
            ),
          );
        },
      );

  String _eventLabel(String value) => switch (value) {
        'auth.login' => 'Connexion au compte',
        'auth.password_change' => 'Modification du mot de passe',
        'auth.email_2fa_settings' => 'Réglage de la double authentification',
        _ => 'Événement de sécurité',
      };

  String _reasonLabel(String value) => value
      .replaceAll('_', ' ')
      .split(' ')
      .where((part) => part.isNotEmpty)
      .map((part) => '${part[0].toUpperCase()}${part.substring(1)}')
      .join(' ');

  String _date(DateTime value) {
    final local = value.toLocal();
    return '${local.day.toString().padLeft(2, '0')}/${local.month.toString().padLeft(2, '0')} ${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}';
  }
}
