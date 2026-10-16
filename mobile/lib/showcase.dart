import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

typedef ShowcaseStep = ({
  IconData icon,
  String eyebrow,
  String title,
  String body,
  List<String> points,
  String metric,
  String metricLabel,
  Color start,
  Color end,
});

class MboloShowcasePage extends StatefulWidget {
  const MboloShowcasePage({super.key});

  @override
  State<MboloShowcasePage> createState() => _MboloShowcasePageState();
}

class _MboloShowcasePageState extends State<MboloShowcasePage>
    with SingleTickerProviderStateMixin {
  final _controller = PageController();
  late final AnimationController _ambient;
  int _page = 0;

  static const _steps = <ShowcaseStep>[
    (
      icon: Icons.auto_awesome_rounded,
      eyebrow: 'L’AFRIQUE SE RENCONTRE AUTREMENT',
      title: 'Une première impression inoubliable',
      body:
          'Un univers élégant, vivant et local qui transforme chaque découverte en moment fort.',
      points: ['Expérience immersive', 'Identité africaine', 'Design premium'],
      metric: '< 3 min',
      metricLabel: 'pour créer un profil',
      start: Color(0xFFE95C8D),
      end: Color(0xFF7D2348),
    ),
    (
      icon: Icons.favorite_rounded,
      eyebrow: 'RENCONTRES INTELLIGENTES',
      title: 'Des connexions qui ont du sens',
      body:
          'MBOLO privilégie la compatibilité, les intentions et les centres d’intérêt plutôt que le défilement vide.',
      points: ['Profils contextualisés', 'Compatibilité visible', 'Découverte locale'],
      metric: '360°',
      metricLabel: 'de contexte utile',
      start: Color(0xFF8A4FFF),
      end: Color(0xFF451F89),
    ),
    (
      icon: Icons.shield_rounded,
      eyebrow: 'TRUST BY DESIGN',
      title: 'La confiance au cœur du produit',
      body:
          'Vérification, signalement, blocage, sessions protégées et confidentialité sont intégrés au parcours.',
      points: ['2FA et sessions', 'Modération', 'Contrôle des données'],
      metric: '24/7',
      metricLabel: 'protection intégrée',
      start: Color(0xFF167D75),
      end: Color(0xFF073C48),
    ),
    (
      icon: Icons.workspace_premium_rounded,
      eyebrow: 'MODÈLE DURABLE',
      title: 'Un produit prêt à changer d’échelle',
      body:
          'Plus, Prestige, Boost, Incognito et Mobile Money créent une offre adaptée au marché gabonais.',
      points: ['Airtel & Moov', 'Abonnements clairs', 'Infrastructure évolutive'],
      metric: '2 offres',
      metricLabel: 'premium accessibles',
      start: Color(0xFFD78338),
      end: Color(0xFF7E3D20),
    ),
  ];

  @override
  void initState() {
    super.initState();
    _ambient = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 7),
    )..repeat();
  }

  @override
  void dispose() {
    _ambient.dispose();
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
      duration: const Duration(milliseconds: 520),
      curve: Curves.easeOutCubic,
    );
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final dark = Theme.of(context).brightness == Brightness.dark;
    return Scaffold(
      body: Stack(
        children: [
          Positioned.fill(
            child: AnimatedBuilder(
              animation: _ambient,
              builder: (context, child) {
                final angle = _ambient.value * math.pi * 2;
                return DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: RadialGradient(
                      center: Alignment(
                        math.sin(angle) * .55,
                        math.cos(angle) * .28 - .45,
                      ),
                      radius: 1.15,
                      colors: [
                        scheme.primary.withValues(alpha: dark ? .20 : .13),
                        scheme.surface.withValues(alpha: 0),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          SafeArea(
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 8, 10, 0),
                  child: Row(
                    children: [
                      Container(
                        width: 36,
                        height: 36,
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [Color(0xFFE95C8D), Color(0xFF7D2348)],
                          ),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(
                          Icons.favorite_rounded,
                          size: 20,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(width: 11),
                      const Expanded(
                        child: Text(
                          'MBOLO',
                          style: TextStyle(
                            fontSize: 19,
                            fontWeight: FontWeight.w900,
                            letterSpacing: 2.4,
                          ),
                        ),
                      ),
                      TextButton(
                        onPressed: () => Navigator.pop(context),
                        child: const Text('Fermer'),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: PageView.builder(
                    controller: _controller,
                    physics: const BouncingScrollPhysics(),
                    itemCount: _steps.length,
                    onPageChanged: (value) {
                      HapticFeedback.selectionClick();
                      setState(() => _page = value);
                    },
                    itemBuilder: (context, index) => _ShowcaseStep(
                      step: _steps[index],
                      ambient: _ambient,
                    ),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(24, 8, 24, 22),
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: List.generate(
                          _steps.length,
                          (index) => AnimatedContainer(
                            duration: const Duration(milliseconds: 320),
                            curve: Curves.easeOutCubic,
                            width: index == _page ? 34 : 8,
                            height: 8,
                            margin: const EdgeInsets.symmetric(horizontal: 4),
                            decoration: BoxDecoration(
                              color: index == _page
                                  ? scheme.primary
                                  : scheme.outlineVariant,
                              borderRadius: BorderRadius.circular(99),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        child: FilledButton.icon(
                          onPressed: _next,
                          icon: Icon(
                            _page == _steps.length - 1
                                ? Icons.rocket_launch_rounded
                                : Icons.arrow_forward_rounded,
                          ),
                          label: Text(
                            _page == _steps.length - 1
                                ? 'Explorer MBOLO'
                                : 'Continuer',
                          ),
                        ),
                      ),
                      const SizedBox(height: 9),
                      Text(
                        '${_page + 1} / ${_steps.length}  •  Glissez pour découvrir',
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: scheme.onSurfaceVariant,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ShowcaseStep extends StatelessWidget {
  const _ShowcaseStep({required this.step, required this.ambient});

  final ShowcaseStep step;
  final Animation<double> ambient;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxHeight < 590;
        return SingleChildScrollView(
          padding: EdgeInsets.fromLTRB(22, compact ? 12 : 24, 22, 10),
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: constraints.maxHeight - 22),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                AnimatedBuilder(
                  animation: ambient,
                  builder: (context, child) {
                    final wave = math.sin(ambient.value * math.pi * 2);
                    return Transform.translate(
                      offset: Offset(0, wave * 5),
                      child: Transform.rotate(angle: wave * .025, child: child),
                    );
                  },
                  child: _ShowcaseIcon(step: step, compact: compact),
                ),
                SizedBox(height: compact ? 24 : 34),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                  decoration: BoxDecoration(
                    color: step.start.withValues(alpha: .11),
                    borderRadius: BorderRadius.circular(99),
                    border: Border.all(color: step.start.withValues(alpha: .24)),
                  ),
                  child: Text(
                    step.eyebrow,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: step.start,
                      fontSize: 10.5,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 1.25,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  step.title,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: compact ? 27 : 32,
                    height: 1.05,
                    fontWeight: FontWeight.w900,
                    letterSpacing: -.8,
                  ),
                ),
                const SizedBox(height: 13),
                ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 560),
                  child: Text(
                    step.body,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      height: 1.45,
                      color: scheme.onSurfaceVariant,
                    ),
                  ),
                ),
                SizedBox(height: compact ? 14 : 19),
                _MetricCard(step: step),
                SizedBox(height: compact ? 13 : 17),
                Wrap(
                  spacing: 7,
                  runSpacing: 7,
                  alignment: WrapAlignment.center,
                  children: step.points
                      .map(
                        (point) => Chip(
                          avatar: Icon(
                            Icons.check_circle_rounded,
                            size: 16,
                            color: step.start,
                          ),
                          label: Text(point),
                          side: BorderSide.none,
                          visualDensity: VisualDensity.compact,
                        ),
                      )
                      .toList(),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _ShowcaseIcon extends StatelessWidget {
  const _ShowcaseIcon({required this.step, required this.compact});
  final ShowcaseStep step;
  final bool compact;

  @override
  Widget build(BuildContext context) => Container(
    width: compact ? 116 : 146,
    height: compact ? 116 : 146,
    decoration: BoxDecoration(
      borderRadius: BorderRadius.circular(compact ? 34 : 44),
      gradient: LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [step.start, step.end],
      ),
      border: Border.all(color: Colors.white.withValues(alpha: .22)),
      boxShadow: [
        BoxShadow(
          color: step.start.withValues(alpha: .32),
          blurRadius: 44,
          spreadRadius: 4,
          offset: const Offset(0, 18),
        ),
      ],
    ),
    child: Stack(
      children: [
        Positioned(
          top: 12,
          right: 12,
          child: Icon(
            Icons.auto_awesome,
            color: Colors.white.withValues(alpha: .55),
            size: 19,
          ),
        ),
        Center(
          child: Icon(
            step.icon,
            color: Colors.white,
            size: compact ? 54 : 66,
          ),
        ),
      ],
    ),
  );
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({required this.step});
  final ShowcaseStep step;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 13),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest.withValues(alpha: .66),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: scheme.outlineVariant.withValues(alpha: .65)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            step.metric,
            style: TextStyle(
              color: step.start,
              fontSize: 20,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(width: 10),
          Flexible(
            child: Text(
              step.metricLabel,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}
