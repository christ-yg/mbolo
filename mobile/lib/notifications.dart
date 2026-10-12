import 'dart:async';

import 'package:flutter/material.dart';

import 'auth_contract.dart';
import 'notification_preferences.dart';

enum _NotificationFilter { all, unread, messages, matches, likes, security }

enum _NotificationSort { recent, unreadFirst }

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
  bool _loadingMore = false;
  bool _hasNextPage = false;
  int _currentPage = 1;
  int _totalCount = 0;
  Timer? _refreshTimer;
  String? _error;
  _NotificationFilter _filter = _NotificationFilter.all;
  _NotificationSort _sort = _NotificationSort.recent;
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  String _searchQuery = '';
  Set<String> _selectedIds = <String>{};

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _scrollController.addListener(_handleScroll);
    _load();
    _startRefreshing();
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    _searchController.dispose();
    _scrollController
      ..removeListener(_handleScroll)
      ..dispose();
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

  void _handleScroll() {
    if (!_scrollController.hasClients ||
        _scrollController.position.extentAfter > 320) {
      return;
    }
    unawaited(_loadMore());
  }

  Future<void> _load({bool silent = false}) async {
    if (_refreshing || _working) return;
    _refreshing = true;
    if (!silent && mounted) setState(() => _error = null);
    try {
      final response = await widget.api.getNotifications();
      if (mounted) {
        setState(() {
          if (silent && _items.isNotEmpty) {
            final freshIds = response.items.map((item) => item.id).toSet();
            _items = <AppNotification>[
              ...response.items,
              ..._items.where((item) => !freshIds.contains(item.id)),
            ];
          } else {
            _items = List<AppNotification>.of(response.items);
            _currentPage = 1;
          }
          _totalCount = response.totalCount;
          _hasNextPage = _items.length < _totalCount;
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

  Future<void> _loadMore() async {
    if (_loadingMore || _refreshing || _working || !_hasNextPage) return;
    final nextPage = _currentPage + 1;
    setState(() => _loadingMore = true);
    try {
      final response = await widget.api.getNotifications(page: nextPage);
      if (!mounted) return;
      setState(() {
        final knownIds = _items.map((item) => item.id).toSet();
        _items = <AppNotification>[
          ..._items,
          ...response.items.where((item) => !knownIds.contains(item.id)),
        ];
        _currentPage = nextPage;
        _totalCount = response.totalCount;
        _hasNextPage = response.hasNext && _items.length < _totalCount;
        _error = null;
      });
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _loadingMore = false);
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

  void _toggleSelection(AppNotification item) {
    if (_working) return;
    setState(() {
      final nextIds = Set<String>.of(_selectedIds);
      if (!nextIds.add(item.id)) nextIds.remove(item.id);
      _selectedIds = nextIds;
    });
  }

  void _clearSelection() => setState(() => _selectedIds = <String>{});

  Future<void> _readSelected() async {
    if (_working || _selectedIds.isEmpty) return;
    final unreadItems = _items
        .where((item) => _selectedIds.contains(item.id) && !item.read)
        .toList(growable: false);
    if (unreadItems.isEmpty) {
      _clearSelection();
      return;
    }
    setState(() => _working = true);
    final results = <AppNotification?>[];
    for (final item in unreadItems) {
      try {
        results.add(await widget.api.markNotificationRead(item.id));
      } catch (_) {
        results.add(null);
      }
    }
    if (!mounted) return;
    final updated = <String, AppNotification>{
      for (final item in results.whereType<AppNotification>()) item.id: item,
    };
    setState(() {
      _items = _items
          .map((item) => updated[item.id] ?? item)
          .toList(growable: true);
      _selectedIds = <String>{};
      _working = false;
      if (updated.length != unreadItems.length) {
        _error = 'Certaines notifications n’ont pas pu être marquées comme lues.';
      }
    });
  }

  Future<void> _confirmDeleteSelected() async {
    if (_working || _selectedIds.isEmpty) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.delete_sweep_rounded),
        title: const Text('Supprimer la sélection ?'),
        content: Text(
          '${_selectedIds.length} notification${_selectedIds.length > 1 ? 's seront supprimées' : ' sera supprimée'} définitivement.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Conserver'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Supprimer'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    await _deleteSelected();
  }

  Future<void> _deleteSelected() async {
    final ids = Set<String>.of(_selectedIds);
    setState(() => _working = true);
    final results = <String?>[];
    for (final id in ids) {
      try {
        await widget.api.deleteNotification(id);
        results.add(id);
      } catch (_) {
        results.add(null);
      }
    }
    if (!mounted) return;
    final deletedIds = results.whereType<String>().toSet();
    setState(() {
      _items.removeWhere((item) => deletedIds.contains(item.id));
      _totalCount = _totalCount > deletedIds.length
          ? _totalCount - deletedIds.length
          : 0;
      _hasNextPage = _items.length < _totalCount;
      _selectedIds = ids.difference(deletedIds);
      _working = false;
      if (deletedIds.length != ids.length) {
        _error = 'Certaines notifications n’ont pas pu être supprimées.';
      }
    });
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
        setState(() {
          _items.removeWhere((current) => current.id == item.id);
          if (_totalCount > 0) _totalCount -= 1;
          _hasNextPage = _items.length < _totalCount;
        });
      }
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    }
  }

  Future<void> _openPreferences() async {
    await Navigator.of(context).push<void>(
      MaterialPageRoute<void>(
        builder: (context) => NotificationPreferencesPage(api: widget.api),
      ),
    );
  }

  IconData _icon(String kind) => switch (kind) {
        'message' => Icons.chat_bubble_rounded,
        'match' => Icons.favorite_rounded,
        'like' || 'super_like' => Icons.auto_awesome_rounded,
        'security' => Icons.shield_rounded,
        _ => Icons.notifications_rounded,
      };

  bool _matchesFilter(AppNotification item, _NotificationFilter filter) =>
      switch (filter) {
        _NotificationFilter.all => true,
        _NotificationFilter.unread => !item.read,
        _NotificationFilter.messages => item.kind == 'message',
        _NotificationFilter.matches => item.kind == 'match',
        _NotificationFilter.likes =>
          item.kind == 'like' || item.kind == 'super_like',
        _NotificationFilter.security =>
          item.kind == 'security' || item.kind == 'system',
      };

  bool _matchesSearch(AppNotification item) {
    final query = _searchQuery.trim().toLowerCase();
    if (query.isEmpty) return true;
    return item.title.toLowerCase().contains(query) ||
        item.body.toLowerCase().contains(query) ||
        _kindLabel(item.kind).toLowerCase().contains(query);
  }

  String _kindLabel(String kind) => switch (kind) {
        'message' => 'Message',
        'match' => 'Match',
        'like' => 'Like',
        'super_like' => 'Super Like',
        'security' => 'Sécurité',
        _ => 'Information',
      };

  String _sortLabel(_NotificationSort sort) => switch (sort) {
        _NotificationSort.recent => 'Plus récentes',
        _NotificationSort.unreadFirst => 'Non lues d’abord',
      };

  String _filterLabel(_NotificationFilter filter) => switch (filter) {
        _NotificationFilter.all => 'Tout',
        _NotificationFilter.unread => 'Non lues',
        _NotificationFilter.messages => 'Messages',
        _NotificationFilter.matches => 'Matchs',
        _NotificationFilter.likes => 'Likes',
        _NotificationFilter.security => 'Sécurité',
      };

  IconData _filterIcon(_NotificationFilter filter) => switch (filter) {
        _NotificationFilter.all => Icons.inbox_rounded,
        _NotificationFilter.unread => Icons.mark_email_unread_rounded,
        _NotificationFilter.messages => Icons.chat_bubble_rounded,
        _NotificationFilter.matches => Icons.favorite_rounded,
        _NotificationFilter.likes => Icons.auto_awesome_rounded,
        _NotificationFilter.security => Icons.shield_rounded,
      };

  int _filterCount(_NotificationFilter filter) =>
      _items.where((item) => _matchesFilter(item, filter)).length;

  String _dayLabel(DateTime value) {
    final local = value.toLocal();
    final now = DateTime.now();
    final day = DateTime(local.year, local.month, local.day);
    final today = DateTime(now.year, now.month, now.day);
    final difference = today.difference(day).inDays;
    if (difference == 0) return 'Aujourd’hui';
    if (difference == 1) return 'Hier';
    if (difference < 7) return 'Cette semaine';
    return 'Plus anciennes';
  }

  String _date(DateTime value) {
    final local = value.toLocal();
    return '${local.day.toString().padLeft(2, '0')}/${local.month.toString().padLeft(2, '0')} • ${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    final unread = _items.where((item) => !item.read).length;
    final visibleItems = _items
        .where((item) =>
            _matchesFilter(item, _filter) && _matchesSearch(item))
        .toList(growable: true)
      ..sort((left, right) {
        if (_sort == _NotificationSort.unreadFirst && left.read != right.read) {
          return left.read ? 1 : -1;
        }
        return right.createdAt.compareTo(left.createdAt);
      });
    return Scaffold(
      appBar: AppBar(
        leading: _selectedIds.isEmpty
            ? null
            : IconButton(
                tooltip: 'Annuler la sélection',
                onPressed: _working ? null : _clearSelection,
                icon: const Icon(Icons.close_rounded),
              ),
        title: Text(
          _selectedIds.isEmpty
              ? 'Notifications'
              : '${_selectedIds.length} sélectionnée${_selectedIds.length > 1 ? 's' : ''}',
        ),
        actions: _selectedIds.isEmpty
            ? [
                IconButton(
                  tooltip: 'Préférences de notifications',
                  onPressed: _openPreferences,
                  icon: const Icon(Icons.tune_rounded),
                ),
                TextButton(
                  onPressed: _working ? null : _readAll,
                  child: const Text('Tout lire'),
                ),
              ]
            : [
                IconButton(
                  tooltip: 'Marquer la sélection comme lue',
                  onPressed: _working ? null : _readSelected,
                  icon: const Icon(Icons.mark_email_read_rounded),
                ),
                IconButton(
                  tooltip: 'Supprimer la sélection',
                  onPressed: _working ? null : _confirmDeleteSelected,
                  icon: const Icon(Icons.delete_outline_rounded),
                ),
              ],
      ),
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: _load,
                child: ListView(
                  controller: _scrollController,
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
                    _NotificationFilters(
                      selected: _filter,
                      labelFor: _filterLabel,
                      iconFor: _filterIcon,
                      countFor: _filterCount,
                      onSelected: (filter) => setState(() => _filter = filter),
                    ),
                    const SizedBox(height: 14),
                    _NotificationSearch(
                      controller: _searchController,
                      query: _searchQuery,
                      sort: _sort,
                      sortLabel: _sortLabel,
                      onChanged: (value) => setState(() => _searchQuery = value),
                      onClear: () {
                        _searchController.clear();
                        setState(() => _searchQuery = '');
                      },
                      onSortChanged: (sort) => setState(() => _sort = sort),
                    ),
                    const SizedBox(height: 20),
                    if (_items.isEmpty)
                      const _NotificationEmptyState()
                    else if (visibleItems.isEmpty)
                      _NotificationFilteredEmptyState(
                        filterLabel: _searchQuery.trim().isEmpty
                            ? _filterLabel(_filter)
                            : 'Recherche : ${_searchQuery.trim()}',
                        onReset: () {
                          _searchController.clear();
                          setState(() {
                            _filter = _NotificationFilter.all;
                            _searchQuery = '';
                          });
                        },
                      )
                    else
                      ...visibleItems.indexed.map(
                        (entry) {
                          final index = entry.$1;
                          final item = entry.$2;
                          final dayLabel = _dayLabel(item.createdAt);
                          final previousLabel = index == 0
                              ? null
                              : _dayLabel(visibleItems[index - 1].createdAt);
                          return Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              if (dayLabel != previousLabel)
                                Padding(
                                  padding: EdgeInsets.only(
                                    top: index == 0 ? 0 : 12,
                                    bottom: 10,
                                    left: 4,
                                  ),
                                  child: Text(
                                    dayLabel,
                                    style: Theme.of(context)
                                        .textTheme
                                        .titleSmall
                                        ?.copyWith(fontWeight: FontWeight.w900),
                                  ),
                                ),
                              Dismissible(
                                key: ValueKey(item.id),
                                direction: _selectedIds.isEmpty
                                    ? DismissDirection.endToStart
                                    : DismissDirection.none,
                                background: Container(
                                  margin: const EdgeInsets.only(bottom: 12),
                                  padding: const EdgeInsets.only(right: 24),
                                  alignment: Alignment.centerRight,
                                  decoration: BoxDecoration(
                                    color: Theme.of(context).colorScheme.error,
                                    borderRadius: BorderRadius.circular(24),
                                  ),
                                  child: const Icon(
                                    Icons.delete_outline,
                                    color: Colors.white,
                                  ),
                                ),
                                onDismissed: (_) => _delete(item),
                                child: _AnimatedNotificationTile(
                                  item: item,
                                  index: index,
                                  icon: _icon(item.kind),
                                  date: _date(item.createdAt),
                                  working: _working,
                                  selected: _selectedIds.contains(item.id),
                                  onTap: () => _selectedIds.isEmpty
                                      ? _open(item)
                                      : _toggleSelection(item),
                                  onLongPress: () => _toggleSelection(item),
                                ),
                              ),
                            ],
                          );
                        },
                      ),
                    if (_loadingMore)
                      const Padding(
                        padding: EdgeInsets.symmetric(vertical: 22),
                        child: Center(child: CircularProgressIndicator()),
                      )
                    else if (_hasNextPage)
                      Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: OutlinedButton.icon(
                          onPressed: () => unawaited(_loadMore()),
                          icon: const Icon(Icons.expand_more_rounded),
                          label: const Text('Charger plus de notifications'),
                        ),
                      )
                    else if (_items.isNotEmpty && _items.length >= _totalCount)
                      Padding(
                        padding: const EdgeInsets.only(top: 18),
                        child: Text(
                          'Tu as consulté tout ton historique.',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.onSurfaceVariant,
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

class _NotificationFilters extends StatelessWidget {
  const _NotificationFilters({
    required this.selected,
    required this.labelFor,
    required this.iconFor,
    required this.countFor,
    required this.onSelected,
  });

  final _NotificationFilter selected;
  final String Function(_NotificationFilter) labelFor;
  final IconData Function(_NotificationFilter) iconFor;
  final int Function(_NotificationFilter) countFor;
  final ValueChanged<_NotificationFilter> onSelected;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Filtrer l’activité',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w900,
              ),
        ),
        const SizedBox(height: 10),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: _NotificationFilter.values.map((filter) {
              final selectedFilter = filter == selected;
              return Padding(
                padding: const EdgeInsets.only(right: 8),
                child: ChoiceChip(
                  selected: selectedFilter,
                  showCheckmark: false,
                  avatar: Icon(iconFor(filter), size: 18),
                  label: Text('${labelFor(filter)} ${countFor(filter)}'),
                  onSelected: (_) => onSelected(filter),
                ),
              );
            }).toList(growable: false),
          ),
        ),
      ],
    );
  }
}

class _NotificationSearch extends StatelessWidget {
  const _NotificationSearch({
    required this.controller,
    required this.query,
    required this.sort,
    required this.sortLabel,
    required this.onChanged,
    required this.onClear,
    required this.onSortChanged,
  });

  final TextEditingController controller;
  final String query;
  final _NotificationSort sort;
  final String Function(_NotificationSort) sortLabel;
  final ValueChanged<String> onChanged;
  final VoidCallback onClear;
  final ValueChanged<_NotificationSort> onSortChanged;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: TextField(
            key: const ValueKey('notification-search-field'),
            controller: controller,
            onChanged: onChanged,
            textInputAction: TextInputAction.search,
            decoration: InputDecoration(
              hintText: 'Rechercher dans ton activité',
              prefixIcon: const Icon(Icons.search_rounded),
              suffixIcon: query.isEmpty
                  ? null
                  : IconButton(
                      tooltip: 'Effacer la recherche',
                      onPressed: onClear,
                      icon: const Icon(Icons.close_rounded),
                    ),
              filled: true,
              fillColor: scheme.surfaceContainerLow,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(18),
                borderSide: BorderSide.none,
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(18),
                borderSide: BorderSide(color: scheme.outlineVariant),
              ),
            ),
          ),
        ),
        const SizedBox(width: 8),
        PopupMenuButton<_NotificationSort>(
          tooltip: 'Trier les notifications',
          initialValue: sort,
          onSelected: onSortChanged,
          itemBuilder: (context) => _NotificationSort.values
              .map(
                (option) => PopupMenuItem<_NotificationSort>(
                  value: option,
                  child: Row(
                    children: [
                      Icon(
                        option == _NotificationSort.recent
                            ? Icons.schedule_rounded
                            : Icons.mark_email_unread_rounded,
                        size: 20,
                      ),
                      const SizedBox(width: 10),
                      Text(sortLabel(option)),
                    ],
                  ),
                ),
              )
              .toList(growable: false),
          child: Semantics(
            button: true,
            label: 'Tri actuel : ${sortLabel(sort)}',
            child: Container(
              width: 54,
              height: 54,
              decoration: BoxDecoration(
                color: scheme.surfaceContainerLow,
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: scheme.outlineVariant),
              ),
              child: const Icon(Icons.swap_vert_rounded),
            ),
          ),
        ),
      ],
    );
  }
}

class _NotificationFilteredEmptyState extends StatelessWidget {
  const _NotificationFilteredEmptyState({
    required this.filterLabel,
    required this.onReset,
  });

  final String filterLabel;
  final VoidCallback onReset;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 28),
      child: Column(
        children: [
          Icon(Icons.filter_alt_off_rounded, size: 48, color: scheme.primary),
          const SizedBox(height: 14),
          Text(
            'Aucune notification « $filterLabel »',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w900,
                ),
          ),
          const SizedBox(height: 6),
          Text(
            'Les nouvelles activités correspondant à ce filtre apparaîtront ici.',
            textAlign: TextAlign.center,
            style: TextStyle(color: scheme.onSurfaceVariant),
          ),
          const SizedBox(height: 14),
          TextButton.icon(
            onPressed: onReset,
            icon: const Icon(Icons.inbox_rounded),
            label: const Text('Voir toute l’activité'),
          ),
        ],
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
    required this.selected,
    required this.onTap,
    required this.onLongPress,
  });

  final AppNotification item;
  final int index;
  final IconData icon;
  final String date;
  final bool working;
  final bool selected;
  final VoidCallback onTap;
  final VoidCallback onLongPress;

  @override
  Widget build(BuildContext context) {
    final reduceMotion = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (reduceMotion) {
      return _NotificationTile(
        item: item,
        icon: icon,
        date: date,
        working: working,
        selected: selected,
        onTap: onTap,
        onLongPress: onLongPress,
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
        selected: selected,
        onTap: onTap,
        onLongPress: onLongPress,
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
    required this.selected,
    required this.onTap,
    required this.onLongPress,
  });

  final AppNotification item;
  final IconData icon;
  final String date;
  final bool working;
  final bool selected;
  final VoidCallback onTap;
  final VoidCallback onLongPress;

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
            color: selected
                ? scheme.secondaryContainer
                : item.read
                    ? scheme.surface
                    : scheme.primaryContainer,
            borderRadius: BorderRadius.circular(24),
            border: Border.all(
              color: selected
                  ? scheme.secondary
                  : item.read
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
              onLongPress: onLongPress,
              leading: AnimatedSwitcher(
                duration: const Duration(milliseconds: 180),
                child: selected
                    ? CircleAvatar(
                        key: const ValueKey('selected'),
                        backgroundColor: scheme.secondary,
                        child: Icon(Icons.check_rounded, color: scheme.onSecondary),
                      )
                    : CircleAvatar(
                        key: const ValueKey('kind'),
                        backgroundColor: item.read
                            ? scheme.surfaceContainerHighest
                            : scheme.primary.withValues(alpha: 0.16),
                        child: Icon(icon, color: scheme.primary),
                      ),
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
