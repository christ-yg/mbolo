import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mbolo_mobile/api.dart';
import 'package:mbolo_mobile/demo_api.dart';
import 'package:mbolo_mobile/main.dart';

void main() {
  testWidgets('Missing configuration does not open a login form', (
    tester,
  ) async {
    await tester.pumpWidget(const MboloApp());
    expect(
      find.textContaining('Configuration MBOLO manquante'),
      findsOneWidget,
    );
    expect(find.byType(TextFormField), findsNothing);
  });
  testWidgets('Demo remains usable on a compact Android viewport', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(360, 640);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(MboloApp(api: DemoApi(), demo: true));
    expect(tester.takeException(), isNull);

    await tester.enterText(
      find.byType(TextFormField).at(0),
      'demo@mbolo.test',
    );
    await tester.enterText(
      find.byType(TextFormField).at(1),
      'MboloDemo!',
    );
    await tester.tap(find.text('Se connecter'));
    await tester.pump();
    await tester.enterText(find.byType(TextFormField), '123456');
    await tester.tap(find.text('Confirmer'));
    await tester.pumpAndSettle();

    expect(find.byType(NavigationBar), findsOneWidget);
    expect(find.text('Découvrir'), findsWidgets);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Empty credentials are rejected locally', (tester) async {
    final api = MboloApi('https://example.com');
    await tester.pumpWidget(MboloApp(api: api));
    await tester.tap(find.text('Se connecter'));
    await tester.pump();
    expect(find.text('Entre ton adresse e-mail.'), findsOneWidget);
    expect(find.text('Entre ton mot de passe.'), findsOneWidget);
  });

  testWidgets('Demo authentication opens discovery navigation', (tester) async {
    await tester.pumpWidget(MboloApp(api: DemoApi(), demo: true));
    await tester.enterText(
      find.byType(TextFormField).at(0),
      'demo@mbolo.test',
    );
    await tester.enterText(
      find.byType(TextFormField).at(1),
      'MboloDemo!',
    );
    await tester.tap(find.text('Se connecter'));
    await tester.pump();
    await tester.enterText(
      find.byType(TextFormField),
      '123456',
    );
    await tester.tap(find.text('Confirmer'));
    await tester.pumpAndSettle();

    expect(find.text('Découvrir'), findsWidgets);
    expect(find.textContaining('Arielle'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Ça me plaît'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Ça me plaît'), findsOneWidget);
    expect(find.text('Profil'), findsOneWidget);
  });

  testWidgets('Messaging opens and logout returns to login', (
    tester,
  ) async {
    await tester.pumpWidget(MboloApp(api: DemoApi(), demo: true));
    await tester.enterText(find.byType(TextFormField).at(0), 'demo@mbolo.test');
    await tester.enterText(find.byType(TextFormField).at(1), 'MboloDemo!');
    await tester.tap(find.text('Se connecter'));
    await tester.pump();
    await tester.enterText(find.byType(TextFormField), '123456');
    await tester.tap(find.text('Confirmer'));
    await tester.pumpAndSettle();

    await tester.scrollUntilVisible(
      find.text('Ça me plaît'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text('Ça me plaît'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Messages'));
    await tester.pumpAndSettle();
    expect(find.text('Messages'), findsWidgets);
    expect(find.text('Grâce'), findsOneWidget);
    expect(find.textContaining('Heureuse de faire ta connaissance'), findsOneWidget);

    await tester.tap(find.text('Profil'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Se déconnecter'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Se déconnecter'));
    await tester.pumpAndSettle();
    expect(find.text('Se connecter'), findsOneWidget);
  });

  testWidgets('Registration validates consent and returns to login', (
    tester,
  ) async {
    await tester.pumpWidget(MboloApp(api: DemoApi(), demo: true));
    await tester.tap(find.text('Créer un compte'));
    await tester.pumpAndSettle();

    expect(find.text('Crée ton compte MBOLO'), findsOneWidget);
    await tester.enterText(
      find.byType(TextFormField).at(0),
      'nouveau@mbolo.test',
    );
    await tester.enterText(
      find.byType(TextFormField).at(1),
      'MotDePasse!2026',
    );
    await tester.enterText(
      find.byType(TextFormField).at(2),
      'MotDePasse!2026',
    );
    final adultConsent = find.text('Je confirme avoir au moins 18 ans.');
    await tester.ensureVisible(adultConsent);
    await tester.pumpAndSettle();
    await tester.tap(adultConsent);

    final termsConsent = find.text('J’accepte les conditions d’utilisation.');
    await tester.ensureVisible(termsConsent);
    await tester.pumpAndSettle();
    await tester.tap(termsConsent);

    final registerButton = find.text('Créer mon compte');
    await tester.ensureVisible(registerButton);
    await tester.pumpAndSettle();
    await tester.tap(registerButton);
    await tester.pumpAndSettle();

    expect(find.text('Se connecter'), findsOneWidget);
    expect(find.textContaining('Compte créé'), findsOneWidget);
  });

  testWidgets('Password reset keeps account existence private', (tester) async {
    await tester.pumpWidget(MboloApp(api: DemoApi(), demo: true));
    await tester.tap(find.text('Mot de passe oublié ?'));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byType(TextFormField),
      'demo@mbolo.test',
    );
    await tester.tap(find.text('Envoyer les instructions'));
    await tester.pumpAndSettle();

    expect(find.text('Se connecter'), findsOneWidget);
    expect(find.textContaining('Si cette adresse existe'), findsOneWidget);
  });


  testWidgets('Profile, photos and preference screens open', (tester) async {
    await tester.pumpWidget(MboloApp(api: DemoApi(), demo: true));
    await tester.enterText(find.byType(TextFormField).at(0), 'demo@mbolo.test');
    await tester.enterText(find.byType(TextFormField).at(1), 'MboloDemo!');
    await tester.tap(find.text('Se connecter'));
    await tester.pump();
    await tester.enterText(find.byType(TextFormField), '123456');
    await tester.tap(find.text('Confirmer'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Profil'));
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(
      find.text('Compléter mon profil'),
      250,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text('Compléter mon profil'));
    await tester.pumpAndSettle();
    expect(find.text('Présente-toi avec authenticité'), findsOneWidget);

    await tester.pageBack();
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(
      find.text('Mes photos'),
      250,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text('Mes photos'));
    await tester.pumpAndSettle();
    expect(find.text('Ta galerie MBOLO'), findsOneWidget);
    expect(find.text('Ajouter'), findsOneWidget);

    await tester.pageBack();
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(
      find.text('Préférences de rencontre'),
      250,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text('Préférences de rencontre'));
    await tester.pumpAndSettle();
    expect(find.text('Choisis qui tu souhaites découvrir'), findsOneWidget);
    expect(find.textContaining('Tranche d’âge'), findsOneWidget);
    expect(find.text('Femmes'), findsOneWidget);
    expect(find.text('Filtres avancés'), findsOneWidget);
    expect(find.text('Enregistrer mes préférences'), findsOneWidget);
  });

}
