import 'package:flutter/material.dart';

import 'auth_contract.dart';
import 'safety_actions.dart';

class MessagesPage extends StatefulWidget {
  const MessagesPage({super.key, required this.api});

  final AuthApi api;

  @override
  State<MessagesPage> createState() => _MessagesPageState();
}

class _MessagesPageState extends State<MessagesPage> {
  List<ConversationSummary> _conversations = <ConversationSummary>[];
  List<MatchSummary> _matches = <MatchSummary>[];
  List<ReceivedLike> _likes = <ReceivedLike>[];
  int _section = 0;
  bool _loading = true;
  String? _workingLike;
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
      final conversations = await widget.api.getConversations();
      final matches = await widget.api.getMatches();
      final likes = await widget.api.getReceivedLikes();
      if (mounted) {
        setState(() {
          _conversations = conversations;
          _matches = matches;
          _likes = likes;
        });
      }
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
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
    await Navigator.of(context).push<void>(
      MaterialPageRoute<void>(
        builder: (context) => ConversationPage(
          api: widget.api,
          conversation: conversation,
        ),
      ),
    );
    await _load();
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

  List<Widget> _messageSection(BuildContext context) => <Widget>[
          Text(
            'Messages',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
          ),
          const SizedBox(height: 12),
          if (_conversations.isEmpty)
            const Card(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Column(
                  children: [
                    Icon(Icons.forum_outlined, size: 48),
                    SizedBox(height: 12),
                    Text(
                      'Tes conversations apparaîtront ici après un match.',
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            )
          else
            ..._conversations.map((conversation) {
              final last = conversation.lastMessage;
              final photo = conversation.otherProfile.photos.isEmpty
                  ? null
                  : conversation.otherProfile.photos.first;
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Card(
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 10,
                    ),
                    onTap: () => _open(conversation),
                    leading: Stack(
                      children: [
                        CircleAvatar(
                          radius: 26,
                          backgroundColor: const Color(0xFFFFD8E3),
                          backgroundImage:
                              photo != null && photo.imageUrl.isNotEmpty
                                  ? NetworkImage(photo.imageUrl)
                                  : null,
                          child: photo == null || photo.imageUrl.isEmpty
                              ? const Icon(Icons.person_outline)
                              : null,
                        ),
                        if (conversation.online)
                          Positioned(
                            right: 0,
                            bottom: 0,
                            child: Container(
                              width: 14,
                              height: 14,
                              decoration: BoxDecoration(
                                color: Colors.green,
                                shape: BoxShape.circle,
                                border: Border.all(
                                  color: Theme.of(context).colorScheme.surface,
                                  width: 2,
                                ),
                              ),
                            ),
                          ),
                      ],
                    ),
                    title: Text(
                      conversation.otherProfile.displayName,
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                    subtitle: Text(
                      last?.body ?? 'Commence la conversation',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    trailing: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        if (last != null)
                          Text(
                            _time(last.createdAt),
                            style: Theme.of(context).textTheme.labelSmall,
                          ),
                        if (conversation.unreadCount > 0) ...[
                          const SizedBox(height: 4),
                          Badge(label: Text('${conversation.unreadCount}')),
                        ],
                      ],
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
        if (_matches.isEmpty)
          const _ConnectionsEmpty(
            icon: Icons.favorite_border,
            message: 'Tes prochains matchs apparaîtront ici.',
          )
        else
          ..._matches.map((match) {
            final profile = match.otherProfile;
            final photo = profile.photos.isEmpty ? null : profile.photos.first;
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Card(
                child: ListTile(
                  contentPadding: const EdgeInsets.all(14),
                  onTap: () => _openMatch(match),
                  leading: CircleAvatar(
                    radius: 28,
                    backgroundColor: const Color(0xFFFFD8E3),
                    backgroundImage: photo != null && photo.imageUrl.isNotEmpty
                        ? NetworkImage(photo.imageUrl)
                        : null,
                    child: photo == null || photo.imageUrl.isEmpty
                        ? const Icon(Icons.person_outline)
                        : null,
                  ),
                  title: Text(
                    '${profile.displayName}, ${profile.age}',
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                  subtitle: Text('${profile.city} · ${profile.datingIntent}'),
                  trailing: const Icon(Icons.chat_bubble_rounded),
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
        if (_likes.isEmpty)
          const _ConnectionsEmpty(
            icon: Icons.visibility_off_outlined,
            message: 'Aucun nouvel intérêt pour le moment.',
          )
        else
          ..._likes.map((like) {
            final busy = _workingLike == like.interactionId;
            final title = like.identityRevealed && like.displayName != null
                ? like.displayName!
                : 'Un profil de ${like.city}';
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Card(
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
                                      const Icon(
                                        Icons.star_rounded,
                                        color: Color(0xFF6750A4),
                                        size: 20,
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

class _ConversationPageState extends State<ConversationPage> {
  final TextEditingController _composer = TextEditingController();
  final ScrollController _scroll = ScrollController();
  List<ChatMessage> _messages = <ChatMessage>[];
  bool _loading = true;
  bool _sending = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _composer.dispose();
    _scroll.dispose();
    super.dispose();
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

  void _scrollToEnd() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
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
    if (_sending || body.isEmpty) return;
    setState(() {
      _sending = true;
      _error = null;
    });
    try {
      final message = await widget.api.sendMessage(
        widget.conversation.id,
        body,
      );
      if (!mounted) return;
      _composer.clear();
      setState(() => _messages = <ChatMessage>[..._messages, message]);
      _scrollToEnd();
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _sending = false);
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

  @override
  Widget build(BuildContext context) {
    final profile = widget.conversation.otherProfile;
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(profile.displayName),
            Text(
              widget.conversation.online ? 'En ligne' : 'Hors ligne',
              style: Theme.of(context).textTheme.labelSmall,
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
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : _messages.isEmpty
                      ? const Center(
                          child: Text('Envoie un premier message respectueux.'),
                        )
                      : ListView.builder(
                          controller: _scroll,
                          padding: const EdgeInsets.all(16),
                          itemCount: _messages.length,
                          itemBuilder: (context, index) {
                            final message = _messages[index];
                            return Align(
                              alignment: message.mine
                                  ? Alignment.centerRight
                                  : Alignment.centerLeft,
                              child: Container(
                                constraints: const BoxConstraints(maxWidth: 320),
                                margin: const EdgeInsets.only(bottom: 10),
                                padding: const EdgeInsets.fromLTRB(14, 10, 14, 8),
                                decoration: BoxDecoration(
                                  color: message.mine
                                      ? Theme.of(context).colorScheme.primaryContainer
                                      : Theme.of(context).colorScheme.surfaceContainerHighest,
                                  borderRadius: BorderRadius.circular(18),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Text(message.body),
                                    const SizedBox(height: 4),
                                    Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Text(
                                          _time(message.createdAt),
                                          style: Theme.of(context).textTheme.labelSmall,
                                        ),
                                        if (message.mine &&
                                            message.readReceiptsAvailable) ...[
                                          const SizedBox(width: 4),
                                          Icon(
                                            message.read
                                                ? Icons.done_all
                                                : Icons.done,
                                            size: 15,
                                          ),
                                        ],
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Text(
                  _error!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ),
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Expanded(
                    child: TextField(
                      controller: _composer,
                      enabled: !_sending,
                      minLines: 1,
                      maxLines: 5,
                      maxLength: 2000,
                      textCapitalization: TextCapitalization.sentences,
                      decoration: const InputDecoration(
                        hintText: 'Écris un message…',
                        counterText: '',
                      ),
                      onSubmitted: (_) => _send(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    tooltip: 'Envoyer',
                    onPressed: _sending ? null : _send,
                    icon: _sending
                        ? const SizedBox.square(
                            dimension: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.send),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
