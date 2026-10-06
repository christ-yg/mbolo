import 'dart:typed_data';

import 'package:dio/dio.dart';

Uri validateOrigin(String value) {
  final uri = Uri.parse(value);
  if (uri.scheme != 'https' ||
      uri.host.isEmpty ||
      uri.userInfo.isNotEmpty ||
      uri.hasQuery ||
      uri.hasFragment ||
      (uri.path.isNotEmpty && uri.path != '/')) {
    throw const FormatException(
      'MBOLO_API_ORIGIN doit être une origine HTTPS.',
    );
  }
  return uri;
}

Map<String, dynamic> objectData(dynamic raw) {
  if (raw is! Map<String, dynamic>) {
    throw const FormatException('Réponse serveur incorrecte.');
  }
  final data = raw.containsKey('data') ? raw['data'] : raw;
  if (data is! Map<String, dynamic>) {
    throw const FormatException('Réponse serveur incomplète.');
  }
  return data;
}

class Account {
  const Account(this.id, this.email, this.verified);
  final String id;
  final String email;
  final bool verified;

  factory Account.fromJson(Map<String, dynamic> data) {
    if (data['id'] is! String ||
        (data['id'] as String).isEmpty ||
        data['email'] is! String ||
        (data['email'] as String).isEmpty) {
      throw const FormatException('Compte incomplet.');
    }
    return Account(
      data['id'] as String,
      data['email'] as String,
      data['isEmailVerified'] == true || data['is_email_verified'] == true,
    );
  }
}

class LoginResult {
  const LoginResult({this.account, this.challenge, this.maskedEmail});
  final Account? account;
  final String? challenge;
  final String? maskedEmail;

  factory LoginResult.fromJson(Map<String, dynamic> data) {
    if (data['requiresTwoFactor'] == true) {
      final token = data['challengeToken'];
      final email = data['maskedEmail'];
      if (token is! String || token.isEmpty || email is! String) {
        throw const FormatException('Confirmation de connexion incomplète.');
      }
      return LoginResult(challenge: token, maskedEmail: email);
    }
    return LoginResult(account: Account.fromJson(data));
  }
}

String friendlyError(Object error) {
  if (error is DioException) {
    final status = error.response?.statusCode;
    if (status == 429) {
      return 'Trop de tentatives. Patiente avant de réessayer.';
    }
    if (status == 400 || status == 401) {
      return 'Vérifie les informations saisies et réessaie.';
    }
    if (status == 403) return 'Accès refusé. Vérifie ton compte et réessaie.';
    return 'Connexion au serveur impossible. Réessaie dans un instant.';
  }
  return 'La réponse du serveur est invalide. Réessaie plus tard.';
}


class MemberProfile {
  const MemberProfile({
    required this.displayName,
    required this.birthDate,
    required this.gender,
    required this.city,
    required this.biography,
    required this.datingIntent,
    required this.interests,
    required this.complete,
  });

  final String displayName;
  final String birthDate;
  final String gender;
  final String city;
  final String biography;
  final String datingIntent;
  final List<String> interests;
  final bool complete;

  factory MemberProfile.fromJson(Map<String, dynamic> data) {
    final rawInterests = data['interests'];
    return MemberProfile(
      displayName: data['display_name'] is String
          ? data['display_name'] as String
          : '',
      birthDate: data['birth_date'] is String
          ? data['birth_date'] as String
          : '',
      gender: data['gender'] is String ? data['gender'] as String : '',
      city: data['city'] is String ? data['city'] as String : '',
      biography: data['biography'] is String
          ? data['biography'] as String
          : '',
      datingIntent: data['dating_intent'] is String
          ? data['dating_intent'] as String
          : '',
      interests: rawInterests is List
          ? rawInterests.whereType<String>().toList(growable: false)
          : const <String>[],
      complete: data['is_complete'] == true,
    );
  }
}

class DiscoveryProfile {
  const DiscoveryProfile({
    required this.id,
    required this.displayName,
    required this.age,
    required this.city,
    required this.biography,
    required this.datingIntent,
    required this.verified,
    required this.photos,
    required this.interestLabels,
    required this.commonInterestLabels,
    required this.compatibilityScore,
    required this.distanceLabel,
  });

  final String id;
  final String displayName;
  final int age;
  final String city;
  final String biography;
  final String datingIntent;
  final bool verified;
  final List<ProfilePhoto> photos;
  final List<String> interestLabels;
  final List<String> commonInterestLabels;
  final int compatibilityScore;
  final String distanceLabel;

  factory DiscoveryProfile.fromJson(Map<String, dynamic> data) {
    final id = data['id'];
    final name = data['display_name'];
    if (id is! String || id.isEmpty || name is! String || name.isEmpty) {
      throw const FormatException('Profil de découverte incomplet.');
    }
    List<String> strings(dynamic raw) => raw is List
        ? raw.whereType<String>().toList(growable: false)
        : const <String>[];
    final rawPhotos = data['photos'];
    return DiscoveryProfile(
      id: id,
      displayName: name,
      age: data['age'] is int ? data['age'] as int : 0,
      city: data['city'] is String ? data['city'] as String : '',
      biography: data['biography'] is String ? data['biography'] as String : '',
      datingIntent: data['dating_intent'] is String
          ? data['dating_intent'] as String
          : '',
      verified: data['is_verified'] == true,
      photos: rawPhotos is List
          ? rawPhotos
                .whereType<Map<String, dynamic>>()
                .map(ProfilePhoto.fromJson)
                .toList(growable: false)
          : const <ProfilePhoto>[],
      interestLabels: strings(data['interest_labels']),
      commonInterestLabels: strings(data['common_interest_labels']),
      compatibilityScore: data['compatibility_score'] is int
          ? data['compatibility_score'] as int
          : 0,
      distanceLabel: data['distance_label'] is String
          ? data['distance_label'] as String
          : '',
    );
  }
}

class InteractionResult {
  const InteractionResult({
    required this.decision,
    required this.matched,
    required this.matchCreated,
    this.matchId,
  });

  final String decision;
  final bool matched;
  final bool matchCreated;
  final String? matchId;

  factory InteractionResult.fromJson(Map<String, dynamic> data) {
    return InteractionResult(
      decision: data['decision'] is String ? data['decision'] as String : '',
      matched: data['matched'] == true,
      matchCreated: data['match_created'] == true,
      matchId: data['match_id'] is String ? data['match_id'] as String : null,
    );
  }
}

class ProfilePhoto {
  const ProfilePhoto({
    required this.id,
    required this.imageUrl,
    required this.position,
    required this.primary,
    required this.moderationStatus,
    required this.moderationStatusLabel,
    this.previewBytes,
  });

  final String id;
  final String imageUrl;
  final int position;
  final bool primary;
  final String moderationStatus;
  final String moderationStatusLabel;
  final Uint8List? previewBytes;

  factory ProfilePhoto.fromJson(Map<String, dynamic> data) {
    final id = data['id'];
    if (id is! String || id.isEmpty) {
      throw const FormatException('Photo de profil incomplète.');
    }
    return ProfilePhoto(
      id: id,
      imageUrl: data['image_url'] is String ? data['image_url'] as String : '',
      position: data['position'] is int ? data['position'] as int : 0,
      primary: data['is_primary'] == true,
      moderationStatus: data['moderation_status'] is String
          ? data['moderation_status'] as String
          : 'pending',
      moderationStatusLabel: data['moderation_status_label'] is String
          ? data['moderation_status_label'] as String
          : 'En attente',
    );
  }
}

class DiscoveryPreferences {
  const DiscoveryPreferences({
    required this.minimumAge,
    required this.maximumAge,
    required this.preferredGenders,
    required this.advancedFiltersAvailable,
  });

  final int minimumAge;
  final int maximumAge;
  final List<String> preferredGenders;
  final bool advancedFiltersAvailable;

  factory DiscoveryPreferences.fromJson(Map<String, dynamic> data) {
    final rawGenders = data['preferred_genders'];
    return DiscoveryPreferences(
      minimumAge: data['minimum_age'] is int
          ? data['minimum_age'] as int
          : 18,
      maximumAge: data['maximum_age'] is int
          ? data['maximum_age'] as int
          : 45,
      preferredGenders: rawGenders is List
          ? rawGenders.whereType<String>().toList(growable: false)
          : const <String>[],
      advancedFiltersAvailable:
          data['advanced_filters_available'] == true,
    );
  }
}


class ChatMessage {
  const ChatMessage({
    required this.id,
    required this.body,
    required this.createdAt,
    required this.mine,
    required this.read,
    required this.readReceiptsAvailable,
  });

  final String id;
  final String body;
  final DateTime createdAt;
  final bool mine;
  final bool read;
  final bool readReceiptsAvailable;

  factory ChatMessage.fromJson(Map<String, dynamic> data) {
    final id = data['id'];
    final body = data['body'];
    final createdAt = DateTime.tryParse(data['created_at']?.toString() ?? '');
    if (id is! String || id.isEmpty || body is! String || createdAt == null) {
      throw const FormatException('Message incomplet.');
    }
    return ChatMessage(
      id: id,
      body: body,
      createdAt: createdAt,
      mine: data['is_mine'] == true,
      read: data['is_read'] == true,
      readReceiptsAvailable: data['read_receipts_available'] == true,
    );
  }
}

class ConversationSummary {
  const ConversationSummary({
    required this.id,
    required this.matchId,
    required this.otherProfile,
    required this.unreadCount,
    required this.online,
    required this.updatedAt,
    this.lastMessage,
  });

  final String id;
  final String matchId;
  final DiscoveryProfile otherProfile;
  final ChatMessage? lastMessage;
  final int unreadCount;
  final bool online;
  final DateTime updatedAt;

  factory ConversationSummary.fromJson(Map<String, dynamic> data) {
    final id = data['id'];
    final matchId = data['match_id'];
    final profile = data['other_profile'];
    final updatedAt = DateTime.tryParse(data['updated_at']?.toString() ?? '');
    if (id is! String ||
        id.isEmpty ||
        matchId is! String ||
        profile is! Map<String, dynamic> ||
        updatedAt == null) {
      throw const FormatException('Conversation incomplète.');
    }
    final rawMessage = data['last_message'];
    final rawPresence = data['other_presence'];
    return ConversationSummary(
      id: id,
      matchId: matchId,
      otherProfile: DiscoveryProfile.fromJson(profile),
      lastMessage: rawMessage is Map<String, dynamic>
          ? ChatMessage.fromJson(rawMessage)
          : null,
      unreadCount: data['unread_count'] is int ? data['unread_count'] as int : 0,
      online: rawPresence is Map<String, dynamic> &&
          rawPresence['is_online'] == true,
      updatedAt: updatedAt,
    );
  }
}

abstract class AuthApi {
  Future<Account> register({
    required String email,
    required String password,
    required String passwordConfirmation,
    required bool acceptTerms,
    required bool confirmAdult,
  });
  Future<void> requestPasswordReset(String email);
  Future<LoginResult> login(String email, String password);
  Future<Account> confirm(String challenge, String code);
  Future<Account> me();
  Future<MemberProfile> getProfile();
  Future<MemberProfile> updateProfile({
    required String displayName,
    required String birthDate,
    required String gender,
    required String city,
    required String biography,
    required String datingIntent,
    required List<String> interests,
  });
  Future<List<DiscoveryProfile>> getDiscovery();
  Future<InteractionResult> decideProfile({
    required String profileId,
    required String decision,
  });
  Future<List<ProfilePhoto>> getPhotos();
  Future<ProfilePhoto> uploadPhoto({
    required Uint8List bytes,
    required String filename,
    required int position,
    required bool primary,
  });
  Future<ProfilePhoto> updatePhoto({
    required String id,
    int? position,
    bool? primary,
  });
  Future<void> deletePhoto(String id);
  Future<DiscoveryPreferences> getPreferences();
  Future<DiscoveryPreferences> updatePreferences({
    required int minimumAge,
    required int maximumAge,
    required List<String> preferredGenders,
  });
  Future<List<ConversationSummary>> getConversations();
  Future<List<ChatMessage>> getMessages(String conversationId);
  Future<ChatMessage> sendMessage(String conversationId, String body);
  Future<void> markConversationRead(String conversationId);
  Future<void> logout();
  void close();
}
