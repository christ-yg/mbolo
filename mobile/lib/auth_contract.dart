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
  Future<void> logout();
  void close();
}
