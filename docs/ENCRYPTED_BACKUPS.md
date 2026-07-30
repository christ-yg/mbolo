# Copies chiffrées des sauvegardes Mbolo

## Créer une copie chiffrée

```bash
bash scripts/encrypt-backup.sh \
  backups/mbolo-YYYYMMDDTHHMMSSZ
```

La commande produit deux fichiers :

```text
encrypted-backups/mbolo-YYYYMMDDTHHMMSSZ.tar.gz.gpg
encrypted-backups/mbolo-YYYYMMDDTHHMMSSZ.tar.gz.gpg.sha256
```

Les deux fichiers doivent être copiés ensemble vers le stockage externe.

## Phrase secrète

La phrase secrète doit :

- être longue et unique ;
- être conservée dans un gestionnaire de mots de passe ;
- ne jamais être enregistrée dans Git, `.env.production` ou un message ;
- être accessible à la personne officiellement responsable de la
  restauration selon la procédure de continuité.

Sans cette phrase, aucune restauration n'est possible.

## Vérifier une copie récupérée

```bash
bash scripts/verify-encrypted-backup.sh \
  encrypted-backups/mbolo-YYYYMMDDTHHMMSSZ.tar.gz.gpg
```

La vérification ne décompresse aucune donnée sur le disque.

## Copie externe

Après vérification, téléverser le fichier `.gpg` et son fichier `.sha256`
dans Google Drive, OneDrive ou un support externe contrôlé.

Le fournisseur de stockage ne reçoit qu'un contenu chiffré. Il ne reçoit
pas la phrase secrète.

## Limites

Une copie conservée uniquement sur le même PC ne protège pas contre :

- le vol du PC ;
- la destruction du disque ;
- un rançongiciel ;
- un sinistre physique.

Au moins une copie chiffrée hors site est donc obligatoire avant la mise
en production.
