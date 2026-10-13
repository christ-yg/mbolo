import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import 'auth_contract.dart';
import 'safety_actions.dart';

class PublicProfilePage extends StatefulWidget {
  const PublicProfilePage({super.key, required this.api, required this.profileId, this.matchId});
  final AuthApi api;
  final String profileId;
  final String? matchId;

  @override
  State<PublicProfilePage> createState() => _PublicProfilePageState();
}

class _PublicProfilePageState extends State<PublicProfilePage> {
  DiscoveryProfile? _profile;
  bool _loading = true;
  bool _acting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    if (_acting) return;
    setState(() { _loading = true; _profile = null; _error = null; });
    try {
      final profile = await widget.api.getPublicProfile(widget.profileId);
      if (mounted) setState(() => _profile = profile);
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error is DioException &&
          (error.response?.statusCode == 404 || error.response?.statusCode == 403)
          ? 'Ce profil n’est pas disponible.' : friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _safety() async {
    final profile = _profile;
    if (profile == null || _acting) return;
    setState(() => _acting = true);
    final changed = await showProfileSafetyActions(
      context: context, api: widget.api, profile: profile, matchId: widget.matchId,
    );
    if (!mounted) return;
    setState(() => _acting = false);
    if (changed) Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    final profile = _profile;
    return Scaffold(
      appBar: AppBar(title: const Text('Profil public'), actions: [
        IconButton(tooltip: 'Actualiser le profil', onPressed: _loading || _acting ? null : _load,
          icon: const Icon(Icons.refresh)),
        IconButton(tooltip: 'Signaler ou bloquer', onPressed: profile == null || _acting ? null : _safety,
          icon: const Icon(Icons.shield_outlined)),
      ]),
      body: SafeArea(child: _loading
        ? const Center(child: CircularProgressIndicator())
        : profile == null
          ? Center(child: Padding(padding: const EdgeInsets.all(24), child: Column(
              mainAxisSize: MainAxisSize.min, children: [
                const Icon(Icons.person_off_outlined, size: 48),
                const SizedBox(height: 12),
                Text(_error ?? 'Ce profil n’est pas disponible.', textAlign: TextAlign.center),
                const SizedBox(height: 12),
                FilledButton.icon(onPressed: _load, icon: const Icon(Icons.refresh), label: const Text('Réessayer')),
              ])))
          : RefreshIndicator(onRefresh: _load, child: ListView(
              physics: const AlwaysScrollableScrollPhysics(), padding: const EdgeInsets.all(20), children: [
                if (_acting) const LinearProgressIndicator(),
                if (profile.photos.isEmpty)
                  const SizedBox(height: 190, child: Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
                    Icon(Icons.person_outline, size: 70), Text('Aucune photo publique'),
                  ])))
                else SizedBox(height: 340, child: PageView.builder(
                  itemCount: profile.photos.length,
                  itemBuilder: (context, index) => Padding(padding: const EdgeInsets.symmetric(horizontal: 3),
                    child: ClipRRect(borderRadius: BorderRadius.circular(24), child: Stack(fit: StackFit.expand, children: [
                      _PublicPhoto(photo: profile.photos[index]),
                      Positioned(bottom: 12, right: 12, child: FilledButton.icon(
                        icon: const Icon(Icons.fullscreen), label: Text('Photo ${index + 1}/${profile.photos.length}'),
                        onPressed: () => Navigator.of(context).push<void>(MaterialPageRoute<void>(
                          builder: (_) => _FullPhoto(photo: profile.photos[index], index: index, count: profile.photos.length))),
                      )),
                    ]))),
                )),
                const SizedBox(height: 20),
                Text('${profile.displayName}, ${profile.age}', style: Theme.of(context).textTheme.headlineMedium),
                const SizedBox(height: 8),
                Align(alignment: Alignment.centerLeft, child: Chip(
                  avatar: Icon(profile.verified ? Icons.verified : Icons.person_outline, size: 18),
                  label: Text(profile.verified ? 'Identité vérifiée' : 'Identité non vérifiée'),
                )),
                if (profile.city.isNotEmpty) ListTile(contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.location_city), title: Text(profile.city)),
                if (profile.datingIntent.isNotEmpty) ListTile(contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.favorite_outline), title: Text(profile.datingIntent)),
                const SizedBox(height: 12),
                Text('À propos', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 8),
                Text(profile.biography.isEmpty ? 'Ce membre n’a pas encore ajouté de présentation.' : profile.biography),
                const SizedBox(height: 24),
                const Text('Seules les informations publiques sont affichées. Une vérification d’identité ne garantit pas le comportement d’un membre.'),
                const SizedBox(height: 16),
                OutlinedButton.icon(onPressed: _acting ? null : _safety,
                  icon: const Icon(Icons.shield_outlined), label: const Text('Sécurité et signalement')),
              ]))),
    );
  }
}

class _PublicPhoto extends StatelessWidget {
  const _PublicPhoto({required this.photo, this.fit = BoxFit.cover});
  final ProfilePhoto photo;
  final BoxFit fit;

  @override
  Widget build(BuildContext context) {
    Widget placeholder() => const Center(child: Icon(Icons.image_not_supported_outlined, size: 56));
    if (photo.previewBytes != null) {
      return Image.memory(photo.previewBytes!, fit: fit, semanticLabel: 'Photo publique du membre',
        errorBuilder: (_, __, ___) => placeholder());
    }
    if (photo.imageUrl.isEmpty) return placeholder();
    return Image.network(photo.imageUrl, fit: fit, semanticLabel: 'Photo publique du membre',
      errorBuilder: (_, __, ___) => placeholder());
  }
}

class _FullPhoto extends StatelessWidget {
  const _FullPhoto({required this.photo, required this.index, required this.count});
  final ProfilePhoto photo;
  final int index;
  final int count;

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text('Photo ${index + 1}/$count')),
    body: SafeArea(child: Center(child: InteractiveViewer(minScale: 1, maxScale: 4,
      child: _PublicPhoto(photo: photo, fit: BoxFit.contain)))),
  );
}
