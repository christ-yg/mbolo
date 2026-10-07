import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';

import 'auth_contract.dart';
import 'messages.dart';
import 'notifications.dart';
import 'premium.dart';
import 'safety_actions.dart';
import 'security.dart';
import 'showcase.dart';

class MboloHome extends StatefulWidget {
  const MboloHome({
    super.key,
    required this.account,
    required this.api,
    required this.onLogout,
    required this.onAccountClosed,
    required this.themeMode,
    required this.onThemeChanged,
  });

  final Account account;
  final AuthApi api;
  final Future<void> Function() onLogout;
  final Future<void> Function() onAccountClosed;
  final ThemeMode themeMode;
  final ValueChanged<ThemeMode> onThemeChanged;

  @override
  State<MboloHome> createState() => _MboloHomeState();
}

class _MboloHomeState extends State<MboloHome> {
  int _tab = 0;
  List<DiscoveryProfile> _profiles = <DiscoveryProfile>[];
  bool _discoveryLoading = true;
  bool _deciding = false;
  int _notificationUnread = 0;
  SuperLikeState? _superLikeState;
  RewindState? _rewindState;
  String? _discoveryError;

  @override
  void initState() {
    super.initState();
    _loadDiscovery();
    _loadNotificationCount();
    _loadPremiumActions();
  }

  Future<void> _loadPremiumActions() async {
    try {
      final superLike = await widget.api.getSuperLikeState();
      final rewind = await widget.api.getRewindState();
      if (!mounted) return;
      setState(() {
        _superLikeState = superLike;
        _rewindState = rewind;
      });
    } catch (_) {
      // Discovery remains usable when premium counters cannot refresh.
    }
  }

  Future<void> _loadNotificationCount() async {
    try {
      final count = await widget.api.getNotificationUnreadCount();
      if (mounted) setState(() => _notificationUnread = count);
    } catch (_) {
      // The main experience remains available when the badge cannot refresh.
    }
  }

  Future<void> _openNotifications() async {
    await Navigator.of(context).push<void>(
      MaterialPageRoute<void>(
        builder: (context) => NotificationsPage(api: widget.api),
      ),
    );
    await _loadNotificationCount();
  }

  Future<void> _loadDiscovery() async {
    setState(() {
      _discoveryLoading = true;
      _discoveryError = null;
    });
    try {
      final profiles = await widget.api.getDiscovery();
      if (!mounted) return;
      setState(() => _profiles = profiles);
    } catch (error) {
      if (mounted) setState(() => _discoveryError = friendlyError(error));
    } finally {
      if (mounted) setState(() => _discoveryLoading = false);
    }
  }

  Future<void> _next({required bool liked, bool superLike = false}) async {
    if (_deciding || _profiles.isEmpty) return;
    if (superLike) {
      await HapticFeedback.mediumImpact();
    } else {
      await HapticFeedback.lightImpact();
    }
    final current = _profiles.first;
    setState(() => _deciding = true);
    try {
      final result = await widget.api.decideProfile(
        profileId: current.id,
        decision: liked ? 'like' : 'pass',
        superLike: superLike,
      );
      if (!mounted) return;
      setState(() {
        _profiles = _profiles.skip(1).toList(growable: false);
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            result.matched
                ? 'C’est un match avec ${current.displayName} !'
                : superLike
                ? 'Super Like envoyé à ${current.displayName} ⭐'
                : liked
                ? 'Intérêt envoyé avec respect.'
                : 'Profil passé.',
          ),
        ),
      );
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(friendlyError(error))),
        );
      }
    } finally {
      if (mounted) setState(() => _deciding = false);
      await _loadPremiumActions();
    }
  }

  Future<void> _rewind() async {
    if (_deciding || _rewindState?.available != true) return;
    await HapticFeedback.selectionClick();
    setState(() => _deciding = true);
    try {
      final profile = await widget.api.rewindLastPass();
      if (!mounted) return;
      setState(() {
        _profiles = <DiscoveryProfile>[
          profile,
          ..._profiles.where((item) => item.id != profile.id),
        ];
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${profile.displayName} est de retour.')),
      );
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(friendlyError(error))),
        );
      }
    } finally {
      if (mounted) setState(() => _deciding = false);
      await _loadPremiumActions();
    }
  }

  Future<void> _openProfileEditor() async {
    await Navigator.of(context).push<void>(
      MaterialPageRoute<void>(
        builder: (context) => _ProfileEditorPage(api: widget.api),
      ),
    );
  }

  Future<void> _openPreferences() async {
    await Navigator.of(context).push<void>(
      MaterialPageRoute<void>(
        builder: (context) => _PreferencesPage(api: widget.api),
      ),
    );
    await _loadDiscovery();
  }

  Future<void> _openPhotos() async {
    await Navigator.of(context).push<void>(
      MaterialPageRoute<void>(
        builder: (context) => _PhotosPage(api: widget.api),
      ),
    );
  }

  Future<void> _openPremium() async {
    await Navigator.of(context).push<void>(MaterialPageRoute<void>(builder: (context) => PremiumPage(api: widget.api)));
    await _loadPremiumActions();
  }

  Future<void> _openShowcase() async {
    await Navigator.of(context).push<void>(
      PageRouteBuilder<void>(
        pageBuilder: (context, animation, secondaryAnimation) => const MboloShowcasePage(),
        transitionsBuilder: (context, animation, secondaryAnimation, child) => FadeTransition(
          opacity: CurvedAnimation(parent: animation, curve: Curves.easeOutCubic),
          child: ScaleTransition(scale: Tween<double>(begin: 0.98, end: 1).animate(animation), child: child),
        ),
      ),
    );
  }

  Widget _discoveryPage() {
    if (_discoveryLoading) {
      return const _DiscoverySkeleton();
    }
    if (_discoveryError != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.cloud_off_outlined, size: 52),
              const SizedBox(height: 12),
              Text(_discoveryError!, textAlign: TextAlign.center),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: _loadDiscovery,
                child: const Text('Réessayer'),
              ),
            ],
          ),
        ),
      );
    }
    if (_profiles.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.favorite_border, size: 56),
              const SizedBox(height: 12),
              const Text(
                'Tu as vu tous les profils disponibles pour le moment.',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              OutlinedButton(
                onPressed: _loadDiscovery,
                child: const Text('Actualiser'),
              ),
              if (_rewindState?.available == true) ...[
                const SizedBox(height: 10),
                FilledButton.icon(
                  onPressed: _deciding ? null : _rewind,
                  icon: const Icon(Icons.replay_rounded),
                  label: const Text('Revenir au dernier profil'),
                ),
              ],
            ],
          ),
        ),
      );
    }
    return _DiscoverPage(
      profile: _profiles.first,
      api: widget.api,
      onNext: _next,
      onRewind: _rewind,
      superLikeState: _superLikeState,
      rewindState: _rewindState,
      onSafetyComplete: () => setState(() {
        _profiles = _profiles.skip(1).toList(growable: false);
      }),
      working: _deciding,
    );
  }

  @override
  Widget build(BuildContext context) {
    final pages = <Widget>[
      _discoveryPage(),
      MessagesPage(api: widget.api),
      SecurityPage(
        api: widget.api,
        initialAccount: widget.account,
        onAccountClosed: widget.onAccountClosed,
      ),
      _ProfilePage(
        account: widget.account,
        onLogout: widget.onLogout,
        onEditProfile: _openProfileEditor,
        onEditPhotos: _openPhotos,
        onEditPreferences: _openPreferences,
        onPremium: _openPremium,
        onShowcase: _openShowcase,
      ),
    ];
    return Scaffold(
      appBar: AppBar(
        title: const _MboloWordmark(),
        actions: [
          PopupMenuButton<ThemeMode>(
            tooltip: 'Apparence',
            initialValue: widget.themeMode,
            onSelected: widget.onThemeChanged,
            icon: Icon(widget.themeMode == ThemeMode.dark ? Icons.dark_mode_rounded : Icons.brightness_6_rounded),
            itemBuilder: (context) => const [
              PopupMenuItem(value: ThemeMode.system, child: ListTile(leading: Icon(Icons.settings_brightness), title: Text('Système'))),
              PopupMenuItem(value: ThemeMode.light, child: ListTile(leading: Icon(Icons.light_mode), title: Text('Clair'))),
              PopupMenuItem(value: ThemeMode.dark, child: ListTile(leading: Icon(Icons.dark_mode), title: Text('Sombre'))),
            ],
          ),
          IconButton(
            tooltip: 'Notifications',
            onPressed: _openNotifications,
            icon: Badge(
              isLabelVisible: _notificationUnread > 0,
              label: Text(
                _notificationUnread > 99 ? '99+' : '$_notificationUnread',
              ),
              child: const Icon(Icons.notifications_none_rounded),
            ),
          ),
          IconButton(
            tooltip: 'Sécurité',
            onPressed: () => setState(() => _tab = 2),
            icon: const Icon(Icons.shield_outlined),
          ),
        ],
      ),
      body: SafeArea(
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 320),
          switchInCurve: Curves.easeOutCubic,
          switchOutCurve: Curves.easeInCubic,
          transitionBuilder: (child, animation) => FadeTransition(
            opacity: animation,
            child: SlideTransition(
              position: Tween<Offset>(
                begin: const Offset(0.035, 0),
                end: Offset.zero,
              ).animate(animation),
              child: child,
            ),
          ),
          child: KeyedSubtree(key: ValueKey<int>(_tab), child: pages[_tab]),
        ),
      ),
      bottomNavigationBar: DecoratedBox(
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surface,
          boxShadow: [
            BoxShadow(
              color: Color(0x18000000),
              blurRadius: 24,
              offset: Offset(0, -8),
            ),
          ],
        ),
        child: NavigationBar(
          selectedIndex: _tab,
          onDestinationSelected: (value) {
            if (value == _tab) return;
            HapticFeedback.selectionClick();
            setState(() => _tab = value);
          },
          destinations: const [
          NavigationDestination(
            icon: Icon(Icons.favorite_outline),
            selectedIcon: Icon(Icons.favorite),
            label: 'Découvrir',
          ),
          NavigationDestination(
            icon: Icon(Icons.chat_bubble_outline),
            selectedIcon: Icon(Icons.chat_bubble),
            label: 'Messages',
          ),
          NavigationDestination(
            icon: Icon(Icons.shield_outlined),
            selectedIcon: Icon(Icons.shield),
            label: 'Sécurité',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: 'Profil',
          ),
          ],
        ),
      ),
    );
  }
}

class _DiscoverySkeleton extends StatefulWidget {
  const _DiscoverySkeleton();

  @override
  State<_DiscoverySkeleton> createState() => _DiscoverySkeletonState();
}

class _DiscoverySkeletonState extends State<_DiscoverySkeleton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1250),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        final color = Color.lerp(
          scheme.surfaceContainerHighest.withValues(alpha: 0.52),
          scheme.primary.withValues(alpha: 0.18),
          _controller.value,
        )!;
        Widget block({required double height, double? width, double radius = 18}) =>
            Container(
              width: width,
              height: height,
              decoration: BoxDecoration(
                color: color,
                borderRadius: BorderRadius.circular(radius),
              ),
            );
        return ListView(
          padding: const EdgeInsets.fromLTRB(18, 10, 18, 28),
          children: [
            block(height: 390, radius: 30),
            const SizedBox(height: 18),
            block(height: 28, width: 220),
            const SizedBox(height: 10),
            block(height: 18),
            const SizedBox(height: 8),
            block(height: 18, width: 270),
            const SizedBox(height: 22),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                block(height: 58, width: 58, radius: 29),
                block(height: 70, width: 70, radius: 35),
                block(height: 58, width: 58, radius: 29),
              ],
            ),
          ],
        );
      },
    );
  }
}

class _MboloWordmark extends StatelessWidget {
  const _MboloWordmark();

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 38,
          height: 38,
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [Color(0xFFFF6B6B), Color(0xFFB51F50)],
            ),
            shape: BoxShape.circle,
          ),
          child: const Icon(Icons.favorite, color: Colors.white, size: 21),
        ),
        const SizedBox(width: 10),
        const Text(
          'MBOLO',
          style: TextStyle(
            fontWeight: FontWeight.w800,
            letterSpacing: 2.2,
            fontSize: 21,
          ),
        ),
      ],
    );
  }
}

class _DiscoverPage extends StatelessWidget {
  const _DiscoverPage({
    required this.profile,
    required this.api,
    required this.onNext,
    required this.onRewind,
    required this.superLikeState,
    required this.rewindState,
    required this.onSafetyComplete,
    required this.working,
  });

  final DiscoveryProfile profile;
  final AuthApi api;
  final Future<void> Function({required bool liked, bool superLike}) onNext;
  final Future<void> Function() onRewind;
  final SuperLikeState? superLikeState;
  final RewindState? rewindState;
  final VoidCallback onSafetyComplete;
  final bool working;

  String _label(String value) {
    if (value.isEmpty) return 'Non précisé';
    final spaced = value.replaceAll('_', ' ');
    return '${spaced[0].toUpperCase()}${spaced.substring(1)}';
  }

  @override
  Widget build(BuildContext context) {
    final photo = profile.photos.isEmpty
        ? null
        : profile.photos.firstWhere(
            (item) => item.primary,
            orElse: () => profile.photos.first,
          );
    return ListView(
      padding: const EdgeInsets.fromLTRB(18, 8, 18, 28),
      children: [
        Text(
          'Une belle rencontre\ncommence ici ✨',
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.w800,
                height: 1.08,
              ),
        ),
        const SizedBox(height: 8),
        const Text('Sélection personnalisée • Profils protégés'),
        const SizedBox(height: 18),
        Card(
          clipBehavior: Clip.antiAlias,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SizedBox(
                height: 390,
                child: photo != null && photo.imageUrl.isNotEmpty
                    ? Image.network(
                        photo.imageUrl,
                        fit: BoxFit.cover,
                        errorBuilder: (context, error, stackTrace) =>
                            const _ProfilePhotoFallback(),
                      )
                    : const _ProfilePhotoFallback(),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(22, 18, 22, 22),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            '${profile.displayName}, ${profile.age}',
                            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                  fontWeight: FontWeight.w800,
                                ),
                          ),
                        ),
                        if (profile.verified)
                          const Icon(
                            Icons.verified,
                            color: Color(0xFF9D3451),
                          ),
                        IconButton(
                          tooltip: 'Actions de sécurité',
                          onPressed: working
                              ? null
                              : () async {
                                  final changed =
                                      await showProfileSafetyActions(
                                    context: context,
                                    api: api,
                                    profile: profile,
                                  );
                                  if (changed) onSafetyComplete();
                                },
                          icon: const Icon(Icons.more_vert),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      [
                        _label(profile.city),
                        if (profile.distanceLabel.isNotEmpty)
                          profile.distanceLabel,
                      ].join(' • '),
                    ),
                    const SizedBox(height: 10),
                    Text(_label(profile.datingIntent)),
                    if (profile.biography.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Text(profile.biography),
                    ],
                    if (profile.interestLabels.isNotEmpty) ...[
                      const SizedBox(height: 14),
                      Wrap(
                        spacing: 6,
                        runSpacing: 4,
                        children: profile.interestLabels
                            .map((label) => Chip(label: Text(label)))
                            .toList(growable: false),
                      ),
                    ],
                    if (profile.compatibilityScore > 0) ...[
                      const SizedBox(height: 10),
                      Text(
                        '${profile.compatibilityScore}% de centres d’intérêt compatibles',
                        style: Theme.of(context).textTheme.labelLarge,
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        if (superLikeState != null || rewindState != null) ...[
          Wrap(
            alignment: WrapAlignment.center,
            spacing: 8,
            runSpacing: 8,
            children: [
              if (superLikeState != null)
                Chip(
                  avatar: const Icon(Icons.star_rounded, size: 18),
                  label: Text(
                    superLikeState!.entitled
                        ? '${superLikeState!.remainingToday}/${superLikeState!.dailyLimit} Super Likes'
                        : 'Super Like · Premium',
                  ),
                ),
              if (rewindState != null && !rewindState!.entitled)
                const Chip(
                  avatar: Icon(Icons.replay_rounded, size: 18),
                  label: Text('Rewind · Premium'),
                ),
            ],
          ),
          const SizedBox(height: 12),
        ],
        Wrap(
          alignment: WrapAlignment.center,
          spacing: 8,
          runSpacing: 12,
          children: [
            SizedBox(
              width: 72,
              child: Column(
                children: [
                  IconButton.filledTonal(
                    tooltip: rewindState?.entitled == true
                        ? 'Revenir au profil précédent'
                        : 'Rewind · MBOLO Plus',
                    onPressed: working || rewindState?.available != true
                        ? null
                        : onRewind,
                    icon: const Icon(Icons.replay_rounded),
                  ),
                  const Text('Rewind', style: TextStyle(fontSize: 12)),
                ],
              ),
            ),
            SizedBox(
              width: 72,
              child: Column(
                children: [
                  IconButton.outlined(
                    tooltip: 'Passer ce profil',
                    onPressed: working ? null : () => onNext(liked: false),
                    icon: const Icon(Icons.close_rounded),
                  ),
                  const Text('Passer', style: TextStyle(fontSize: 12)),
                ],
              ),
            ),
            SizedBox(
              width: 72,
              child: Column(
                children: [
                  IconButton.filledTonal(
                    tooltip: superLikeState?.entitled == true
                        ? 'Envoyer un Super Like'
                        : 'Super Like · MBOLO Plus',
                    onPressed: working ||
                            superLikeState?.entitled != true ||
                            superLikeState!.remainingToday < 1
                        ? null
                        : () => onNext(liked: true, superLike: true),
                    icon: const Icon(Icons.star_rounded),
                  ),
                  const Text('Super Like', style: TextStyle(fontSize: 12)),
                ],
              ),
            ),
            SizedBox(
              width: 72,
              child: Column(
                children: [
                  IconButton.filled(
                    tooltip: 'Ça me plaît',
                    onPressed: working ? null : () => onNext(liked: true),
                    icon: const Icon(Icons.favorite),
                    style: IconButton.styleFrom(
                      backgroundColor: const Color(0xFFB51F50),
                    ),
                  ),
                  const Text('Ça me plaît', style: TextStyle(fontSize: 12)),
                ],
              ),
            ),
          ],
        ),
        if (working) ...[
          const SizedBox(height: 12),
          const LinearProgressIndicator(),
        ],
      ],
    );
  }
}

class _ProfilePhotoFallback extends StatelessWidget {
  const _ProfilePhotoFallback();

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFF6CAD6), Color(0xFF9D3451)],
        ),
      ),
      child: const Center(
        child: Icon(Icons.person, size: 150, color: Colors.white70),
      ),
    );
  }
}

class _ProfilePage extends StatelessWidget {
  const _ProfilePage({
    required this.account,
    required this.onLogout,
    required this.onEditProfile,
    required this.onEditPhotos,
    required this.onEditPreferences,
    required this.onPremium,
    required this.onShowcase,
  });
  final Account account;
  final Future<void> Function() onLogout;
  final VoidCallback onEditProfile;
  final VoidCallback onEditPhotos;
  final VoidCallback onEditPreferences;
  final VoidCallback onPremium;
  final VoidCallback onShowcase;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(18, 8, 18, 28),
      children: [
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFFB51F50), Color(0xFF6F1735)],
            ),
            borderRadius: BorderRadius.circular(30),
            boxShadow: const [
              BoxShadow(
                color: Color(0x3DB51F50),
                blurRadius: 28,
                offset: Offset(0, 12),
              ),
            ],
          ),
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.all(5),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.white70, width: 2),
                ),
                child: const CircleAvatar(
                  radius: 48,
                  backgroundColor: Color(0xFFFFD8E3),
                  child: Icon(Icons.person, size: 55, color: Color(0xFF6F1735)),
                ),
              ),
              const SizedBox(height: 14),
              const Text(
                'Mon profil',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 27,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 6),
              Text(account.email, style: const TextStyle(color: Colors.white70)),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.16),
                  borderRadius: BorderRadius.circular(99),
                ),
                child: Text(
                  account.verified ? '✓ E-mail confirmé' : 'E-mail à confirmer',
                  style: const TextStyle(color: Colors.white),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 26),
        Text(
          'Mon espace',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w800,
              ),
        ),
        const SizedBox(height: 12),
        Card(
          child: Column(
            children: [
              ListTile(
                leading: const Icon(
                  Icons.auto_awesome_rounded,
                  color: Color(0xFFB51F50),
                ),
                title: const Text(
                  'Visite guidée MBOLO',
                  style: TextStyle(fontWeight: FontWeight.w800),
                ),
                subtitle: const Text(
                  'Découvrir la vision et les avantages',
                ),
                trailing: const Icon(Icons.chevron_right),
                onTap: onShowcase,
              ),
              const Divider(height: 1),
              ListTile(
                leading: const Icon(Icons.workspace_premium, color: Color(0xFFB51F50)),
                title: const Text('MBOLO Premium', style: TextStyle(fontWeight: FontWeight.w800)),
                subtitle: const Text('Plus, Prestige, Boost et avantages'),
                trailing: const Icon(Icons.chevron_right),
                onTap: onPremium,
              ),
              const Divider(height: 1),
              ListTile(
                leading: const Icon(Icons.edit_outlined),
                title: const Text('Compléter mon profil'),
                trailing: const Icon(Icons.chevron_right),
                onTap: onEditProfile,
              ),
              const Divider(height: 1),
              ListTile(
                leading: const Icon(Icons.photo_library_outlined),
                title: const Text('Mes photos'),
                subtitle: const Text('Jusqu’à 6 photos avec modération'),
                trailing: const Icon(Icons.chevron_right),
                onTap: onEditPhotos,
              ),
              const Divider(height: 1),
              ListTile(
                leading: const Icon(Icons.tune),
                title: const Text('Préférences de rencontre'),
                trailing: const Icon(Icons.chevron_right),
                onTap: onEditPreferences,
              ),
              const Divider(height: 1),
              const ListTile(
                leading: Icon(Icons.privacy_tip_outlined),
                title: Text('Confidentialité'),
                trailing: Icon(Icons.chevron_right),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        OutlinedButton.icon(
          onPressed: onLogout,
          icon: const Icon(Icons.logout),
          label: const Text('Se déconnecter'),
        ),
      ],
    );
  }
}


class _PhotosPage extends StatefulWidget {
  const _PhotosPage({required this.api});

  final AuthApi api;

  @override
  State<_PhotosPage> createState() => _PhotosPageState();
}

class _PhotosPageState extends State<_PhotosPage> {
  final ImagePicker _picker = ImagePicker();
  List<ProfilePhoto> _photos = <ProfilePhoto>[];
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
      final photos = await widget.api.getPhotos();
      if (!mounted) return;
      setState(() {
        _photos = photos;
        _error = null;
      });
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  int _nextPosition() {
    for (var position = 0; position < 6; position += 1) {
      if (!_photos.any((photo) => photo.position == position)) return position;
    }
    return _photos.length;
  }

  Future<void> _pickPhoto() async {
    if (_working || _photos.length >= 6) return;
    final picked = await _picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 85,
      maxWidth: 2048,
      maxHeight: 2048,
      requestFullMetadata: false,
    );
    if (picked == null || !mounted) return;
    setState(() {
      _working = true;
      _error = null;
    });
    try {
      final bytes = await picked.readAsBytes();
      if (bytes.length > 10 * 1024 * 1024) {
        throw const FormatException('La photo dépasse 10 Mo.');
      }
      await widget.api.uploadPhoto(
        bytes: bytes,
        filename: picked.name,
        position: _nextPosition(),
        primary: _photos.isEmpty,
      );
      await _load();
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Future<void> _makePrimary(ProfilePhoto photo) async {
    if (_working || photo.primary) return;
    setState(() => _working = true);
    try {
      await widget.api.updatePhoto(id: photo.id, primary: true);
      await _load();
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Future<void> _delete(ProfilePhoto photo) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Supprimer cette photo ?'),
        content: const Text(
          'La suppression est définitive. Tu pourras ajouter une autre photo.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Supprimer'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() => _working = true);
    try {
      await widget.api.deletePhoto(photo.id);
      await _load();
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Widget _photoImage(ProfilePhoto photo) {
    if (photo.previewBytes != null) {
      return Image.memory(
        photo.previewBytes!,
        fit: BoxFit.cover,
        width: double.infinity,
        height: double.infinity,
      );
    }
    if (photo.imageUrl.isNotEmpty) {
      return Image.network(
        photo.imageUrl,
        fit: BoxFit.cover,
        width: double.infinity,
        height: double.infinity,
        errorBuilder: (context, error, stackTrace) => const Center(
          child: Icon(Icons.broken_image_outlined, size: 48),
        ),
      );
    }
    return const Center(child: Icon(Icons.image_outlined, size: 48));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mes photos')),
      floatingActionButton: _photos.length >= 6
          ? null
          : FloatingActionButton.extended(
              onPressed: _working ? null : _pickPhoto,
              icon: const Icon(Icons.add_a_photo_outlined),
              label: const Text('Ajouter'),
            ),
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: _load,
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 96),
                  children: [
                    Text(
                      'Ta galerie MBOLO',
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Ajoute jusqu’à 6 photos. Les fichiers sont nettoyés et modérés avant leur affichage public.',
                    ),
                    const SizedBox(height: 20),
                    if (_photos.isEmpty)
                      const Card(
                        child: Padding(
                          padding: EdgeInsets.all(24),
                          child: Column(
                            children: [
                              Icon(Icons.add_photo_alternate_outlined, size: 52),
                              SizedBox(height: 12),
                              Text(
                                'Ajoute une première photo claire de ton visage.',
                                textAlign: TextAlign.center,
                              ),
                            ],
                          ),
                        ),
                      )
                    else
                      GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: _photos.length,
                        gridDelegate:
                            const SliverGridDelegateWithFixedCrossAxisCount(
                              crossAxisCount: 2,
                              crossAxisSpacing: 12,
                              mainAxisSpacing: 12,
                              childAspectRatio: 0.72,
                            ),
                        itemBuilder: (context, index) {
                          final photo = _photos[index];
                          return Card(
                            clipBehavior: Clip.antiAlias,
                            child: Column(
                              children: [
                                Expanded(
                                  child: Stack(
                                    fit: StackFit.expand,
                                    children: [
                                      _photoImage(photo),
                                      if (photo.primary)
                                        const Positioned(
                                          top: 8,
                                          left: 8,
                                          child: Chip(
                                            avatar: Icon(Icons.star, size: 16),
                                            label: Text('Principale'),
                                          ),
                                        ),
                                    ],
                                  ),
                                ),
                                Padding(
                                  padding: const EdgeInsets.fromLTRB(8, 6, 4, 4),
                                  child: Row(
                                    children: [
                                      Expanded(
                                        child: Text(
                                          photo.moderationStatusLabel,
                                          overflow: TextOverflow.ellipsis,
                                          style: Theme.of(
                                            context,
                                          ).textTheme.bodySmall,
                                        ),
                                      ),
                                      IconButton(
                                        tooltip: 'Définir comme principale',
                                        onPressed: _working || photo.primary
                                            ? null
                                            : () => _makePrimary(photo),
                                        icon: Icon(
                                          photo.primary
                                              ? Icons.star
                                              : Icons.star_border,
                                        ),
                                      ),
                                      IconButton(
                                        tooltip: 'Supprimer',
                                        onPressed: _working
                                            ? null
                                            : () => _delete(photo),
                                        icon: const Icon(Icons.delete_outline),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          );
                        },
                      ),
                    if (_working)
                      const Padding(
                        padding: EdgeInsets.only(top: 16),
                        child: LinearProgressIndicator(),
                      ),
                    if (_error != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 16),
                        child: Text(
                          _error!,
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.error,
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

class _ProfileEditorPage extends StatefulWidget {
  const _ProfileEditorPage({required this.api});

  final AuthApi api;

  @override
  State<_ProfileEditorPage> createState() => _ProfileEditorPageState();
}

class _ProfileEditorPageState extends State<_ProfileEditorPage> {
  static const _cities = <String, String>{
    'libreville': 'Libreville',
    'port_gentil': 'Port-Gentil',
    'franceville': 'Franceville',
    'oyem': 'Oyem',
    'moanda': 'Moanda',
    'lambarene': 'Lambaréné',
    'mouila': 'Mouila',
    'tchibanga': 'Tchibanga',
    'koulamoutou': 'Koulamoutou',
    'makokou': 'Makokou',
    'bitam': 'Bitam',
    'other': 'Autre ville',
  };
  static const _genders = <String, String>{
    'man': 'Homme',
    'woman': 'Femme',
    'non_binary': 'Non binaire',
    'prefer_not_to_say': 'Je préfère ne pas préciser',
  };
  static const _intents = <String, String>{
    'serious_relationship': 'Relation sérieuse',
    'friendship': 'Amitié',
    'discussion': 'Discussion',
    'marriage': 'Mariage',
    'not_sure': 'Je ne sais pas encore',
  };
  static const _interestOptions = <String, String>{
    'music': 'Musique',
    'football': 'Football',
    'fitness': 'Fitness',
    'martial_arts': 'Arts martiaux',
    'technology': 'Technologie',
    'cybersecurity': 'Cybersécurité',
    'travel': 'Voyages',
    'cooking': 'Cuisine',
    'cinema': 'Cinéma',
    'reading': 'Lecture',
    'entrepreneurship': 'Entrepreneuriat',
    'personal_growth': 'Développement personnel',
    'dance': 'Danse',
    'art': 'Art',
    'nature': 'Nature',
    'family': 'Famille',
  };

  final _form = GlobalKey<FormState>();
  final _displayName = TextEditingController();
  final _biography = TextEditingController();
  DateTime? _birthDate;
  String? _city;
  String? _gender;
  String? _datingIntent;
  Set<String> _interests = <String>{};
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
      final profile = await widget.api.getProfile();
      if (!mounted) return;
      _displayName.text = profile.displayName;
      _birthDate = DateTime.tryParse(profile.birthDate);
      _gender = profile.gender.isEmpty ? null : profile.gender;
      _city = profile.city.isEmpty ? null : profile.city;
      _biography.text = profile.biography;
      _datingIntent =
          profile.datingIntent.isEmpty ? null : profile.datingIntent;
      _interests = profile.interests.toSet();
    } catch (error) {
      if (mounted) {
        setState(() => _error = friendlyError(error));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _displayName.dispose();
    _biography.dispose();
    super.dispose();
  }

  String _isoDate(DateTime value) {
    final year = value.year.toString().padLeft(4, '0');
    final month = value.month.toString().padLeft(2, '0');
    final day = value.day.toString().padLeft(2, '0');
    return '$year-$month-$day';
  }

  String _displayDate(DateTime value) {
    final day = value.day.toString().padLeft(2, '0');
    final month = value.month.toString().padLeft(2, '0');
    return '$day/$month/${value.year}';
  }

  Future<void> _selectBirthDate() async {
    final now = DateTime.now();
    final adultLimit = DateTime(now.year - 18, now.month, now.day);
    final selected = await showDatePicker(
      context: context,
      initialDate: _birthDate ?? DateTime(adultLimit.year - 7),
      firstDate: DateTime(1920),
      lastDate: adultLimit,
      helpText: 'Date de naissance',
      cancelText: 'Annuler',
      confirmText: 'Confirmer',
    );
    if (selected != null && mounted) {
      setState(() => _birthDate = selected);
    }
  }

  void _toggleInterest(String value) {
    setState(() {
      if (_interests.contains(value)) {
        _interests.remove(value);
      } else if (_interests.length < 8) {
        _interests.add(value);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Choisis au maximum 8 centres d’intérêt.')),
        );
      }
    });
  }

  Future<void> _continue() async {
    if (_saving || !(_form.currentState?.validate() ?? false)) return;
    if (_birthDate == null) {
      setState(() => _error = 'Indique ta date de naissance.');
      return;
    }
    if (_interests.length < 3) {
      setState(() => _error = 'Choisis au moins 3 centres d’intérêt.');
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await widget.api.updateProfile(
        displayName: _displayName.text,
        birthDate: _isoDate(_birthDate!),
        gender: _gender!,
        city: _city!,
        biography: _biography.text,
        datingIntent: _datingIntent!,
        interests: _interests.toList(growable: false),
      );
      if (!mounted) return;
      final messenger = ScaffoldMessenger.of(context);
      Navigator.of(context).pop();
      messenger.showSnackBar(
        const SnackBar(content: Text('Profil complet enregistré en sécurité.')),
      );
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Compléter mon profil')),
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : Form(
                key: _form,
                child: ListView(
                  padding: const EdgeInsets.all(24),
                  children: [
                    Text(
                      'Présente-toi avec authenticité',
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Ces informations permettent à MBOLO de proposer des rencontres pertinentes.',
                    ),
                    const SizedBox(height: 24),
                    TextFormField(
                      controller: _displayName,
                      textCapitalization: TextCapitalization.words,
                      decoration: const InputDecoration(labelText: 'Nom public'),
                      validator: (value) => (value ?? '').trim().length < 2
                          ? 'Entre au moins 2 caractères.'
                          : null,
                    ),
                    const SizedBox(height: 16),
                    OutlinedButton.icon(
                      onPressed: _saving ? null : _selectBirthDate,
                      icon: const Icon(Icons.cake_outlined),
                      label: Text(
                        _birthDate == null
                            ? 'Choisir ma date de naissance'
                            : 'Né(e) le ${_displayDate(_birthDate!)}',
                      ),
                    ),
                    const SizedBox(height: 16),
                    DropdownButtonFormField<String>(
                      initialValue: _gender,
                      decoration: const InputDecoration(labelText: 'Genre'),
                      items: _genders.entries
                          .map(
                            (entry) => DropdownMenuItem(
                              value: entry.key,
                              child: Text(entry.value),
                            ),
                          )
                          .toList(growable: false),
                      onChanged: _saving
                          ? null
                          : (value) => setState(() => _gender = value),
                      validator: (value) => value == null || value.isEmpty
                          ? 'Indique ton genre.'
                          : null,
                    ),
                    const SizedBox(height: 16),
                    DropdownButtonFormField<String>(
                      initialValue: _city,
                      decoration: const InputDecoration(labelText: 'Ville'),
                      items: _cities.entries
                          .map(
                            (entry) => DropdownMenuItem(
                              value: entry.key,
                              child: Text(entry.value),
                            ),
                          )
                          .toList(growable: false),
                      onChanged: _saving
                          ? null
                          : (value) => setState(() => _city = value),
                      validator: (value) => value == null || value.isEmpty
                          ? 'Indique ta ville.'
                          : null,
                    ),
                    const SizedBox(height: 16),
                    DropdownButtonFormField<String>(
                      initialValue: _datingIntent,
                      decoration: const InputDecoration(
                        labelText: 'Ce que je recherche',
                      ),
                      items: _intents.entries
                          .map(
                            (entry) => DropdownMenuItem(
                              value: entry.key,
                              child: Text(entry.value),
                            ),
                          )
                          .toList(growable: false),
                      onChanged: _saving
                          ? null
                          : (value) => setState(() => _datingIntent = value),
                      validator: (value) => value == null || value.isEmpty
                          ? 'Indique ce que tu recherches.'
                          : null,
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _biography,
                      minLines: 4,
                      maxLines: 6,
                      maxLength: 500,
                      decoration: const InputDecoration(
                        labelText: 'À propos de toi',
                        alignLabelWithHint: true,
                      ),
                      validator: (value) => (value ?? '').trim().length < 20
                          ? 'Écris au moins 20 caractères.'
                          : null,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Centres d’intérêt (${_interests.length}/8)',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 4),
                    const Text('Choisis-en au moins 3.'),
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      children: _interestOptions.entries
                          .map(
                            (entry) => FilterChip(
                              label: Text(entry.value),
                              selected: _interests.contains(entry.key),
                              onSelected: _saving
                                  ? null
                                  : (_) => _toggleInterest(entry.key),
                            ),
                          )
                          .toList(growable: false),
                    ),
                    const SizedBox(height: 24),
                    FilledButton(
                      onPressed: _saving ? null : _continue,
                      child: Text(
                        _saving ? 'Enregistrement…' : 'Enregistrer le profil',
                      ),
                    ),
                    if (_error != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 16),
                        child: Text(
                          _error!,
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.error,
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

class _PreferencesPage extends StatefulWidget {
  const _PreferencesPage({required this.api});

  final AuthApi api;

  @override
  State<_PreferencesPage> createState() => _PreferencesPageState();
}

class _PreferencesPageState extends State<_PreferencesPage> {
  static const _genderOptions = <String, String>{
    'woman': 'Femmes',
    'man': 'Hommes',
    'non_binary': 'Personnes non binaires',
    'prefer_not_to_say': 'Genre non précisé',
  };

  RangeValues _ages = const RangeValues(18, 45);
  Set<String> _preferredGenders = <String>{};
  bool _loading = true;
  bool _saving = false;
  String? _error;
  bool _advancedFiltersAvailable = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final preferences = await widget.api.getPreferences();
      if (!mounted) return;
      setState(() {
        _ages = RangeValues(
          preferences.minimumAge.toDouble(),
          preferences.maximumAge.toDouble(),
        );
        _preferredGenders = preferences.preferredGenders.toSet();
        _advancedFiltersAvailable = preferences.advancedFiltersAvailable;
      });
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _toggleGender(String value) {
    setState(() {
      if (_preferredGenders.contains(value)) {
        _preferredGenders.remove(value);
      } else {
        _preferredGenders.add(value);
      }
    });
  }

  Future<void> _continue() async {
    if (_saving) return;
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await widget.api.updatePreferences(
        minimumAge: _ages.start.round(),
        maximumAge: _ages.end.round(),
        preferredGenders: _preferredGenders.toList(growable: false),
      );
      if (!mounted) return;
      final messenger = ScaffoldMessenger.of(context);
      Navigator.of(context).pop();
      messenger.showSnackBar(
        const SnackBar(content: Text('Préférences enregistrées en sécurité.')),
      );
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Préférences de rencontre')),
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  Text(
                    'Choisis qui tu souhaites découvrir',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Tes choix restent privés. Une sélection vide affiche tous les genres.',
                  ),
                  const SizedBox(height: 24),
                  Text(
                    'Tranche d’âge : ${_ages.start.round()} à ${_ages.end.round()} ans',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  RangeSlider(
                    values: _ages,
                    min: 18,
                    max: 99,
                    divisions: 81,
                    labels: RangeLabels(
                      '${_ages.start.round()} ans',
                      '${_ages.end.round()} ans',
                    ),
                    onChanged: _saving
                        ? null
                        : (values) => setState(() => _ages = values),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Je souhaite voir',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 4,
                    children: _genderOptions.entries
                        .map(
                          (entry) => FilterChip(
                            label: Text(entry.value),
                            selected: _preferredGenders.contains(entry.key),
                            onSelected: _saving
                                ? null
                                : (_) => _toggleGender(entry.key),
                          ),
                        )
                        .toList(growable: false),
                  ),
                  const SizedBox(height: 24),
                  Card(
                    child: ListTile(
                      leading: Icon(
                        _advancedFiltersAvailable
                            ? Icons.workspace_premium
                            : Icons.lock_outline,
                      ),
                      title: const Text('Filtres avancés'),
                      subtitle: Text(
                        _advancedFiltersAvailable
                            ? 'Disponibles avec ton abonnement actif.'
                            : 'Villes, intentions, distance et profils vérifiés seront proposés avec MBOLO Plus.',
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                  FilledButton(
                    onPressed: _saving ? null : _continue,
                    child: Text(
                      _saving
                          ? 'Enregistrement…'
                          : 'Enregistrer mes préférences',
                    ),
                  ),
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 16),
                      child: Text(
                        _error!,
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.error,
                        ),
                      ),
                    ),
                ],
              ),
      ),
    );
  }
}
