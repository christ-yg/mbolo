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
        builder: (context) => _PreferencesPage(api: widget.api),
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

class _SuggestedProfile {
  const _SuggestedProfile(this.name, this.age, this.city, this.interests);
  final String name;
  final int age;
  final String city;
  final String interests;
}
