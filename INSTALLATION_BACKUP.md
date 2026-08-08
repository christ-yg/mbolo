# Mbolo — Lot 03 Sauvegarde et restauration

## Objectif

Ce lot protège gratuitement les données irremplaçables de Mbolo :

- la base PostgreSQL ;
- les médias publics ;
- les médias privés ;
- l'intégrité des archives grâce aux empreintes SHA-256.

Le dossier `backups/` est ignoré par Git. Aucun compte, photo ou export de base
de données ne doit être envoyé dans le dépôt GitHub.

## Créer une sauvegarde

```bash
chmod +x scripts/backup-local.sh scripts/backup-verify.sh scripts/restore-local.sh
bash scripts/backup-local.sh
```

Une sauvegarde horodatée est créée dans `backups/mbolo-...`.

## Vérifier une sauvegarde

```bash
bash scripts/backup-verify.sh
```

Cette opération contrôle les empreintes, les archives de médias et le catalogue
PostgreSQL sans modifier la base active. Sans argument, le script vérifie
automatiquement la sauvegarde Mbolo la plus récente.

## Restaurer après un incident

La restauration remplace la base et les médias actifs. Le second argument est
une confirmation volontaire empêchant une exécution accidentelle :

```bash
bash scripts/restore-local.sh \
  backups/mbolo-YYYYMMDDTHHMMSSZ \
  JE_RESTAURE_MBOLO
```

Avant toute restauration, le script crée automatiquement une nouvelle
sauvegarde de sécurité de l'état courant.

## Conservation

Par défaut, les sauvegardes locales âgées de plus de 14 jours sont supprimées.
La durée peut être changée pour une exécution :

```bash
MBOLO_BACKUP_RETENTION_DAYS=30 bash scripts/backup-local.sh
```

## Règle 3-2-1 sans abonnement

Conserver au minimum :

1. les données actives dans Docker ;
2. une copie dans `backups/` ;
3. une seconde copie sur un disque USB stocké séparément.

Débrancher le disque USB après la copie réduit le risque qu'un rançongiciel
chiffre simultanément les données actives et leur sauvegarde.

## Limites actuelles

Ce lot ne remplace pas une sauvegarde distante automatisée. Lorsque le budget
sera disponible, une copie chiffrée hors site devra être ajoutée. En attendant,
la copie régulière sur un disque externe reste indispensable.
