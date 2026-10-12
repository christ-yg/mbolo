import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'auth_contract.dart';

class ProfileVerificationPage extends StatefulWidget {
  const ProfileVerificationPage({super.key, required this.api});

  final AuthApi api;

  @override
  State<ProfileVerificationPage> createState() =>
      _ProfileVerificationPageState();
}

class _ProfileVerificationPageState extends State<ProfileVerificationPage> {
  final ImagePicker _picker = ImagePicker();
  ProfileVerificationState? _state;
  Uint8List? _selfie;
  String _filename = 'selfie.jpg';
  bool _consented = false;
  bool _loading = true;
  bool _submitting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final value = await widget.api.getProfileVerification();
      if (mounted) setState(() => _state = value);
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _capture() async {
    final photo = await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 88,
      maxWidth: 1800,
      maxHeight: 1800,
      requestFullMetadata: false,
    );
    if (photo == null) return;
    final bytes = await photo.readAsBytes();
    if (bytes.length > 10 * 1024 * 1024) {
      if (mounted) {
        setState(() => _error = 'Le selfie dépasse la limite de 10 Mo.');
      }
      return;
    }
    if (mounted) {
      setState(() {
        _selfie = bytes;
        _filename = photo.name.isEmpty ? 'selfie.jpg' : photo.name;
        _error = null;
      });
    }
  }

  Future<void> _submit() async {
    final selfie = _selfie;
    if (selfie == null || !_consented || _submitting) return;
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      final value = await widget.api.submitProfileVerification(
        bytes: selfie,
        filename: _filename,
      );
      if (!mounted) return;
      setState(() {
        _state = value;
        _selfie = null;
        _consented = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selfie transmis pour examen.')),
      );
    } catch (error) {
      if (mounted) setState(() => _error = friendlyError(error));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = _state;
    final scheme = Theme.of(context).colorScheme;
    final canSubmit = state?.canSubmit == true;
    return Scaffold(
      appBar: AppBar(title: const Text('Vérification du profil')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
              children: [
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFFB51F50), Color(0xFF6F1735)],
                    ),
                    borderRadius: BorderRadius.circular(28),
                  ),
                  child: Column(
                    children: [
                      const Icon(Icons.verified_user_rounded,
                          color: Colors.white, size: 54),
                      const SizedBox(height: 12),
                      Text(
                        state?.statusLabel ?? 'Vérification indisponible',
                        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                              color: Colors.white,
                              fontWeight: FontWeight.w800,
                            ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        _statusMessage(state),
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: Colors.white70),
                      ),
                    ],
                  ),
                ),
                if (state?.rejectionReason.isNotEmpty == true) ...[
                  const SizedBox(height: 16),
                  Card(
                    color: scheme.errorContainer,
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Text('À corriger : ${state!.rejectionReason}'),
                    ),
                  ),
                ],
                const SizedBox(height: 24),
                Text('Pourquoi ce selfie ?',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w800,
                        )),
                const SizedBox(height: 12),
                const _TrustPoint(Icons.lock_outline_rounded,
                    'Il reste privé et n’apparaît jamais sur ton profil.'),
                const _TrustPoint(Icons.shield_outlined,
                    'Il sert uniquement à confirmer que ton profil est authentique.'),
                const _TrustPoint(Icons.visibility_off_outlined,
                    'Aucun chemin de stockage n’est envoyé à l’application.'),
                if (canSubmit) ...[
                  const SizedBox(height: 22),
                  Semantics(
                    button: true,
                    label: 'Prendre un selfie de vérification',
                    child: InkWell(
                      onTap: _submitting ? null : _capture,
                      borderRadius: BorderRadius.circular(24),
                      child: Ink(
                        height: 210,
                        decoration: BoxDecoration(
                          color: scheme.surfaceContainerHighest,
                          borderRadius: BorderRadius.circular(24),
                          border: Border.all(color: scheme.outlineVariant),
                          image: _selfie == null
                              ? null
                              : DecorationImage(
                                  image: MemoryImage(_selfie!),
                                  fit: BoxFit.cover,
                                ),
                        ),
                        child: _selfie == null
                            ? const Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.photo_camera_front_outlined, size: 44),
                                  SizedBox(height: 10),
                                  Text('Prendre un selfie récent',
                                      style: TextStyle(fontWeight: FontWeight.w800)),
                                  Text('Visage net · bonne lumière · sans filtre'),
                                ],
                              )
                            : const Align(
                                alignment: Alignment.bottomRight,
                                child: Padding(
                                  padding: EdgeInsets.all(12),
                                  child: Chip(
                                    avatar: Icon(Icons.refresh, size: 18),
                                    label: Text('Reprendre'),
                                  ),
                                ),
                              ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  CheckboxListTile(
                    contentPadding: EdgeInsets.zero,
                    value: _consented,
                    onChanged: _submitting
                        ? null
                        : (value) => setState(() => _consented = value ?? false),
                    title: const Text(
                      'J’accepte l’utilisation privée de ce selfie pour vérifier mon identité.',
                    ),
                    controlAffinity: ListTileControlAffinity.leading,
                  ),
                  const SizedBox(height: 8),
                  FilledButton.icon(
                    key: const ValueKey('submit-profile-verification'),
                    onPressed: _selfie != null && _consented && !_submitting
                        ? _submit
                        : null,
                    icon: _submitting
                        ? const SizedBox.square(
                            dimension: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.verified_rounded),
                    label: Text(_submitting ? 'Envoi sécurisé…' : 'Envoyer pour vérification'),
                  ),
                ],
                if (_error != null) ...[
                  const SizedBox(height: 16),
                  Text(_error!, style: TextStyle(color: scheme.error)),
                ],
              ],
            ),
    );
  }

  String _statusMessage(ProfileVerificationState? state) {
    switch (state?.status) {
      case 'pending':
        return 'Notre équipe examine ta demande. Tu recevras une notification.';
      case 'approved':
        return 'Ton identité est confirmée. Ton badge renforce la confiance.';
      case 'rejected':
        return 'Tu peux reprendre un selfie en suivant les recommandations.';
      default:
        return 'Obtiens un badge de confiance avec un selfie privé.';
    }
  }
}

class _TrustPoint extends StatelessWidget {
  const _TrustPoint(this.icon, this.label);
  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Row(
          children: [
            Icon(icon, color: const Color(0xFFB51F50)),
            const SizedBox(width: 12),
            Expanded(child: Text(label)),
          ],
        ),
      );
}
