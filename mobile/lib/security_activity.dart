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
  bool _refreshing = false;
  final _search = TextEditingController();
  String _query = '';
  String _outcome = 'all';
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    if (_refreshing || _working) return;
    setState(() { _refreshing = true; _error = null; });
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
      if (mounted) setState(() { _loading = false; _refreshing = false; });
    }
  }

  Future<void> _toggleAlert(bool enabled) async {
    if (_working || _refreshing || _preference == null) return;
    setState(() { _working = true; _error = null; });
    try {
      final password = await showDialog<String>(context: context,
        builder: (_) => const _PasswordConfirmation());
      if (password == null || password.trim().isEmpty || !mounted) return;
      final preference = await widget.api.updateLoginAlertPreference(
        enabled: enabled, currentPassword: password,
      );
      if (!mounted) return;
      setState(() => _preference = preference);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(enabled
        ? 'Alertes de connexion par e-mail activées.'
        : 'Alertes e-mail désactivées. Les alertes internes restent actives.')));
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Activité de sécurité'),
          actions: [IconButton(tooltip: 'Actualiser l’activité',
            onPressed: _refreshing || _working ? null : _load,
            icon: const Icon(Icons.refresh))],
          bottom: const TabBar(
            tabs: [Tab(text: 'Connexions'), Tab(text: 'Journal')],
          ),
        ),
        body: _loading ? const Center(child: CircularProgressIndicator()) : Column(
          children: [
            if (MediaQuery.viewInsetsOf(context).bottom == 0) SwitchListTile(
              value: _preference?.emailEnabled ?? false,
              onChanged: _working || _refreshing || _preference == null ? null : _toggleAlert,
              secondary: const Icon(Icons.mark_email_read_outlined),
              title: const Text('Alertes de connexion par e-mail'),
              subtitle: const Text('Les notifications internes restent toujours actives.'),
            ),
            if (_refreshing) const LinearProgressIndicator(),
            if (_working) const Text('Confirmation de sécurité en cours…'),
            Padding(padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: TextField(controller: _search, textInputAction: TextInputAction.done,
                onSubmitted: (_) => FocusScope.of(context).unfocus(),
                decoration: InputDecoration(labelText: 'Rechercher dans l’activité',
                  prefixIcon: const Icon(Icons.search),
                  suffixIcon: _query.isEmpty ? null : IconButton(tooltip: 'Effacer la recherche',
                    icon: const Icon(Icons.clear), onPressed: () => setState(() { _search.clear(); _query = ''; }))),
                onChanged: (value) => setState(() => _query = value.trim().toLowerCase()))),
            const Text('Recherche dans les événements chargés.'),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.all(12),
                child: Column(children: [
                  Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                  TextButton(onPressed: _refreshing || _working ? null : _load, child: const Text('Réessayer')),
                ]),
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

  bool _matches(String value) => _query.isEmpty || value.toLowerCase().contains(_query);

  Widget _historyList({required int count, required String empty,
    required Widget Function(BuildContext, int) itemBuilder}) => RefreshIndicator(
    onRefresh: _load,
    child: ListView.separated(physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(18), itemCount: count == 0 ? 1 : count,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: count == 0 ? (_, __) => Padding(padding: const EdgeInsets.all(24),
        child: Text(empty, textAlign: TextAlign.center)) : itemBuilder),
  );

  Widget _loginList() {
    final items = _logins.where((item) => _matches(
      '${item.device} ${_method(item.method)} ${item.ipFingerprint} ${_date(item.createdAt)}')).toList();
    return _historyList(count: items.length,
      empty: _logins.isEmpty ? 'Aucune connexion enregistrée.' : 'Aucune connexion ne correspond à ta recherche.',
      itemBuilder: (context, index) {
        final item = items[index];
        return Card(child: ListTile(
          leading: const Icon(Icons.devices), title: Text(item.device,
            style: const TextStyle(fontWeight: FontWeight.w800)),
          subtitle: Text('${_method(item.method)} · ${_date(item.createdAt)}\nEmpreinte ${item.ipFingerprint}'),
          isThreeLine: true,
        ));
      });
  }

  Widget _eventList() {
    final items = _events.where((item) => (_outcome == 'all' ||
      (_outcome == 'other' ? !['success', 'failure', 'blocked', 'accepted'].contains(item.outcome) : item.outcome == _outcome)) &&
      _matches('${_eventLabel(item.event)} ${_reasonLabel(item.reason)} ${_date(item.createdAt)}')).toList();
    const filters = {'all': 'Tout', 'success': 'Réussites', 'failure': 'Refus',
      'blocked': 'Bloqués', 'accepted': 'Acceptés', 'other': 'Autres'};
    return Column(children: [
      SingleChildScrollView(scrollDirection: Axis.horizontal, padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Row(children: filters.entries.map((entry) => Padding(padding: const EdgeInsets.only(right: 6),
          child: ChoiceChip(label: Text(entry.value), selected: _outcome == entry.key,
            onSelected: (_) => setState(() => _outcome = entry.key)))).toList())),
      Text('${items.length} événement(s) affiché(s)'),
      Expanded(child: _historyList(count: items.length,
        empty: _events.isEmpty ? 'Aucun événement de sécurité.' : 'Aucun événement ne correspond aux filtres.',
        itemBuilder: (context, index) {
          final item = items[index];
          return Card(child: ListTile(
            leading: Icon(item.outcome == 'success' ? Icons.check_circle_outline : Icons.info_outline),
            title: Text(_eventLabel(item.event), style: const TextStyle(fontWeight: FontWeight.w800)),
            subtitle: Text('${_reasonLabel(item.reason)} · ${_date(item.createdAt)}'),
            trailing: Text(_outcomeLabel(item.outcome)),
          ));
        })),
    ]);
  }

  String _method(String value) => switch (value) {
    'email_2fa' => 'Double authentification', 'password' => 'Mot de passe', _ => 'Autre méthode',
  };
  String _outcomeLabel(String value) => switch (value) {
    'success' => 'Réussi', 'failure' => 'Refusé', 'blocked' => 'Bloqué', 'accepted' => 'Accepté', _ => 'Non précisé',
  };

  String _eventLabel(String value) => switch (value) {
        'auth.login' => 'Connexion au compte',
        'auth.password_change' => 'Modification du mot de passe',
        'auth.email_2fa_settings' => 'Réglage de la double authentification',
        _ => 'Événement de sécurité',
      };

  String _reasonLabel(String value) => switch (value) {
    'authenticated' || 'email_2fa_confirmed' => 'Authentification réussie',
    'invalid_credentials' => 'Identifiants incorrects',
    'rate_limited' => 'Trop de tentatives',
    'invalid_or_expired_code' => 'Code invalide ou expiré',
    'password_changed' => 'Mot de passe modifié',
    'other_sessions_revoked' => 'Autres sessions révoquées',
    'enabled' => 'Option activée', 'disabled' => 'Option désactivée',
    'session_destroyed' => 'Session fermée',
    'code_sent' => 'Code de confirmation envoyé',
    'generic_response' => 'Demande prise en compte',
    _ => 'Autre motif de sécurité',
  };

  String _date(DateTime value) {
    final local = value.toLocal();
    return '${local.day.toString().padLeft(2, '0')}/${local.month.toString().padLeft(2, '0')}/${local.year} ${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}';
  }
}

class _PasswordConfirmation extends StatefulWidget {
  const _PasswordConfirmation();
  @override
  State<_PasswordConfirmation> createState() => _PasswordConfirmationState();
}

class _PasswordConfirmationState extends State<_PasswordConfirmation> {
  final _controller = TextEditingController();
  @override
  void dispose() { _controller.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Confirmer cette modification'),
    content: TextField(controller: _controller, obscureText: true, autofocus: true,
      enableSuggestions: false, autocorrect: false,
      onChanged: (_) => setState(() {}),
      decoration: const InputDecoration(labelText: 'Mot de passe actuel', prefixIcon: Icon(Icons.lock_outline))),
    actions: [
      TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Annuler')),
      FilledButton(onPressed: _controller.text.trim().isEmpty ? null : () => Navigator.of(context).pop(_controller.text),
        child: const Text('Confirmer')),
    ],
  );
}
