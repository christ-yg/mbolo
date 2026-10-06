import 'dart:typed_data';

import 'auth_contract.dart';

/// Local-only demonstration: no HTTP client and no persistent storage.
class DemoApi implements AuthApi {
  static const account = Account('demo', 'demo@mbolo.test', true);
  bool _authenticated = false;
  MemberProfile _profile = const MemberProfile(
    displayName: '',
    birthDate: '',
    gender: '',
    city: '',
    biography: '',
    datingIntent: '',
    interests: <String>[],
    complete: false,
  );
  static const _discoveryProfiles = <DiscoveryProfile>[
    DiscoveryProfile(
      id: '11111111-1111-1111-1111-111111111111',
      displayName: 'Arielle',
      age: 27,
      city: 'Libreville',
      biography: 'Passionnée de lecture, de cuisine et de voyages.',
      datingIntent: 'Relation sérieuse',
      verified: true,
      photos: <ProfilePhoto>[],
      interestLabels: <String>['Lecture', 'Cuisine', 'Voyages'],
      commonInterestLabels: <String>['Voyages'],
      compatibilityScore: 78,
      distanceLabel: 'À moins de 10 km',
    ),
    DiscoveryProfile(
      id: '22222222-2222-2222-2222-222222222222',
      displayName: 'Grâce',
      age: 29,
      city: 'Akanda',
      biography: 'Sport, musique et entrepreneuriat au quotidien.',
      datingIntent: 'Amitié',
      verified: true,
      photos: <ProfilePhoto>[],
      interestLabels: <String>['Fitness', 'Musique', 'Entrepreneuriat'],
      commonInterestLabels: <String>['Fitness', 'Musique'],
      compatibilityScore: 84,
      distanceLabel: 'À moins de 20 km',
    ),
    DiscoveryProfile(
      id: '33333333-3333-3333-3333-333333333333',
      displayName: 'Mélissa',
      age: 26,
      city: 'Port-Gentil',
      biography: 'Cinéma, nature et belles découvertes.',
      datingIntent: 'Discussion',
      verified: false,
      photos: <ProfilePhoto>[],
      interestLabels: <String>['Cinéma', 'Nature', 'Art'],
      commonInterestLabels: <String>[],
      compatibilityScore: 61,
      distanceLabel: '',
    ),
  ];

  final List<ChatMessage> _messages = <ChatMessage>[
    ChatMessage(
      id: 'demo-message-1',
      body: 'Bonsoir ! Heureuse de faire ta connaissance 😊',
      createdAt: DateTime(2026, 10, 5, 18, 30),
      mine: false,
      read: false,
      readReceiptsAvailable: false,
    ),
  ];

  final List<ProfilePhoto> _photos = <ProfilePhoto>[];
  final Set<String> _blockedProfiles = <String>{};
  bool _demoMatchActive = true;

  DiscoveryPreferences _preferences = const DiscoveryPreferences(
    minimumAge: 18,
    maximumAge: 45,
    preferredGenders: <String>[],
    advancedFiltersAvailable: false,
  );

  @override
  Future<Account> register({
    required String email,
    required String password,
    required String passwordConfirmation,
    required bool acceptTerms,
    required bool confirmAdult,
  }) async {
    if (!email.trim().contains('@') ||
        password.length < 12 ||
        password != passwordConfirmation ||
        !acceptTerms ||
        !confirmAdult) {
      throw const FormatException('Inscription de démonstration incorrecte.');
    }
    return Account('demo-new', email.trim(), false);
  }

  @override
  Future<void> requestPasswordReset(String email) async {
    if (!email.trim().contains('@')) {
      throw const FormatException('Adresse e-mail incorrecte.');
    }
  }

  @override
  Future<LoginResult> login(String email, String password) async {
    if (email.trim() != account.email || password != 'MboloDemo!') {
      throw const FormatException('Identifiants de démonstration incorrects.');
    }
    return const LoginResult(
      challenge: 'demo-challenge',
      maskedEmail: 'demo@mbolo.test',
    );
  }

  @override
  Future<Account> confirm(String challenge, String code) async {
    if (challenge != 'demo-challenge' || code.trim() != '123456') {
      throw const FormatException('Code de démonstration incorrect.');
    }
    _authenticated = true;
    return account;
  }

  @override
  Future<Account> me() async {
    if (!_authenticated) throw const FormatException('Session absente.');
    return account;
  }


  @override
  Future<MemberProfile> getProfile() async => _profile;

  @override
  Future<MemberProfile> updateProfile({
    required String displayName,
    required String birthDate,
    required String gender,
    required String city,
    required String biography,
    required String datingIntent,
    required List<String> interests,
  }) async {
    _profile = MemberProfile(
      displayName: displayName.trim(),
      birthDate: birthDate,
      gender: gender,
      city: city,
      biography: biography.trim(),
      datingIntent: datingIntent,
      interests: List<String>.unmodifiable(interests),
      complete: displayName.trim().length >= 2 &&
          birthDate.isNotEmpty &&
          gender.isNotEmpty &&
          city.isNotEmpty &&
          datingIntent.isNotEmpty,
    );
    return _profile;
  }

  @override
  Future<List<DiscoveryProfile>> getDiscovery() async {
    return _discoveryProfiles;
  }

  @override
  Future<InteractionResult> decideProfile({
    required String profileId,
    required String decision,
  }) async {
    if (!_discoveryProfiles.any((profile) => profile.id == profileId) ||
        (decision != 'like' && decision != 'pass')) {
      throw const FormatException('Interaction de démonstration incorrecte.');
    }
    return InteractionResult(
      decision: decision,
      matched: decision == 'like' &&
          profileId == '22222222-2222-2222-2222-222222222222',
      matchCreated: decision == 'like' &&
          profileId == '22222222-2222-2222-2222-222222222222',
      matchId: decision == 'like' &&
              profileId == '22222222-2222-2222-2222-222222222222'
          ? 'demo-match-1'
          : null,
    );
  }

  @override
  Future<List<ProfilePhoto>> getPhotos() async {
    return List<ProfilePhoto>.unmodifiable(_photos);
  }

  @override
  Future<ProfilePhoto> uploadPhoto({
    required Uint8List bytes,
    required String filename,
    required int position,
    required bool primary,
  }) async {
    if (_photos.length >= 6 || bytes.isEmpty) {
      throw const FormatException('Photo de démonstration incorrecte.');
    }
    final shouldBePrimary = primary || _photos.isEmpty;
    if (shouldBePrimary) {
      for (var index = 0; index < _photos.length; index += 1) {
        final photo = _photos[index];
        _photos[index] = ProfilePhoto(
          id: photo.id,
          imageUrl: photo.imageUrl,
          position: photo.position,
          primary: false,
          moderationStatus: photo.moderationStatus,
          moderationStatusLabel: photo.moderationStatusLabel,
          previewBytes: photo.previewBytes,
        );
      }
    }
    final photo = ProfilePhoto(
      id: 'demo-photo-${_photos.length + 1}',
      imageUrl: '',
      position: position,
      primary: shouldBePrimary,
      moderationStatus: 'pending',
      moderationStatusLabel: 'En attente',
      previewBytes: bytes,
    );
    _photos.add(photo);
    _photos.sort((first, second) => first.position.compareTo(second.position));
    return photo;
  }

  @override
  Future<ProfilePhoto> updatePhoto({
    required String id,
    int? position,
    bool? primary,
  }) async {
    final currentIndex = _photos.indexWhere((photo) => photo.id == id);
    if (currentIndex < 0) throw const FormatException('Photo absente.');
    if (primary == true) {
      for (var index = 0; index < _photos.length; index += 1) {
        final photo = _photos[index];
        _photos[index] = ProfilePhoto(
          id: photo.id,
          imageUrl: photo.imageUrl,
          position: photo.position,
          primary: false,
          moderationStatus: photo.moderationStatus,
          moderationStatusLabel: photo.moderationStatusLabel,
          previewBytes: photo.previewBytes,
        );
      }
    }
    final current = _photos[currentIndex];
    final updated = ProfilePhoto(
      id: current.id,
      imageUrl: current.imageUrl,
      position: position ?? current.position,
      primary: primary ?? current.primary,
      moderationStatus: current.moderationStatus,
      moderationStatusLabel: current.moderationStatusLabel,
      previewBytes: current.previewBytes,
    );
    _photos[currentIndex] = updated;
    _photos.sort((first, second) => first.position.compareTo(second.position));
    return updated;
  }

  @override
  Future<void> deletePhoto(String id) async {
    _photos.removeWhere((photo) => photo.id == id);
  }

  @override
  Future<DiscoveryPreferences> getPreferences() async => _preferences;

  @override
  Future<DiscoveryPreferences> updatePreferences({
    required int minimumAge,
    required int maximumAge,
    required List<String> preferredGenders,
  }) async {
    _preferences = DiscoveryPreferences(
      minimumAge: minimumAge,
      maximumAge: maximumAge,
      preferredGenders: List<String>.unmodifiable(preferredGenders),
      advancedFiltersAvailable: false,
    );
    return _preferences;
  }

  @override
  Future<SafetyActionResult> blockProfile(String profileId) async {
    if (!_discoveryProfiles.any((profile) => profile.id == profileId)) {
      throw const FormatException('Profil absent.');
    }
    final created = _blockedProfiles.add(profileId);
    if (profileId == _discoveryProfiles[1].id) _demoMatchActive = false;
    return SafetyActionResult(
      created: created,
      message: created ? 'Ce profil a été bloqué.' : 'Ce profil est déjà bloqué.',
      deactivatedMatches: profileId == _discoveryProfiles[1].id ? 1 : 0,
    );
  }

  @override
  Future<SafetyActionResult> reportProfile({
    required String profileId,
    required String reason,
    required String description,
  }) async {
    if (!_discoveryProfiles.any((profile) => profile.id == profileId) ||
        reason.isEmpty ||
        (reason == 'other' && description.trim().isEmpty)) {
      throw const FormatException('Signalement incorrect.');
    }
    return const SafetyActionResult(
      created: true,
      message: 'Le signalement a été transmis à la modération.',
    );
  }

  @override
  Future<void> unmatch(String matchId) async {
    if (matchId != 'demo-match-1') {
      throw const FormatException('Match absent.');
    }
    _demoMatchActive = false;
  }

  @override
  Future<List<ConversationSummary>> getConversations() async {
    if (!_demoMatchActive) return <ConversationSummary>[];
    return <ConversationSummary>[
      ConversationSummary(
        id: 'demo-conversation-1',
        matchId: 'demo-match-1',
        otherProfile: _discoveryProfiles[1],
        lastMessage: _messages.isEmpty ? null : _messages.last,
        unreadCount: _messages.where((message) => !message.mine && !message.read).length,
        online: true,
        updatedAt: _messages.isEmpty
            ? DateTime(2026, 10, 5, 18)
            : _messages.last.createdAt,
      ),
    ];
  }

  @override
  Future<List<ChatMessage>> getMessages(String conversationId) async {
    if (conversationId != 'demo-conversation-1') {
      throw const FormatException('Conversation absente.');
    }
    return List<ChatMessage>.unmodifiable(_messages);
  }

  @override
  Future<ChatMessage> sendMessage(String conversationId, String body) async {
    final trimmed = body.trim();
    if (conversationId != 'demo-conversation-1' ||
        trimmed.isEmpty ||
        trimmed.length > 2000) {
      throw const FormatException('Message de démonstration incorrect.');
    }
    final message = ChatMessage(
      id: 'demo-message-${_messages.length + 1}',
      body: trimmed,
      createdAt: DateTime.now(),
      mine: true,
      read: false,
      readReceiptsAvailable: false,
    );
    _messages.add(message);
    return message;
  }

  @override
  Future<void> markConversationRead(String conversationId) async {
    if (conversationId != 'demo-conversation-1') {
      throw const FormatException('Conversation absente.');
    }
    for (var index = 0; index < _messages.length; index += 1) {
      final message = _messages[index];
      if (!message.mine && !message.read) {
        _messages[index] = ChatMessage(
          id: message.id,
          body: message.body,
          createdAt: message.createdAt,
          mine: false,
          read: true,
          readReceiptsAvailable: message.readReceiptsAvailable,
        );
      }
    }
  }

  @override
  Future<void> logout() async {
    _authenticated = false;
  }

  @override
  void close() {
    _authenticated = false;
  }
}
