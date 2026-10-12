import 'package:flutter/material.dart';

import 'auth_contract.dart';

class NotificationPreferencesPage extends StatefulWidget {
  const NotificationPreferencesPage({super.key, required this.api});

  final AuthApi api;

  @override
  State<NotificationPreferencesPage> createState() =>
      _NotificationPreferencesPageState();
}

class _NotificationPreferencesPageState
    extends State<NotificationPreferencesPage> {
  NotificationPreferences? _preferences;
  bool _loading = true;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final preferences = await widget.api.getNotificationPreferences();
      if (mounted) {
        setState(() {
          _preferences = preferences;
          _error = null;
        });
      }
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  TimeOfDay _parseTime(String value) {
    final parts = value.split(':');
    return TimeOfDay(hour: int.parse(parts[0]), minute: int.parse(parts[1]));
  }

  String _formatTime(TimeOfDay value) =>
      '${value.hour.toString().padLeft(2, '0')}:'
      '${value.minute.toString().padLeft(2, '0')}';

  Future<void> _pickTime({required bool start}) async {
    final preferences = _preferences;
    if (preferences == null || _saving) return;
    final selected = await showTimePicker(
      context: context,
      initialTime: _parseTime(
        start ? preferences.quietStart : preferences.quietEnd,
      ),
      helpText: start ? 'Début du mode silencieux' : 'Fin du mode silencieux',
    );
    if (selected == null || !mounted) return;
    setState(() {
      _preferences = start
          ? preferences.copyWith(quietStart: _formatTime(selected))
          : preferences.copyWith(quietEnd: _formatTime(selected));
    });
  }

  Future<void> _save() async {
    final preferences = _preferences;
    if (preferences == null || _saving) return;
    if (preferences.quietStart == preferences.quietEnd) {
      setState(() {
        _error = 'Le début et la fin du mode silencieux doivent différer.';
      });
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final saved = await widget.api.updateNotificationPreferences(preferences);
      if (!mounted) return;
      setState(() => _preferences = saved);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Préférences enregistrées.')),
      );
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final preferences = _preferences;
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Préférences de notifications')),
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : preferences == null
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(_error ?? 'Préférences indisponibles.'),
                          const SizedBox(height: 12),
                          FilledButton.tonal(
                            onPressed: _load,
                            child: const Text('Réessayer'),
                          ),
                        ],
                      ),
                    ),
                  )
                : ListView(
                    padding: const EdgeInsets.fromLTRB(18, 12, 18, 32),
                    children: [
                      Container(
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              scheme.primaryContainer,
                              scheme.secondaryContainer,
                            ],
                          ),
                          borderRadius: BorderRadius.circular(28),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              Icons.tune_rounded,
                              size: 34,
                              color: scheme.primary,
                            ),
                            const SizedBox(width: 14),
                            const Expanded(
                              child: Text(
                                'Choisis les activités importantes sans manquer les alertes de sécurité.',
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 18),
                      _PreferenceSwitch(
                        icon: Icons.notifications_active_rounded,
                        title: 'Notifications MBOLO',
                        subtitle: 'Activer les alertes personnalisées',
                        value: preferences.notificationsEnabled,
                        onChanged: (value) => setState(() {
                          _preferences = preferences.copyWith(
                            notificationsEnabled: value,
                          );
                        }),
                      ),
                      const SizedBox(height: 14),
                      Text(
                        'Catégories',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.w900,
                            ),
                      ),
                      const SizedBox(height: 8),
                      _PreferenceSwitch(
                        icon: Icons.chat_bubble_rounded,
                        title: 'Messages',
                        subtitle: 'Nouveaux messages et réactions',
                        value: preferences.messagesEnabled,
                        enabled: preferences.notificationsEnabled,
                        onChanged: (value) => setState(() {
                          _preferences = preferences.copyWith(
                            messagesEnabled: value,
                          );
                        }),
                      ),
                      _PreferenceSwitch(
                        icon: Icons.favorite_rounded,
                        title: 'Matchs',
                        subtitle: 'Nouvelles connexions réciproques',
                        value: preferences.matchesEnabled,
                        enabled: preferences.notificationsEnabled,
                        onChanged: (value) => setState(() {
                          _preferences = preferences.copyWith(
                            matchesEnabled: value,
                          );
                        }),
                      ),
                      _PreferenceSwitch(
                        icon: Icons.auto_awesome_rounded,
                        title: 'Likes et Super Likes',
                        subtitle: 'Activité reçue sur ton profil',
                        value: preferences.likesEnabled,
                        enabled: preferences.notificationsEnabled,
                        onChanged: (value) => setState(() {
                          _preferences = preferences.copyWith(
                            likesEnabled: value,
                          );
                        }),
                      ),
                      _PreferenceSwitch(
                        icon: Icons.shield_rounded,
                        title: 'Sécurité du compte',
                        subtitle: 'Toujours active pour protéger ton compte',
                        value: preferences.securityEnabled,
                        enabled: false,
                        onChanged: (_) {},
                      ),
                      const SizedBox(height: 14),
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            children: [
                              SwitchListTile.adaptive(
                                contentPadding: EdgeInsets.zero,
                                secondary: const Icon(Icons.bedtime_rounded),
                                title: const Text('Heures silencieuses'),
                                subtitle: const Text(
                                  'Suspendre les alertes non urgentes pendant ton repos',
                                ),
                                value: preferences.quietHoursEnabled,
                                onChanged: preferences.notificationsEnabled
                                    ? (value) => setState(() {
                                          _preferences = preferences.copyWith(
                                            quietHoursEnabled: value,
                                          );
                                        })
                                    : null,
                              ),
                              if (preferences.quietHoursEnabled) ...[
                                const Divider(),
                                Row(
                                  children: [
                                    Expanded(
                                      child: _TimeButton(
                                        label: 'Début',
                                        value: preferences.quietStart,
                                        onPressed: () => _pickTime(start: true),
                                      ),
                                    ),
                                    const SizedBox(width: 12),
                                    Expanded(
                                      child: _TimeButton(
                                        label: 'Fin',
                                        value: preferences.quietEnd,
                                        onPressed: () => _pickTime(start: false),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ],
                          ),
                        ),
                      ),
                      if (_error != null) ...[
                        const SizedBox(height: 12),
                        Text(
                          _error!,
                          style: TextStyle(color: scheme.error),
                        ),
                      ],
                      const SizedBox(height: 20),
                      FilledButton.icon(
                        onPressed: _saving ? null : _save,
                        icon: _saving
                            ? const SizedBox.square(
                                dimension: 18,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.check_rounded),
                        label: Text(_saving ? 'Enregistrement…' : 'Enregistrer'),
                      ),
                    ],
                  ),
      ),
    );
  }
}

class _PreferenceSwitch extends StatelessWidget {
  const _PreferenceSwitch({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.value,
    required this.onChanged,
    this.enabled = true,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final bool value;
  final bool enabled;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) => SwitchListTile.adaptive(
        secondary: Icon(icon),
        title: Text(title),
        subtitle: Text(subtitle),
        value: value,
        onChanged: enabled ? onChanged : null,
      );
}

class _TimeButton extends StatelessWidget {
  const _TimeButton({
    required this.label,
    required this.value,
    required this.onPressed,
  });

  final String label;
  final String value;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) => OutlinedButton.icon(
        onPressed: onPressed,
        icon: const Icon(Icons.schedule_rounded),
        label: Text('$label · $value'),
      );
}
