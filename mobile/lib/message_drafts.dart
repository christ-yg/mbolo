import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Private, per-conversation text drafts. Attachments are deliberately excluded
/// so that photos never remain cached after leaving the composer.
abstract class MessageDraftStore {
  Future<String?> read(String conversationId);
  Future<void> write(String conversationId, String value);
  Future<void> clear(String conversationId);
}

class EncryptedMessageDraftStore implements MessageDraftStore {
  EncryptedMessageDraftStore({FlutterSecureStorage? storage})
    : _storage = storage ??
          const FlutterSecureStorage(aOptions: AndroidOptions());

  static const _prefix = 'mbolo_message_draft_v1_';
  static const _maximumLength = 2000;
  final FlutterSecureStorage _storage;

  String _key(String conversationId) => '$_prefix$conversationId';

  @override
  Future<String?> read(String conversationId) async {
    final value = await _storage.read(key: _key(conversationId));
    if (value == null || value.trim().isEmpty) return null;
    return value.length <= _maximumLength
        ? value
        : value.substring(0, _maximumLength);
  }

  @override
  Future<void> write(String conversationId, String value) async {
    if (value.trim().isEmpty) {
      await clear(conversationId);
      return;
    }
    final safeValue = value.length <= _maximumLength
        ? value
        : value.substring(0, _maximumLength);
    await _storage.write(key: _key(conversationId), value: safeValue);
  }

  @override
  Future<void> clear(String conversationId) =>
      _storage.delete(key: _key(conversationId));
}

class MemoryMessageDraftStore implements MessageDraftStore {
  final Map<String, String> _drafts = <String, String>{};

  @override
  Future<String?> read(String conversationId) async => _drafts[conversationId];

  @override
  Future<void> write(String conversationId, String value) async {
    if (value.trim().isEmpty) {
      _drafts.remove(conversationId);
    } else {
      _drafts[conversationId] = value;
    }
  }

  @override
  Future<void> clear(String conversationId) async {
    _drafts.remove(conversationId);
  }
}
