# MBOLO Mobile — lot 1–100 en cours

Application Flutter native Android d'abord. Source backend vérifiée : `main`
`6e9573a8954fdda4b48a518d4428cb5c98190755`. Branche indépendante de la stabilisation web.

## Premier incrément

Écran français de connexion, confirmation e-mail 2FA, compte connecté et déconnexion.
Le client appelle réellement `/api/v1/csrf/`, `auth/login/`,
`auth/login/2fa/confirm/`, `auth/me/`, `auth/logout/`.
Le backend utilise des sessions Django, pas JWT. Aucune modification backend nécessaire.
Cookies en mémoire uniquement : redémarrer l'application impose une reconnexion.
La persistance Keychain/Keystore reste à réaliser. Aucun secret ni mot de passe journalisé.
HTTPS obligatoire, redirections désactivées et délais réseau bornés.

## Exécuter après installation de Flutter

Version de référence pour ce premier incrément : Flutter 3.35.7.
Depuis `mobile/` :

```sh
flutter pub get
dart format lib test
flutter analyze
flutter test
flutter create --platforms=android --project-name mbolo_mobile .
```

Avant le lancement Android, ajouter la permission INTERNET dans le manifeste
principal `android/app/src/main/AndroidManifest.xml` (sous `manifest`) :

```xml
<uses-permission android:name="android.permission.INTERNET" />
```

```sh
flutter run --dart-define=MBOLO_API_ORIGIN=https://VOTRE-HOTE-DE-TEST
```

Utiliser une instance de test HTTPS joignable depuis le téléphone, avec certificat
valide et ALLOWED_HOSTS configuré. L'origine doit être sans chemin `/api`.
Ne pas désactiver la vérification TLS. Le serveur et le site gardent leur configuration CSRF.
Pas encore de projet Android généré/validé, d'APK signé, ni de publication boutique.
Ne pas utiliser Flutter Web avec ce client natif.

## Plan du lot de 100

Les numéros sont des unités de travail planifiées, pas des fonctionnalités déclarées finies.

| Unités | Objectif | État |
| --- | --- | --- |
| 001–010 | Audit API, structure Flutter, configuration et thème | Commencé |
| 011–020 | Client HTTP, cookies, CSRF, erreurs et tests | Code écrit, validation à exécuter |
| 021–030 | Connexion, 2FA, session et déconnexion | Code écrit, validation à exécuter |
| 031–040 | Inscription, majorité, CGU et vérification e-mail | À réaliser |
| 041–050 | Récupération du mot de passe et sécurité session | À réaliser |
| 051–060 | Onboarding et lecture/édition du profil | À réaliser |
| 061–070 | Photos, validation et permissions minimales | À réaliser |
| 071–080 | Navigation et gestion des états réseau | À réaliser |
| 081–090 | Persistance sécurisée, accessibilité et tests téléphone | À réaliser |
| 091–100 | Projet Android, compilation, CI et bilan du lot | À réaliser |

La découverte, les matchs, la messagerie et les notifications push viendront ensuite.
L'application mobile n'est pas encore prête à être distribuée.

## Aperçu sur le PC Windows

Installer Flutter suivant https://docs.flutter.dev/install et ajouter son dossier
`bin` au PATH Windows. Ouvrir un nouveau PowerShell. Git doit aussi être installé.
Utiliser un clone séparé pour ne pas toucher au travail web dans Ubuntu :

```powershell
cd C:\Users\User
git clone --branch agent/mobile-1-100 https://github.com/christ-yg/mbolo.git mbolo-mobile-preview
cd mbolo-mobile-preview\mobile
flutter pub get
flutter run -d edge -t lib/main_preview.dart --web-hostname 127.0.0.1 --web-port 7357
```

Chrome est aussi possible : remplacer `edge` par `chrome`.
Le navigateur ouvre l'aperçu à http://127.0.0.1:7357.
Identifiants fictifs : `demo@mbolo.test` / `MboloDemo!`, puis code `123456`.
Bannière DÉMO visible. Aucun appel au backend : aucun vrai compte ni e-mail envoyé.
C'est le même composant d'interface que l'application native, avec un service fictif.
Ce premier aperçu montre connexion, 2FA, compte et déconnexion, pas encore le swipe.
Ne pas saisir ses véritables identifiants dans cet aperçu.

Pour récupérer nos prochaines évolutions : arrêter Flutter avec `q`, puis :

```powershell
git pull --ff-only
flutter pub get
flutter run -d edge -t lib/main_preview.dart --web-hostname 127.0.0.1 --web-port 7357
```

## Vérification locale

Formatage Dart, diff, contrôle des secrets et épinglage des actions vérifiés.
Tests Flutter et compilation non exécutés localement : initialisation du SDK bloquée
par le contrôle automatique après détection d'un accès aux métadonnées cloud.
Le workflow GitHub lance analyse, tests et compilation de l'aperçu web.
Le premier refus de publication a été suivi de l'accord explicite de l'utilisateur.
