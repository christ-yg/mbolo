import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class MboloShowcasePage extends StatefulWidget {
  const MboloShowcasePage({super.key});

  @override
  State<MboloShowcasePage> createState() => _MboloShowcasePageState();
}

class _MboloShowcasePageState extends State<MboloShowcasePage> {
  final _controller = PageController();
  int _page = 0;

  static const _steps = <({IconData icon, String eyebrow, String title, String body, List<String> points})>[
    (
      icon: Icons.favorite_rounded,
      eyebrow: 'RENCONTRES INTELLIGENTES',
      title: 'Des connexions qui ont du sens',
      body: 'MBOLO privilégie la compatibilité, les intentions et les centres d’intérêt plutôt que le défilement vide.',
      points: <String>['Profils contextualisés', 'Compatibilité visible', 'Découverte locale'],
    ),
    (
      icon: Icons.shield_rounded,
      eyebrow: 'TRUST BY DESIGN',
      title: 'La sécurité au cœur du produit',
      body: 'Vérification, signalement, blocage, sessions protégées et confidentialité sont intégrés au parcours.',
      points: <String>['2FA et sessions', 'Modération', 'Contrôle des données'],
    ),
    (
      icon: Icons.workspace_premium_rounded,
      eyebrow: 'MODÈLE DURABLE',
      title: 'Une expérience Premium monétisable',
      body: 'Plus, Prestige, Boost, Incognito et Mobile Money créent une offre adaptée au marché gabonais.',
      points: <String>['Airtel & Moov', 'Abonnements clairs', 'Infrastructure évolutive'],
    ),
  ];

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _next() {
    HapticFeedback.selectionClick();
    if (_page == _steps.length - 1) {
      Navigator.of(context).pop();
      return;
    }
    _controller.nextPage(
      duration: const Duration(milliseconds: 420),
      curve: Curves.easeOutCubic,
    );
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 8, 10, 0),
              child: Row(
                children: [
                  const Expanded(
                    child: Text('MBOLO', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900, letterSpacing: 2.4)),
                  ),
                  TextButton(onPressed: () => Navigator.pop(context), child: const Text('Fermer')),
                ],
              ),
            ),
            Expanded(
              child: PageView.builder(
                controller: _controller,
                itemCount: _steps.length,
                onPageChanged: (value) => setState(() => _page = value),
                itemBuilder: (context, index) {
                  final step = _steps[index];
                  return Padding(
                    padding: const EdgeInsets.fromLTRB(24, 20, 24, 12),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Container(
                          width: 142,
                          height: 142,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: const LinearGradient(colors: [Color(0xFFE95C8D), Color(0xFF7D2348), Color(0xFFD78338)]),
                            boxShadow: [BoxShadow(color: scheme.primary.withValues(alpha: 0.3), blurRadius: 44, spreadRadius: 5)],
                          ),
                          child: Icon(step.icon, color: Colors.white, size: 66),
                        ),
                        const SizedBox(height: 38),
                        Text(step.eyebrow, style: TextStyle(color: scheme.primary, fontSize: 12, fontWeight: FontWeight.w900, letterSpacing: 1.8)),
                        const SizedBox(height: 12),
                        Text(step.title, textAlign: TextAlign.center, style: const TextStyle(fontSize: 30, height: 1.08, fontWeight: FontWeight.w900)),
                        const SizedBox(height: 16),
                        Text(step.body, textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.5)),
                        const SizedBox(height: 24),
                        Wrap(spacing: 8, runSpacing: 8, alignment: WrapAlignment.center, children: step.points.map((point) => Chip(avatar: const Icon(Icons.check, size: 16), label: Text(point))).toList()),
                      ],
                    ),
                  );
                },
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 10, 24, 26),
              child: Column(
                children: [
                  Row(mainAxisAlignment: MainAxisAlignment.center, children: List.generate(_steps.length, (index) => AnimatedContainer(duration: const Duration(milliseconds: 260), width: index == _page ? 28 : 8, height: 8, margin: const EdgeInsets.symmetric(horizontal: 4), decoration: BoxDecoration(color: index == _page ? scheme.primary : scheme.outlineVariant, borderRadius: BorderRadius.circular(99))))),
                  const SizedBox(height: 20),
                  SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: _next, icon: Icon(_page == _steps.length - 1 ? Icons.rocket_launch : Icons.arrow_forward), label: Text(_page == _steps.length - 1 ? 'Explorer MBOLO' : 'Continuer'))),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
