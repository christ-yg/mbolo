# Lot 32 — Registre des risques

| Risque | Impact | Probabilité | Traitement | Propriétaire |
|---|---|---|---|---|
| Prise de contrôle de compte | Élevé | Moyenne | MFA, alertes, révocation des sessions | Sécurité |
| Accès indu aux médias privés | Élevé | Faible | Autorisation objet, tests API | Backend |
| Dépendance vulnérable | Élevé | Moyenne | Dependabot, Trivy, SBOM | DevSecOps |
| Perte de données | Critique | Faible | Sauvegarde, chiffrement, restauration testée | Exploitation |
| Indisponibilité | Élevé | Moyenne | Readiness, supervision, PRA | Exploitation |

Révision minimale : mensuelle et avant toute mise en production majeure.
