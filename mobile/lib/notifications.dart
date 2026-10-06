import 'package:flutter/material.dart';

import 'auth_contract.dart';

class NotificationsPage extends StatefulWidget {
  const NotificationsPage({super.key, required this.api});

  final AuthApi api;

  @override
  State<NotificationsPage> createState() => _NotificationsPageState();
}

class _NotificationsPageState extends State<NotificationsPage> {
  List<AppNotification> _items = <AppNotification>[];
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
      final items = await widget.api.getNotifications();
      if (mounted) setState(() => _items = items);
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
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
                    Container(
                      padding: const EdgeInsets.all(22),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFFFFE3EA), Color(0xFFFFF1E9)],
                        ),
                        borderRadius: BorderRadius.circular(28),
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.notifications_active_rounded,
                            color: Color(0xFFB51F50),
                            size: 34,
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
                                      ?.copyWith(fontWeight: FontWeight.w800),
                                ),
                                const Text('Toute l’activité importante de ton compte.'),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: 12),
                      Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                    ],
                    const SizedBox(height: 20),
                    if (_items.isEmpty)
                      const Padding(
                        padding: EdgeInsets.all(32),
                        child: Text(
                          'Aucune notification pour le moment.',
                          textAlign: TextAlign.center,
                        ),
                      )
                    else
                      ..._items.map(
                        (item) => Dismissible(
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
                          child: Padding(
                            padding: const EdgeInsets.only(bottom: 12),
                            child: Card(
                              color: item.read ? Colors.white : const Color(0xFFFFF0F4),
                              child: ListTile(
                                contentPadding: const EdgeInsets.all(16),
                                onTap: () => _read(item),
                                leading: CircleAvatar(
                                  backgroundColor: item.read
                                      ? const Color(0xFFF2EAED)
                                      : const Color(0xFFFFD3DF),
                                  child: Icon(_icon(item.kind), color: const Color(0xFFB51F50)),
                                ),
                                title: Text(
                                  item.title,
                                  style: TextStyle(
                                    fontWeight: item.read ? FontWeight.w600 : FontWeight.w800,
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
                                    Text(_date(item.createdAt)),
                                  ],
                                ),
                                trailing: item.read
                                    ? null
                                    : const Badge(smallSize: 9),
                              ),
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
      ),
    );
  }
}
