import 'package:flutter/material.dart';

import 'auth_contract.dart';

class MboloHome extends StatefulWidget {
  const MboloHome({
    super.key,
    required this.account,
    required this.api,
    required this.onLogout,
  });

  final Account account;
  final AuthApi api;
  final Future<void> Function() onLogout;

  @override
  State<MboloHome> createState() => _MboloHomeState();
}

class _MboloHomeState extends State<MboloHome> {
  int _tab = 0;
  int _profile = 0;
  final Set<String> _liked = <String>{};

  static const _profiles = [
    _SuggestedProfile(
      'Arielle',
      27,
      'Libreville',
      'Lecture • Cuisine • Voyages',
    ),
    _SuggestedProfile('Grâce', 29, 'Akanda', 'Sport • Musique • Entrepreneuriat'),
    _SuggestedProfile(
      'Mélissa',
      26,
      'Port-Gentil',
      'Cinéma • Nature • Photographie',
    ),
  ];

  void _next({required bool liked}) {
    final current = _profiles[_profile];
    setState(() {
      if (liked) _liked.add(current.name);
      _profile = (_profile + 1) % _profiles.length;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          liked ? 'Intérêt envoyé avec respect.' : 'Profil suivant.',
        ),
        duration: const Duration(seconds: 1),
      ),
    );
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
        builder: (context) => const _PreferencesPage(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final pages = [
      _DiscoverPage(profile: _profiles[_profile], onNext: _next),
      _ActivityPage(liked: _liked.toList(growable: false)),
      _SafetyPage(onOpenProfile: () => setState(() => _tab = 3)),
      _ProfilePage(
        account: widget.account,
        onLogout: widget.onLogout,
        onEditProfile: _openProfileEditor,
        onEditPreferences: _openPreferences,
      ),
    ];
    return Scaffold(
      appBar: AppBar(
        title: const Text('MBOLO'),
        actions: [
          IconButton(
            tooltip: 'Sécurité',
            onPressed: () => setState(() => _tab = 2),
            icon: const Icon(Icons.shield_outlined),
          ),
        ],
      ),
      body: SafeArea(child: pages[_tab]),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (value) => setState(() => _tab = value),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.favorite_outline),
            selectedIcon: Icon(Icons.favorite),
            label: 'Découvrir',
          ),
          NavigationDestination(
            icon: Icon(Icons.bolt_outlined),
            selectedIcon: Icon(Icons.bolt),
            label: 'Activité',
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
    );
  }
}

class _DiscoverPage extends StatelessWidget {
  const _DiscoverPage({required this.profile, required this.onNext});
  final _SuggestedProfile profile;
  final void Function({required bool liked}) onNext;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
      children: [
        Text('Découvrir', style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 4),
        const Text('Des profils proches de tes valeurs, à ton rythme.'),
        const SizedBox(height: 20),
        Card(
          clipBehavior: Clip.antiAlias,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Container(
                height: 300,
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [Color(0xFFF6CAD6), Color(0xFF9D3451)],
                  ),
                ),
                child: const Icon(Icons.person, size: 150, color: Colors.white70),
              ),
              Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            '${profile.name}, ${profile.age}',
                            style: Theme.of(context).textTheme.headlineSmall,
                          ),
                        ),
                        const Icon(Icons.verified, color: Color(0xFF9D3451)),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text('${profile.city} • Profil vérifié'),
                    const SizedBox(height: 12),
                    Text(profile.interests),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            OutlinedButton.icon(
              onPressed: () => onNext(liked: false),
              icon: const Icon(Icons.close),
              label: const Text('Passer'),
            ),
            const SizedBox(width: 16),
            FilledButton.icon(
              onPressed: () => onNext(liked: true),
              icon: const Icon(Icons.favorite),
              label: const Text('Ça me plaît'),
            ),
          ],
        ),
      ],
    );
  }
}

class _ActivityPage extends StatelessWidget {
  const _ActivityPage({required this.liked});
  final List<String> liked;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Text('Ton activité', style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 8),
        Text(
          '${liked.length} intérêt${liked.length == 1 ? '' : 's'} '
          'envoyé${liked.length == 1 ? '' : 's'}',
        ),
        const SizedBox(height: 20),
        if (liked.isEmpty)
          const Card(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Text('Tes likes et futurs matchs apparaîtront ici.'),
            ),
          )
        else
          ...liked.map(
            (name) => ListTile(
              leading: const CircleAvatar(child: Icon(Icons.person)),
              title: Text(name),
              subtitle: const Text('Intérêt envoyé'),
              trailing: const Icon(Icons.favorite, color: Color(0xFF9D3451)),
            ),
          ),
      ],
    );
  }
}

class _SafetyPage extends StatelessWidget {
  const _SafetyPage({required this.onOpenProfile});
  final VoidCallback onOpenProfile;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Text('Sécurité', style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 8),
        const Text('Ta sécurité passe avant chaque rencontre.'),
        const SizedBox(height: 20),
        const ListTile(
          leading: Icon(Icons.verified_user_outlined),
          title: Text('Profils vérifiés'),
          subtitle: Text(
            'Privilégie les personnes ayant confirmé leur identité.',
          ),
        ),
        const ListTile(
          leading: Icon(Icons.location_off_outlined),
          title: Text('Localisation protégée'),
          subtitle: Text('Ta position exacte n’est jamais affichée.'),
        ),
        const ListTile(
          leading: Icon(Icons.report_outlined),
          title: Text('Bloquer et signaler'),
          subtitle: Text('Un comportement déplacé peut être signalé rapidement.'),
        ),
        const SizedBox(height: 20),
        FilledButton.icon(
          onPressed: onOpenProfile,
          icon: const Icon(Icons.tune),
          label: const Text('Gérer mes préférences'),
        ),
      ],
    );
  }
}

class _ProfilePage extends StatelessWidget {
  const _ProfilePage({
    required this.account,
    required this.onLogout,
    required this.onEditProfile,
    required this.onEditPreferences,
  });
  final Account account;
  final Future<void> Function() onLogout;
  final VoidCallback onEditProfile;
  final VoidCallback onEditPreferences;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        const Center(
          child: CircleAvatar(radius: 52, child: Icon(Icons.person, size: 58)),
        ),
        const SizedBox(height: 16),
        Text(
          'Mon profil',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 8),
        Text(account.email, textAlign: TextAlign.center),
        const SizedBox(height: 4),
        Text(
          account.verified ? 'Adresse e-mail confirmée' : 'E-mail à confirmer',
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 24),
        Card(
          child: Column(
            children: [
              ListTile(
                leading: const Icon(Icons.edit_outlined),
                title: const Text('Compléter mon profil'),
                trailing: const Icon(Icons.chevron_right),
                onTap: onEditProfile,
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


class _ProfileEditorPage extends StatefulWidget {
  const _ProfileEditorPage({required this.api});

  final AuthApi api;

  @override
  State<_ProfileEditorPage> createState() => _ProfileEditorPageState();
}

class _ProfileEditorPageState extends State<_ProfileEditorPage> {
  final _form = GlobalKey<FormState>();
  final _displayName = TextEditingController();
  final _city = TextEditingController();
  final _biography = TextEditingController();
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
      _city.text = profile.city;
      _biography.text = profile.biography;
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
    _city.dispose();
    _biography.dispose();
    super.dispose();
  }

  Future<void> _continue() async {
    if (_saving || !(_form.currentState?.validate() ?? false)) return;
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await widget.api.updateProfile(
        displayName: _displayName.text,
        city: _city.text,
        biography: _biography.text,
      );
      if (!mounted) return;
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Profil enregistré en sécurité.')),
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
                'Ton nom public, ta ville et ta présentation seront visibles.',
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
              DropdownButtonFormField<String>(
                initialValue: _city.text.isEmpty ? null : _city.text,
                decoration: const InputDecoration(labelText: 'Ville'),
                items: const [
                  DropdownMenuItem(value: 'libreville', child: Text('Libreville')),
                  DropdownMenuItem(value: 'port_gentil', child: Text('Port-Gentil')),
                  DropdownMenuItem(value: 'franceville', child: Text('Franceville')),
                  DropdownMenuItem(value: 'oyem', child: Text('Oyem')),
                  DropdownMenuItem(value: 'moanda', child: Text('Moanda')),
                  DropdownMenuItem(value: 'lambarene', child: Text('Lambaréné')),
                  DropdownMenuItem(value: 'mouila', child: Text('Mouila')),
                  DropdownMenuItem(value: 'tchibanga', child: Text('Tchibanga')),
                  DropdownMenuItem(value: 'other', child: Text('Autre ville')),
                ],
                onChanged: _saving
                    ? null
                    : (value) => _city.text = value ?? '',
                validator: (value) =>
                    value == null || value.isEmpty ? 'Indique ta ville.' : null,
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
              FilledButton(
                onPressed: _saving ? null : _continue,
                child: Text(_saving ? 'Enregistrement…' : 'Enregistrer le profil'),
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
  const _PreferencesPage();

  @override
  State<_PreferencesPage> createState() => _PreferencesPageState();
}

class _PreferencesPageState extends State<_PreferencesPage> {
  String _lookingFor = 'Tous';
  String _intent = 'Relation sérieuse';
  double _distance = 25;

  void _continue() {
    Navigator.of(context).pop();
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'Préférences prêtes. La synchronisation sécurisée arrive ensuite.',
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Préférences de rencontre')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            Text(
              'Choisis qui tu souhaites découvrir',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            const Text(
              'Ces réglages restent modifiables et ta position exacte est masquée.',
            ),
            const SizedBox(height: 24),
            DropdownButtonFormField<String>(
              initialValue: _lookingFor,
              decoration: const InputDecoration(labelText: 'Je souhaite voir'),
              items: const [
                DropdownMenuItem(value: 'Tous', child: Text('Tous les profils')),
                DropdownMenuItem(value: 'Femmes', child: Text('Des femmes')),
                DropdownMenuItem(value: 'Hommes', child: Text('Des hommes')),
              ],
              onChanged: (value) => setState(() {
                _lookingFor = value ?? _lookingFor;
              }),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              initialValue: _intent,
              decoration: const InputDecoration(labelText: 'Intention'),
              items: const [
                DropdownMenuItem(
                  value: 'Relation sérieuse',
                  child: Text('Relation sérieuse'),
                ),
                DropdownMenuItem(value: 'Amitié', child: Text('Amitié')),
                DropdownMenuItem(
                  value: 'Découverte',
                  child: Text('Découvrir sans pression'),
                ),
              ],
              onChanged: (value) => setState(() {
                _intent = value ?? _intent;
              }),
            ),
            const SizedBox(height: 24),
            Text('Distance approximative : ${_distance.round()} km'),
            Slider(
              value: _distance,
              min: 5,
              max: 100,
              divisions: 19,
              label: '${_distance.round()} km',
              onChanged: (value) => setState(() {
                _distance = value;
              }),
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _continue,
              child: const Text('Enregistrer mes préférences'),
            ),
          ],
        ),
      ),
    );
  }
}

class _SuggestedProfile {
  const _SuggestedProfile(this.name, this.age, this.city, this.interests);
  final String name;
  final int age;
  final String city;
  final String interests;
}
