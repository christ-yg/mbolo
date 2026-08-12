# Épinglage immuable des GitHub Actions

Ce lot protège la chaîne d'intégration continue contre le remplacement d'un tag Git mutable. Chaque action externe est désormais référencée par le SHA complet du commit officiel qui correspondait à sa version au moment de la préparation du lot.

## Fichiers fournis

- `.github/workflows/ci.yml`
- `.github/workflows/container-security.yml`
- `scripts/github-actions-pin-check.sh`
- `INSTALLATION_GITHUB_ACTIONS_PINNING.md`

## Protection appliquée

Les références comme `actions/checkout@v7` sont remplacées par une empreinte Git de 40 caractères. Le commentaire de version reste présent pour la lisibilité et pour les mises à jour automatiques de Dependabot.

Le job `Secrets et artefacts` exécute désormais `scripts/github-actions-pin-check.sh`. Le script inspecte tous les fichiers YAML de `.github/workflows` et refuse :

- un tag ou une branche mutable ;
- une action externe sans version ;
- une révision qui n'est pas un SHA Git complet.

Les actions locales commençant par `./` et les images `docker://` ne sont pas concernées par ce contrôle.

## Vérification locale

Depuis la racine du dépôt :

```bash
chmod +x scripts/github-actions-pin-check.sh
bash scripts/github-actions-pin-check.sh
```

Le résultat attendu se termine par :

```text
GITHUB_ACTIONS_PINNING=OK
```

## Mises à jour

Dependabot est déjà configuré pour l'écosystème `github-actions`. Il peut proposer les nouveaux SHA officiels dans une pull request. Il faut conserver le SHA complet et le commentaire de version, attendre tous les contrôles verts, puis fusionner normalement.

## Limite du contrôle

L'épinglage garantit que GitHub exécute exactement le commit examiné. Il ne remplace ni la revue des changements proposés par Dependabot, ni les permissions minimales des workflows, ni les scans des images de production.
