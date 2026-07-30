# Sauvegarde et restauration Mbolo

## Périmètre

La sauvegarde complète contient :

- PostgreSQL, qui stocke les comptes, profils, matchs et messages ;
- les médias publics approuvés ;
- les médias privés de vérification ;
- les sommes de contrôle SHA-256 ;
- des métadonnées techniques non sensibles.

Redis et les fichiers statiques ne sont pas sauvegardés :

- Redis contient des états temporaires et peut être reconstruit ;
- les fichiers statiques sont reconstruits depuis le code source.

## Créer une sauvegarde

Depuis la racine du projet :

```bash
bash scripts/backup-mbolo.sh
```

La sauvegarde est créée dans :

```text
backups/mbolo-YYYYMMDDTHHMMSSZ/
```

Les permissions sont restrictives :

- dossier : accessible uniquement par le propriétaire ;
- fichiers : lecture et écriture uniquement par le propriétaire.

## Vérifier une sauvegarde

Contrôle simple :

```bash
bash scripts/verify-backup.sh backups/mbolo-YYYYMMDDTHHMMSSZ
```

Test de restauration isolé :

```bash
bash scripts/verify-backup.sh \
  backups/mbolo-YYYYMMDDTHHMMSSZ \
  --restore-test
```

Le test isolé crée une base temporaire, y restaure le dump, vérifie les
tables puis supprime uniquement cette base temporaire. La base active reste
inchangée.

## Restaurer Mbolo

```bash
bash scripts/restore-mbolo.sh backups/mbolo-YYYYMMDDTHHMMSSZ
```

Le script :

1. vérifie SHA-256 et les archives ;
2. crée une sauvegarde de sécurité de l’état actuel ;
3. exige la phrase exacte `RESTAURER MBOLO` ;
4. arrête le frontend et le backend ;
5. restaure PostgreSQL et les médias ;
6. redémarre les services.

## Sécurité et conformité

- `.env.production` n’est jamais copié.
- Les mots de passe ne sont jamais affichés.
- Le dump n’expose pas les propriétaires et privilèges PostgreSQL.
- Une sauvegarde incomplète reste dans un dossier temporaire caché.
- Le nom définitif n’est attribué qu’après validation.
- Les sauvegardes sont exclues de Git.

Une copie hors du PC reste obligatoire. Cette copie devra être chiffrée et
soumise à une politique de rétention documentée avant la production.
