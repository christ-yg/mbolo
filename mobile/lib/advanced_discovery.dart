import 'package:flutter/material.dart';

import 'auth_contract.dart';

class AdvancedDiscoveryPage extends StatefulWidget {
  const AdvancedDiscoveryPage({super.key, required this.api});
  final AuthApi api;

  @override
  State<AdvancedDiscoveryPage> createState() => _AdvancedDiscoveryPageState();
}

class _AdvancedDiscoveryPageState extends State<AdvancedDiscoveryPage> {
  static const _cities = {
    'libreville': 'Libreville', 'port_gentil': 'Port-Gentil',
    'franceville': 'Franceville', 'oyem': 'Oyem', 'moanda': 'Moanda',
    'lambarene': 'Lambaréné', 'mouila': 'Mouila', 'tchibanga': 'Tchibanga',
    'koulamoutou': 'Koulamoutou', 'makokou': 'Makokou', 'bitam': 'Bitam',
    'other': 'Autre ville',
  };
  static const _intents = {
    'serious_relationship': 'Relation sérieuse', 'friendship': 'Amitié',
    'discussion': 'Discussion', 'marriage': 'Mariage',
    'not_sure': 'Je ne sais pas encore',
  };
  Set<String> _selectedCities = {};
  Set<String> _selectedIntents = {};
  int _distance = 50;
  bool _verified = false;
  bool _photos = false;
  bool _available = false;
  bool _loading = true;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final value = await widget.api.getAdvancedDiscoveryFilters();
      if (!mounted) return;
      setState(() {
        _available = value.available;
        _selectedCities = value.cities.toSet();
        _selectedIntents = value.intents.toSet();
        _distance = value.distanceKm;
        _verified = value.verifiedOnly;
        _photos = value.photosOnly;
      });
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _save() async {
    if (_saving || !_available) return;
    setState(() { _saving = true; _error = null; });
    try {
      await widget.api.updateAdvancedDiscoveryFilters(AdvancedDiscoveryFilters(
        available: _available,
        cities: _selectedCities.toList(), intents: _selectedIntents.toList(),
        distanceKm: _distance, verifiedOnly: _verified, photosOnly: _photos,
      ));
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Filtres avancés enregistrés.')),
      );
      Navigator.of(context).pop();
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  void _reset() => setState(() {
    _selectedCities = {}; _selectedIntents = {}; _distance = 50;
    _verified = false; _photos = false;
  });

  Widget _choices(String title, Map<String, String> options, Set<String> selected) =>
    Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(title, style: Theme.of(context).textTheme.titleMedium),
      const SizedBox(height: 8),
      Wrap(spacing: 8, runSpacing: 4, children: options.entries.map((entry) => FilterChip(
        label: Text(entry.value), selected: selected.contains(entry.key),
        onSelected: !_available || _saving ? null : (enabled) => setState(() {
          if (enabled) { selected.add(entry.key); } else { selected.remove(entry.key); }
        }),
      )).toList()),
      const SizedBox(height: 20),
    ]);

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Découverte avancée')),
    body: SafeArea(child: _loading
      ? const Center(child: CircularProgressIndicator())
      : ListView(padding: const EdgeInsets.all(20), children: [
        if (_error != null) ...[
          Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
          TextButton.icon(onPressed: _saving ? null : _load,
            icon: const Icon(Icons.refresh), label: const Text('Réessayer')),
        ],
        if (!_available) const Card(child: Padding(padding: EdgeInsets.all(16),
          child: Text('Ces filtres nécessitent un abonnement Plus ou Prestige actif. Tes préférences de base restent disponibles.'))),
        Card(child: Padding(padding: const EdgeInsets.all(16), child: Text(
          '${_selectedCities.isEmpty ? 'Toutes les villes' : '${_selectedCities.length} ville(s)'} · '
          '${_selectedIntents.isEmpty ? 'Toutes les intentions' : '${_selectedIntents.length} intention(s)'} · $_distance km',
        ))),
        const SizedBox(height: 16),
        _choices('Villes recherchées', _cities, _selectedCities),
        _choices('Intentions de rencontre', _intents, _selectedIntents),
        Text('Distance maximale : $_distance km', style: Theme.of(context).textTheme.titleMedium),
        Slider(value: _distance.toDouble(), min: 1, max: 500, divisions: 499,
          label: '$_distance km', semanticFormatterCallback: (value) => '${value.round()} kilomètres',
          onChanged: !_available || _saving ? null : (value) => setState(() => _distance = value.round())),
        const Text('Distance approximative entre les villes déclarées, sans localisation GPS précise.'),
        const SizedBox(height: 16),
        SwitchListTile(contentPadding: EdgeInsets.zero, title: const Text('Profils vérifiés uniquement'),
          value: _verified, onChanged: !_available || _saving ? null : (value) => setState(() => _verified = value)),
        SwitchListTile(contentPadding: EdgeInsets.zero, title: const Text('Profils avec photo uniquement'),
          value: _photos, onChanged: !_available || _saving ? null : (value) => setState(() => _photos = value)),
        const SizedBox(height: 16),
        const Text('Aucune sélection de ville ou d’intention signifie : toutes. Les filtres se cumulent et peuvent réduire les résultats.'),
        const SizedBox(height: 16),
        OutlinedButton(onPressed: !_available || _saving ? null : _reset,
          child: const Text('Réinitialiser les filtres')),
        const Text('La remise à zéro sera appliquée après enregistrement.'),
        const SizedBox(height: 12),
        FilledButton(onPressed: !_available || _saving ? null : _save,
          child: Text(_saving ? 'Enregistrement…' : 'Enregistrer les filtres')),
      ])),
  );
}
