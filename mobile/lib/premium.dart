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
    return Scaffold(
      appBar: AppBar(title: const Text('MBOLO Premium')),
      body: _loading ? const Center(child: CircularProgressIndicator()) : _error != null ? Center(child: FilledButton(onPressed: _load, child: const Text('Réessayer'))) : RefreshIndicator(
        onRefresh: _load,
        child: ListView(padding: const EdgeInsets.fromLTRB(18, 8, 18, 32), children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(gradient: const LinearGradient(colors: [Color(0xFF391126), Color(0xFFB51F50), Color(0xFFE08A35)]), borderRadius: BorderRadius.circular(28)),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Icon(Icons.workspace_premium, color: Color(0xFFFFD58A), size: 42),
              const SizedBox(height: 12),
              Text(_overview!.subscription.isPremium ? _overview!.subscription.planName : 'Passe au niveau supérieur', style: const TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.w900)),
              const SizedBox(height: 6),
              Text(_overview!.subscription.isPremium ? 'Ton abonnement est actif.' : 'Plus de possibilités, toujours avec sécurité et respect.', style: const TextStyle(color: Colors.white70, fontSize: 15)),
            ]),
          ),
          const SizedBox(height: 20),
          ..._overview!.plans.where((plan) => plan.code != 'free').map((plan) => Padding(
            padding: const EdgeInsets.only(bottom: 14),
            child: Card(
              elevation: plan.code == 'prestige' ? 5 : 1,
              child: Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [Expanded(child: Text(plan.name, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900))), if (plan.code == 'prestige') const Chip(label: Text('ULTIME'))]),
                Text(plan.priceLabel, style: const TextStyle(color: Color(0xFFB51F50), fontSize: 18, fontWeight: FontWeight.w800)),
                const SizedBox(height: 8), Text(plan.description), const SizedBox(height: 12),
                ...plan.features.map((feature) => Padding(padding: const EdgeInsets.symmetric(vertical: 3), child: Row(children: [const Icon(Icons.check_circle, size: 18, color: Color(0xFFB51F50)), const SizedBox(width: 8), Expanded(child: Text(feature))]))),
                const SizedBox(height: 16),
                SizedBox(width: double.infinity, child: FilledButton(onPressed: _paying ? null : () => _choosePayment(plan), child: Text(_storeBillingRequired ? 'Disponible bientôt sur la boutique' : plan.paymentAvailable ? 'Choisir ${plan.name}' : 'Bientôt disponible'))),
              ])),
            ),
          )),
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
