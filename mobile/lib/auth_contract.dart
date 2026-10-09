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
  const Account(
    this.id,
    this.email,
    this.verified, {
    this.emailTwoFactorEnabled = false,
  });
  final String id;
  final String email;
  final bool verified;
  final bool emailTwoFactorEnabled;

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
      emailTwoFactorEnabled: data['emailTwoFactorEnabled'] == true ||
          data['email_2fa_enabled'] == true,
    );
  }
}

class ConnectedSession {
  const ConnectedSession({
    required this.id,
    required this.device,
    required this.ipFingerprint,
    required this.createdAt,
    required this.lastSeenAt,
    required this.current,
  });

  final String id;
  final String device;
  final String ipFingerprint;
  final DateTime createdAt;
  final DateTime lastSeenAt;
  final bool current;

  factory ConnectedSession.fromJson(Map<String, dynamic> data) {
    final id = data['id'];
    final createdAt = DateTime.tryParse(data['createdAt']?.toString() ?? '');
    final lastSeenAt = DateTime.tryParse(data['lastSeenAt']?.toString() ?? '');
    if (id is! String || id.isEmpty || createdAt == null || lastSeenAt == null) {
      throw const FormatException('Session connectée incorrecte.');
    }
    return ConnectedSession(
      id: id,
      device: data['device'] is String ? data['device'] as String : 'Appareil',
      ipFingerprint: data['ipFingerprint'] is String
          ? data['ipFingerprint'] as String
          : '',
      createdAt: createdAt,
      lastSeenAt: lastSeenAt,
      current: data['isCurrent'] == true,
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


class AppNotification {
  const AppNotification({
    required this.id,
    required this.kind,
    required this.title,
    required this.body,
    required this.targetPath,
    required this.read,
    required this.createdAt,
  });

  final String id;
  final String kind;
  final String title;
  final String body;
  final String targetPath;
  final bool read;
  final DateTime createdAt;

  factory AppNotification.fromJson(Map<String, dynamic> data) {
    final createdAt = DateTime.tryParse(data['created_at']?.toString() ?? '');
    if (data['id'] is! String ||
        (data['id'] as String).isEmpty ||
        data['kind'] is! String ||
        data['title'] is! String ||
        createdAt == null) {
      throw const FormatException('Notification incomplète.');
    }
    return AppNotification(
      id: data['id'] as String,
      kind: data['kind'] as String,
      title: data['title'] as String,
      body: data['body'] is String ? data['body'] as String : '',
      targetPath:
          data['target_path'] is String ? data['target_path'] as String : '',
      read: data['is_read'] == true,
      createdAt: createdAt,
    );
  }

  AppNotification copyWith({bool? read}) => AppNotification(
        id: id,
        kind: kind,
        title: title,
        body: body,
        targetPath: targetPath,
        read: read ?? this.read,
        createdAt: createdAt,
      );
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

class SuperLikeState {
  const SuperLikeState({
    required this.entitled,
    required this.dailyLimit,
    required this.remainingToday,
  });

  final bool entitled;
  final int dailyLimit;
  final int remainingToday;

  factory SuperLikeState.fromJson(Map<String, dynamic> data) {
    final limit = data['daily_limit'];
    final remaining = data['remaining_today'];
    if (limit is! int || remaining is! int || limit < 0 || remaining < 0) {
      throw const FormatException('État des Super Likes incorrect.');
    }
    return SuperLikeState(
      entitled: data['entitled'] == true,
      dailyLimit: limit,
      remainingToday: remaining,
    );
  }
}

class RewindState {
  const RewindState({
    required this.entitled,
    required this.available,
    required this.reason,
  });

  final bool entitled;
  final bool available;
  final String reason;

  factory RewindState.fromJson(Map<String, dynamic> data) {
    final reason = data['reason'];
    if (reason is! String || reason.isEmpty) {
      throw const FormatException('État du retour arrière incorrect.');
    }
    return RewindState(
      entitled: data['entitled'] == true,
      available: data['available'] == true,
      reason: reason,
    );
  }
}

class MatchSummary {
  const MatchSummary({
    required this.id,
    required this.otherProfile,
    required this.createdAt,
  });

  final String id;
  final DiscoveryProfile otherProfile;
  final DateTime createdAt;

  factory MatchSummary.fromJson(Map<String, dynamic> data) {
    final id = data['id'];
    final profile = data['other_profile'];
    final createdAt = DateTime.tryParse(data['created_at']?.toString() ?? '');
    if (id is! String ||
        id.isEmpty ||
        profile is! Map<String, dynamic> ||
        createdAt == null) {
      throw const FormatException('Match incomplet.');
    }
    return MatchSummary(
      id: id,
      otherProfile: DiscoveryProfile.fromJson(profile),
      createdAt: createdAt,
    );
  }
}

class ReceivedLike {
  const ReceivedLike({
    required this.interactionId,
    required this.city,
    required this.ageRange,
    required this.datingIntent,
    required this.hasPhoto,
    required this.identityRevealed,
    required this.superLike,
    required this.receivedAt,
    this.profileId,
    this.displayName,
    this.imageUrl,
  });

  final String interactionId;
  final String city;
  final String ageRange;
  final String datingIntent;
  final bool hasPhoto;
  final bool identityRevealed;
  final bool superLike;
  final DateTime receivedAt;
  final String? profileId;
  final String? displayName;
  final String? imageUrl;

  factory ReceivedLike.fromJson(Map<String, dynamic> data) {
    final id = data['interaction_id'];
    final receivedAt = DateTime.tryParse(data['received_at']?.toString() ?? '');
    if (id is! String || id.isEmpty || receivedAt == null) {
      throw const FormatException('Like reçu incomplet.');
    }
    return ReceivedLike(
      interactionId: id,
      city: data['city'] is String ? data['city'] as String : 'Ville inconnue',
      ageRange: data['age_range'] is String ? data['age_range'] as String : '',
      datingIntent:
          data['dating_intent'] is String ? data['dating_intent'] as String : '',
      hasPhoto: data['has_photo'] == true,
      identityRevealed: data['is_identity_revealed'] == true,
      superLike: data['is_super_like'] == true,
      receivedAt: receivedAt,
      profileId: data['profile_id'] is String ? data['profile_id'] as String : null,
      displayName:
          data['display_name'] is String ? data['display_name'] as String : null,
      imageUrl: data['image_url'] is String ? data['image_url'] as String : null,
    );
  }
}

class ReceivedLikeResult {
  const ReceivedLikeResult({
    required this.decision,
    required this.matched,
    required this.matchCreated,
    this.matchId,
    this.revealedProfile,
  });

  final String decision;
  final bool matched;
  final bool matchCreated;
  final String? matchId;
  final DiscoveryProfile? revealedProfile;

  factory ReceivedLikeResult.fromJson(Map<String, dynamic> data) {
    final rawProfile = data['revealed_profile'];
    return ReceivedLikeResult(
      decision: data['decision'] is String ? data['decision'] as String : '',
      matched: data['matched'] == true,
      matchCreated: data['match_created'] == true,
      matchId: data['match_id'] is String ? data['match_id'] as String : null,
      revealedProfile: rawProfile is Map<String, dynamic>
          ? DiscoveryProfile.fromJson(rawProfile)
          : null,
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



class SafetyActionResult {
  const SafetyActionResult({
    required this.created,
    required this.message,
    this.deactivatedMatches = 0,
  });

  final bool created;
  final String message;
  final int deactivatedMatches;

  factory SafetyActionResult.fromJson(Map<String, dynamic> data) {
    return SafetyActionResult(
      created: data['created'] == true,
      message: data['message'] is String
          ? data['message'] as String
          : 'Action de sécurité enregistrée.',
      deactivatedMatches: data['deactivated_matches'] is int
          ? data['deactivated_matches'] as int
          : 0,
    );
  }
}

class MessageReactionSummary {
  const MessageReactionSummary(this.emoji, this.count);

  final String emoji;
  final int count;

  factory MessageReactionSummary.fromJson(Map<String, dynamic> data) {
    final emoji = data['emoji'];
    final count = data['count'];
    if (emoji is! String || emoji.isEmpty || count is! int || count < 1) {
      throw const FormatException('Réaction incorrecte.');
    }
    return MessageReactionSummary(emoji, count);
  }
}

class ChatReplyPreview {
  const ChatReplyPreview({
    required this.id,
    required this.body,
    required this.hasImage,
    required this.senderName,
    this.deleted = false,
  });

  final String id;
  final String body;
  final bool hasImage;
  final String senderName;
  final bool deleted;

  factory ChatReplyPreview.fromJson(Map<String, dynamic> data) {
    if (data['id'] is! String || data['sender_name'] is! String) {
      throw const FormatException('Message cité incorrect.');
    }
    return ChatReplyPreview(
      id: data['id'] as String,
      body: data['body'] is String ? data['body'] as String : '',
      hasImage: data['has_image'] == true,
      senderName: data['sender_name'] as String,
      deleted: data['is_deleted'] == true,
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
    this.imageUrl,
    this.imageBytes,
    this.reactions = const <MessageReactionSummary>[],
    this.myReaction,
    this.replyPreview,
    this.deleted = false,
    this.edited = false,
  });

  final String id;
  final String body;
  final DateTime createdAt;
  final bool mine;
  final bool read;
  final bool readReceiptsAvailable;
  final String? imageUrl;
  final Uint8List? imageBytes;
  final List<MessageReactionSummary> reactions;
  final String? myReaction;
  final ChatReplyPreview? replyPreview;
  final bool deleted;
  final bool edited;

  factory ChatMessage.fromJson(Map<String, dynamic> data) {
    final id = data['id'];
    final body = data['body'];
    final createdAt = DateTime.tryParse(data['created_at']?.toString() ?? '');
    final imageUrl = data['image_url'];
    final rawReactions = data['reactions'];
    final rawReply = data['reply_preview'];
    if (id is! String ||
        id.isEmpty ||
        body is! String ||
        (data['is_deleted'] != true &&
            body.trim().isEmpty &&
            (imageUrl is! String || imageUrl.isEmpty)) ||
        createdAt == null) {
      throw const FormatException('Message incomplet.');
    }
    return ChatMessage(
      id: id,
      body: body,
      createdAt: createdAt,
      mine: data['is_mine'] == true,
      read: data['is_read'] == true,
      readReceiptsAvailable: data['read_receipts_available'] == true,
      imageUrl: imageUrl is String && imageUrl.isNotEmpty ? imageUrl : null,
      reactions: rawReactions is List
          ? rawReactions
              .whereType<Map<String, dynamic>>()
              .map(MessageReactionSummary.fromJson)
              .toList(growable: false)
          : const <MessageReactionSummary>[],
      myReaction: data['my_reaction'] is String
          ? data['my_reaction'] as String
          : null,
      replyPreview: rawReply is Map<String, dynamic>
          ? ChatReplyPreview.fromJson(rawReply)
          : null,
      deleted: data['is_deleted'] == true,
      edited: data['is_edited'] == true,
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

class PremiumPlan {
  const PremiumPlan({required this.code, required this.name, required this.description, required this.features, required this.priceLabel, required this.amountXaf, required this.paymentAvailable});
  final String code;
  final String name;
  final String description;
  final List<String> features;
  final String priceLabel;
  final int amountXaf;
  final bool paymentAvailable;

  factory PremiumPlan.fromJson(Map<String, dynamic> data) => PremiumPlan(
    code: data['code']?.toString() ?? '',
    name: data['name']?.toString() ?? '',
    description: data['description']?.toString() ?? '',
    features: data['features'] is List ? (data['features'] as List).whereType<String>().toList(growable: false) : const <String>[],
    priceLabel: data['price_label']?.toString() ?? '',
    amountXaf: data['amount_xaf'] is int ? data['amount_xaf'] as int : 0,
    paymentAvailable: data['payment_available'] == true,
  );
}

class PremiumSubscription {
  const PremiumSubscription({required this.plan, required this.planName, required this.status, required this.isPremium, this.endsAt});
  final String plan;
  final String planName;
  final String status;
  final bool isPremium;
  final DateTime? endsAt;

  factory PremiumSubscription.fromJson(Map<String, dynamic> data) => PremiumSubscription(
    plan: data['plan']?.toString() ?? 'free',
    planName: data['plan_name']?.toString() ?? 'Gratuit',
    status: data['status']?.toString() ?? 'inactive',
    isPremium: data['is_premium'] == true,
    endsAt: DateTime.tryParse(data['ends_at']?.toString() ?? ''),
  );
}

class PremiumPaymentMethod {
  const PremiumPaymentMethod({required this.code, required this.name, required this.description, required this.available});
  final String code;
  final String name;
  final String description;
  final bool available;
  factory PremiumPaymentMethod.fromJson(Map<String, dynamic> data) => PremiumPaymentMethod(
    code: data['code']?.toString() ?? '', name: data['name']?.toString() ?? '',
    description: data['description']?.toString() ?? '', available: data['available'] == true,
  );
}

class PremiumOverview {
  const PremiumOverview({required this.subscription, required this.plans, required this.paymentMethods, required this.paymentNotice, required this.privacy, required this.boost});
  final PremiumSubscription subscription;
  final List<PremiumPlan> plans;
  final List<PremiumPaymentMethod> paymentMethods;
  final String paymentNotice;
  final PremiumPrivacy privacy;
  final PremiumBoost boost;
  factory PremiumOverview.fromJson(Map<String, dynamic> data) {
    if (data['subscription'] is! Map<String, dynamic> || data['plans'] is! List || data['payment_methods'] is! List || data['privacy'] is! Map<String, dynamic> || data['boost'] is! Map<String, dynamic>) {
      throw const FormatException('Offres Premium incorrectes.');
    }
    return PremiumOverview(
      subscription: PremiumSubscription.fromJson(data['subscription'] as Map<String, dynamic>),
      plans: (data['plans'] as List).whereType<Map<String, dynamic>>().map(PremiumPlan.fromJson).toList(growable: false),
      paymentMethods: (data['payment_methods'] as List).whereType<Map<String, dynamic>>().map(PremiumPaymentMethod.fromJson).toList(growable: false),
      paymentNotice: data['payment_notice']?.toString() ?? '',
      privacy: PremiumPrivacy.fromJson(data['privacy'] as Map<String, dynamic>),
      boost: PremiumBoost.fromJson(data['boost'] as Map<String, dynamic>),
    );
  }
}

class PremiumPrivacy {
  const PremiumPrivacy({required this.enabled, required this.available, required this.effective});
  final bool enabled;
  final bool available;
  final bool effective;
  factory PremiumPrivacy.fromJson(Map<String, dynamic> data) => PremiumPrivacy(enabled: data['incognito_enabled'] == true, available: data['incognito_available'] == true, effective: data['effective_incognito'] == true);
}

class PremiumBoost {
  const PremiumBoost({required this.entitled, required this.active, required this.durationMinutes, required this.remaining, this.activeUntil, this.nextAvailableAt});
  final bool entitled;
  final bool active;
  final int durationMinutes;
  final int remaining;
  final DateTime? activeUntil;
  final DateTime? nextAvailableAt;
  factory PremiumBoost.fromJson(Map<String, dynamic> data) => PremiumBoost(
    entitled: data['entitled'] == true, active: data['active'] == true,
    durationMinutes: data['duration_minutes'] is int ? data['duration_minutes'] as int : 0,
    remaining: data['remaining'] is int ? data['remaining'] as int : 0,
    activeUntil: DateTime.tryParse(data['active_until']?.toString() ?? ''),
    nextAvailableAt: DateTime.tryParse(data['next_available_at']?.toString() ?? ''),
  );
}

class PremiumPayment {
  const PremiumPayment({required this.id, required this.planName, required this.methodName, required this.status, required this.amountXaf, required this.currency, required this.canConfirmInTestMode, this.customerPhoneMasked = ''});
  final String id;
  final String planName;
  final String methodName;
  final String status;
  final int amountXaf;
  final String currency;
  final bool canConfirmInTestMode;
  final String customerPhoneMasked;
  factory PremiumPayment.fromJson(Map<String, dynamic> data) {
    final id = data['id'];
    if (id is! String || id.isEmpty) throw const FormatException('Transaction incorrecte.');
    return PremiumPayment(id: id, planName: data['plan_name']?.toString() ?? '', methodName: data['method_name']?.toString() ?? '', status: data['status']?.toString() ?? '', amountXaf: data['amount_xaf'] is int ? data['amount_xaf'] as int : 0, currency: data['currency']?.toString() ?? 'XAF', canConfirmInTestMode: data['can_confirm_in_test_mode'] == true, customerPhoneMasked: data['customer_phone_masked']?.toString() ?? '');
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
  Future<void> confirmPasswordReset({
    required String uid,
    required String token,
    required String password,
    required String passwordConfirmation,
  });
  Future<LoginResult> login(String email, String password);
  Future<Account> confirm(String challenge, String code);
  Future<Account> me();
  Future<Account?> restoreSession();
  Future<List<ConnectedSession>> getConnectedSessions();
  Future<void> revokeConnectedSession({
    required String sessionId,
    required String currentPassword,
  });
  Future<int> revokeOtherSessions(String currentPassword);
  Future<bool> setEmailTwoFactor({
    required bool enabled,
    required String currentPassword,
  });
  Future<int> changePassword({
    required String currentPassword,
    required String newPassword,
    required String newPasswordConfirmation,
  });
  Future<Map<String, dynamic>> exportPersonalData();
  Future<void> deactivateAccount(String currentPassword);
  Future<void> deleteAccount(String currentPassword);
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
    bool superLike = false,
  });
  Future<SuperLikeState> getSuperLikeState();
  Future<RewindState> getRewindState();
  Future<DiscoveryProfile> rewindLastPass();
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
  Future<SafetyActionResult> blockProfile(String profileId);
  Future<SafetyActionResult> reportProfile({
    required String profileId,
    required String reason,
    required String description,
  });
  Future<void> unmatch(String matchId);
  Future<List<MatchSummary>> getMatches();
  Future<List<ReceivedLike>> getReceivedLikes();
  Future<ReceivedLikeResult> respondToReceivedLike({
    required String interactionId,
    required String decision,
  });
  Future<List<ConversationSummary>> getConversations();
  Future<int> getMessageUnreadCount();
  Future<List<ChatMessage>> getMessages(String conversationId);
  Future<ChatMessage> sendMessage(
    String conversationId,
    String body, {
    Uint8List? imageBytes,
    String? imageFilename,
    String? replyToId,
  });
  Future<ChatMessage> reactToMessage(
    String conversationId,
    String messageId,
    String emoji,
  );
  Future<ChatMessage> deleteMessage(String conversationId, String messageId);
  Future<ChatMessage> editMessage(
    String conversationId,
    String messageId,
    String body,
  );
  Future<SafetyActionResult> reportMessage({
    required String conversationId,
    required String messageId,
    required String reason,
    required String description,
  });
  Future<void> markConversationRead(String conversationId);
  Future<bool> getTypingStatus(String conversationId);
  Future<void> setTypingStatus(String conversationId, bool isTyping);
  Future<List<AppNotification>> getNotifications();
  Future<int> getNotificationUnreadCount();
  Future<AppNotification> markNotificationRead(String notificationId);
  Future<void> markAllNotificationsRead();
  Future<void> deleteNotification(String notificationId);
  Future<PremiumOverview> getPremiumOverview();
  Future<PremiumPayment> createPremiumCheckout({required String plan, required String method, required String phoneNumber});
  Future<List<PremiumPayment>> getPremiumPaymentHistory();
  Future<PremiumPrivacy> updatePremiumPrivacy(bool enabled);
  Future<PremiumBoost> activatePremiumBoost();
  Future<PremiumPayment> confirmPremiumPaymentTest(String transactionId);
  Future<PremiumPayment> cancelPremiumPayment(String transactionId);
  Future<void> logout();
  void close();
}
