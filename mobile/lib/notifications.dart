import 'dart:async';

import 'package:flutter/material.dart';

import 'auth_contract.dart';

class NotificationsPage extends StatefulWidget {
  const NotificationsPage({
    super.key,
    required this.api,
    this.onOpenTarget,
  });

  final AuthApi api;
  final Future<void> Function(String targetPath)? onOpenTarget;

  @override
  State<NotificationsPage> createState() => _NotificationsPageState();
}

class _NotificationsPageState extends State<NotificationsPage>
    with WidgetsBindingObserver {
  List<AppNotification> _items = <AppNotification>[];
  bool _loading = true;
  bool _working = false;
  bool _refreshing = false;
  Timer? _refreshTimer;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _load();
    _startRefreshing();
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _startRefreshing();
      unawaited(_load(silent: true));
    } else if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.inactive ||
        state == AppLifecycleState.detached ||
        state == AppLifecycleState.hidden) {
      _refreshTimer?.cancel();
      _refreshTimer = null;
    }
  }

  void _startRefreshing() {
    _refreshTimer?.cancel();
    _refreshTimer = Timer.periodic(
      const Duration(seconds: 12),
      (_) => unawaited(_load(silent: true)),
    );
  }

  Future<void> _load({bool silent = false}) async {
    if (_refreshing || _working) return;
    _refreshing = true;
    if (!silent && mounted) setState(() => _error = null);
    try {
      final items = await widget.api.getNotifications();
      if (mounted) {
        setState(() {
          _items = items;
          _error = null;
        });
      }
    } catch (error) {
      if (!silent && mounted) setState(() => _error = friendlyError(error));
    } finally {
      _refreshing = false;
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _read(AppNotification item) async {
    if (_working || item.read) return;
    setState(() => _working = true);
    try {
      final updated = await widget.api.markNotificationRead(item.id);
      if (!mounted) return;
      setState(() {
        _items = _items
            .map((current) => current.id == updated.id ? updated : current)
            .toList(growable: false);
      });
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  bool _isSafeTarget(String path) {
    if (!path.startsWith('/') || path.startsWith('//')) return false;
    final uri = Uri.tryParse(path);
    return uri != null &&
        !uri.hasScheme &&
        uri.host.isEmpty &&
        uri.userInfo.isEmpty &&
        !uri.hasQuery &&
        !uri.hasFragment;
  }

  Future<void> _open(AppNotification item) async {
    await _read(item);
    if (!mounted ||
        widget.onOpenTarget == null ||
        !_isSafeTarget(item.targetPath)) {
      return;
    }
    Navigator.of(context).pop();
    await widget.onOpenTarget!(item.targetPath);
  }

  Future<void> _readAll() async {
    if (_working || !_items.any((item) => !item.read)) return;
    setState(() => _working = true);
    try {
      await widget.api.markAllNotificationsRead();
      if (mounted) {
        setState(() {
          _items = _items.map((item) => item.copyWith(read: true)).toList();
        });
      }
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Future<void> _delete(AppNotification item) async {
    try {
      await widget.api.deleteNotification(item.id);
      if (mounted) {
        setState(() => _items.removeWhere((current) => current.id == item.id));
      }
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    }
  }

  IconData _icon(String kind) => switch (kind) {
        'message' => Icons.chat_bubble_rounded,
        'match' => Icons.favorite_rounded,
        'like' || 'super_like' => Icons.auto_awesome_rounded,
        'security' => Icons.shield_rounded,
        _ => Icons.notifications_rounded,
      };

  String _date(DateTime value) {
    final local = value.toLocal();
    return '${local.day.toString().padLeft(2, '0')}/${local.month.toString().padLeft(2, '0')} • ${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    final unread = _items.where((item) => !item.read).length;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          TextButton(
            onPressed: _working ? null : _readAll,
            child: const Text('Tout lire'),
          ),
        ],
      ),
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: _load,
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(18, 8, 18, 32),
                  children: [
                    TweenAnimationBuilder<double>(
                      tween: Tween<double>(begin: 0, end: 1),
                      duration: const Duration(milliseconds: 620),
                      curve: Curves.easeOutBack,
                      builder: (context, value, child) => Transform.translate(
                        offset: Offset(0, 16 * (1 - value)),
                        child: Opacity(
                          opacity: value.clamp(0, 1),
                          child: child,
                        ),
                      ),
                      child: Container(
                      padding: const EdgeInsets.all(22),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [
                            Color(0xFF351020),
                            Color(0xFF8B1744),
                            Color(0xFFE0667C),
                          ],
                        ),
                        borderRadius: BorderRadius.circular(28),
                        boxShadow: const [
                          BoxShadow(
                            color: Color(0x388B1744),
                            blurRadius: 30,
                            offset: Offset(0, 14),
                          ),
                        ],
                      ),
                      child: Row(
                        children: [
                          Container(
                            width: 56,
                            height: 56,
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.14),
                              shape: BoxShape.circle,
                              border: Border.all(
                                color: Colors.white.withValues(alpha: 0.24),
                              ),
                            ),
                            child: const Icon(
                              Icons.notifications_active_rounded,
                              color: Colors.white,
                              size: 30,
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '$unread nouvelle${unread > 1 ? 's' : ''}',
                                  style: Theme.of(context)
                                      .textTheme
                                      .titleLarge
                                      ?.copyWith(
                                        color: Colors.white,
                                        fontWeight: FontWeight.w900,
                                      ),
                                ),
                                const Text(
                                  'Toute l’activité importante de ton compte.',
                                  style: TextStyle(color: Color(0xFFFFEAF0)),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      ),
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: 12),
                      _NotificationError(
                        message: _error!,
                        onRetry: _load,
                      ),
                    ],
                    const SizedBox(height: 20),
                    if (_items.isEmpty)
                      const _NotificationEmptyState()
                    else
                      ..._items.indexed.map(
                        (entry) {
                          final index = entry.$1;
                          final item = entry.$2;
                          return Dismissible(
                          key: ValueKey(item.id),
                          direction: DismissDirection.endToStart,
                          background: Container(
                            margin: const EdgeInsets.only(bottom: 12),
                            padding: const EdgeInsets.only(right: 24),
                            alignment: Alignment.centerRight,
                            decoration: BoxDecoration(
                              color: Theme.of(context).colorScheme.error,
                              borderRadius: BorderRadius.circular(24),
                            ),
                            child: const Icon(Icons.delete_outline, color: Colors.white),
                          ),
                          onDismissed: (_) => _delete(item),
                          child: _AnimatedNotificationTile(
                            item: item,
                            index: index,
                            icon: _icon(item.kind),
                            date: _date(item.createdAt),
                            working: _working,
                            onTap: () => _open(item),
                          ),
                        );
                        },
                      ),
                  ],
                ),
              ),
      ),
    );
  }
}

class _NotificationError extends StatelessWidget {
  const _NotificationError({required this.message, required this.onRetry});

  final String message;
  final Future<void> Function({bool silent}) onRetry;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Material(
      color: scheme.errorContainer,
      borderRadius: BorderRadius.circular(20),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(Icons.cloud_off_rounded, color: scheme.onErrorContainer),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                message,
                style: TextStyle(color: scheme.onErrorContainer),
              ),
            ),
            TextButton(
              onPressed: () => onRetry(silent: false),
              child: const Text('Réessayer'),
            ),
          ],
        ),
      ),
    );
  }
}

class _NotificationEmptyState extends StatelessWidget {
  const _NotificationEmptyState();

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 34),
      child: Column(
        children: [
          Container(
            width: 82,
            height: 82,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [scheme.primaryContainer, scheme.secondaryContainer],
              ),
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.notifications_none_rounded,
              size: 38,
              color: scheme.primary,
            ),
          ),
          const SizedBox(height: 18),
          Text(
            'Tout est calme pour le moment',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w900,
                ),
          ),
          const SizedBox(height: 7),
          Text(
            'Tes matchs, messages et alertes de sécurité apparaîtront ici.',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
          ),
        ],
      ),
    );
  }
}

class _AnimatedNotificationTile extends StatelessWidget {
  const _AnimatedNotificationTile({
    required this.item,
    required this.index,
    required this.icon,
    required this.date,
    required this.working,
    required this.onTap,
  });

  final AppNotification item;
  final int index;
  final IconData icon;
  final String date;
  final bool working;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final reduceMotion = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (reduceMotion) {
      return _NotificationTile(
        item: item,
        icon: icon,
        date: date,
        working: working,
        onTap: onTap,
      );
    }
    return TweenAnimationBuilder<double>(
      tween: Tween<double>(begin: 0, end: 1),
      duration: Duration(milliseconds: 320 + (index.clamp(0, 6) * 45)),
      curve: Curves.easeOutCubic,
      builder: (context, value, child) => Opacity(
        opacity: value,
        child: Transform.translate(
          offset: Offset(18 * (1 - value), 0),
          child: child,
        ),
      ),
      child: _NotificationTile(
        item: item,
        icon: icon,
        date: date,
        working: working,
        onTap: onTap,
      ),
    );
  }
}

class _NotificationTile extends StatelessWidget {
  const _NotificationTile({
    required this.item,
    required this.icon,
    required this.date,
    required this.working,
    required this.onTap,
  });

  final AppNotification item;
  final IconData icon;
  final String date;
  final bool working;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Semantics(
      button: true,
      label: item.read
          ? '${item.title}. Notification lue.'
          : '${item.title}. Nouvelle notification.',
      child: Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 260),
          decoration: BoxDecoration(
            color: item.read ? scheme.surface : scheme.primaryContainer,
            borderRadius: BorderRadius.circular(24),
            border: Border.all(
              color: item.read
                  ? scheme.outlineVariant
                  : scheme.primary.withValues(alpha: 0.24),
            ),
            boxShadow: item.read
                ? null
                : [
                    BoxShadow(
                      color: scheme.primary.withValues(alpha: 0.11),
                      blurRadius: 22,
                      offset: const Offset(0, 9),
                    ),
                  ],
          ),
          child: Material(
            type: MaterialType.transparency,
            borderRadius: BorderRadius.circular(24),
            clipBehavior: Clip.antiAlias,
            child: ListTile(
              contentPadding: const EdgeInsets.all(16),
              enabled: !working,
              onTap: onTap,
              leading: CircleAvatar(
                backgroundColor: item.read
                    ? scheme.surfaceContainerHighest
                    : scheme.primary.withValues(alpha: 0.16),
                child: Icon(icon, color: scheme.primary),
              ),
              title: Text(
                item.title,
                style: TextStyle(
                  fontWeight: item.read ? FontWeight.w600 : FontWeight.w900,
                ),
              ),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (item.body.isNotEmpty) ...[
                    const SizedBox(height: 5),
                    Text(item.body),
                  ],
                  const SizedBox(height: 7),
                  Text(date, style: Theme.of(context).textTheme.labelSmall),
                ],
              ),
              trailing: item.read ? null : const Badge(smallSize: 9),
            ),
          ),
        ),
      ),
    );
  }
}
