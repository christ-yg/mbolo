import 'package:flutter/material.dart';

import 'auth_contract.dart';

// Les boutiques exigent leur système de facturation pour les abonnements
// numériques. Les moyens Web externes restent donc invisibles dans les builds
// distribués, jusqu'à l'intégration de Play Billing / Apple In-App Purchase.
const bool _storeBillingRequired = bool.fromEnvironment(
  'MBOLO_STORE_BILLING_REQUIRED',
  defaultValue: true,
);

class PremiumPage extends StatefulWidget {
  const PremiumPage({super.key, required this.api});
  final AuthApi api;

  @override
  State<PremiumPage> createState() => _PremiumPageState();
}

class _PremiumPageState extends State<PremiumPage> {
  PremiumOverview? _overview;
  List<PremiumPayment> _history = const <PremiumPayment>[];
  bool _loading = true;
  bool _paying = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final results = await Future.wait<Object>([
        widget.api.getPremiumOverview(),
        widget.api.getPremiumPaymentHistory(),
      ]);
      if (!mounted) return;
      setState(() {
        _overview = results[0] as PremiumOverview;
        _history = results[1] as List<PremiumPayment>;
      });
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _choosePayment(PremiumPlan plan) async {
    final available = _overview!.paymentMethods
        .where(
          (item) =>
              item.available &&
              (!_storeBillingRequired ||
                  item.code == 'google_play' ||
                  item.code == 'apple_iap'),
        )
        .toList();
    if (!plan.paymentAvailable || available.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            _storeBillingRequired
                ? 'L’abonnement sera disponible ici avec la facturation sécurisée de la boutique.'
                : 'Le paiement sera ouvert dès la validation du prestataire marchand.',
          ),
        ),
      );
      return;
    }
    final method = await showModalBottomSheet<PremiumPaymentMethod>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Payer ${plan.name}', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
            const SizedBox(height: 8),
            const Text('MBOLO ne te demandera jamais ton code PIN Mobile Money.'),
            const SizedBox(height: 12),
            ...available.map((item) => Card(child: ListTile(
              leading: Icon(item.code == 'bank_card' ? Icons.credit_card : Icons.phone_android, color: const Color(0xFFB51F50)),
              title: Text(item.name, style: const TextStyle(fontWeight: FontWeight.w700)),
              subtitle: Text(item.description), trailing: const Icon(Icons.chevron_right),
              onTap: () => Navigator.pop(context, item),
            ))),
          ]),
        ),
      ),
    );
    if (method == null || !mounted) return;
    final phoneController = TextEditingController();
    final phoneNumber = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.phone_android, color: Color(0xFFB51F50)),
        title: Text('Numéro ${method.name}'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          const Text('Saisis le numéro qui recevra la demande de paiement. Ton code PIN reste secret.'),
          const SizedBox(height: 14),
          TextField(
            controller: phoneController,
            keyboardType: TextInputType.phone,
            autofillHints: const [AutofillHints.telephoneNumber],
            decoration: const InputDecoration(prefixText: '+241 ', labelText: 'Numéro Mobile Money'),
          ),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Annuler')),
          FilledButton(onPressed: () => Navigator.pop(context, phoneController.text), child: const Text('Continuer')),
        ],
      ),
    );
    phoneController.dispose();
    if (phoneNumber == null || phoneNumber.trim().isEmpty || !mounted) return;
    setState(() => _paying = true);
    try {
      final payment = await widget.api.createPremiumCheckout(plan: plan.code, method: method.code, phoneNumber: phoneNumber);
      if (!mounted) return;
      setState(() => _history = <PremiumPayment>[payment, ..._history]);
      await showDialog<void>(context: context, builder: (context) => AlertDialog(
        icon: const Icon(Icons.verified_user_outlined, size: 42, color: Color(0xFFB51F50)),
        title: const Text('Demande créée'),
        content: Text('${payment.planName} · ${payment.methodName}\n${payment.amountXaf} ${payment.currency}\n${payment.customerPhoneMasked}\n\nLe serveur confirmera le paiement avant d’activer l’abonnement.'),
        actions: [FilledButton(onPressed: () => Navigator.pop(context), child: const Text('Compris'))],
      ));
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(friendlyError(error))));
    } finally {
      if (mounted) setState(() => _paying = false);
    }
  }

  Future<void> _toggleIncognito(bool enabled) async {
    try {
      final privacy = await widget.api.updatePremiumPrivacy(enabled);
      if (!mounted) return;
      setState(() => _overview = PremiumOverview(subscription: _overview!.subscription, plans: _overview!.plans, paymentMethods: _overview!.paymentMethods, paymentNotice: _overview!.paymentNotice, privacy: privacy, boost: _overview!.boost));
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(friendlyError(error))));
    }
  }

  Future<void> _activateBoost() async {
    try {
      final boost = await widget.api.activatePremiumBoost();
      if (!mounted) return;
      setState(() => _overview = PremiumOverview(subscription: _overview!.subscription, plans: _overview!.plans, paymentMethods: _overview!.paymentMethods, paymentNotice: _overview!.paymentNotice, privacy: _overview!.privacy, boost: boost));
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Ton profil est mis en avant pendant ${boost.durationMinutes} minutes.')));
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(friendlyError(error))));
    }
  }

  Future<void> _updatePayment(PremiumPayment payment, {required bool confirm}) async {
    setState(() => _paying = true);
    try {
      final updated = confirm ? await widget.api.confirmPremiumPaymentTest(payment.id) : await widget.api.cancelPremiumPayment(payment.id);
      if (!mounted) return;
      setState(() => _history = _history.map((item) => item.id == updated.id ? updated : item).toList(growable: false));
      if (confirm) await _load();
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(friendlyError(error))));
    } finally {
      if (mounted) setState(() => _paying = false);
    }
  }

  String _paymentStatusLabel(String status) => switch (status) {
        'created' => 'Créé',
        'pending' => 'En attente',
        'succeeded' => 'Réussi',
        'failed' => 'Échoué',
        'canceled' => 'Annulé',
        'expired' => 'Expiré',
        _ => 'À vérifier',
      };

  Color _paymentStatusColor(String status) => switch (status) {
        'succeeded' => const Color(0xFF16794B),
        'failed' || 'canceled' || 'expired' => const Color(0xFF9A2D36),
        _ => const Color(0xFF9A5B13),
      };

  IconData _paymentStatusIcon(String status) => switch (status) {
        'succeeded' => Icons.check_circle_outline,
        'failed' => Icons.error_outline,
        'canceled' => Icons.cancel_outlined,
        'expired' => Icons.timer_off_outlined,
        _ => Icons.hourglass_top_rounded,
      };

  @override
  Widget build(BuildContext context) {
    final paidPlans = _overview?.plans
            .where((plan) => plan.code != 'free')
            .toList(growable: false) ??
        const <PremiumPlan>[];
    return Scaffold(
      appBar: AppBar(title: const Text('MBOLO Premium')),
      body: _loading ? const Center(child: CircularProgressIndicator()) : _error != null ? Center(child: FilledButton(onPressed: _load, child: const Text('Réessayer'))) : RefreshIndicator(
        onRefresh: _load,
        child: ListView(padding: const EdgeInsets.fromLTRB(18, 8, 18, 32), children: [
          _PremiumEntrance(index: 0, child: Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(gradient: const LinearGradient(colors: [Color(0xFF391126), Color(0xFFB51F50), Color(0xFFE08A35)]), borderRadius: BorderRadius.circular(28)),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Icon(Icons.workspace_premium, color: Color(0xFFFFD58A), size: 42),
              const SizedBox(height: 12),
              Text(_overview!.subscription.isPremium ? _overview!.subscription.planName : 'Passe au niveau supérieur', style: const TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.w900)),
              const SizedBox(height: 6),
              Text(_overview!.subscription.isPremium ? 'Ton abonnement est actif.' : 'Plus de possibilités, toujours avec sécurité et respect.', style: const TextStyle(color: Colors.white70, fontSize: 15)),
            ]),
          )),
          const SizedBox(height: 20),
          ...paidPlans.asMap().entries.map((entry) {
            final plan = entry.value;
            return _PremiumEntrance(
              index: entry.key + 1,
              child: Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: _PremiumPlanCard(
                  plan: plan,
                  busy: _paying,
                  onPressed: () => _choosePayment(plan),
                ),
              ),
            );
          }),
          Card(color: const Color(0xFFFFF4E8), child: Padding(padding: const EdgeInsets.all(16), child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [const Icon(Icons.lock_outline, color: Color(0xFF8B5520)), const SizedBox(width: 10), Expanded(child: Text(_overview!.paymentNotice))]))),
          if (_storeBillingRequired)
            const Card(
              child: ListTile(
                leading: Icon(Icons.storefront_outlined),
                title: Text('Paiement conforme à la boutique'),
                subtitle: Text('Les abonnements mobiles seront activés avec Google Play Billing ou Apple In-App Purchase. Aucun paiement externe n’est proposé dans cette version.'),
              ),
            ),
          const SizedBox(height: 18),
          Text('Avantages Prestige', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
          Card(child: Column(children: [
            SwitchListTile(
              secondary: const Icon(Icons.visibility_off_outlined),
              title: const Text('Mode incognito'),
              subtitle: Text(_overview!.privacy.available ? 'Seules les personnes que tu likes peuvent te voir.' : 'Disponible avec MBOLO Prestige.'),
              value: _overview!.privacy.effective,
              onChanged: _overview!.privacy.available ? _toggleIncognito : null,
            ),
            const Divider(height: 1),
            ListTile(
              leading: const Icon(Icons.rocket_launch_outlined),
              title: Text(_overview!.boost.active ? 'Boost actif' : 'Booster mon profil'),
              subtitle: Text(_overview!.boost.active ? 'Ton profil est actuellement prioritaire.' : '${_overview!.boost.remaining} boost restant · ${_overview!.boost.durationMinutes} minutes'),
              trailing: FilledButton(onPressed: _overview!.boost.entitled && !_overview!.boost.active && _overview!.boost.remaining > 0 ? _activateBoost : null, child: Text(_overview!.boost.active ? 'Actif' : 'Activer')),
            ),
          ])),
          if (_history.isNotEmpty) ...[
            const SizedBox(height: 22),
            Text('Paiements récents', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
            ..._history.map((item) => Card(child: Padding(padding: const EdgeInsets.all(12), child: Column(children: [
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: Icon(_paymentStatusIcon(item.status), color: _paymentStatusColor(item.status)),
                title: Text(item.planName),
                subtitle: Text('${item.methodName} · ${item.amountXaf} ${item.currency}${item.customerPhoneMasked.isEmpty ? '' : '\n${item.customerPhoneMasked}'}'),
                trailing: Chip(
                  avatar: Icon(_paymentStatusIcon(item.status), size: 16, color: _paymentStatusColor(item.status)),
                  label: Text(_paymentStatusLabel(item.status)),
                ),
              ),
              if (item.status == 'created' || item.status == 'pending') Row(mainAxisAlignment: MainAxisAlignment.end, children: [
                IconButton(onPressed: _paying ? null : _load, tooltip: 'Actualiser le statut', icon: const Icon(Icons.refresh)),
                TextButton(onPressed: _paying ? null : () => _updatePayment(item, confirm: false), child: const Text('Annuler')),
                if (item.canConfirmInTestMode) FilledButton(onPressed: _paying ? null : () => _updatePayment(item, confirm: true), child: const Text('Confirmer le test')),
              ]),
            ])))),
          ],
        ]),
      ),
    );
  }
}

class _PremiumEntrance extends StatelessWidget {
  const _PremiumEntrance({required this.index, required this.child});

  final int index;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final reduceMotion = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: reduceMotion
          ? Duration.zero
          : Duration(milliseconds: 480 + (index * 110)),
      curve: Curves.easeOutCubic,
      child: child,
      builder: (context, value, child) => Opacity(
        opacity: value,
        child: Transform.translate(
          offset: Offset(0, 24 * (1 - value)),
          child: Transform.scale(
            scale: 0.975 + (0.025 * value),
            child: child,
          ),
        ),
      ),
    );
  }
}

class _PremiumPlanCard extends StatefulWidget {
  const _PremiumPlanCard({
    required this.plan,
    required this.busy,
    required this.onPressed,
  });

  final PremiumPlan plan;
  final bool busy;
  final VoidCallback onPressed;

  @override
  State<_PremiumPlanCard> createState() => _PremiumPlanCardState();
}

class _PremiumPlanCardState extends State<_PremiumPlanCard> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final prestige = widget.plan.code == 'prestige';
    final foreground = prestige ? Colors.white : scheme.onSurface;
    final muted = prestige ? Colors.white70 : scheme.onSurfaceVariant;
    final accent = prestige ? const Color(0xFFFFD58A) : scheme.primary;

    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      child: AnimatedScale(
        scale: _hovered ? 1.018 : 1,
        duration: const Duration(milliseconds: 240),
        curve: Curves.easeOutCubic,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 280),
          curve: Curves.easeOutCubic,
          padding: const EdgeInsets.all(22),
          decoration: BoxDecoration(
            gradient: prestige
                ? const LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [Color(0xFF2B0E1D), Color(0xFF721D45), Color(0xFFB54C71)],
                  )
                : LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [scheme.surface, scheme.primaryContainer.withValues(alpha: 0.58)],
                  ),
            borderRadius: BorderRadius.circular(30),
            border: Border.all(color: prestige ? const Color(0x55FFD58A) : scheme.primary.withValues(alpha: 0.22)),
            boxShadow: [
              BoxShadow(
                color: prestige
                    ? const Color(0x55391126)
                    : scheme.primary.withValues(alpha: _hovered ? 0.22 : 0.12),
                blurRadius: _hovered ? 42 : 28,
                offset: Offset(0, _hovered ? 16 : 10),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  AnimatedRotation(
                    turns: _hovered ? 0.04 : 0,
                    duration: const Duration(milliseconds: 260),
                    child: Icon(
                      prestige ? Icons.diamond_outlined : Icons.auto_awesome,
                      color: accent,
                      size: 32,
                    ),
                  ),
                  const Spacer(),
                  Chip(
                    backgroundColor: prestige ? Colors.white12 : scheme.primaryContainer,
                    side: BorderSide.none,
                    label: Text(
                      prestige ? 'EXPÉRIENCE ULTIME' : 'LE PLUS CHOISI',
                      style: TextStyle(color: foreground, fontWeight: FontWeight.w800, fontSize: 11),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 18),
              Text(
                widget.plan.name,
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      color: foreground,
                      fontWeight: FontWeight.w900,
                      letterSpacing: -1,
                    ),
              ),
              const SizedBox(height: 6),
              Text(widget.plan.priceLabel, style: TextStyle(color: accent, fontSize: 20, fontWeight: FontWeight.w900)),
              const SizedBox(height: 10),
              Text(widget.plan.description, style: TextStyle(color: muted, height: 1.45)),
              const SizedBox(height: 16),
              ...widget.plan.features.map(
                (feature) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 5),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.check_circle_rounded, size: 19, color: accent),
                      const SizedBox(width: 9),
                      Expanded(child: Text(feature, style: TextStyle(color: foreground, height: 1.35))),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: widget.busy ? null : widget.onPressed,
                  icon: Icon(prestige ? Icons.workspace_premium : Icons.favorite_rounded),
                  label: Text(
                    _storeBillingRequired
                        ? 'Disponible bientôt sur la boutique'
                        : widget.plan.paymentAvailable
                            ? 'Choisir ${widget.plan.name}'
                            : 'Bientôt disponible',
                  ),
                  style: FilledButton.styleFrom(
                    backgroundColor: prestige ? const Color(0xFFFFD58A) : scheme.primary,
                    foregroundColor: prestige ? const Color(0xFF351220) : scheme.onPrimary,
                    minimumSize: const Size.fromHeight(56),
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
