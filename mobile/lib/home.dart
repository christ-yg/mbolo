import 'package:flutter/material.dart';

import 'auth_contract.dart';

class MboloHome extends StatefulWidget {
  const MboloHome({super.key, required this.account, required this.onLogout});

  final Account account;
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

  @override
  Widget build(BuildContext context) {
    final pages = [
      _DiscoverPage(profile: _profiles[_profile], onNext: _next),
      _ActivityPage(liked: _liked.toList(growable: false)),
      _SafetyPage(onOpenProfile: () => setState(() => _tab = 3)),
      _ProfilePage(account: widget.account, onLogout: widget.onLogout),
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
  const _ProfilePage({required this.account, required this.onLogout});
  final Account account;
  final Future<void> Function() onLogout;

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
        const Card(
          child: Column(
            children: [
              ListTile(
                leading: Icon(Icons.edit_outlined),
                title: Text('Compléter mon profil'),
                trailing: Icon(Icons.chevron_right),
              ),
              Divider(height: 1),
              ListTile(
                leading: Icon(Icons.tune),
                title: Text('Préférences de rencontre'),
                trailing: Icon(Icons.chevron_right),
              ),
              Divider(height: 1),
              ListTile(
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

class _SuggestedProfile {
  const _SuggestedProfile(this.name, this.age, this.city, this.interests);
  final String name;
  final int age;
  final String city;
  final String interests;
}
