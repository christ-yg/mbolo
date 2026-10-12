import 'package:flutter/material.dart';

import 'auth_contract.dart';

class TrustCenterPage extends StatefulWidget {
  const TrustCenterPage({super.key, required this.api});

  final AuthApi api;

  @override
  State<TrustCenterPage> createState() => _TrustCenterPageState();
}

class _TrustCenterPageState extends State<TrustCenterPage> {
  List<BlockedUserItem> _blocked = const <BlockedUserItem>[];
  List<UserReportItem> _reports = const <UserReportItem>[];
  bool _loading = true;
  String? _workingId;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final values = await Future.wait<Object>([
        widget.api.getBlockedUsers(),
        widget.api.getMyReports(),
      ]);
      if (!mounted) return;
      setState(() {
        _blocked = values[0] as List<BlockedUserItem>;
        _reports = values[1] as List<UserReportItem>;
      });
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _unblock(BlockedUserItem item) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.lock_open_rounded),
        title: Text('Débloquer ${item.displayName} ?'),
        content: const Text(
          'Cette personne pourra de nouveau apparaître dans les espaces compatibles avec vos préférences.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Débloquer'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() => _workingId = item.id);
    try {
      await widget.api.unblockUser(item.id);
      if (!mounted) return;
      setState(() => _blocked = _blocked
          .where((blocked) => blocked.id != item.id)
          .toList(growable: false));
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${item.displayName} a été débloqué.')),
      );
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _workingId = null);
    }
  }

  @override
  Widget build(BuildContext context) => DefaultTabController(
        length: 2,
        child: Scaffold(
          appBar: AppBar(
            title: const Text('Confiance et modération'),
            bottom: const TabBar(
              tabs: [
                Tab(text: 'Bloqués'),
                Tab(text: 'Signalements'),
              ],
            ),
          ),
          body: _loading
              ? const Center(child: CircularProgressIndicator())
              : _error != null && _blocked.isEmpty && _reports.isEmpty
                  ? _ErrorState(message: _error!, onRetry: _load)
                  : TabBarView(
                      children: [
                        _blockedTab(),
                        _reportsTab(),
                      ],
                    ),
        ),
      );

  Widget _blockedTab() {
    if (_blocked.isEmpty) {
      return const _EmptyState(
        icon: Icons.shield_outlined,
        title: 'Aucun profil bloqué',
        message: 'Les profils bloqués apparaîtront ici, sans données privées.',
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.separated(
        padding: const EdgeInsets.all(18),
        itemCount: _blocked.length,
        separatorBuilder: (_, __) => const SizedBox(height: 10),
        itemBuilder: (context, index) {
          final item = _blocked[index];
          return Card(
            child: ListTile(
              contentPadding: const EdgeInsets.all(14),
              leading: CircleAvatar(
                backgroundImage: item.photoUrl.isEmpty
                    ? null
                    : NetworkImage(item.photoUrl),
                child: item.photoUrl.isEmpty
                    ? const Icon(Icons.person_off_outlined)
                    : null,
              ),
              title: Text(item.displayName,
                  style: const TextStyle(fontWeight: FontWeight.w800)),
              subtitle: Text(item.city.isEmpty ? 'Profil bloqué' : item.city),
              trailing: _workingId == item.id
                  ? const SizedBox.square(
                      dimension: 22,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : TextButton(
                      onPressed: () => _unblock(item),
                      child: const Text('Débloquer'),
                    ),
            ),
          );
        },
      ),
    );
  }

  Widget _reportsTab() {
    if (_reports.isEmpty) {
      return const _EmptyState(
        icon: Icons.fact_check_outlined,
        title: 'Aucun signalement',
        message: 'Le suivi de tes signalements apparaîtra ici.',
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.separated(
        padding: const EdgeInsets.all(18),
        itemCount: _reports.length,
        separatorBuilder: (_, __) => const SizedBox(height: 10),
        itemBuilder: (context, index) {
          final item = _reports[index];
          final status = _status(item.status);
          return Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(item.displayName,
                            style: const TextStyle(fontWeight: FontWeight.w800)),
                      ),
                      Chip(
                        avatar: Icon(status.$1, size: 17),
                        label: Text(status.$2),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(_reason(item.reason)),
                  if (item.description.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(item.description,
                        maxLines: 3, overflow: TextOverflow.ellipsis),
                  ],
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  (IconData, String) _status(String value) => switch (value) {
        'under_review' => (Icons.manage_search_rounded, 'En examen'),
        'resolved' => (Icons.check_circle_outline, 'Traité'),
        'rejected' => (Icons.cancel_outlined, 'Classé'),
        _ => (Icons.schedule_rounded, 'Reçu'),
      };

  String _reason(String value) => switch (value) {
        'harassment' => 'Harcèlement',
        'fake_profile' => 'Faux profil',
        'scam' => 'Arnaque',
        'inappropriate_content' => 'Contenu inapproprié',
        'threat' => 'Menace',
        'spam' => 'Spam',
        'underage_suspicion' => 'Suspicion de minorité',
        _ => 'Autre motif',
      };
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.icon, required this.title, required this.message});
  final IconData icon;
  final String title;
  final String message;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 54, color: Theme.of(context).colorScheme.primary),
              const SizedBox(height: 14),
              Text(title, style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 6),
              Text(message, textAlign: TextAlign.center),
            ],
          ),
        ),
      );
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});
  final String message;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.cloud_off_outlined, size: 48),
              const SizedBox(height: 12),
              Text(message, textAlign: TextAlign.center),
              const SizedBox(height: 14),
              FilledButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('Réessayer'),
              ),
            ],
          ),
        ),
      );
}
