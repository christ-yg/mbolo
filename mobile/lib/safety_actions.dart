import 'package:flutter/material.dart';

import 'auth_contract.dart';

const reportReasons = <String, String>{
  'harassment': 'Harcèlement',
  'fake_profile': 'Faux profil',
  'scam': 'Arnaque',
  'inappropriate_content': 'Contenu inapproprié',
  'threat': 'Menace',
  'spam': 'Spam',
  'underage_suspicion': 'Suspicion de minorité',
  'other': 'Autre motif',
};

Future<bool> showProfileSafetyActions({
  required BuildContext context,
  required AuthApi api,
  required DiscoveryProfile profile,
  String? matchId,
}) async {
  final action = await showModalBottomSheet<String>(
    context: context,
    showDragHandle: true,
    builder: (sheetContext) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Sécurité avec ${profile.displayName}',
              style: Theme.of(sheetContext).textTheme.titleLarge,
            ),
            const SizedBox(height: 12),
            ListTile(
              leading: const Icon(Icons.flag_outlined),
              title: const Text('Signaler ce profil'),
              subtitle: const Text(
                'Transmettre un motif confidentiel à la modération.',
              ),
              onTap: () => Navigator.of(sheetContext).pop('report'),
            ),
            ListTile(
              leading: const Icon(Icons.block, color: Colors.red),
              title: const Text('Bloquer ce profil'),
              subtitle: const Text(
                'Ce profil ne pourra plus interagir avec toi.',
              ),
              onTap: () => Navigator.of(sheetContext).pop('block'),
            ),
            if (matchId != null)
              ListTile(
                leading: const Icon(Icons.heart_broken_outlined),
                title: const Text('Supprimer le match'),
                subtitle: const Text(
                  'La conversation sera fermée définitivement.',
                ),
                onTap: () => Navigator.of(sheetContext).pop('unmatch'),
              ),
          ],
        ),
      ),
    ),
  );

  if (!context.mounted || action == null) return false;
  if (action == 'report') {
    return _report(context: context, api: api, profile: profile);
  }

  final label = action == 'block' ? 'Bloquer' : 'Supprimer le match';
  final explanation = action == 'block'
      ? 'Le blocage est immédiat et désactive vos matchs actifs.'
      : 'La conversation deviendra inaccessible. Cette action est définitive.';
  final confirmed = await showDialog<bool>(
    context: context,
    builder: (dialogContext) => AlertDialog(
      title: Text('$label ${profile.displayName} ?'),
      content: Text(explanation),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(dialogContext).pop(false),
          child: const Text('Annuler'),
        ),
        FilledButton(
          onPressed: () => Navigator.of(dialogContext).pop(true),
          child: Text(label),
        ),
      ],
    ),
  );
  if (confirmed != true || !context.mounted) return false;

  try {
    String notice;
    if (action == 'block') {
      final result = await api.blockProfile(profile.id);
      notice = result.message;
    } else {
      await api.unmatch(matchId!);
      notice = 'Le match et la conversation ont été fermés.';
    }
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(notice)),
      );
    }
    return true;
  } catch (error) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(friendlyError(error))),
      );
    }
    return false;
  }
}

Future<bool> _report({
  required BuildContext context,
  required AuthApi api,
  required DiscoveryProfile profile,
}) async {
  var reason = reportReasons.keys.first;
  final description = TextEditingController();
  final submitted = await showDialog<bool>(
    context: context,
    builder: (dialogContext) => StatefulBuilder(
      builder: (context, setState) => AlertDialog(
        title: Text('Signaler ${profile.displayName}'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                initialValue: reason,
                decoration: const InputDecoration(labelText: 'Motif'),
                items: reportReasons.entries
                    .map(
                      (entry) => DropdownMenuItem(
                        value: entry.key,
                        child: Text(entry.value),
                      ),
                    )
                    .toList(growable: false),
                onChanged: (value) => setState(() {
                  if (value != null) reason = value;
                }),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: description,
                minLines: 3,
                maxLines: 5,
                maxLength: 2000,
                onChanged: (_) => setState(() {}),
                decoration: InputDecoration(
                  labelText: reason == 'other'
                      ? 'Description obligatoire'
                      : 'Précisions facultatives',
                  alignLabelWithHint: true,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Le profil ne sera pas informé de ton identité ni du contenu du signalement.',
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: reason == 'other' && description.text.trim().isEmpty
                ? null
                : () => Navigator.of(dialogContext).pop(true),
            child: const Text('Envoyer'),
          ),
        ],
      ),
    ),
  );

  if (submitted != true || !context.mounted) {
    description.dispose();
    return false;
  }

  try {
    final result = await api.reportProfile(
      profileId: profile.id,
      reason: reason,
      description: description.text,
    );
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result.message)),
      );
    }
    return result.created;
  } catch (error) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(friendlyError(error))),
      );
    }
    return false;
  } finally {
    description.dispose();
  }
}
