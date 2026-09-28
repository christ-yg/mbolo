# Mbolo — super-lot 70–89

Ce lot consolide la résilience opérationnelle sans modifier les données actives.

## Corrections essentielles

- format canonique unique : `postgres.dump`, `media.tar.gz`, `private-media.tar.gz`, `METADATA.txt`, `SHA256SUMS` ;
- anciens scripts transformés en points d’entrée compatibles ;
- vérification de release réparée grâce au sélecteur automatique de la dernière sauvegarde ;
- rétention en simulation par défaut, suppression uniquement avec `--apply` ;
- précontrôle des variables obligatoires et des permissions de `.env.production` ;
- manifeste de release sans valeur secrète ;
- barrière CI statique dédiée.

## Installation

Depuis la racine du dépôt Mbolo, extraire l’archive en conservant les chemins, puis exécuter :

```bash
chmod +x install-super-lot-70-89.sh
bash install-super-lot-70-89.sh
bash scripts/production-env-preflight.sh
git diff --check
git status --short
```

Ne pas lancer une restauration pendant l’installation. La restauration est destructive et conserve sa confirmation humaine dédiée.

## Exploitation

```bash
bash scripts/backup-mbolo.sh
bash scripts/backup-verify.sh
bash scripts/backup-verify.sh backups/mbolo-YYYYMMDDTHHMMSSZ --restore-test
bash scripts/backup-retention.sh --dry-run
bash scripts/release-manifest.sh
```

La commande `bash scripts/backup-retention.sh --apply` supprime réellement les sauvegardes expirées après validation de chacune. Elle ne doit être exécutée qu’après vérification de la copie chiffrée hors machine.

## Correspondance des lots

- 70 : inventaire du dispositif de sauvegarde ;
- 71 : format de sauvegarde canonique ;
- 72 : compatibilité de `backup-local.sh` ;
- 73 : compatibilité de `backup-verify.sh` ;
- 74 : compatibilité de `restore-local.sh` ;
- 75 : contrôle SHA-256 ;
- 76 : validation du catalogue PostgreSQL ;
- 77 : test de restauration isolé ;
- 78 : cohérence base et médias ;
- 79 : chiffrement AES-256 existant conservé ;
- 80 : vérification des archives chiffrées ;
- 81 : rétention en simulation par défaut ;
- 82 : suppression contrôlée des sauvegardes expirées ;
- 83 : permissions restrictives des sauvegardes ;
- 84 : inventaire des variables obligatoires ;
- 85 : détection des valeurs fictives ou faibles ;
- 86 : contrôle des permissions de `.env.production` ;
- 87 : manifeste de release ;
- 88 : barrière opérationnelle CI ;
- 89 : installation atomique et contrôle `git diff --check`.
