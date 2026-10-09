# MBOLO — contrôle de publication mobile

Ce registre doit être vérifié avant chaque livraison Play Store ou App Store.

## Déjà couvert par le produit

- majorité obligatoire à l'inscription et application réservée aux adultes ;
- conditions et confidentialité acceptées et versionnées ;
- signalement, blocage, suppression de match et modération des photos ;
- suppression définitive du compte depuis l'application ;
- export des données personnelles et révocation des sessions ;
- HTTPS obligatoire, stockage de session chiffré et permissions minimales ;
- compte ou mode de démonstration pour la revue ;
- moyens de paiement Web externes masqués dans les builds boutique.
- identité Android et iOS réservée : `ga.mbolo.app` ;
- Android cible l'API 36, obligatoire pour les soumissions Play à partir du 31 août 2026 ;
- version produit et numéro de build centralisés dans `mobile/pubspec.yaml` ;
- génération du bundle Android de contrôle en CI ;
- script iOS reproductible pour macOS/Xcode 26 avec cible minimale iOS 13.

## Bloquants avant soumission

- intégrer Google Play Billing pour les abonnements Android ;
- intégrer Apple In-App Purchase pour les abonnements iOS ;
- générer et valider le projet iOS sur macOS/Xcode ;
- créer les clés de signature Android dans Play App Signing et les certificats/profils Apple ;
- publier une URL de confidentialité, une URL d'assistance et une URL externe de suppression de compte ;
- finaliser les informations Data safety de Google et App Privacy d'Apple ;
- fournir les coordonnées publiques du support et le délai de traitement des signalements ;
- remplir honnêtement les questionnaires d'âge, de contenu et de contenu généré par les utilisateurs ;
- tester le bundle Android signé et l'archive iOS sur appareils réels ;
- fournir au reviewer un compte de test, le code 2FA de revue et des instructions complètes ;
- préparer icône, captures réelles, description, politique de remboursement et gestion des abonnements.

## Règle de livraison

Une release boutique est interdite si un paiement numérique externe est visible,
si la suppression de compte ne fonctionne pas de bout en bout, si les outils de
signalement ou blocage sont indisponibles ou si les URL légales ne sont pas publiques.

Le bundle construit par la CI est un contrôle de compilation et ne doit jamais être
publié. La livraison Play Store doit être signée avec une clé de téléversement gardée
hors du dépôt ; l'archive iOS doit être signée sur macOS par le compte Apple Developer.
