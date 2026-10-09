import 'dart:async';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';

import 'auth_contract.dart';
import 'safety_actions.dart';

class MessagesPage extends StatefulWidget {
  const MessagesPage({
    super.key,
    required this.api,
    this.initialSection = 0,
  });

  final AuthApi api;
  final int initialSection;

  @override
  State<MessagesPage> createState() => _MessagesPageState();
}

class _MessagesPageState extends State<MessagesPage>
    with WidgetsBindingObserver {
  final TextEditingController _searchController = TextEditingController();
  List<ConversationSummary> _conversations = <ConversationSummary>[];
  List<MatchSummary> _matches = <MatchSummary>[];
  List<ReceivedLike> _likes = <ReceivedLike>[];
  late int _section = widget.initialSection.clamp(0, 2).toInt();
  bool _loading = true;
  bool _refreshing = false;
  Timer? _refreshTimer;
  String _query = '';
  String? _workingLike;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _searchController.addListener(_onSearchChanged);
    _load();
    _startRefreshing();
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    _searchController.removeListener(_onSearchChanged);
    _searchController.dispose();
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
      const Duration(seconds: 15),
      (_) => unawaited(_load(silent: true)),
    );
  }

  void _onSearchChanged() {
    final query = _searchController.text.trim().toLowerCase();
    if (query != _query && mounted) setState(() => _query = query);
  }

  @override
  void didUpdateWidget(covariant MessagesPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialSection != widget.initialSection) {
      setState(() => _section = widget.initialSection.clamp(0, 2).toInt());
    }
  }

  Future<void> _load({bool silent = false}) async {
    if (_refreshing || _workingLike != null) return;
    _refreshing = true;
    if (!silent) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }
    try {
      final results = await Future.wait<Object>([
        widget.api.getConversations(),
        widget.api.getMatches(),
        widget.api.getReceivedLikes(),
      ]);
      final conversations = List<ConversationSummary>.of(
        results[0] as List<ConversationSummary>,
      )
        ..sort((a, b) {
          final unread = b.unreadCount.compareTo(a.unreadCount);
          return unread != 0 ? unread : b.updatedAt.compareTo(a.updatedAt);
        });
      final matches = List<MatchSummary>.of(results[1] as List<MatchSummary>)
        ..sort((a, b) => b.createdAt.compareTo(a.createdAt));
      final likes = List<ReceivedLike>.of(results[2] as List<ReceivedLike>)
        ..sort((a, b) {
          if (a.superLike != b.superLike) return a.superLike ? -1 : 1;
          return b.receivedAt.compareTo(a.receivedAt);
        });
      if (mounted) {
        setState(() {
          _conversations = conversations;
          _matches = matches;
          _likes = likes;
        });
      }
    } catch (error) {
      if (!silent && mounted) setState(() => _error = friendlyError(error));
    } finally {
      _refreshing = false;
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _openMatch(MatchSummary match) async {
    ConversationSummary? conversation;
    for (final item in _conversations) {
      if (item.matchId == match.id) {
        conversation = item;
        break;
      }
    }
    if (conversation == null) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('La conversation sera disponible dans un instant.'),
          ),
        );
      }
      await _load();
      return;
    }
    await _open(conversation);
  }

  Future<void> _respond(ReceivedLike like, String decision) async {
    if (_workingLike != null) return;
    setState(() => _workingLike = like.interactionId);
    try {
      final result = await widget.api.respondToReceivedLike(
        interactionId: like.interactionId,
        decision: decision,
      );
      if (!mounted) return;
      setState(() => _likes.removeWhere(
            (item) => item.interactionId == like.interactionId,
          ));
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            result.matched
                ? 'C’est un match${result.revealedProfile == null ? ' !' : ' avec ${result.revealedProfile!.displayName} !'}'
                : decision == 'like'
                    ? 'Ton intérêt a été envoyé.'
                    : 'Profil passé en toute discrétion.',
          ),
        ),
      );
      if (result.matched) await _load();
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(friendlyError(error))),
        );
      }
    } finally {
      if (mounted) setState(() => _workingLike = null);
    }
  }

  Future<void> _open(ConversationSummary conversation) async {
    _refreshTimer?.cancel();
    try {
      await Navigator.of(context).push<void>(
        MaterialPageRoute<void>(
          builder: (context) => ConversationPage(
            api: widget.api,
            conversation: conversation,
          ),
        ),
      );
      await _load(silent: true);
    } finally {
      _startRefreshing();
    }
  }

  Future<void> _showProfilePreview(
    DiscoveryProfile profile, {
    required VoidCallback onMessage,
  }) async {
    await HapticFeedback.selectionClick();
    if (!mounted) return;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      useSafeArea: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      builder: (sheetContext) => _ProfilePreviewSheet(
        profile: profile,
        onMessage: () {
          Navigator.of(sheetContext).pop();
          onMessage();
        },
      ),
    );
  }

  String _time(DateTime value) {
    final local = value.toLocal();
    return '${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.chat_bubble_outline, size: 52),
              const SizedBox(height: 12),
              Text(_error!, textAlign: TextAlign.center),
              const SizedBox(height: 16),
              FilledButton(onPressed: _load, child: const Text('Réessayer')),
            ],
          ),
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 8, 18, 96),
        children: [
          _MessagesHero(
            matchCount: _matches.length,
            likeCount: _likes.length,
          ),
          const SizedBox(height: 18),
          TextField(
            controller: _searchController,
            textInputAction: TextInputAction.search,
            decoration: InputDecoration(
              hintText: switch (_section) {
                1 => 'Rechercher un match',
                2 => 'Rechercher dans les likes',
                _ => 'Rechercher une conversation',
              },
              prefixIcon: const Icon(Icons.search_rounded),
              suffixIcon: _query.isEmpty
                  ? null
                  : IconButton(
                      tooltip: 'Effacer la recherche',
                      onPressed: _searchController.clear,
                      icon: const Icon(Icons.close_rounded),
                    ),
              filled: true,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(22),
                borderSide: BorderSide.none,
              ),
            ),
          ),
          const SizedBox(height: 22),
          SegmentedButton<int>(
            segments: [
              ButtonSegment<int>(
                value: 0,
                label: Text('Messages${_conversations.isEmpty ? '' : ' ${_conversations.length}'}'),
              ),
              ButtonSegment<int>(
                value: 1,
                label: Text('Matchs${_matches.isEmpty ? '' : ' ${_matches.length}'}'),
              ),
              ButtonSegment<int>(
                value: 2,
                label: Text('Likes${_likes.isEmpty ? '' : ' ${_likes.length}'}'),
              ),
            ],
            selected: <int>{_section},
            onSelectionChanged: (value) => setState(() => _section = value.first),
            showSelectedIcon: false,
          ),
          const SizedBox(height: 22),
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 340),
            switchInCurve: Curves.easeOutCubic,
            switchOutCurve: Curves.easeInCubic,
            transitionBuilder: (child, animation) => FadeTransition(
              opacity: animation,
              child: SlideTransition(
                position: Tween<Offset>(
                  begin: const Offset(0.045, 0),
                  end: Offset.zero,
                ).animate(animation),
                child: child,
              ),
            ),
            child: Column(
              key: ValueKey<int>(_section),
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: switch (_section) {
                1 => _matchSection(context),
                2 => _likeSection(context),
                _ => _messageSection(context),
              },
            ),
          ),
        ],
      ),
    );
  }

  List<ConversationSummary> get _visibleConversations => _query.isEmpty
      ? _conversations
      : _conversations.where((conversation) {
          final profile = conversation.otherProfile;
          final haystack = '${profile.displayName} ${profile.city} '
              '${conversation.lastMessage?.body ?? ''}'.toLowerCase();
          return haystack.contains(_query);
        }).toList(growable: false);

  List<MatchSummary> get _visibleMatches => _query.isEmpty
      ? _matches
      : _matches.where((match) {
          final profile = match.otherProfile;
          return '${profile.displayName} ${profile.city} ${profile.datingIntent}'
              .toLowerCase()
              .contains(_query);
        }).toList(growable: false);

  List<ReceivedLike> get _visibleLikes => _query.isEmpty
      ? _likes
      : _likes.where((like) {
          return '${like.displayName ?? ''} ${like.city} ${like.ageRange} ${like.datingIntent}'
              .toLowerCase()
              .contains(_query);
        }).toList(growable: false);

  List<Widget> _messageSection(BuildContext context) => <Widget>[
          Text(
            'Messages',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
          ),
          const SizedBox(height: 12),
          if (_visibleConversations.isEmpty)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    const Icon(Icons.forum_outlined, size: 48),
                    const SizedBox(height: 12),
                    Text(
                      _query.isEmpty
                          ? 'Tes conversations apparaîtront ici après un match.'
                          : 'Aucune conversation ne correspond à ta recherche.',
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            )
          else
            ..._visibleConversations.asMap().entries.map((entry) {
              final index = entry.key;
              final conversation = entry.value;
              final last = conversation.lastMessage;
              final photo = conversation.otherProfile.photos.isEmpty
                  ? null
                  : conversation.otherProfile.photos.first;
              return _StaggeredConnectionEntry(
                order: index,
                child: Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: _PremiumConversationCard(
                    conversation: conversation,
                    photo: photo,
                    time: last == null ? null : _time(last.createdAt),
                    onTap: () => _open(conversation),
                    onProfileTap: () => _showProfilePreview(
                      conversation.otherProfile,
                      onMessage: () => _open(conversation),
                    ),
                  ),
                ),
              );
            }),
        ];

  List<Widget> _matchSection(BuildContext context) => <Widget>[
        Text(
          'Mes matchs',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w800,
              ),
        ),
        const SizedBox(height: 12),
        if (_visibleMatches.isEmpty)
          _ConnectionsEmpty(
            icon: Icons.favorite_border,
            message: _query.isEmpty
                ? 'Tes prochains matchs apparaîtront ici.'
                : 'Aucun match ne correspond à ta recherche.',
          )
        else
          ..._visibleMatches.map((match) {
            final profile = match.otherProfile;
            final photo = profile.photos.isEmpty ? null : profile.photos.first;
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _PremiumMatchCard(
                match: match,
                photo: photo,
                onTap: () => _openMatch(match),
                onProfileTap: () => _showProfilePreview(
                  profile,
                  onMessage: () => _openMatch(match),
                ),
              ),
            );
          }),
      ];

  List<Widget> _likeSection(BuildContext context) => <Widget>[
        Text(
          'Ils s’intéressent à toi',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w800,
              ),
        ),
        const SizedBox(height: 6),
        Text(
          'Leur identité reste protégée jusqu’au match. Réponds sans pression.',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 12),
        if (_visibleLikes.isEmpty)
          _ConnectionsEmpty(
            icon: Icons.visibility_off_outlined,
            message: _query.isEmpty
                ? 'Aucun nouvel intérêt pour le moment.'
                : 'Aucun like ne correspond à ta recherche.',
          )
        else
          ..._visibleLikes.map((like) {
            final busy = _workingLike == like.interactionId;
            final title = like.identityRevealed && like.displayName != null
                ? like.displayName!
                : 'Un profil de ${like.city}';
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Card(
                color: like.superLike
                    ? Theme.of(context).colorScheme.secondaryContainer
                    : null,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(26),
                  side: BorderSide(
                    color: like.superLike
                        ? Theme.of(context)
                            .colorScheme
                            .secondary
                            .withValues(alpha: .38)
                        : Theme.of(context).colorScheme.outlineVariant,
                  ),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          CircleAvatar(
                            radius: 27,
                            backgroundColor: const Color(0xFFFFE2EA),
                            backgroundImage: like.imageUrl != null
                                ? NetworkImage(like.imageUrl!)
                                : null,
                            child: like.imageUrl == null
                                ? Icon(like.hasPhoto
                                    ? Icons.lock_outline
                                    : Icons.person_outline)
                                : null,
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Flexible(
                                      child: Text(
                                        title,
                                        style: const TextStyle(
                                          fontWeight: FontWeight.w800,
                                          fontSize: 16,
                                        ),
                                      ),
                                    ),
                                    if (like.superLike) ...[
                                      const SizedBox(width: 6),
                                      Container(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 8,
                                          vertical: 4,
                                        ),
                                        decoration: BoxDecoration(
                                          color: Theme.of(context)
                                              .colorScheme
                                              .secondary,
                                          borderRadius:
                                              BorderRadius.circular(99),
                                        ),
                                        child: Text(
                                          'SUPER LIKE',
                                          style: Theme.of(context)
                                              .textTheme
                                              .labelSmall
                                              ?.copyWith(
                                                color: Theme.of(context)
                                                    .colorScheme
                                                    .onSecondary,
                                                fontWeight: FontWeight.w900,
                                                letterSpacing: .6,
                                              ),
                                        ),
                                      ),
                                    ],
                                  ],
                                ),
                                Text('${like.ageRange} · ${like.datingIntent}'),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed: busy ? null : () => _respond(like, 'pass'),
                              icon: const Icon(Icons.close_rounded),
                              label: const Text('Passer'),
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: FilledButton.icon(
                              onPressed: busy ? null : () => _respond(like, 'like'),
                              icon: busy
                                  ? const SizedBox.square(
                                      dimension: 16,
                                      child: CircularProgressIndicator(strokeWidth: 2),
                                    )
                                  : const Icon(Icons.favorite_rounded),
                              label: const Text('Accepter'),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            );
          }),
      ];
}

class _PremiumConversationCard extends StatelessWidget {
  const _PremiumConversationCard({
    required this.conversation,
    required this.photo,
    required this.time,
    required this.onTap,
    required this.onProfileTap,
  });

  final ConversationSummary conversation;
  final ProfilePhoto? photo;
  final String? time;
  final VoidCallback onTap;
  final VoidCallback onProfileTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final profile = conversation.otherProfile;
    final unread = conversation.unreadCount > 0;
    return Semantics(
      button: true,
      label: unread
          ? '${profile.displayName}, ${conversation.unreadCount} messages non lus'
          : 'Conversation avec ${profile.displayName}',
      child: Material(
        color: unread ? scheme.primaryContainer : scheme.surface,
        borderRadius: BorderRadius.circular(26),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: () {
            HapticFeedback.lightImpact();
            onTap();
          },
          onLongPress: () {
            HapticFeedback.mediumImpact();
            onProfileTap();
          },
          child: Container(
            padding: const EdgeInsets.all(15),
            decoration: BoxDecoration(
              border: Border.all(
                color: unread
                    ? scheme.primary.withValues(alpha: .3)
                    : scheme.outlineVariant,
              ),
              borderRadius: BorderRadius.circular(26),
            ),
            child: Row(
              children: [
                _PremiumAvatar(
                  imageUrl: photo?.imageUrl,
                  online: conversation.online,
                  heroTag: 'conversation-avatar-${conversation.id}',
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Flexible(
                            child: Text(
                              profile.displayName,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: Theme.of(context)
                                  .textTheme
                                  .titleMedium
                                  ?.copyWith(fontWeight: FontWeight.w900),
                            ),
                          ),
                          if (profile.verified) ...[
                            const SizedBox(width: 5),
                            Icon(Icons.verified_rounded,
                                size: 18, color: scheme.primary),
                          ],
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        conversation.lastMessage?.body ??
                            'Commence la conversation',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              fontWeight:
                                  unread ? FontWeight.w700 : FontWeight.w400,
                              color: scheme.onSurfaceVariant,
                            ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        conversation.online
                            ? 'En ligne maintenant'
                            : profile.city,
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                              color: conversation.online
                                  ? const Color(0xFF238A55)
                                  : scheme.onSurfaceVariant,
                              fontWeight: FontWeight.w700,
                            ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 10),
                Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (time != null)
                      Text(time!, style: Theme.of(context).textTheme.labelSmall),
                    const SizedBox(height: 7),
                    if (unread)
                      Badge(
                        largeSize: 25,
                        label: Text('${conversation.unreadCount}'),
                      )
                    else
                      Icon(Icons.chevron_right_rounded,
                          color: scheme.onSurfaceVariant),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _PremiumMatchCard extends StatelessWidget {
  const _PremiumMatchCard({
    required this.match,
    required this.photo,
    required this.onTap,
    required this.onProfileTap,
  });

  final MatchSummary match;
  final ProfilePhoto? photo;
  final VoidCallback onTap;
  final VoidCallback onProfileTap;

  @override
  Widget build(BuildContext context) {
    final profile = match.otherProfile;
    final scheme = Theme.of(context).colorScheme;
    return Card(
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(26),
        side: BorderSide(color: scheme.outlineVariant),
      ),
      child: InkWell(
        onTap: () {
          HapticFeedback.lightImpact();
          onTap();
        },
        child: SizedBox(
          height: 126,
          child: Row(
            children: [
              SizedBox(
                width: 106,
                height: double.infinity,
                child: photo != null && photo!.imageUrl.isNotEmpty
                    ? Image.network(
                        photo!.imageUrl,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) =>
                            const _PremiumPhotoFallback(),
                      )
                    : const _PremiumPhotoFallback(),
              ),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(15),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Row(
                        children: [
                          Flexible(
                            child: Text(
                              '${profile.displayName}, ${profile.age}',
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: Theme.of(context)
                                  .textTheme
                                  .titleMedium
                                  ?.copyWith(fontWeight: FontWeight.w900),
                            ),
                          ),
                          if (profile.verified) ...[
                            const SizedBox(width: 5),
                            Icon(Icons.verified_rounded,
                                size: 18, color: scheme.primary),
                          ],
                        ],
                      ),
                      const SizedBox(height: 5),
                      Text(
                        '${profile.city} · ${profile.datingIntent}',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(color: scheme.onSurfaceVariant),
                      ),
                      const Spacer(),
                      Row(
                        children: [
                          Icon(Icons.favorite_rounded,
                              size: 16, color: scheme.primary),
                          const SizedBox(width: 5),
                          Text('Nouveau match',
                              style: Theme.of(context).textTheme.labelMedium),
                          const Spacer(),
                          IconButton(
                            tooltip: 'Voir le profil',
                            visualDensity: VisualDensity.compact,
                            onPressed: onProfileTap,
                            icon: const Icon(Icons.person_search_rounded),
                          ),
                          Icon(Icons.chat_bubble_rounded,
                              size: 20, color: scheme.primary),
                        ],
                      ),
                    ],
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

class _PremiumAvatar extends StatelessWidget {
  const _PremiumAvatar({
    required this.imageUrl,
    required this.online,
    required this.heroTag,
  });

  final String? imageUrl;
  final bool online;
  final String heroTag;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Hero(
      tag: heroTag,
      child: Stack(
        children: [
          Container(
            padding: const EdgeInsets.all(2),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [scheme.primary, scheme.secondary],
              ),
              shape: BoxShape.circle,
            ),
            child: CircleAvatar(
              radius: 29,
              backgroundColor: scheme.surfaceContainerHighest,
              backgroundImage: imageUrl != null && imageUrl!.isNotEmpty
                  ? NetworkImage(imageUrl!)
                  : null,
              child: imageUrl == null || imageUrl!.isEmpty
                  ? const Icon(Icons.person_outline)
                  : null,
            ),
          ),
          if (online)
            Positioned(
              right: 1,
              bottom: 1,
              child: Container(
                width: 15,
                height: 15,
                decoration: BoxDecoration(
                  color: const Color(0xFF35C779),
                  shape: BoxShape.circle,
                  border: Border.all(color: scheme.surface, width: 2),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _PremiumPhotoFallback extends StatelessWidget {
  const _PremiumPhotoFallback();

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [scheme.primaryContainer, scheme.secondaryContainer],
        ),
      ),
      child: Icon(Icons.person_rounded, size: 48, color: scheme.primary),
    );
  }
}

class _ProfilePreviewSheet extends StatelessWidget {
  const _ProfilePreviewSheet({
    required this.profile,
    required this.onMessage,
  });

  final DiscoveryProfile profile;
  final VoidCallback onMessage;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final photo = profile.photos.isEmpty ? null : profile.photos.first;
    final reduceMotion = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    return FractionallySizedBox(
      heightFactor: .86,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 4, 18, 28),
        children: [
          TweenAnimationBuilder<double>(
            tween: Tween<double>(begin: 0, end: 1),
            duration: reduceMotion
                ? Duration.zero
                : const Duration(milliseconds: 320),
            curve: Curves.easeOutCubic,
            builder: (context, value, child) => Opacity(
              opacity: value,
              child: Transform.scale(
                scale: .97 + (.03 * value),
                child: child,
              ),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(30),
              child: SizedBox(
                height: 280,
                child: photo != null && photo.imageUrl.isNotEmpty
                    ? Image.network(
                        photo.imageUrl,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) =>
                            const _PremiumPhotoFallback(),
                      )
                    : const _PremiumPhotoFallback(),
              ),
            ),
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: Text(
                  '${profile.displayName}, ${profile.age}',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.w900,
                      ),
                ),
              ),
              if (profile.verified)
                Icon(Icons.verified_rounded, color: scheme.primary, size: 25),
            ],
          ),
          const SizedBox(height: 7),
          Row(
            children: [
              Icon(Icons.location_on_outlined,
                  size: 18, color: scheme.onSurfaceVariant),
              const SizedBox(width: 5),
              Expanded(
                child: Text(
                  [profile.city, profile.distanceLabel]
                      .where((value) => value.isNotEmpty)
                      .join(' · '),
                  style: TextStyle(color: scheme.onSurfaceVariant),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              if (profile.compatibilityScore > 0)
                Chip(
                  avatar: const Icon(Icons.auto_awesome_rounded, size: 17),
                  label: Text('${profile.compatibilityScore}% compatible'),
                ),
              if (profile.datingIntent.isNotEmpty)
                Chip(
                  avatar: const Icon(Icons.favorite_outline_rounded, size: 17),
                  label: Text(profile.datingIntent),
                ),
            ],
          ),
          if (profile.biography.isNotEmpty) ...[
            const SizedBox(height: 22),
            Text(
              'À propos',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w900,
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              profile.biography,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    height: 1.5,
                  ),
            ),
          ],
          if (profile.interestLabels.isNotEmpty) ...[
            const SizedBox(height: 22),
            Text(
              'Centres d’intérêt',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w900,
                  ),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: profile.interestLabels
                  .map((interest) => Chip(label: Text(interest)))
                  .toList(growable: false),
            ),
          ],
          const SizedBox(height: 26),
          FilledButton.icon(
            onPressed: () {
              HapticFeedback.mediumImpact();
              onMessage();
            },
            icon: const Icon(Icons.chat_bubble_rounded),
            label: const Text('Envoyer un message'),
          ),
        ],
      ),
    );
  }
}

class _MessagesHero extends StatelessWidget {
  const _MessagesHero({required this.matchCount, required this.likeCount});

  final int matchCount;
  final int likeCount;

  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<double>(
      tween: Tween<double>(begin: 0, end: 1),
      duration: const Duration(milliseconds: 680),
      curve: Curves.easeOutBack,
      builder: (context, value, child) => Transform.translate(
        offset: Offset(0, 18 * (1 - value)),
        child: Opacity(opacity: value.clamp(0, 1), child: child),
      ),
      child: Container(
        padding: const EdgeInsets.fromLTRB(22, 22, 22, 20),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF6E1235), Color(0xFFB51F50), Color(0xFFE56B6F)],
          ),
          borderRadius: BorderRadius.circular(28),
          boxShadow: const [
            BoxShadow(
              color: Color(0x3DB51F50),
              blurRadius: 28,
              offset: Offset(0, 14),
            ),
          ],
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Tes connexions',
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.w900,
                        ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    '$matchCount match${matchCount > 1 ? 's' : ''} · $likeCount intérêt${likeCount > 1 ? 's' : ''}',
                    style: const TextStyle(color: Color(0xFFFFE9F0)),
                  ),
                ],
              ),
            ),
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.16),
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white.withValues(alpha: 0.28)),
              ),
              child: const Icon(Icons.forum_rounded, color: Colors.white, size: 29),
            ),
          ],
        ),
      ),
    );
  }
}

class _ConnectionsEmpty extends StatelessWidget {
  const _ConnectionsEmpty({required this.icon, required this.message});

  final IconData icon;
  final String message;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            Icon(icon, size: 48),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}

class _StaggeredConnectionEntry extends StatelessWidget {
  const _StaggeredConnectionEntry({required this.order, required this.child});

  final int order;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final reduceMotion = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (reduceMotion) return child;
    return TweenAnimationBuilder<double>(
      tween: Tween<double>(begin: 0, end: 1),
      duration: Duration(milliseconds: 360 + order.clamp(0, 6) * 55),
      curve: Curves.easeOutCubic,
      builder: (context, value, animatedChild) => Opacity(
        opacity: value,
        child: Transform.translate(
          offset: Offset(0, 22 * (1 - value)),
          child: Transform.scale(
            scale: .985 + (.015 * value),
            alignment: Alignment.bottomCenter,
            child: animatedChild,
          ),
        ),
      ),
      child: child,
    );
  }
}

class ConversationPage extends StatefulWidget {
  const ConversationPage({
    super.key,
    required this.api,
    required this.conversation,
  });

  final AuthApi api;
  final ConversationSummary conversation;

  @override
  State<ConversationPage> createState() => _ConversationPageState();
}

class _ConversationPageState extends State<ConversationPage>
    with WidgetsBindingObserver {
  final TextEditingController _composer = TextEditingController();
  final ScrollController _scroll = ScrollController();
  final ImagePicker _imagePicker = ImagePicker();
  List<ChatMessage> _messages = <ChatMessage>[];
  bool _loading = true;
  bool _sending = false;
  bool _otherTyping = false;
  bool _selfTyping = false;
  bool _nearBottom = true;
  bool _refreshingMessages = false;
  int _newMessageCount = 0;
  Timer? _typingDebounce;
  Timer? _typingPoll;
  Timer? _messagePoll;
  String? _error;
  String? _failedBody;
  Uint8List? _pendingImage;
  String? _pendingImageName;
  bool _pickingImage = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _composer.addListener(_onComposerChanged);
    _scroll.addListener(_onScroll);
    _load();
    _pollTyping();
    _typingPoll = Timer.periodic(
      const Duration(seconds: 3),
      (_) => _pollTyping(),
    );
    _startMessagePolling();
  }

  @override
  void dispose() {
    _typingDebounce?.cancel();
    _typingPoll?.cancel();
    _messagePoll?.cancel();
    if (_selfTyping) {
      unawaited(_publishTyping(false));
    }
    _composer.removeListener(_onComposerChanged);
    _scroll.removeListener(_onScroll);
    _composer.dispose();
    _scroll.dispose();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _startMessagePolling();
      unawaited(_syncMessages());
    } else if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.inactive ||
        state == AppLifecycleState.detached ||
        state == AppLifecycleState.hidden) {
      _messagePoll?.cancel();
      _messagePoll = null;
    }
  }

  void _startMessagePolling() {
    _messagePoll?.cancel();
    _messagePoll = Timer.periodic(
      const Duration(seconds: 4),
      (_) => unawaited(_syncMessages()),
    );
  }

  void _onScroll() {
    if (!_scroll.hasClients) return;
    final nearBottom =
        _scroll.position.maxScrollExtent - _scroll.position.pixels < 96;
    if (nearBottom != _nearBottom && mounted) {
      setState(() {
        _nearBottom = nearBottom;
        if (nearBottom) _newMessageCount = 0;
      });
      if (nearBottom) {
        unawaited(_markReadQuietly());
      }
    }
  }

  void _onComposerChanged() {
    _typingDebounce?.cancel();
    final hasText = _composer.text.trim().isNotEmpty;
    if (hasText && !_selfTyping) {
      _selfTyping = true;
      unawaited(_publishTyping(true));
    } else if (!hasText && _selfTyping) {
      _selfTyping = false;
      unawaited(_publishTyping(false));
    }
    if (hasText) {
      _typingDebounce = Timer(const Duration(milliseconds: 1200), () {
        if (!_selfTyping) return;
        _selfTyping = false;
        unawaited(_publishTyping(false));
      });
    }
  }

  Future<void> _publishTyping(bool isTyping) async {
    try {
      await widget.api.setTypingStatus(widget.conversation.id, isTyping);
    } catch (_) {
      // Typing presence is best-effort and never interrupts message editing.
    }
  }

  Future<void> _markReadQuietly() async {
    try {
      await widget.api.markConversationRead(widget.conversation.id);
    } catch (_) {
      // Read receipts are resynchronised during the next successful refresh.
    }
  }

  Future<void> _pollTyping() async {
    try {
      final typing = await widget.api.getTypingStatus(widget.conversation.id);
      if (mounted && typing != _otherTyping) {
        setState(() => _otherTyping = typing);
      }
    } catch (_) {
      // Typing presence is ephemeral and must never block the conversation.
    }
  }

  Future<void> _syncMessages() async {
    if (_refreshingMessages || _loading) return;
    _refreshingMessages = true;
    try {
      final fresh = await widget.api.getMessages(widget.conversation.id);
      if (!mounted) return;
      final knownIds = _messages.map((message) => message.id).toSet();
      final incoming = fresh
          .where((message) => !knownIds.contains(message.id))
          .length;
      if (incoming == 0 && fresh.length == _messages.length) return;

      final shouldFollow = _nearBottom;
      setState(() {
        _messages = fresh;
        if (!shouldFollow) _newMessageCount += incoming;
      });
      if (shouldFollow) {
        await widget.api.markConversationRead(widget.conversation.id);
        _scrollToEnd(force: false);
      }
    } catch (_) {
      // A background refresh is best-effort; explicit actions still report errors.
    } finally {
      _refreshingMessages = false;
    }
  }

  Future<void> _load() async {
    try {
      final messages = await widget.api.getMessages(widget.conversation.id);
      await widget.api.markConversationRead(widget.conversation.id);
      if (!mounted) return;
      setState(() {
        _messages = messages;
        _error = null;
      });
      _scrollToEnd();
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _scrollToEnd({bool force = true}) {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients && (force || _nearBottom)) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _send() async {
    final body = _composer.text.trim();
    if (_sending || (body.isEmpty && _pendingImage == null)) return;
    final image = _pendingImage;
    final imageName = _pendingImageName;
    setState(() {
      _sending = true;
      _error = null;
      _failedBody = null;
    });
    try {
      final message = await widget.api.sendMessage(
        widget.conversation.id,
        body,
        imageBytes: image,
        imageFilename: imageName,
      );
      if (!mounted) return;
      _composer.clear();
      setState(() {
        _failedBody = null;
        _pendingImage = null;
        _pendingImageName = null;
        if (!_messages.any((item) => item.id == message.id)) {
          _messages = <ChatMessage>[..._messages, message];
        }
      });
      _scrollToEnd();
    } catch (error) {
      if (mounted) {
        setState(() {
          _error = friendlyError(error);
          _failedBody = body;
        });
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _pickMessageImage() async {
    if (_sending || _pickingImage) return;
    setState(() => _pickingImage = true);
    try {
      final picked = await _imagePicker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 85,
        maxWidth: 1600,
        maxHeight: 1600,
        requestFullMetadata: false,
      );
      if (picked == null || !mounted) return;
      final bytes = await picked.readAsBytes();
      if (bytes.isEmpty || bytes.length > 8 * 1024 * 1024) {
        throw const FormatException('La photo doit peser moins de 8 Mo.');
      }
      if (!mounted) return;
      setState(() {
        _pendingImage = bytes;
        _pendingImageName = picked.name;
        _error = null;
      });
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _pickingImage = false);
    }
  }

  Future<void> _openSafetyActions() async {
    final changed = await showProfileSafetyActions(
      context: context,
      api: widget.api,
      profile: widget.conversation.otherProfile,
      matchId: widget.conversation.matchId,
    );
    if (changed && mounted) Navigator.of(context).pop();
  }

  String _time(DateTime value) {
    final local = value.toLocal();
    return '${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}';
  }

  bool _sameDay(DateTime first, DateTime second) {
    final a = first.toLocal();
    final b = second.toLocal();
    return a.year == b.year && a.month == b.month && a.day == b.day;
  }

  String _dateLabel(DateTime value) {
    final date = value.toLocal();
    final now = DateTime.now();
    if (_sameDay(date, now)) return 'Aujourd’hui';
    if (_sameDay(date, now.subtract(const Duration(days: 1)))) return 'Hier';
    return '${date.day.toString().padLeft(2, '0')}/'
        '${date.month.toString().padLeft(2, '0')}/${date.year}';
  }

  @override
  Widget build(BuildContext context) {
    final profile = widget.conversation.otherProfile;
    final photo = profile.photos.isEmpty ? null : profile.photos.first;
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 0,
        title: Row(
          children: [
            Hero(
              tag: 'conversation-avatar-${widget.conversation.id}',
              child: CircleAvatar(
                radius: 20,
                backgroundColor: scheme.primaryContainer,
                backgroundImage: photo != null && photo.imageUrl.isNotEmpty
                    ? NetworkImage(photo.imageUrl)
                    : null,
                child: photo == null || photo.imageUrl.isEmpty
                    ? const Icon(Icons.person_outline)
                    : null,
              ),
            ),
            const SizedBox(width: 11),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  profile.displayName,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                Row(
                  children: [
                    Container(
                      width: 7,
                      height: 7,
                      decoration: BoxDecoration(
                        color: widget.conversation.online
                            ? const Color(0xFF38A169)
                            : scheme.outline,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 5),
                    Text(
                      widget.conversation.online ? 'En ligne' : 'Hors ligne',
                      style: Theme.of(context).textTheme.labelSmall,
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'Actions de sécurité',
            onPressed: _openSafetyActions,
            icon: const Icon(Icons.more_vert),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: Stack(
                children: [
                  Positioned.fill(
                    child: _loading
                        ? const Center(child: CircularProgressIndicator())
                        : _messages.isEmpty
                            ? const Center(
                                child: Text(
                                  'Envoie un premier message respectueux.',
                                ),
                              )
                            : ListView.builder(
                                controller: _scroll,
                                padding: const EdgeInsets.all(16),
                                itemCount: _messages.length,
                                itemBuilder: (context, index) {
                                  final message = _messages[index];
                                  final showDate = index == 0 ||
                                      !_sameDay(
                                        _messages[index - 1].createdAt,
                                        message.createdAt,
                                      );
                                  return Column(
                                    key: ValueKey<String>(message.id),
                                    children: [
                                      if (showDate)
                                        _ConversationDateDivider(
                                          label: _dateLabel(message.createdAt),
                                        ),
                                      _AnimatedMessageBubble(
                                        message: message,
                                        time: _time(message.createdAt),
                                        order: index,
                                      ),
                                    ],
                                  );
                                },
                              ),
                  ),
                  if ((!_nearBottom || _newMessageCount > 0) && !_loading)
                    Positioned(
                      right: 16,
                      bottom: 12,
                      child: FloatingActionButton.extended(
                        heroTag: 'conversation-scroll-bottom',
                        tooltip: 'Aller aux messages récents',
                        onPressed: () {
                          setState(() {
                            _nearBottom = true;
                            _newMessageCount = 0;
                          });
                          unawaited(_markReadQuietly());
                          _scrollToEnd();
                        },
                        icon: const Icon(Icons.keyboard_arrow_down_rounded),
                        label: Text(
                          _newMessageCount > 0
                              ? '$_newMessageCount ${_newMessageCount > 1 ? 'nouveaux' : 'nouveau'}'
                              : 'Messages récents',
                        ),
                      ),
                    ),
                ],
              ),
            ),
            AnimatedSwitcher(
              duration: const Duration(milliseconds: 180),
              child: _otherTyping
                  ? Padding(
                      key: const ValueKey<String>('typing'),
                      padding: const EdgeInsets.fromLTRB(18, 4, 18, 8),
                      child: Align(
                        alignment: Alignment.centerLeft,
                        child: Semantics(
                          liveRegion: true,
                          label: '${profile.displayName} écrit',
                          child: _TypingIndicator(name: profile.displayName),
                        ),
                      ),
                    )
                  : const SizedBox.shrink(key: ValueKey<String>('idle')),
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 2, 16, 8),
                child: _MessageSendError(
                  message: _error!,
                  canRetry: _failedBody != null,
                  sending: _sending,
                  onRetry: _send,
                  onDismiss: () => setState(() {
                    _error = null;
                    _failedBody = null;
                  }),
                ),
              ),
            Container(
              padding: const EdgeInsets.fromLTRB(12, 10, 12, 14),
              decoration: BoxDecoration(
                color: scheme.surface,
                border: Border(top: BorderSide(color: scheme.outlineVariant)),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x12000000),
                    blurRadius: 20,
                    offset: Offset(0, -8),
                  ),
                ],
              ),
              child: SafeArea(
                top: false,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (_pendingImage != null)
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Stack(
                          children: [
                            ClipRRect(
                              borderRadius: BorderRadius.circular(18),
                              child: Image.memory(
                                _pendingImage!,
                                width: 104,
                                height: 104,
                                fit: BoxFit.cover,
                                gaplessPlayback: true,
                              ),
                            ),
                            Positioned(
                              right: 4,
                              top: 4,
                              child: IconButton.filledTonal(
                                tooltip: 'Retirer la photo',
                                visualDensity: VisualDensity.compact,
                                onPressed: _sending
                                    ? null
                                    : () => setState(() {
                                          _pendingImage = null;
                                          _pendingImageName = null;
                                        }),
                                icon: const Icon(Icons.close_rounded, size: 18),
                              ),
                            ),
                          ],
                        ),
                      ),
                    if (_pendingImage != null) const SizedBox(height: 10),
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        IconButton(
                          tooltip: 'Ajouter une photo',
                          onPressed: _sending || _pickingImage
                              ? null
                              : _pickMessageImage,
                          icon: _pickingImage
                              ? const SizedBox.square(
                                  dimension: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Icon(Icons.add_photo_alternate_rounded),
                        ),
                        Expanded(
                          child: TextField(
                        controller: _composer,
                        enabled: !_sending,
                        minLines: 1,
                        maxLines: 5,
                        maxLength: 2000,
                        textCapitalization: TextCapitalization.sentences,
                        keyboardType: TextInputType.multiline,
                        textInputAction: TextInputAction.newline,
                        decoration: InputDecoration(
                          hintText: 'Écris un message…',
                          counterText: '',
                          filled: true,
                          fillColor: scheme.surfaceContainerHighest,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(24),
                            borderSide: BorderSide.none,
                          ),
                        ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        IconButton.filled(
                      tooltip: 'Envoyer',
                      onPressed: _sending ? null : _send,
                      style: IconButton.styleFrom(
                        minimumSize: const Size.square(52),
                      ),
                      icon: _sending
                          ? const SizedBox.square(
                              dimension: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.arrow_upward_rounded),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ConversationDateDivider extends StatelessWidget {
  const _ConversationDateDivider({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.fromLTRB(0, 8, 0, 18),
      child: Row(
        children: [
          Expanded(child: Divider(color: scheme.outlineVariant)),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Text(
              label,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                    fontWeight: FontWeight.w700,
                    letterSpacing: .35,
                  ),
            ),
          ),
          Expanded(child: Divider(color: scheme.outlineVariant)),
        ],
      ),
    );
  }
}

class _MessageSendError extends StatelessWidget {
  const _MessageSendError({
    required this.message,
    required this.canRetry,
    required this.sending,
    required this.onRetry,
    required this.onDismiss,
  });

  final String message;
  final bool canRetry;
  final bool sending;
  final VoidCallback onRetry;
  final VoidCallback onDismiss;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Semantics(
      liveRegion: true,
      child: Material(
        color: scheme.errorContainer,
        borderRadius: BorderRadius.circular(18),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 9, 6, 9),
          child: Row(
            children: [
              Icon(Icons.cloud_off_rounded, color: scheme.onErrorContainer),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  message,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: scheme.onErrorContainer,
                        fontWeight: FontWeight.w600,
                      ),
                ),
              ),
              if (canRetry)
                TextButton(
                  onPressed: sending ? null : onRetry,
                  child: const Text('Réessayer'),
                ),
              IconButton(
                tooltip: 'Masquer l’erreur',
                onPressed: onDismiss,
                icon: const Icon(Icons.close_rounded),
                color: scheme.onErrorContainer,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TypingIndicator extends StatefulWidget {
  const _TypingIndicator({required this.name});

  final String name;

  @override
  State<_TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<_TypingIndicator>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final reduceMotion = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    final color = Theme.of(context).colorScheme.primary;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          '${widget.name} écrit',
          style: Theme.of(context).textTheme.labelMedium,
        ),
        const SizedBox(width: 7),
        ...List<Widget>.generate(3, (index) {
          return Padding(
            padding: const EdgeInsets.only(right: 3),
            child: AnimatedBuilder(
              animation: _controller,
              builder: (context, _) {
                final phase = reduceMotion
                    ? 1.0
                    : ((_controller.value * 3 - index) % 3).clamp(0.0, 1.0);
                return Transform.translate(
                  offset: Offset(0, -2 * Curves.easeInOut.transform(phase)),
                  child: CircleAvatar(radius: 2.5, backgroundColor: color),
                );
              },
            ),
          );
        }),
      ],
    );
  }
}

class _AnimatedMessageBubble extends StatelessWidget {
  const _AnimatedMessageBubble({
    required this.message,
    required this.time,
    required this.order,
  });

  final ChatMessage message;
  final String time;
  final int order;

  Future<void> _showActions(BuildContext context) async {
    HapticFeedback.selectionClick();
    final shouldCopy = await showModalBottomSheet<bool>(
      context: context,
      showDragHandle: true,
      builder: (sheetContext) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(12, 2, 12, 10),
                child: Text(
                  'Actions du message',
                  style: Theme.of(sheetContext).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
              ),
              ListTile(
                leading: const Icon(Icons.content_copy_rounded),
                title: const Text('Copier le message'),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                onTap: () => Navigator.of(sheetContext).pop(true),
              ),
              TextButton(
                onPressed: () => Navigator.of(sheetContext).pop(false),
                child: const Text('Fermer'),
              ),
            ],
          ),
        ),
      ),
    );
    if (shouldCopy != true || !context.mounted) return;
    await Clipboard.setData(ClipboardData(text: message.body));
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Message copié.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final mine = message.mine;
    final reduceMotion = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    return TweenAnimationBuilder<double>(
      tween: Tween<double>(begin: 0, end: 1),
      duration: reduceMotion
          ? Duration.zero
          : Duration(milliseconds: 260 + (order.clamp(0, 6) * 35)),
      curve: Curves.easeOutCubic,
      builder: (context, value, child) => Opacity(
        opacity: value,
        child: Transform.translate(
          offset: Offset((mine ? 18 : -18) * (1 - value), 5 * (1 - value)),
          child: child,
        ),
      ),
      child: Align(
        alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
        child: GestureDetector(
          onLongPress: () => _showActions(context),
          child: Container(
            constraints: const BoxConstraints(maxWidth: 320),
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.fromLTRB(15, 11, 15, 8),
            decoration: BoxDecoration(
              gradient: mine
                  ? const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [Color(0xFFC52C61), Color(0xFF8B1744)],
                    )
                  : null,
              color: mine ? null : scheme.surfaceContainerHighest,
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(20),
                topRight: const Radius.circular(20),
                bottomLeft: Radius.circular(mine ? 20 : 5),
                bottomRight: Radius.circular(mine ? 5 : 20),
              ),
              boxShadow: mine
                  ? const [
                      BoxShadow(
                        color: Color(0x2E8B1744),
                        blurRadius: 18,
                        offset: Offset(0, 7),
                      ),
                    ]
                  : null,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                if (message.imageBytes != null || message.imageUrl != null) ...[
                  ClipRRect(
                    borderRadius: BorderRadius.circular(14),
                    child: message.imageBytes != null
                        ? Image.memory(
                            message.imageBytes!,
                            width: 250,
                            height: 230,
                            fit: BoxFit.cover,
                            gaplessPlayback: true,
                          )
                        : Image.network(
                            message.imageUrl!,
                            width: 250,
                            height: 230,
                            fit: BoxFit.cover,
                            errorBuilder: (_, __, ___) => const SizedBox(
                              width: 250,
                              height: 120,
                              child: Center(
                                child: Icon(Icons.broken_image_outlined),
                              ),
                            ),
                          ),
                  ),
                  if (message.body.isNotEmpty) const SizedBox(height: 9),
                ],
                Text(
                  message.body,
                  style: TextStyle(
                    color: mine ? Colors.white : scheme.onSurface,
                  ),
                ),
                const SizedBox(height: 4),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      time,
                      style: Theme.of(context).textTheme.labelSmall?.copyWith(
                            color: mine
                                ? Colors.white70
                                : scheme.onSurfaceVariant,
                          ),
                    ),
                    if (mine && message.readReceiptsAvailable) ...[
                      const SizedBox(width: 4),
                      Icon(
                        message.read ? Icons.done_all : Icons.done,
                        size: 15,
                        color: message.read
                            ? const Color(0xFF9FE7FF)
                            : Colors.white70,
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
