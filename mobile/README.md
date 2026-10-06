# MBOLO Mobile — fondation et expérience de découverte

Application Flutter native Android d'abord. Source backend vérifiée : `main`
`6e9573a8954fdda4b48a518d4428cb5c98190755`. Branche indépendante de la stabilisation web.

## Premier incrément

Écran français de connexion, confirmation e-mail 2FA, compte connecté et déconnexion.
Le client appelle réellement `/api/v1/csrf/`, `auth/login/`,
`auth/login/2fa/confirm/`, `auth/me/`, `auth/logout/`.
Le backend utilise des sessions Django, pas JWT. Aucune modification backend nécessaire.
L'identifiant de session est conservé dans Keychain/Keystore et restauré au redémarrage.
Aucun mot de passe, jeton CSRF ou challenge 2FA n'est persisté ni journalisé.
HTTPS obligatoire, redirections désactivées et délais réseau bornés.

## Exécuter après installation de Flutter

Version de référence pour ce premier incrément : Flutter 3.35.7.
Depuis `mobile/` :

```sh
flutter pub get
dart format lib test
flutter analyze
flutter test
bash tool/prepare_android.sh
```

```sh
flutter run --dart-define=MBOLO_API_ORIGIN=https://VOTRE-HOTE-DE-TEST
```

Utiliser une instance de test HTTPS joignable depuis le téléphone, avec certificat
valide et ALLOWED_HOSTS configuré. L'origine doit être sans chemin `/api`.
Ne pas désactiver la vérification TLS. Le serveur et le site gardent leur configuration CSRF.
Le script prépare le projet Android, ajoute la permission Internet, nomme l'application
MBOLO et interdit le trafic HTTP non chiffré. La CI produit un APK de démonstration
signé pour test par Android, mais aucune clé de production ni publication boutique
n'est encore configurée.
Ne pas utiliser Flutter Web avec ce client natif.

## Plan du lot de 100

Les numéros sont des unités de travail planifiées, pas des fonctionnalités déclarées finies.

| Unités | Objectif | État |
| --- | --- | --- |
| 001–010 | Audit API, structure Flutter, configuration et thème | Commencé |
| 011–020 | Client HTTP, cookies, CSRF, erreurs et tests | Code écrit, validation à exécuter |
| 021–030 | Connexion, 2FA, session et déconnexion | Code écrit, validation à exécuter |
| 031–040 | Inscription, majorité, CGU et vérification e-mail | Inscription et consentements réalisés |
| 041–050 | Récupération du mot de passe et sécurité session | Réinitialisation complète et session chiffrée |
| 051–060 | Onboarding et lecture/édition du profil | Profil complet et préférences synchronisés |
| 061–070 | Photos, validation et permissions minimales | Galerie et sélection de photos réalisées |
| 071–080 | Navigation et gestion des états réseau | Navigation d’aperçu écrite |
| 081–090 | Persistance sécurisée, accessibilité et tests téléphone | Persistance et tests automatisés réalisés ; téléphone à valider |
| 091–100 | Projet Android, compilation, CI et bilan du lot | Génération Android et APK démo automatisées |

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
L’aperçu montre connexion, 2FA, navigation, profils suggérés, likes locaux,
centre de sécurité, profil et déconnexion. Les profils sont fictifs et aucune
action de démonstration n’est envoyée au serveur.
Ne pas saisir ses véritables identifiants dans cet aperçu.

## Démonstration sur un téléphone, sans installation

Le PC et le téléphone doivent utiliser le même Wi-Fi. Dans Ubuntu/WSL :

```sh
cd ~/projects/mbolo
git fetch origin
git switch agent/mobile-1-100
git pull --ff-only
cd mobile
~/develop/flutter/bin/flutter pub get
~/develop/flutter/bin/flutter run -d web-server \
  --web-hostname=0.0.0.0 \
  --web-port=8083 \
  -t lib/main_preview.dart
```

Dans Windows, exécuter `ipconfig` et relever l'adresse IPv4 de la carte Wi-Fi,
par exemple `192.168.1.25`. Sur le téléphone, ouvrir :

```text
http://ADRESSE_IPV4_DU_PC:8083
```

Utiliser `demo@mbolo.test`, `MboloDemo!`, puis `123456`.
Cette démonstration est locale et fictive. Elle ne nécessite pas Django.
Si Windows demande l'autorisation réseau pour Flutter, autoriser uniquement le
réseau privé. Ne jamais ouvrir ce port sur un Wi-Fi public.

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
Le workflow GitHub lance analyse, tests, compilation Web et génération de l'APK démo.
Le premier refus de publication a été suivi de l'accord explicite de l'utilisateur.
