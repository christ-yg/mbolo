# Super-lot 20 à 29 — portail de sécurité

Ce paquet regroupe dix améliorations dans une seule branche et une seule pull request.

## Les dix lots

1. **Lot 20 — SAST Python** : Bandit 1.9.4 analyse le backend.
2. **Lot 21 — Vulnérabilités du dépôt** : Trivy inspecte les dépendances du système de fichiers.
3. **Lot 22 — Détection de secrets** : Trivy bloque les secrets détectés dans le dépôt.
4. **Lot 23 — Mauvaises configurations** : Trivy analyse les fichiers Docker, Compose et CI.
5. **Lot 24 — Hygiène Git** : aucun secret ou artefact local sensible ne peut être suivi.
6. **Lot 25 — Chaîne CI immuable** : toutes les actions externes restent épinglées sur quarante caractères SHA.
7. **Lot 26 — Qualité des scripts** : tous les scripts Bash suivis passent `bash -n`.
8. **Lot 27 — Exécution et verrouillage** : modes exécutables et manifestes verrouillés sont contrôlés.
9. **Lot 28 — Durcissement des conteneurs** : backend non-root, runtime frontend minimal et protections Compose sont vérifiés.
10. **Lot 29 — Moindre privilège** : les workflows déclarent leurs permissions et les motifs dangereux sont refusés.

## Installation et contrôle local

Depuis la racine du dépôt :

```bash
unzip -o /mnt/c/Users/User/Downloads/mbolo-security-super-gate-batch-20-29.zip
chmod +x scripts/security-super-gate-check.sh
bash scripts/security-super-gate-check.sh
git diff --check
git status -sb
git diff --stat
git ls-files --others --exclude-standard
```

Le contrôle local ne télécharge aucun outil. Bandit et Trivy sont exécutés uniquement par GitHub Actions sur un runner éphémère.

## Fichiers ajoutés

- `.github/workflows/security-super-gate.yml`
- `scripts/security-super-gate-check.sh`
- `INSTALLATION_SECURITY_SUPER_GATE_20_29.md`

## Branche et commit recommandés

- Branche : `agent/security-super-gate-20-29`
- Commit : `ci: add security super gate for lots 20-29`

Une fois les contrôles GitHub verts, la pull request unique peut être fusionnée.
