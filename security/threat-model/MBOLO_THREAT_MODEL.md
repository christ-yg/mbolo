# Lot 31 — Modèle de menace

## Actifs critiques

- comptes, sessions et secrets d’authentification ;
- profils, photos privées et conversations ;
- données PostgreSQL, Redis et sauvegardes ;
- chaîne CI/CD et images de production.

## Menaces prioritaires

Usurpation de compte, contournement d’autorisation, injection, exposition de médias, abus automatisé, fuite de secrets, compromission de dépendance et indisponibilité.

Les mesures existantes incluent MFA, throttling par IP fiable, contrôles d’accès, conteneurs non-root, scans SAST/Trivy, SBOM, sauvegardes et journaux de sécurité.
