# Flutter navigateur connecté — fondation

Entrée : lib/main_browser.dart, distincte de main_preview.dart (démonstration).
Cette entrée sélectionne exclusivement l'origine HTTPS de la page. Elle ne prend
pas d'origine API externe par variable et refuse HTTP avec la validation existante.

## Session

MboloApi(browserSession: true) laisse le navigateur gérer les cookies HttpOnly.
Il n'ajoute ni Cookie ni Origin et ne lit pas Set-Cookie. Il n'utilise pas le
stockage natif de session. restoreSession appelle auth/me ; 401/403 donnent une
session absente, les erreurs réseau restent des erreurs. Les mutations gardent
la récupération d'un jeton CSRF. La déconnexion doit réussir côté serveur avant
que l'interface considère la session fermée.
Le mode natif reste le mode par défaut.

## Hébergement nécessaire avant recette connectée

Servir la compilation Flutter et /api/v1/ sur la même origine HTTPS, avec
certificat reconnu. Prévoir également les routes de médias et de liens de compte.
Ne pas utiliser le serveur de preview fictive sur 8092 pour ce mode connecté.
Ne pas ouvrir CORS ni désactiver les cookies Secure/HttpOnly ou la protection CSRF.
Les sessions de deux onglets d'une même origine sont communes : pour comparer
Alex et Sarah, utiliser deux profils de navigateur distincts.

## Validation restant à exécuter

- flutter analyze et flutter test, dont test/browser_session_test.dart ;
- compilation Web de lib/main_browser.dart ;
- recette dans un vrai navigateur avec Django : cookies réellement HttpOnly,
  connexion, 2FA, rafraîchissement, expiration, déconnexion et erreurs réseau ;
- échanges React/Flutter avec deux sessions distinctes et contrôle d'isolation.

Les tests avec adaptateur HTTP simulé ne prouvent pas la politique des cookies
d'un navigateur réel. Aucun succès de recette connectée n'est encore déclaré.
L'environnement de préparation ne dispose pas de Flutter ; seul diff --check
est exécuté ici. Aucun changement de serveur HTTPS n'est inclus dans ce lot.
