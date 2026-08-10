# Lot 18 — Inventaire SBOM des images de production

## Objectif

Ce lot ajoute une nomenclature logicielle, ou SBOM (*Software Bill of
Materials*), pour les images Docker backend et frontend de Mbolo.

Le SBOM inventorie les paquets du système d'exploitation et les bibliothèques
applicatives réellement présentes dans chaque image finale. Il facilite les
audits, la recherche d'un composant vulnérable et la gestion des fournisseurs
dans une démarche ISO/IEC 27001.

## Fonctionnement gratuit

Le workflow de sécurité existant :

1. construit les deux images de production ;
2. génère un SBOM CycloneDX JSON pour chaque image avec Syft ;
3. rassemble les deux fichiers dans un artefact GitHub Actions ;
4. conserve cet artefact pendant 7 jours ;
5. exécute ensuite les analyses Trivy existantes.

Aucun serveur, registre privé, compte externe ou secret de production n'est
requis. Les images et les SBOM restent dans l'exécution GitHub Actions.

## Fichiers du lot

- `.github/workflows/container-security.yml` : workflow complet enrichi ;
- `scripts/sbom-local-check.sh` : génération et validation locales ;
- `INSTALLATION_SBOM.md` : présente procédure.

## Installation

```bash
cd ~/projects/mbolo
unzip -o /mnt/c/Users/User/Downloads/mbolo-sbom-batch-18.zip
chmod +x scripts/sbom-local-check.sh
```

## Contrôle local complet

Le contrôle construit les deux images et peut prendre plusieurs minutes lors
du premier lancement :

```bash
bash scripts/sbom-local-check.sh
```

Résultat attendu :

```text
Deux SBOM JSON valides : OK
✅ SBOM_CHECK=OK
```

Les fichiers générés sont placés dans `tmp/sbom/`. Le dossier `tmp/` est déjà
exclu du contexte Docker et ne doit pas être ajouté à Git.

## Contrôle Git avant le commit

```bash
git diff --check
git status -sb
git diff --stat
git ls-files --others --exclude-standard
```

## Résultat attendu sur GitHub

La pull request doit exécuter `Mbolo Container Security`. Le job doit rester
vert et afficher une étape `Publier les SBOM du contrôle`. Dans les artefacts
de l'exécution, un fichier nommé `mbolo-production-sbom-<commit>` doit contenir
les deux documents :

- `mbolo-backend.cdx.json` ;
- `mbolo-frontend.cdx.json`.

## Limites et sécurité

Un SBOM ne contient pas les secrets de production, car ceux-ci ne sont ni
copiés dans les images ni fournis au workflow. Il décrit les composants, mais
ne remplace pas l'analyse Trivy : les deux contrôles sont complémentaires.
